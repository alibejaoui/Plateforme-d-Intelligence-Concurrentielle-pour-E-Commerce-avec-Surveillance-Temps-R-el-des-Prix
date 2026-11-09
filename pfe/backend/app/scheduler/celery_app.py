"""
Celery application configuration
"""
from celery import Celery

from app.core.settings import settings

celery_app = Celery(
    "competitive_intelligence",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.scheduler.tasks",
        "app.scheduler.tasks_catalog",
        "app.scheduler.tasks_competitor_catalog",
        "app.scheduler.tasks_alerts_ci",
    ]
)

# Ensure beat_schedule is registered.
# This module only mutates Celery configuration at import time.
from app.scheduler import cron_manager  # noqa: E402,F401

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

