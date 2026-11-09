"""
User model
"""
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    role = Column(String(50), default="analyst", nullable=False, index=True)
    
    # Relationships
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    
