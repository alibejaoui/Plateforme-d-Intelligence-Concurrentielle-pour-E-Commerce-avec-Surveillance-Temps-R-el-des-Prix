"""
Configurable content source (RSS, API, or web) for admin-managed ingestion.
"""

from sqlalchemy import Boolean, Column, String

from app.models.base import BaseModel


class Source(BaseModel):
    __tablename__ = "sources"

    name = Column(String(255), nullable=False)
    url = Column(String(2000), nullable=False)
    source_type = Column(String(16), nullable=False, default="web")
    is_active = Column(Boolean, default=True, nullable=False)
