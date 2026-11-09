"""
Competitor schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CompetitorBase(BaseModel):
    """Base competitor schema"""
    name: str
    website_url: str
    base_url: str
    description: Optional[str] = None
    is_active: bool = True
    scraping_config: Optional[str] = None
    rate_limit_per_minute: int = 10


class CompetitorCreate(CompetitorBase):
    """Competitor creation schema"""
    pass


class CompetitorUpdate(BaseModel):
    """Competitor update schema"""
    name: Optional[str] = None
    website_url: Optional[str] = None
    base_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    scraping_config: Optional[str] = None
    rate_limit_per_minute: Optional[int] = None


class CompetitorResponse(CompetitorBase):
    """Competitor response schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompetitorListResponse(BaseModel):
    """Competitor list response schema"""
    items: list[CompetitorResponse]
    total: int
    page: int
    page_size: int

