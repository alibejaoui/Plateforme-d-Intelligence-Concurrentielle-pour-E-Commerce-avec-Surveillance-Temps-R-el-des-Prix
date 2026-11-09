"""
Analytics endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.services.competitive_analytics_service import CompetitiveAnalyticsService

router = APIRouter()


@router.get("/trends/{product_id}")
async def get_price_trends(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    competitor_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price trends for a product"""
    service = AnalyticsService(db)
    return service.get_price_trends(product_id, days, competitor_id)


@router.get("/comparison/{product_id}")
async def get_competitor_comparison(
    product_id: int,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare prices across competitors for a product"""
    service = AnalyticsService(db)
    return service.get_competitor_comparison(product_id, days=days)


@router.get("/insights")
async def get_market_insights(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get market insights for user's products"""
    service = AnalyticsService(db)
    return service.get_market_insights(current_user.id, days)


@router.get("/price-gaps")
async def get_price_gaps(
    competitor_id: int = Query(..., ge=1),
    limit: int = Query(200, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CompetitiveAnalyticsService(db)
    return service.price_gaps(user_id=current_user.id, competitor_id=competitor_id, limit=limit)


@router.get("/opportunities")
async def get_opportunities(
    competitor_id: int = Query(..., ge=1),
    limit: int = Query(200, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CompetitiveAnalyticsService(db)
    return service.opportunities(user_id=current_user.id, competitor_id=competitor_id, limit=limit)


@router.get("/competitor-aggressiveness")
async def get_competitor_aggressiveness(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CompetitiveAnalyticsService(db)
    return service.competitor_aggressiveness(user_id=current_user.id, limit=limit)


@router.get("/products-at-risk")
async def get_products_at_risk(
    days: int = Query(30, ge=7, le=365),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CompetitiveAnalyticsService(db)
    return service.products_at_risk(user_id=current_user.id, days=days, limit=limit)


@router.get("/opportunity-products")
async def get_opportunity_products(
    days: int = Query(30, ge=7, le=365),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CompetitiveAnalyticsService(db)
    return service.opportunity_products(user_id=current_user.id, days=days, limit=limit)
