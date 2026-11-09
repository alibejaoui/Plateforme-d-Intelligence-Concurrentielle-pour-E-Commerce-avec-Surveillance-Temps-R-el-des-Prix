from __future__ import annotations

from typing import Any
import re
import random
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests import Response
from requests.exceptions import RequestException, Timeout

from app.core.logging import get_logger


logger = get_logger(__name__)


class CatalogAdapterError(RuntimeError):
    def __init__(self, message: str, *, url: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code


class CatalogBlockedError(CatalogAdapterError):
    pass


class BaseCatalogAdapter:
    platform = "generic"

    def __init__(self, config: dict[str, Any]):
        self.config = config or {}
        self.catalog_cfg = self.config.get("catalog") or {}
        self.base_url = (self.catalog_cfg.get("base_url") or self.config.get("base_url") or "").rstrip("/") + "/"
        self.headers = self.catalog_cfg.get("headers") or self.config.get("headers") or {}
        self.timeout_s = int(self.catalog_cfg.get("timeout_s", 25))
        self.retry_count = int(self.catalog_cfg.get("retry_count", 3))
        self.backoff_base_s = float(self.catalog_cfg.get("backoff_base_s", 0.5))
        self.retryable_status_codes = set(self.catalog_cfg.get("retryable_status_codes") or [408, 425, 429, 500, 502, 503, 504])
        self.rate_limit_per_minute = int(self.catalog_cfg.get("rate_limit_per_minute") or 0)
        self.block_detection_patterns = [
            re.compile(p, re.I)
            for p in (
                self.catalog_cfg.get("block_detection_patterns")
                or [r"captcha", r"access denied", r"temporarily blocked", r"verify you are human"]
            )
        ]
        self.user_agents = self.catalog_cfg.get("user_agents") or self.config.get("user_agents") or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123 Safari/537.36",
        ]
        self.session = requests.Session()
        self._last_request_at = 0.0
        self.metrics = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "retries": 0,
            "total_response_time_ms": 0.0,
            "blocked": 0,
        }

    def _normalize_url(self, url: str | None) -> str | None:
        if not url:
            return None
        raw = str(url).strip()
        if not raw:
            return None
        abs_url = urljoin(self.base_url, raw)
        p = urlparse(abs_url)
        if p.scheme not in {"http", "https"} or not p.netloc:
            return None
        return abs_url

    def fetch_html(self, url: str) -> str:
        normalized = self._normalize_url(url)
        if not normalized:
            raise ValueError(f"Invalid URL for fetch_html: {url!r}")
        resp = self._request_with_retries(normalized)
        resp.encoding = resp.apparent_encoding or resp.encoding
        if self._looks_blocked(resp.text):
            self.metrics["blocked"] += 1
            raise CatalogBlockedError("Blocked/captcha page detected", url=normalized, status_code=resp.status_code)
        return resp.text

    def _rate_limit(self) -> None:
        if self.rate_limit_per_minute <= 0:
            return
        min_interval = 60.0 / max(1, self.rate_limit_per_minute)
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _headers_for_request(self) -> dict[str, str]:
        headers = dict(self.headers)
        headers.setdefault("User-Agent", random.choice(self.user_agents))
        headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        headers.setdefault("Accept-Language", "fr-FR,fr;q=0.9,en;q=0.8")
        return headers

    def _request_with_retries(self, url: str) -> Response:
        last_error: Exception | None = None
        for attempt in range(self.retry_count + 1):
            self._rate_limit()
            started = time.monotonic()
            self.metrics["requests"] += 1
            try:
                response = self.session.get(url, headers=self._headers_for_request(), timeout=self.timeout_s)
                self._last_request_at = time.monotonic()
                elapsed_ms = (time.monotonic() - started) * 1000.0
                self.metrics["total_response_time_ms"] += elapsed_ms
                if response.status_code in {403, 429}:
                    self.metrics["blocked"] += 1
                    if attempt >= self.retry_count:
                        raise CatalogBlockedError(
                            f"Request blocked with HTTP {response.status_code}",
                            url=url,
                            status_code=response.status_code,
                        )
                if response.status_code in self.retryable_status_codes and attempt < self.retry_count:
                    self.metrics["retries"] += 1
                    time.sleep(self.backoff_base_s * (2 ** attempt))
                    continue
                response.raise_for_status()
                self.metrics["successes"] += 1
                logger.info(
                    "catalog_fetch_success",
                    extra={"url": url, "status_code": response.status_code, "elapsed_ms": round(elapsed_ms, 2)},
                )
                return response
            except Timeout as exc:
                last_error = exc
            except CatalogBlockedError:
                raise
            except RequestException as exc:
                last_error = exc
            self.metrics["failures"] += 1
            if attempt < self.retry_count:
                self.metrics["retries"] += 1
                time.sleep(self.backoff_base_s * (2 ** attempt))
        raise CatalogAdapterError(f"Failed to fetch {url}: {last_error}", url=url)

    def _looks_blocked(self, html: str) -> bool:
        sample = html[:5000]
        return any(pattern.search(sample) for pattern in self.block_detection_patterns)

    def health_status(self) -> dict[str, Any]:
        requests_count = max(1, int(self.metrics["requests"]))
        return {
            **self.metrics,
            "success_rate": self.metrics["successes"] / requests_count,
            "average_response_time_ms": self.metrics["total_response_time_ms"] / requests_count,
            "status": "blocked" if self.metrics["blocked"] else "healthy",
        }

    def discover_product_urls(self, seed_urls: list[str]) -> list[str]:
        max_pages = int(self.catalog_cfg.get("max_pages", 200))
        max_urls = int(self.catalog_cfg.get("max_urls", 50_000))
        product_link_selector = self.catalog_cfg.get("product_link_selector") or "a[href]"
        product_link_attr = self.catalog_cfg.get("product_link_attr") or "href"
        product_url_regex = self.catalog_cfg.get("product_url_regex")
        next_page_selector = self.catalog_cfg.get("next_page_selector")
        next_page_attr = self.catalog_cfg.get("next_page_attr") or "href"
        rx = re.compile(product_url_regex) if product_url_regex else None

        discovered: set[str] = set()
        for seed in seed_urls:
            page_url = self._normalize_url(seed)
            if not page_url:
                continue
            pages = 0
            while page_url and pages < max_pages and len(discovered) < max_urls:
                pages += 1
                try:
                    html = self.fetch_html(page_url)
                except CatalogAdapterError as exc:
                    logger.warning(
                        "catalog_discovery_page_failed",
                        extra={"url": page_url, "error": str(exc), "status_code": getattr(exc, "status_code", None)},
                    )
                    page_url = None
                    continue
                soup = BeautifulSoup(html, "lxml")
                for el in soup.select(product_link_selector):
                    href = el.get(product_link_attr)
                    if not href:
                        continue
                    u = self._normalize_url(href)
                    if not u:
                        continue
                    if rx and not rx.search(u):
                        continue
                    discovered.add(u)
                    if len(discovered) >= max_urls:
                        break
                next_url = None
                if next_page_selector:
                    next_el = soup.select_one(next_page_selector)
                    if next_el:
                        href = next_el.get(next_page_attr)
                        if href:
                            next_url = self._normalize_url(href)
                page_url = next_url
        return list(discovered)

    def extract_product(self, url: str) -> dict[str, Any]:
        normalized_url = self._normalize_url(url)
        if not normalized_url:
            raise ValueError(f"Invalid product URL: {url!r}")
        html = self.fetch_html(normalized_url)
        soup = BeautifulSoup(html, "lxml")
        title_selector = self.catalog_cfg.get("title_selector") or self.config.get("title_selector")
        price_selector = self.catalog_cfg.get("price_selector") or self.config.get("price_selector")
        availability_selector = self.catalog_cfg.get("availability_selector") or self.config.get("availability_selector")
        image_selector = self.catalog_cfg.get("image_selector")
        brand_selector = self.catalog_cfg.get("brand_selector")
        sku_selector = self.catalog_cfg.get("sku_selector")
        gtin_selector = self.catalog_cfg.get("gtin_selector")
        category_selector = self.catalog_cfg.get("category_selector")

        def txt(sel: str | None) -> str | None:
            if not sel:
                return None
            el = soup.select_one(sel)
            if not el:
                return None
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() or None

        def attr(sel: str | None, k: str) -> str | None:
            if not sel:
                return None
            el = soup.select_one(sel)
            if not el:
                return None
            v = (el.get(k) or "").strip()
            return v or None

        title = txt(title_selector)
        if not title:
            h1 = soup.find("h1")
            title = (h1.get_text(" ", strip=True) if h1 else None) or (soup.title.text.strip() if soup.title else None)
        price_text = txt(price_selector)
        price = None
        if price_text:
            m = re.search(r"(-?\d+(?:[.,]\d{1,2})?)", price_text.replace("\xa0", " "))
            if m:
                try:
                    price = float(m.group(1).replace(",", "."))
                except Exception:
                    price = None
        return {
            "title": title,
            "price": price,
            "currency": self.catalog_cfg.get("currency") or self.config.get("currency"),
            "availability": txt(availability_selector),
            "image_url": attr(image_selector, "src"),
            "brand": txt(brand_selector),
            "sku": txt(sku_selector),
            "gtin": txt(gtin_selector),
            "category": txt(category_selector),
            "url": normalized_url,
        }

