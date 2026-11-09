"""Database models"""
from app.models.base import Base, BaseModel
from app.models.user import User
from app.models.product import Product
from app.models.competitor import Competitor
from app.models.price import Price
from app.models.alert import Alert
from app.models.scraping_job import ScrapingJob
from app.models.source import Source
from app.models.catalog_source import CatalogSource
from app.models.import_job import ImportJob
from app.models.internal_product import InternalProduct
from app.models.competitor_product import CompetitorProduct
from app.models.crawl_session import CrawlSession, CrawlSessionItem, CrawlError
from app.models.product_match import ProductMatch
from app.models.missing_detection import MissingProduct, UnmatchedInternalProduct
from app.models.alert_rule import AlertRule
from app.models.competitive_alert import CompetitiveAlert

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Product",
    "Competitor",
    "Price",
    "Alert",
    "ScrapingJob",
    "Source",
    "CatalogSource",
    "ImportJob",
    "InternalProduct",
    "CompetitorProduct",
    "CrawlSession",
    "CrawlSessionItem",
    "CrawlError",
    "ProductMatch",
    "MissingProduct",
    "UnmatchedInternalProduct",
    "AlertRule",
    "CompetitiveAlert",
]

