"""
System metrics collection
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime, timedelta

from app.models.product import Product
from app.models.competitor import Competitor
from app.models.price import Price
from app.models.scraping_job import ScrapingJob, JobStatus


def get_system_metrics(db: Session) -> Dict[str, Any]:
    """Get system metrics"""
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    # Product metrics
    total_products = db.query(func.count(Product.id)).scalar()
    
    # Competitor metrics
    total_competitors = db.query(func.count(Competitor.id)).scalar()
    active_competitors = db.query(func.count(Competitor.id)).filter(
        Competitor.is_active == True
    ).scalar()
    
    # Price metrics
    total_prices = db.query(func.count(Price.id)).scalar()
    prices_last_24h = db.query(func.count(Price.id)).filter(
        Price.created_at >= last_24h
    ).scalar()
    
    # Scraping job metrics
    total_jobs = db.query(func.count(ScrapingJob.id)).scalar()
    jobs_last_24h = db.query(func.count(ScrapingJob.id)).filter(
        ScrapingJob.created_at >= last_24h
    ).scalar()
    running_jobs = db.query(func.count(ScrapingJob.id)).filter(
        ScrapingJob.status == JobStatus.RUNNING
    ).scalar()
    failed_jobs_24h = db.query(func.count(ScrapingJob.id)).filter(
        ScrapingJob.status == JobStatus.FAILED,
        ScrapingJob.created_at >= last_24h
    ).scalar()
    
    return {
        "timestamp": now.isoformat(),
        "products": {
            "total": total_products
        },
        "competitors": {
            "total": total_competitors,
            "active": active_competitors
        },
        "prices": {
            "total": total_prices,
            "last_24h": prices_last_24h
        },
        "scraping_jobs": {
            "total": total_jobs,
            "last_24h": jobs_last_24h,
            "running": running_jobs,
            "failed_last_24h": failed_jobs_24h
        }
    }

