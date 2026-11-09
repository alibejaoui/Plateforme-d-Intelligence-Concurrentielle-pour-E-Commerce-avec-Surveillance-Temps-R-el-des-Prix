"""
Scraper engine base class
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class ScraperEngine(ABC):
    """Base class for scraper engines"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def scrape_product(self, product_url: str, product_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scrape a single product
        
        Returns:
            Dict with keys: price, availability, url, scraped_at
        """
        pass
    
    @abstractmethod
    def scrape_search_results(self, search_query: str, max_results: int = 10) -> list[Dict[str, Any]]:
        """
        Scrape search results
        
        Returns:
            List of product dictionaries
        """
        pass
    
    def validate_price(self, price: Any) -> Optional[float]:
        """Validate and normalize price"""
        try:
            if isinstance(price, str):
                # Remove currency symbols and whitespace
                price = (
                    price.replace("€", "")
                    .replace("$", "")
                    .replace("TND", "")
                    .replace("DT", "")
                    .replace("\xa0", " ")
                    .replace(",", ".")
                    .strip()
                )
            return float(price)
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid price format: {price}")
            return None
    
    def normalize_availability(self, availability: str) -> str:
        """Normalize availability status"""
        availability_lower = availability.lower()
        if any(word in availability_lower for word in ["in stock", "available", "en stock"]):
            return "in_stock"
        elif any(word in availability_lower for word in ["out of stock", "unavailable", "rupture"]):
            return "out_of_stock"
        elif any(word in availability_lower for word in ["preorder", "pre-order", "précommande"]):
            return "preorder"
        else:
            return "unknown"

