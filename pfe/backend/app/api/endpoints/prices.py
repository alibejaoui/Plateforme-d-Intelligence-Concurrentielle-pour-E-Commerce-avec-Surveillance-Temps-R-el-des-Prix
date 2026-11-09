"""
Price endpoints
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.price_service import PriceService
from app.api.schemas.price_schema import (
    PriceCreate,
    PriceResponse,
    PriceHistoryResponse,
    PriceComparisonResponse
)

router = APIRouter()


@router.post("", response_model=PriceResponse, status_code=status.HTTP_201_CREATED)
async def create_price(
    price_data: PriceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new price record"""
    return PriceService.create_price(db, price_data)


@router.get("/history/{product_id}", response_model=PriceHistoryResponse)
async def get_price_history(
    product_id: int,
    competitor_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price history for a product"""
    prices = PriceService.get_price_history(db, product_id, competitor_id, days)
    
    if not prices:
        return PriceHistoryResponse(
            product_id=product_id,
            competitor_id=competitor_id or 0,
            competitor_name="",
            prices=[],
            current_price=None,
            min_price=None,
            max_price=None,
            avg_price=None
        )
    
    # Calculate statistics
    price_values = [p.price for p in prices]
    min_price = min(price_values)
    max_price = max(price_values)
    avg_price = sum(price_values) / len(price_values)
    
    return PriceHistoryResponse(
        product_id=product_id,
        competitor_id=competitor_id or 0,
        competitor_name="",
        prices=prices,
        current_price=prices[0] if prices else None,
        min_price=min_price,
        max_price=max_price,
        avg_price=avg_price
    )


@router.get("/current/{product_id}", response_model=list[PriceResponse])
async def get_current_prices(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current prices for a product from all competitors"""
    return PriceService.get_current_prices(db, product_id)


@router.get("/statistics/{product_id}")
async def get_price_statistics(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price statistics for a product"""
    return PriceService.get_price_statistics(db, product_id, days)

