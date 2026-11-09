"""
Alert model for price alerts
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class AlertType(str, enum.Enum):
    """Alert type enumeration"""
    PRICE_DROP = "price_drop"
    PRICE_INCREASE = "price_increase"
    THRESHOLD_BELOW = "threshold_below"
    THRESHOLD_ABOVE = "threshold_above"
    AVAILABILITY_CHANGE = "availability_change"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    ARCHIVED = "archived"


class Alert(BaseModel):
    """Alert model for price change notifications"""
    __tablename__ = "alerts"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.PENDING, nullable=False)
    message = Column(Text, nullable=False)
    old_price = Column(String(50), nullable=True)
    new_price = Column(String(50), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    product = relationship("Product", back_populates="alerts")

