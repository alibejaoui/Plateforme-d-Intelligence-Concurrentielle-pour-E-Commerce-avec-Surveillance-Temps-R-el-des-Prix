"""
Schemas for competitor catalog sync/crawl.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class CompetitorCatalogSyncRequest(BaseModel):
    seed_url: Optional[str] = Field(None, max_length=2000)


class CrawlSessionResponse(BaseModel):
    id: int
    competitor_id: int
    user_id: Optional[int] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    seed_url: Optional[str] = None
    stats: Optional[dict[str, Any]] = None
    celery_group_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompetitorCatalogSyncResponse(BaseModel):
    session: CrawlSessionResponse
    task: dict[str, Any]

