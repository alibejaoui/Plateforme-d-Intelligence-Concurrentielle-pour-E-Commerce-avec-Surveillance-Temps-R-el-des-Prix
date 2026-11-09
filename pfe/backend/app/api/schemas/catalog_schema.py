"""
Catalog import schemas
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Literal, Any
from datetime import datetime


CatalogSourceType = Literal["sitemap", "feed", "crawl"]


class CatalogSourceCreate(BaseModel):
    source_type: CatalogSourceType
    source_url: str = Field(..., max_length=2000)
    name: Optional[str] = Field(None, max_length=255)
    config: Optional[dict[str, Any]] = None


class CatalogImportRequest(BaseModel):
    """
    Creates a CatalogSource (if not exists for same user+type+url) and launches an ImportJob.
    """

    source: CatalogSourceCreate


class CatalogSourceResponse(BaseModel):
    id: int
    user_id: int
    source_type: str
    source_url: str
    name: Optional[str] = None
    config: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ImportJobResponse(BaseModel):
    id: int
    user_id: int
    catalog_source_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    celery_task_id: Optional[str] = None
    stats: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CatalogImportResponse(BaseModel):
    source: CatalogSourceResponse
    job: ImportJobResponse

