"""
Competitor endpoints
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.competitor_service import CompetitorService
from app.services.competitor_catalog_service import CompetitorCatalogService
from app.api.schemas.competitor_schema import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    CompetitorListResponse
)
from app.api.schemas.competitor_catalog_schema import (
    CompetitorCatalogSyncRequest,
    CompetitorCatalogSyncResponse,
)
from app.scheduler.tasks_competitor_catalog import run_competitor_catalog_sync
from app.models.crawl_session import CrawlSession

router = APIRouter()


@router.post("", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def create_competitor(
    competitor_data: CompetitorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new competitor"""
    return CompetitorService.create_competitor(db, competitor_data)


@router.get("", response_model=CompetitorListResponse)
async def get_competitors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get competitors with pagination and filters"""
    competitors, total = CompetitorService.get_competitors(
        db, skip, limit, is_active, search
    )
    return CompetitorListResponse(
        items=competitors,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a competitor by ID"""
    return CompetitorService.get_competitor(db, competitor_id)


@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: int,
    competitor_data: CompetitorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a competitor"""
    return CompetitorService.update_competitor(db, competitor_id, competitor_data)


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a competitor"""
    CompetitorService.delete_competitor(db, competitor_id)
    return None


@router.post("/{competitor_id}/catalog/sync", response_model=CompetitorCatalogSyncResponse)
async def sync_competitor_catalog(
    competitor_id: int,
    payload: CompetitorCatalogSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger a full competitor catalog sync (discovery + detail extraction).
    """
    service = CompetitorCatalogService(db)
    session = service.start_sync(
        competitor_id=competitor_id, user_id=current_user.id, seed_url=payload.seed_url
    )

    task = run_competitor_catalog_sync.delay(session.id)
    # persist orchestration task id (group id will be filled after discovery)
    session_db = db.query(CrawlSession).filter(CrawlSession.id == session.id).first()
    if session_db:
        session_db.celery_group_id = task.id
        db.commit()
        db.refresh(session_db)
        session = session_db

    return {"session": session, "task": {"celery_task_id": task.id}}

