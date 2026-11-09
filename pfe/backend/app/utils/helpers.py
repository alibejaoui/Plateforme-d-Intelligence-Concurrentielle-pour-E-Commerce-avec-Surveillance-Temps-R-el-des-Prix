"""
Helper utilities
"""
from typing import Any, Dict, List
from datetime import datetime


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO string"""
    if dt:
        return dt.isoformat()
    return None


def paginate_query(query, page: int, page_size: int) -> Dict[str, Any]:
    """Paginate a SQLAlchemy query"""
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
    }


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers"""
    if denominator == 0:
        return default
    return numerator / denominator

