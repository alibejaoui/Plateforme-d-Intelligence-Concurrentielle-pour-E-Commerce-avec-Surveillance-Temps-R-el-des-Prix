from __future__ import annotations

import re
import random
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from app.scraping.scraper_engine import ScraperEngine


DEFAULT_SEARCH_URL_TEMPLATE = "{base_url}/search?q={query}"
DEFAULT_PRICE_REGEX = r"(\d+(?:[.,]\d{1,2})?)"


class BeautifulSoupScraper(ScraperEngine):
    """
    Scraper générique (débutant-friendly) basé sur BeautifulSoup:
    - construit une URL de recherche à partir de `search_url_template`
    - choisit le 1er lien "product" (heuristique)
    - extrait un prix via selector CSS ou regex sur le HTML
    - optionnellement extrait availability

    Le but est que le pipeline scraping -> prices -> alerts fonctionne,
    même si `scraping_config` est vide (on fournit des defaults).
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config=config)

        self.base_url: str = config.get("base_url", "").rstrip("/")

        # Search
        self.search_url_template: str = config.get(
            "search_url_template", DEFAULT_SEARCH_URL_TEMPLATE
        )
        self.link_selector: Optional[str] = config.get("link_selector")

        # Price
        self.price_selector: Optional[str] = config.get("price_selector")
        self.price_regex: str = config.get("price_regex", DEFAULT_PRICE_REGEX)
        self.currency: str = config.get("currency", "EUR")
        self.timeout_s: int = int(config.get("timeout_s", 30))
        self.user_agents: list[str] = config.get("user_agents") or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 Safari/605.1.15",
        ]

        # Availability
        self.availability_selector: Optional[str] = config.get(
            "availability_selector"
        )
        self.availability_regex: Optional[str] = config.get("availability_regex")

    def _fetch(self, url: str) -> str:
        headers = dict(self.config.get("headers") or {})
        headers.setdefault("User-Agent", random.choice(self.user_agents))
        headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        resp = requests.get(url, headers=headers, timeout=self.timeout_s)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or resp.encoding
        return resp.text

    def scrape_search_results(
        self, search_query: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        if not self.base_url:
            return []

        search_url = self.search_url_template.format(
            base_url=self.base_url, query=quote(search_query)
        )

        html = self._fetch(search_url)
        soup = BeautifulSoup(html, "lxml")

        if self.link_selector:
            anchors = soup.select(self.link_selector)
        else:
            anchors = soup.select("a[href]")

        results: List[Dict[str, Any]] = []

        # Heuristique: le "premier lien" est suffisant pour démarrer.
        for a in anchors:
            href = a.get("href")
            if not href:
                continue
            if href.startswith("javascript:") or href.startswith("#"):
                continue

            href_l = href.lower()
            text_l = (a.get_text() or "").lower()
            q_l = search_query.lower().strip()
            q_token = q_l.split()[0] if q_l else ""

            likely_product = any(
                token in href_l
                for token in [
                    "product",
                    "/p/",
                    "/dp/",
                    "/item/",
                    "/details",
                    "article",
                ]
            )

            if self.link_selector or likely_product or (q_token and q_token in text_l):
                full_url = urljoin(self.base_url + "/", href)
                results.append({"url": full_url})
            else:
                # fallback: si rien d'autre ne marche, on garde aussi des candidats
                # mais on les ajoute à la fin de la liste.
                if len(results) < 1:
                    full_url = urljoin(self.base_url + "/", href)
                    results.append({"url": full_url})

            if len(results) >= max_results:
                break

        return results

    def scrape_product(
        self, product_url: str, product_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        html = self._fetch(product_url)
        soup = BeautifulSoup(html, "lxml")

        price_value: Optional[float] = None
        availability: Optional[str] = None

        # Price extraction: selector CSS > regex fallback
        if self.price_selector:
            el = soup.select_one(self.price_selector)
            if el:
                text = el.get_text(" ", strip=True)
                m = re.search(self.price_regex, text)
                if m:
                    price_value = self.validate_price(m.group(1))
        if price_value is None:
            text = soup.get_text(" ", strip=True)
            m = re.search(self.price_regex, text)
            if m:
                price_value = self.validate_price(m.group(1))

        # Availability extraction (optional)
        if self.availability_selector:
            el2 = soup.select_one(self.availability_selector)
            if el2:
                availability_text = el2.get_text(" ", strip=True)
                availability = self.normalize_availability(availability_text)
        elif self.availability_regex:
            text_l = soup.get_text(" ", strip=True).lower()
            m2 = re.search(self.availability_regex, text_l)
            if m2:
                availability = self.normalize_availability(m2.group(0))

        # If price doesn't parse, return it as None so caller can decide.
        return {
            "price": price_value,
            "currency": self.currency,
            "availability": availability,
            "url": product_url,
        }

