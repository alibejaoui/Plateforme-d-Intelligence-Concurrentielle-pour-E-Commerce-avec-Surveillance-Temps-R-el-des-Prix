"""Admin-only CRUD for content sources (mounted at /sources)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Literal

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.models.source import Source

router = APIRouter()

SourceTypeLit = Literal["rss", "api", "web"]
SourceStatusLit = Literal["active", "inactive"]


def _source_to_dict(s: Source) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "url": s.url,
        "type": s.source_type,
        "status": "active" if s.is_active else "inactive",
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=1, max_length=2000)
    type: SourceTypeLit
    status: SourceStatusLit


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: str | None = Field(default=None, min_length=1, max_length=2000)
    type: SourceTypeLit | None = None
    status: SourceStatusLit | None = None


@router.get("/")
async def list_sources(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = db.query(Source).order_by(Source.created_at.desc()).all()
    return [_source_to_dict(s) for s in rows]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    row = Source(
        name=payload.name.strip(),
        url=payload.url.strip(),
        source_type=payload.type,
        is_active=(payload.status == "active"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _source_to_dict(row)


@router.patch("/{source_id}")
async def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    row = db.query(Source).filter(Source.id == source_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    if payload.name is not None:
        row.name = payload.name.strip()
    if payload.url is not None:
        row.url = payload.url.strip()
    if payload.type is not None:
        row.source_type = payload.type
    if payload.status is not None:
        row.is_active = payload.status == "active"
    db.commit()
    db.refresh(row)
    return _source_to_dict(row)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    row = db.query(Source).filter(Source.id == source_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    db.delete(row)
    db.commit()
    return None
