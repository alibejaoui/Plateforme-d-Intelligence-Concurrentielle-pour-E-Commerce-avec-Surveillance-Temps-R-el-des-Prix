from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.alert import AlertStatus, AlertType


class AlertResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    alert_type: AlertType
    status: AlertStatus
    message: str
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

