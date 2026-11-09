"""
Celery tasks for asynchronous operations
"""
from celery import Task
from sqlalchemy.orm import Session
from datetime import datetime

from app.scheduler.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.scraping_job import ScrapingJob, JobStatus
from app.models.competitor import Competitor
from app.models.product import Product
from app.scraping.scraping_manager import ScrapingManager
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="scraping.trigger_scraping")
def trigger_scraping_task(self: Task, competitor_id: int, product_id: int = None) -> dict:
    """Trigger a scraping task"""
    db: Session = SessionLocal()
    try:
        # Update job status
        job = db.query(ScrapingJob).filter(
            ScrapingJob.competitor_id == competitor_id,
            ScrapingJob.product_id == product_id
        ).order_by(ScrapingJob.created_at.desc()).first()
        
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
        
        # Initialize scraping manager
        manager = ScrapingManager(db)
        
        # Perform scraping
        if product_id:
            result = manager.scrape_product(
                competitor_id=competitor_id,
                product_id=product_id,
                scraper=None,
            )
        else:
            # Batch scraping: scrape all products for this competitor
            products = db.query(Product).all()
            scraped_count = 0
            errors: list[str] = []

            for p in products:
                res = manager.scrape_product(
                    competitor_id=competitor_id,
                    product_id=p.id,
                    scraper=None,
                )
                if res.get("success"):
                    scraped_count += 1
                else:
                    errors.append(str(res.get("error") or "unknown error"))

            result = {
                "success": True,
                "message": "Batch scraping completed",
                "scraped_count": scraped_count,
                "errors": errors[:20],
            }

        # Update job status (single-product: FAILED if no price was stored — avoids "completed" with empty chart)
        if job:
            job.completed_at = datetime.utcnow()
            job.result_data = result
            if product_id and isinstance(result, dict) and result.get("success") is False:
                job.status = JobStatus.FAILED
                job.error_message = str(result.get("error") or "Scraping failed — no price saved")
            else:
                job.status = JobStatus.COMPLETED
            db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error in scraping task: {str(e)}")
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        raise
    
    finally:
        db.close()


@celery_app.task(name="scraping.run_batch_scraping")
def run_batch_scraping() -> dict:
    """
    Scrape all active competitors against all products.
    Called periodically by Celery beat.
    """
    db: Session = SessionLocal()
    try:
        manager = ScrapingManager(db)

        competitors = db.query(Competitor).filter(Competitor.is_active == True).all()
        products = db.query(Product).all()

        scraped_total = 0
        error_total = 0

        for competitor in competitors:
            for product in products:
                res = manager.scrape_product(
                    competitor_id=competitor.id,
                    product_id=product.id,
                    scraper=None,
                )
                if res.get("success"):
                    scraped_total += 1
                else:
                    error_total += 1

        return {"success": True, "scraped_total": scraped_total, "error_total": error_total}
    finally:
        db.close()


@celery_app.task(name="analytics.generate_daily_report")
def generate_daily_report(user_id: int) -> dict:
    """Generate daily analytics report"""
    db: Session = SessionLocal()
    try:
        # Daily report generation logic
        logger.info(f"Generating daily report for user {user_id}")
        return {"success": True, "message": "Daily report generated"}
    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(name="alerts.check_price_alerts")
def check_price_alerts() -> dict:
    """Check and generate price alerts"""
    db: Session = SessionLocal()
    try:
        # Alert checking logic
        logger.info("Checking price alerts")
        return {"success": True, "alerts_generated": 0}
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}")
        raise
    finally:
        db.close()

