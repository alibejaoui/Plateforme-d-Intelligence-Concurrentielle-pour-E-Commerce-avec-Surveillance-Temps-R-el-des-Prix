"""
Scraping manager for orchestrating scraping operations
"""

import json
import re
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from bs4 import BeautifulSoup

from app.models.competitor import Competitor
from app.models.product import Product
from app.models.price import Price
from app.models.scraping_job import ScrapingJob, JobStatus
from app.scraping.scraper_engine import ScraperEngine
from app.core.logging import get_logger
from app.services.alert_service import AlertService
from app.scraping.simple_soup_scraper import BeautifulSoupScraper

logger = get_logger(__name__)


class ScrapingManager:
    """Manager for scraping operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger

    def _build_scraper_config(self, competitor: Competitor) -> Dict[str, Any]:
        """
        Normalize legacy single-product config and the newer `catalog` config
        into the flat shape expected by BeautifulSoupScraper.
        """
        config: Dict[str, Any] = {}
        if competitor.scraping_config:
            try:
                parsed = json.loads(competitor.scraping_config)
                config = parsed if isinstance(parsed, dict) else {}
            except Exception:
                self.logger.warning("Invalid competitor.scraping_config JSON; using defaults")
                config = {}

        catalog_config = config.get("catalog") if isinstance(config.get("catalog"), dict) else {}
        normalized: Dict[str, Any] = {**config, **catalog_config}
        normalized.setdefault("base_url", competitor.base_url or competitor.website_url)

        # Some configs are written for catalogue extraction. Reuse their detail
        # selectors for single product scraping.
        for key in [
            "price_selector",
            "availability_selector",
            "currency",
            "headers",
            "user_agents",
            "timeout_s",
            "retry_count",
            "backoff_base_s",
            "rate_limit_per_minute",
        ]:
            if key not in normalized and key in catalog_config:
                normalized[key] = catalog_config[key]

        return normalized
    
    def scrape_product(
        self,
        competitor_id: int,
        product_id: int,
        scraper: Optional[ScraperEngine] = None,
    ) -> Dict[str, Any]:
        """Scrape a single product"""
        try:
            # Get product and competitor
            product = self.db.query(Product).filter(Product.id == product_id).first()
            competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
            
            if not product or not competitor:
                raise ValueError("Product or competitor not found")

            # Instantiate scraper when not provided (default to BeautifulSoupScraper)
            if scraper is None:
                scraper = BeautifulSoupScraper(config=self._build_scraper_config(competitor))

            # 1) Try listing-page extraction directly (webscraper test-site style)
            scraped_data: Dict[str, Any] = {}
            if isinstance(scraper, BeautifulSoupScraper) and scraper.base_url:
                html = scraper._fetch(scraper.base_url)
                soup = BeautifulSoup(html, "lxml")
                card_selector = scraper.config.get("listing_card_selector") or scraper.config.get("product_card_selector") or "div.thumbnail"
                title_selector = scraper.config.get("listing_title_selector") or "a.title"
                listing_price_selector = scraper.config.get("listing_price_selector") or "h4.price"
                products = soup.select(card_selector)
                db_product_name = (product.name or "").strip().lower()
                db_tokens = [t for t in re.split(r"\s+", db_product_name) if t]
                best_match = None
                best_score = -1

                for p in products:
                    title_el = p.select_one(title_selector)
                    price_el = p.select_one(listing_price_selector)
                    if not title_el or not price_el:
                        continue

                    title = title_el.get_text(strip=True).lower()
                    if not title:
                        continue

                    # Prefer exact title; otherwise pick the card with highest token overlap.
                    if db_product_name and title == db_product_name:
                        score = 10_000
                    else:
                        score = sum(1 for tok in db_tokens if tok in title)
                    if score <= 0:
                        continue

                    if score > best_score:
                        best_score = score
                        best_match = (title_el, price_el)

                if best_match:
                    title_el, price_el = best_match
                    price_text = price_el.get_text(strip=True)
                    # Keep decimal dot and thousands commas safe: "$1,769.00" -> "1769.00"
                    clean = re.sub(r"[^\d,.\-]", "", price_text).replace(",", "")
                    price = float(clean)
                    scraped_data = {
                        "price": price,
                        "url": title_el.get("href"),
                        "currency": "USD",
                    }

            # 2) Fallback to existing generic scraping logic if listing match not found
            if not scraped_data:
                search_results = scraper.scrape_search_results(
                    search_query=product.name, max_results=5
                )
                if not search_results:
                    return {"success": False, "error": "No product URL found in search"}

                product_url = search_results[0]["url"]
                scraped_data = scraper.scrape_product(
                    product_url=product_url,
                    product_data={"name": product.name, "sku": product.sku},
                )

            scraped_price = scraped_data.get("price")
            if scraped_data and scraped_price is not None:
                # Create price record
                new_price = Price(
                    product_id=product_id,
                    competitor_id=competitor_id,
                    price=float(scraped_price),
                    currency=scraped_data.get("currency", "EUR"),
                    availability=scraped_data.get("availability"),
                    url=scraped_data.get("url"),
                    scraped_at=datetime.utcnow(),
                )
                self.db.add(new_price)
                self.db.commit()

                # Trigger alerts on threshold
                AlertService.check_price_thresholds(
                    self.db, product_id, float(scraped_price)
                )

                return {
                    "success": True,
                    "price": float(scraped_price),
                    "availability": scraped_data.get("availability"),
                    "url": scraped_data.get("url"),
                }

            return {"success": False, "error": "No price data scraped"}
        
        except Exception as e:
            self.logger.error(f"Error scraping product {product_id}: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_job_status(
        self,
        job_id: int,
        status: JobStatus,
        error_message: Optional[str] = None,
        result_data: Optional[Dict] = None
    ):
        """Update scraping job status"""
        job = self.db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            if result_data:
                job.result_data = result_data
            if status == JobStatus.RUNNING:
                job.started_at = datetime.utcnow()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job.completed_at = datetime.utcnow()
            
            self.db.commit()
