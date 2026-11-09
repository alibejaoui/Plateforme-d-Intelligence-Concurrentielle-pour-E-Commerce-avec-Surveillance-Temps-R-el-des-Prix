"""
Validation utilities
"""
import re
from typing import Optional
from urllib.parse import urlparse


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_price(price: Any) -> bool:
    """Validate price value"""
    try:
        price_float = float(price)
        return price_float >= 0
    except (ValueError, TypeError):
        return False

