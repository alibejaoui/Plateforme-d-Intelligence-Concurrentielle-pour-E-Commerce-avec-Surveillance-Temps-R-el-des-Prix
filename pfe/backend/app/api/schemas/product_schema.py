"""
Product schemas
"""
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    """Base product schema"""
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    target_price: Optional[float] = None
    min_price_threshold: Optional[float] = None
    max_price_threshold: Optional[float] = None


class ProductCreate(ProductBase):
    """Product creation schema"""
    pass


class ProductUpdate(BaseModel):
    """Product update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    target_price: Optional[float] = None
    min_price_threshold: Optional[float] = None
    max_price_threshold: Optional[float] = None


class ProductResponse(ProductBase):
    """Product response schema"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Product list response schema"""
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int

