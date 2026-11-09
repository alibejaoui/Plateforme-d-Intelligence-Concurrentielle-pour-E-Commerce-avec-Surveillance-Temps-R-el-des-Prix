"""
Cron job manager for scheduled tasks
"""
from celery.schedules import crontab

from app.scheduler.celery_app import celery_app
from app.core.settings import settings

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "scraping-run-batch": {
        "task": "scraping.run_batch_scraping",
        "schedule": crontab(minute=0),  # Every hour
    },
    "hourly-price-check": {
        "task": "alerts.check_price_alerts",
        "schedule": crontab(minute=0),  # Every hour
    },
    "daily-analytics-report": {
        "task": "analytics.generate_daily_report",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    "competitive-alerts-evaluation": {
        "task": "alerts.evaluate_competitive_alerts",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
}

