"""
Catalog import endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.import_job import ImportJob
from app.services.catalog_import_service import CatalogImportService
from app.api.schemas.catalog_schema import CatalogImportRequest, CatalogImportResponse, ImportJobResponse
from app.scheduler.tasks_catalog import run_catalog_import_job

router = APIRouter()


@router.post("/import", response_model=CatalogImportResponse, status_code=status.HTTP_201_CREATED)
async def import_catalog(
    payload: CatalogImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CatalogImportService(db)
    src = payload.source
    source = service.get_or_create_source(
        user_id=current_user.id,
        source_type=src.source_type,
        source_url=src.source_url,
        name=src.name,
        config=src.config,
    )
    job = service.create_job(user_id=current_user.id, source=source)

    task = run_catalog_import_job.delay(job.id)
    job.celery_task_id = task.id
    db.commit()
    db.refresh(job)

    return {"source": source, "job": job}


@router.get("/import-jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(ImportJob)
        .filter(ImportJob.id == job_id, ImportJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return job

