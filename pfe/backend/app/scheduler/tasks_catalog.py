"""
Celery tasks for catalog import workflows.
"""

from celery import Task
from sqlalchemy.orm import Session

from app.scheduler.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.catalog_import_service import CatalogImportService

logger = get_logger(__name__)


@celery_app.task(bind=True, name="catalog.run_import_job")
def run_catalog_import_job(self: Task, job_id: int) -> dict:
    db: Session = SessionLocal()
    try:
        service = CatalogImportService(db)
        stats = service.run_job(job_id)
        db.commit()
        return {"success": True, "job_id": job_id, "stats": stats}
    except Exception as e:
        logger.error("Catalog import job failed: %s", e)
        db.rollback()
        raise
    finally:
        db.close()

