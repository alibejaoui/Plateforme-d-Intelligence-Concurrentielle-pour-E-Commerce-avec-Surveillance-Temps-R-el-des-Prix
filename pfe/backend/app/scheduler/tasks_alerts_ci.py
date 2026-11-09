"""
Scheduled tasks for competitive alerts engine.
"""

from sqlalchemy.orm import Session

from app.scheduler.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.user import User
from app.services.competitive_alert_engine import CompetitiveAlertEngine


@celery_app.task(name="alerts.evaluate_competitive_alerts")
def evaluate_competitive_alerts_task() -> dict:
    db: Session = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        total_created = 0
        total_rules = 0
        for u in users:
            res = CompetitiveAlertEngine(db).evaluate_user(u.id)
            total_created += int(res.get("alerts_created", 0))
            total_rules += int(res.get("rules_evaluated", 0))
        return {
            "success": True,
            "users": len(users),
            "rules_evaluated": total_rules,
            "alerts_created": total_created,
        }
    finally:
        db.close()

