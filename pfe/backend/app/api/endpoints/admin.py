"""
Admin endpoints (read-only; role-based access).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.core.security import require_admin, get_password_hash
from app.models.user import User
from app.models.scraping_job import ScrapingJob
from app.models.alert import Alert
from app.models.product import Product
from app.services.demo_seed_service import DemoSeedService

router = APIRouter()


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="analyst")
    full_name: str | None = None


class DemoSeedRequest(BaseModel):
    reset: bool = True


def _normalize_role(role: str) -> str:
    r = (role or "").strip().lower()
    if r in {"admin", "analyst", "analysateur"}:
        return "analyst" if r == "analysateur" else r
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Invalid role. Allowed: admin, analyst",
    )


@router.get("/test")
async def admin_test(current_user: User = Depends(require_admin)):
    return "admin access granted"


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return all users (simple query)."""
    rows = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in rows
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    role = _normalize_role(payload.role)
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=role,
        full_name=payload.full_name,
        is_active=True,
        is_superuser=(role == "admin"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot delete own account",
        )
    db.delete(user)
    db.commit()
    return None


@router.get("/scraping-jobs")
async def list_scraping_jobs(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = db.query(ScrapingJob).order_by(ScrapingJob.created_at.desc()).all()
    return [
        {
            "id": j.id,
            "competitor_id": j.competitor_id,
            "product_id": j.product_id,
            "status": j.status.value if j.status else None,
            "job_type": j.job_type,
            "error_message": j.error_message,
            "created_at": j.created_at,
            "started_at": j.started_at,
            "completed_at": j.completed_at,
        }
        for j in rows
    ]


@router.get("/alerts")
async def list_all_alerts(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = db.query(Alert).order_by(Alert.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "product_id": a.product_id,
            "alert_type": a.alert_type.value if a.alert_type else None,
            "status": a.status.value if a.status else None,
            "message": a.message,
            "old_price": a.old_price,
            "new_price": a.new_price,
            "created_at": a.created_at,
        }
        for a in rows
    ]


@router.get("/analytics")
async def admin_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    total_jobs = db.query(func.count(ScrapingJob.id)).scalar() or 0
    return {
        "total_users": int(total_users),
        "total_products": int(total_products),
        "total_alerts": int(total_alerts),
        "total_jobs": int(total_jobs),
    }


@router.post("/demo/seed")
async def seed_demo(
    payload: DemoSeedRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Seed deterministic demo data for a stable CI/demo walkthrough.
    Admin-only.
    """
    service = DemoSeedService(db)
    result = service.seed(reset=payload.reset)
    return result
