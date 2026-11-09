"""
Catalog import service (sitemap/feed/crawl) that populates internal_products.
"""

from __future__ import annotations

import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Iterable, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.catalog_source import CatalogSource
from app.models.import_job import ImportJob, ImportJobStatus
from app.models.internal_product import InternalProduct
from app.models.product import Product

logger = get_logger(__name__)


DEFAULT_TIMEOUT_S = 20


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _safe_json_dumps(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return "{}"


@dataclass(frozen=True)
class CatalogItem:
    name: str
    url: str
    brand: Optional[str] = None
    sku: Optional[str] = None
    gtin: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    availability: Optional[str] = None
    description: Optional[str] = None


class CatalogImportService:
    def __init__(self, db: Session):
        self.db = db
        self._warnings: list[dict[str, str]] = []

    def get_or_create_source(self, user_id: int, source_type: str, source_url: str, name: str | None, config: dict | None) -> CatalogSource:
        source = (
            self.db.query(CatalogSource)
            .filter(
                CatalogSource.user_id == user_id,
                CatalogSource.source_type == source_type,
                CatalogSource.source_url == source_url,
            )
            .first()
        )
        if source:
            # update mutable metadata
            if name:
                source.name = name
            if config is not None:
                source.config = _safe_json_dumps(config)
            self.db.commit()
            self.db.refresh(source)
            return source

        source = CatalogSource(
            user_id=user_id,
            source_type=source_type,
            source_url=source_url,
            name=name,
            config=_safe_json_dumps(config) if config is not None else None,
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def create_job(self, user_id: int, source: CatalogSource) -> ImportJob:
        job = ImportJob(user_id=user_id, catalog_source_id=source.id, status=ImportJobStatus.PENDING)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def run_job(self, job_id: int) -> dict:
        job = self.db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            raise ValueError("ImportJob not found")

        source = self.db.query(CatalogSource).filter(CatalogSource.id == job.catalog_source_id).first()
        if not source:
            raise ValueError("CatalogSource not found")

        config = self._parse_config(source.config)
        timeout_s = int(config.get("timeout_s", DEFAULT_TIMEOUT_S))
        user_agent = config.get("user_agent")
        max_items = int(config.get("max_items", 50_000))
        url_filter_regex = config.get("url_filter_regex")
        include_regex = re.compile(url_filter_regex) if url_filter_regex else None

        job.mark_running()
        self.db.commit()

        self._warnings = []
        created = 0
        updated = 0
        skipped = 0
        errors: list[str] = []

        try:
            items: list[CatalogItem]
            if source.source_type == "sitemap":
                items = self._load_from_sitemap(
                    source.source_url,
                    timeout_s=timeout_s,
                    user_agent=user_agent,
                    include_regex=include_regex,
                    max_urls=max_items,
                )
            elif source.source_type == "feed":
                try:
                    items = self._load_from_feed(
                        source.source_url,
                        timeout_s=timeout_s,
                        user_agent=user_agent,
                        max_items=max_items,
                    )
                except Exception as e:
                    self._warn("feed_parse", source.source_url, str(e))
                    items = []
            elif source.source_type == "crawl":
                # Placeholder: will be implemented when category crawling fallback is wired.
                items = []
            else:
                raise ValueError(f"Unknown source_type: {source.source_type}")

            for idx, item in enumerate(items):
                if idx >= max_items:
                    break
                try:
                    res = self._upsert_internal_product(user_id=job.user_id, item=item)
                    if res == "created":
                        created += 1
                    elif res == "updated":
                        updated += 1
                    else:
                        skipped += 1
                except Exception as e:
                    skipped += 1
                    errors.append(str(e))
                    if len(errors) > 50:
                        break

            stats = {
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "errors_sample": errors[:20],
                "source_type": source.source_type,
                "source_url": source.source_url,
                "warnings_count": len(self._warnings),
                "warnings_sample": self._warnings[:30],
                "completion_state": "completed_with_errors" if (errors or self._warnings) else "completed",
            }
            job.mark_completed(stats=stats)
            self.db.commit()
            return stats
        except Exception as e:
            context = f"source_type={source.source_type} source_url={source.source_url}"
            job.mark_failed(f"{context} :: {str(e)}")
            self.db.commit()
            raise

    def _warn(self, stage: str, url: str | None, message: str) -> None:
        msg = (message or "").strip()
        row = {"stage": stage, "url": url or "", "message": msg[:500]}
        self._warnings.append(row)
        logger.warning("catalog_import warning stage=%s url=%s msg=%s", stage, url, msg)

    def _load_from_html_catalog_fallback(
        self,
        page_url: str,
        html_text: str,
        *,
        include_regex: re.Pattern[str] | None,
        max_urls: int,
    ) -> list[CatalogItem]:
        """
        Fallback mode when sitemap/feed content is HTML (or malformed XML).
        Extract candidate product links instead of failing the whole import.
        """
        self._warn("sitemap_fallback_html", page_url, "Non-XML content detected; using HTML link extraction fallback")

        soup = BeautifulSoup(html_text, "html.parser")
        host = urlparse(page_url).netloc
        seen: set[str] = set()
        items: list[CatalogItem] = []

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            u = urljoin(page_url, href)
            if not u.startswith("http"):
                continue
            # Keep links on same host for safety.
            if host and urlparse(u).netloc and urlparse(u).netloc != host:
                continue
            if include_regex and not include_regex.search(u):
                continue
            # Product heuristics (webscraper demo and common ecommerce URL patterns).
            ul = u.lower()
            likely_product = any(
                token in ul for token in ["/product/", "/products/", "/item/", "/p/", "/dp/"]
            ) or ("title" in ((a.get("class") and " ".join(a.get("class"))) or "").lower())
            if not likely_product:
                continue
            if u in seen:
                continue
            seen.add(u)
            name = _normalize_whitespace(a.get_text(" ", strip=True)) or u
            items.append(CatalogItem(name=name, url=u))
            if len(items) >= max_urls:
                break

        # Last-resort: if heuristic found nothing, keep unique same-host links so import can still progress.
        if not items:
            for a in soup.select("a[href]"):
                href = (a.get("href") or "").strip()
                if not href:
                    continue
                u = urljoin(page_url, href)
                if not u.startswith("http"):
                    continue
                if host and urlparse(u).netloc and urlparse(u).netloc != host:
                    continue
                if include_regex and not include_regex.search(u):
                    continue
                if u in seen:
                    continue
                seen.add(u)
                name = _normalize_whitespace(a.get_text(" ", strip=True)) or u
                items.append(CatalogItem(name=name, url=u))
                if len(items) >= max_urls:
                    break

        return items

    def _parse_config(self, raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            val = json.loads(raw)
            return val if isinstance(val, dict) else {}
        except Exception:
            return {}

    def _http_get_text(self, url: str, timeout_s: int, user_agent: str | None) -> str:
        headers = {}
        if user_agent:
            headers["User-Agent"] = user_agent
        resp = requests.get(url, timeout=timeout_s, headers=headers)
        resp.raise_for_status()
        return resp.text

    def _load_from_sitemap(
        self,
        sitemap_url: str,
        *,
        timeout_s: int,
        user_agent: str | None,
        include_regex: re.Pattern[str] | None,
        max_urls: int,
        _depth: int = 0,
    ) -> list[CatalogItem]:
        if _depth > 3:
            return []

        try:
            xml_text = self._http_get_text(sitemap_url, timeout_s=timeout_s, user_agent=user_agent)
        except Exception as e:
            self._warn("sitemap_fetch", sitemap_url, str(e))
            return []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            self._warn("sitemap_xml_parse", sitemap_url, f"{str(e)}")
            return self._load_from_html_catalog_fallback(
                sitemap_url,
                xml_text,
                include_regex=include_regex,
                max_urls=max_urls,
            )

        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        urls: list[str] = []
        sitemaps: list[str] = []

        if root.tag.endswith("sitemapindex"):
            for sm in root.findall(f"{ns}sitemap/{ns}loc"):
                if sm.text:
                    sitemaps.append(sm.text.strip())
        elif root.tag.endswith("urlset"):
            for loc in root.findall(f"{ns}url/{ns}loc"):
                if loc.text:
                    urls.append(loc.text.strip())
        else:
            # Some providers return XML that is not a proper sitemap format.
            # Attempt generic <loc> extraction before falling back to HTML parsing.
            for loc in root.findall(".//{*}loc"):
                if loc.text:
                    urls.append(loc.text.strip())
            for loc in root.findall(".//loc"):
                if loc.text:
                    urls.append(loc.text.strip())
            if not urls:
                self._warn("sitemap_structure", sitemap_url, f"Unsupported root tag: {root.tag}")
                return self._load_from_html_catalog_fallback(
                    sitemap_url,
                    xml_text,
                    include_regex=include_regex,
                    max_urls=max_urls,
                )

        items: list[CatalogItem] = []
        for sm_url in sitemaps:
            if len(items) >= max_urls:
                break
            try:
                items.extend(
                    self._load_from_sitemap(
                        sm_url,
                        timeout_s=timeout_s,
                        user_agent=user_agent,
                        include_regex=include_regex,
                        max_urls=max_urls - len(items),
                        _depth=_depth + 1,
                    )
                )
            except Exception as e:
                self._warn("sitemap_child", sm_url, str(e))
                continue

        for u in urls:
            if len(items) >= max_urls:
                break
            if include_regex and not include_regex.search(u):
                continue
            # Name is not available from sitemap. We store URL now; title can be enriched later via crawl/import enhancement.
            items.append(CatalogItem(name=u, url=u))

        return items

    def _load_from_feed(self, feed_url: str, *, timeout_s: int, user_agent: str | None, max_items: int) -> list[CatalogItem]:
        # Detect CSV vs XML by extension or content
        content = self._http_get_text(feed_url, timeout_s=timeout_s, user_agent=user_agent)
        trimmed = content.lstrip()
        if trimmed.startswith("<"):
            return self._load_from_feed_xml(content, max_items=max_items)
        return self._load_from_feed_csv(content, max_items=max_items)

    def _load_from_feed_csv(self, csv_text: str, *, max_items: int) -> list[CatalogItem]:
        reader = csv.DictReader(io.StringIO(csv_text))
        items: list[CatalogItem] = []
        for i, row in enumerate(reader):
            if i >= max_items:
                break
            url = (row.get("link") or row.get("url") or "").strip()
            name = (row.get("title") or row.get("name") or url).strip()
            if not url:
                continue
            price_val = self._parse_price(row.get("price") or row.get("sale_price"))
            items.append(
                CatalogItem(
                    name=_normalize_whitespace(name),
                    url=url,
                    brand=_normalize_whitespace(row.get("brand") or "") or None,
                    sku=_normalize_whitespace(row.get("sku") or row.get("mpn") or "") or None,
                    gtin=_normalize_whitespace(row.get("gtin") or row.get("ean") or "") or None,
                    category=_normalize_whitespace(row.get("product_type") or row.get("category") or "") or None,
                    image_url=(row.get("image_link") or row.get("image_url") or "").strip() or None,
                    price=price_val,
                    currency=self._parse_currency(row.get("price") or row.get("sale_price")),
                    availability=_normalize_whitespace(row.get("availability") or "") or None,
                    description=row.get("description"),
                )
            )
        return items

    def _load_from_feed_xml(self, xml_text: str, *, max_items: int) -> list[CatalogItem]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            self._warn("feed_xml_parse", "", str(e))
            return []
        items: list[CatalogItem] = []

        # Support Google Merchant style <item> under RSS
        for i, item in enumerate(root.findall(".//item")):
            if i >= max_items:
                break

            def _t(path: str) -> str | None:
                el = item.find(path)
                return el.text.strip() if el is not None and el.text else None

            # some feeds use namespaces (e.g. g:price). Try both raw and stripped tag names.
            def _find_any(tag_names: list[str]) -> str | None:
                for name in tag_names:
                    # search by exact tag and by suffix-match
                    el = item.find(name)
                    if el is not None and el.text:
                        return el.text.strip()
                    for child in item:
                        if child.tag.endswith(name) and child.text:
                            return child.text.strip()
                return None

            url = _find_any(["link", "url"])
            title = _find_any(["title", "name"]) or url
            if not url:
                continue

            price_raw = _find_any(["price", "sale_price"])
            price_val = self._parse_price(price_raw)

            items.append(
                CatalogItem(
                    name=_normalize_whitespace(title or url),
                    url=url,
                    brand=_normalize_whitespace(_find_any(["brand"]) or "") or None,
                    sku=_normalize_whitespace(_find_any(["sku", "mpn"]) or "") or None,
                    gtin=_normalize_whitespace(_find_any(["gtin", "ean"]) or "") or None,
                    category=_normalize_whitespace(_find_any(["product_type", "category"]) or "") or None,
                    image_url=(_find_any(["image_link", "image_url"]) or "").strip() or None,
                    price=price_val,
                    currency=self._parse_currency(price_raw),
                    availability=_normalize_whitespace(_find_any(["availability"]) or "") or None,
                    description=_find_any(["description"]),
                )
            )
        return items

    def _parse_price(self, raw: str | None) -> float | None:
        if not raw:
            return None
        s = str(raw).strip()
        # "123.45 EUR" or "EUR 123.45"
        m = re.search(r"(-?\d+(?:[.,]\d+)?)", s)
        if not m:
            return None
        num = m.group(1).replace(",", ".")
        try:
            return float(num)
        except Exception:
            return None

    def _parse_currency(self, raw: str | None) -> str | None:
        if not raw:
            return None
        s = str(raw).upper()
        for cur in ["EUR", "USD", "GBP", "MAD", "CAD", "AED", "SAR"]:
            if cur in s:
                return cur
        return None

    def _upsert_internal_product(self, *, user_id: int, item: CatalogItem) -> str:
        # Prefer URL as stable key. If missing, use SKU/GTIN.
        q = self.db.query(InternalProduct).filter(InternalProduct.user_id == user_id)
        existing = None
        if item.url:
            existing = q.filter(InternalProduct.url == item.url).first()
        if existing is None and item.sku:
            existing = q.filter(InternalProduct.sku == item.sku).first()
        if existing is None and item.gtin:
            existing = q.filter(InternalProduct.gtin == item.gtin).first()

        if existing is None:
            row = InternalProduct(
                user_id=user_id,
                name=_normalize_whitespace(item.name) or item.url,
                brand=_normalize_whitespace(item.brand or "") or None,
                sku=_normalize_whitespace(item.sku or "") or None,
                gtin=_normalize_whitespace(item.gtin or "") or None,
                category=_normalize_whitespace(item.category or "") or None,
                url=item.url,
                image_url=item.image_url,
                price=item.price,
                currency=item.currency or "EUR",
                availability=item.availability,
                description=item.description,
            )
            self.db.add(row)
            self.db.flush()
            # Keep legacy `products` (price history) in sync for CI historical intelligence.
            self._upsert_legacy_product(user_id=user_id, item=item)
            return "created"

        changed = False
        # Update only when provided and different
        for field, value in [
            ("name", _normalize_whitespace(item.name) if item.name else None),
            ("brand", _normalize_whitespace(item.brand or "") or None),
            ("sku", _normalize_whitespace(item.sku or "") or None),
            ("gtin", _normalize_whitespace(item.gtin or "") or None),
            ("category", _normalize_whitespace(item.category or "") or None),
            ("image_url", item.image_url),
            ("price", item.price),
            ("currency", item.currency),
            ("availability", item.availability),
            ("description", item.description),
        ]:
            if value is None:
                continue
            if getattr(existing, field) != value:
                setattr(existing, field, value)
                changed = True

        if changed:
            self.db.flush()
            # Keep legacy `products` in sync for CI historical intelligence.
            self._upsert_legacy_product(user_id=user_id, item=item)
            return "updated"
        return "skipped"

    def _upsert_legacy_product(self, *, user_id: int, item: CatalogItem) -> None:
        """
        Legacy mapping: internal_products <-> products (required by Price history table).

        We do best-effort upsert based on SKU first, then GTIN.
        """
        sku = _normalize_whitespace(item.sku or "") or None
        gtin = _normalize_whitespace(item.gtin or "") or None

        if not sku and not gtin:
            return

        # SKU is globally unique in the legacy schema.
        legacy = None
        if sku:
            legacy = self.db.query(Product).filter(Product.sku == sku).first()
            if legacy and legacy.user_id != user_id:
                # Avoid cross-tenant edits that would violate data integrity.
                return

        if legacy is None and gtin:
            legacy = (
                self.db.query(Product)
                .filter(Product.user_id == user_id, Product.gtin == gtin)
                .first()
            )

        if legacy is None:
            legacy = Product(
                name=_normalize_whitespace(item.name) or item.url,
                description=item.description,
                sku=sku,
                gtin=gtin,
                category=_normalize_whitespace(item.category or "") or None,
                brand=_normalize_whitespace(item.brand or "") or None,
                image_url=item.image_url,
                user_id=user_id,
            )
            self.db.add(legacy)
            self.db.flush()
            return

        # Update existing legacy product.
        if item.name:
            legacy.name = _normalize_whitespace(item.name)
        if item.description is not None:
            legacy.description = item.description
        if sku is not None:
            legacy.sku = sku
        if gtin is not None:
            legacy.gtin = gtin
        if item.category is not None:
            legacy.category = _normalize_whitespace(item.category or "") or None
        if item.brand is not None:
            legacy.brand = _normalize_whitespace(item.brand or "") or None
        if item.image_url is not None:
            legacy.image_url = item.image_url
        self.db.flush()

