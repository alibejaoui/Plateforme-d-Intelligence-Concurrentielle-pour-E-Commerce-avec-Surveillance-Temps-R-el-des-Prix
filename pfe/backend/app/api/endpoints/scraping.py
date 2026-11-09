"""
Scraping endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.scheduler.tasks import trigger_scraping_task
from app.scheduler.celery_app import celery_app
from app.models.scraping_job import ScrapingJob, JobStatus
from app.models.competitor import Competitor
from app.models.product import Product

router = APIRouter()


@router.post("/trigger/{competitor_id}")
async def trigger_scraping(
    competitor_id: int,
    product_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger a scraping job for a competitor"""
    # Verify competitor exists
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )
    
    # If product_id provided, verify it exists and belongs to user
    if product_id:
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.user_id == current_user.id
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
    
    # Create scraping job record
    job = ScrapingJob(
        competitor_id=competitor_id,
        product_id=product_id,
        status=JobStatus.PENDING,
        job_type="single" if product_id else "batch"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Trigger Celery task when a worker is available. In local demos, the API is
    # often running without a Celery worker; in that case execute synchronously
    # so the "Scrape now" button still produces a real price/history result.
    run_sync = False
    try:
        active_workers = celery_app.control.ping(timeout=0.8)
        run_sync = not bool(active_workers)
    except Exception:
        run_sync = True

    if run_sync:
        result = trigger_scraping_task.apply(args=(competitor_id, product_id), throw=False)
        db.refresh(job)
        return {
            "job_id": job.id,
            "celery_task_id": None,
            "status": job.status.value,
            "message": "Scraping executed synchronously because no Celery worker is available",
            "result_data": result.result if result.successful() else None,
        }

    task = trigger_scraping_task.delay(competitor_id, product_id)

    job.celery_task_id = task.id
    db.commit()
    
    return {
        "job_id": job.id,
        "celery_task_id": task.id,
        "status": job.status.value,
        "message": "Scraping job triggered successfully"
    }


@router.get("/jobs/{job_id}")
async def get_scraping_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scraping job status"""
    job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraping job not found"
        )
    
    return {
        "id": job.id,
        "competitor_id": job.competitor_id,
        "product_id": job.product_id,
        "status": job.status.value,
        "job_type": job.job_type,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
        "celery_task_id": job.celery_task_id,
        "result_data": job.result_data,
    }
