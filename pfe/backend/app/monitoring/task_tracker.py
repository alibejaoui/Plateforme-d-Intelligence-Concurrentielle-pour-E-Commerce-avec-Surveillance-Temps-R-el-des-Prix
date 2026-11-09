"""
Task tracking utilities for Celery tasks
"""
from typing import Dict, Any, Optional
from celery.result import AsyncResult

from app.scheduler.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a Celery task"""
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        return {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
            "successful": task_result.successful() if task_result.ready() else None,
            "result": task_result.result if task_result.ready() else None,
            "error": str(task_result.result) if task_result.failed() else None
        }
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return {
            "task_id": task_id,
            "status": "ERROR",
            "error": str(e)
        }

