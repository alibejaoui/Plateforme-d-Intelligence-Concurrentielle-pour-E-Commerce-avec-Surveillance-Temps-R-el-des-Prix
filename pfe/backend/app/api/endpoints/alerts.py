from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.schemas.alert_schema import AlertResponse
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.alert import AlertStatus
from app.services.alert_service import AlertService

router = APIRouter()


@router.get("", response_model=dict)
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[AlertStatus] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List alerts for the current user."""
    alerts, total = AlertService.get_user_alerts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status_filter,
    )

    return {
        "items": [AlertResponse.model_validate(a) for a in alerts],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.patch(
    "/{alert_id}/read",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_alert_as_read(
    alert_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark an alert as read."""
    alert = AlertService.mark_alert_as_read(
        db=db,
        alert_id=alert_id,
        user_id=current_user.id,
    )
    return AlertResponse.model_validate(alert)

