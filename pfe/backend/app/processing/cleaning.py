"""
Data cleaning utilities
"""
import re
from typing import Any, Optional


def clean_price(price: Any) -> Optional[float]:
    """Clean and normalize price string"""
    if price is None:
        return None
    
    if isinstance(price, (int, float)):
        return float(price)
    
    if isinstance(price, str):
        # Remove all non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.,]', '', price)
        # Replace comma with dot for decimal
        cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    return None


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and special characters"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def clean_url(url: str) -> str:
    """Clean and normalize URL"""
    if not url:
        return ""
    
    url = url.strip()
    
    # Ensure URL starts with http:// or https://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url

