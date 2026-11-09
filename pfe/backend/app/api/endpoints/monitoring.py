"""
Monitoring endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.monitoring.health_check import check_health
from app.monitoring.metrics import get_system_metrics

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return check_health()


@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system metrics"""
    return get_system_metrics(db)

