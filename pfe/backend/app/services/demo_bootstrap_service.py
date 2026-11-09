"""
Demo bootstrap: ensure at least demo admin/analyst users exist.

This is intentionally minimal: it does not seed any CI data.
It enables first-time demo walkthrough without manual scripts.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User


DEMO_ADMIN_EMAIL = "admin@platform.com"
DEMO_ADMIN_PASSWORD = "Admin123!"

DEMO_ANALYST_EMAIL = "analyst@platform.com"
DEMO_ANALYST_PASSWORD = "Analyst123!"


def ensure_demo_users(db: Session) -> dict:
    created = {"admin": False, "analyst": False}

    if db.query(User).count() > 0:
        # Avoid touching an existing real environment.
        admin = db.query(User).filter(User.email == DEMO_ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                email=DEMO_ADMIN_EMAIL,
                hashed_password=get_password_hash(DEMO_ADMIN_PASSWORD),
                full_name="Admin",
                is_active=True,
                is_superuser=False,
                role="admin",
            )
            db.add(admin)
            created["admin"] = True
        analyst = db.query(User).filter(User.email == DEMO_ANALYST_EMAIL).first()
        if not analyst:
            analyst = User(
                email=DEMO_ANALYST_EMAIL,
                hashed_password=get_password_hash(DEMO_ANALYST_PASSWORD),
                full_name="Analyst",
                is_active=True,
                is_superuser=False,
                role="analyst",
            )
            db.add(analyst)
            created["analyst"] = True
        db.commit()
        return created

    # Fresh DB: create demo users.
    admin = User(
        email=DEMO_ADMIN_EMAIL,
        hashed_password=get_password_hash(DEMO_ADMIN_PASSWORD),
        full_name="Admin",
        is_active=True,
        is_superuser=False,
        role="admin",
    )
    analyst = User(
        email=DEMO_ANALYST_EMAIL,
        hashed_password=get_password_hash(DEMO_ANALYST_PASSWORD),
        full_name="Analyst",
        is_active=True,
        is_superuser=False,
        role="analyst",
    )
    db.add(admin)
    db.add(analyst)
    db.commit()
    created["admin"] = True
    created["analyst"] = True
    return created

