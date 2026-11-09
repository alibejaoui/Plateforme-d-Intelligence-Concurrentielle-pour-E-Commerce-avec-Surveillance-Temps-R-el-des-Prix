"""
Main API router
"""
from fastapi import APIRouter

from app.api.endpoints import (
    auth,
    products,
    competitors,
    prices,
    alerts,
    analytics,
    scraping,
    monitoring,
    admin,
    sources,
    catalog,
    intelligence,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(competitors.router, prefix="/competitors", tags=["Competitors"])
api_router.include_router(prices.router, prefix="/prices", tags=["Prices"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(scraping.router, prefix="/scraping", tags=["Scraping"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(sources.router, prefix="/sources", tags=["Sources"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["Catalog"])
api_router.include_router(intelligence.router, tags=["Intelligence"])

