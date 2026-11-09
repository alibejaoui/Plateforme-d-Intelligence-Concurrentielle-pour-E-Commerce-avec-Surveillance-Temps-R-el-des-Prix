"""
Price schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PriceBase(BaseModel):
    """Base price schema"""
    product_id: int
    competitor_id: int
    price: float
    currency: str = "EUR"
    availability: Optional[str] = None
    url: Optional[str] = None


class PriceCreate(PriceBase):
    """Price creation schema"""
    scraped_at: Optional[datetime] = None


class PriceResponse(PriceBase):
    """Price response schema"""
    id: int
    scraped_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """Price history response schema"""
    product_id: int
    competitor_id: int
    competitor_name: str
    prices: list[PriceResponse]
    current_price: Optional[PriceResponse] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    avg_price: Optional[float] = None


class PriceComparisonResponse(BaseModel):
    """Price comparison response schema"""
    product_id: int
    product_name: str
    competitors: list[dict]
    best_price: Optional[dict] = None
    price_difference: Optional[float] = None

