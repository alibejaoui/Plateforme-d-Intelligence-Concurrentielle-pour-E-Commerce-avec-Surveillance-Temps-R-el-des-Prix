"""
Price comparison utilities
"""
from typing import List, Dict, Any, Optional


def compare_prices(prices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare prices and find best deal"""
    if not prices:
        return {
            "best_price": None,
            "worst_price": None,
            "price_range": None,
            "average_price": None
        }
    
    valid_prices = [p for p in prices if p.get("price") is not None]
    
    if not valid_prices:
        return {
            "best_price": None,
            "worst_price": None,
            "price_range": None,
            "average_price": None
        }
    
    best_price = min(valid_prices, key=lambda x: x["price"])
    worst_price = max(valid_prices, key=lambda x: x["price"])
    price_values = [p["price"] for p in valid_prices]
    
    return {
        "best_price": best_price,
        "worst_price": worst_price,
        "price_range": {
            "min": min(price_values),
            "max": max(price_values),
            "difference": max(price_values) - min(price_values),
            "difference_percent": ((max(price_values) - min(price_values)) / min(price_values)) * 100
        },
        "average_price": sum(price_values) / len(price_values),
        "count": len(valid_prices)
    }


def calculate_price_change(old_price: float, new_price: float) -> Dict[str, Any]:
    """Calculate price change metrics"""
    if old_price == 0:
        return {
            "change": 0,
            "change_percent": 0,
            "direction": "stable"
        }
    
    change = new_price - old_price
    change_percent = (change / old_price) * 100
    
    if change > 0:
        direction = "increase"
    elif change < 0:
        direction = "decrease"
    else:
        direction = "stable"
    
    return {
        "change": change,
        "change_percent": change_percent,
        "direction": direction,
        "old_price": old_price,
        "new_price": new_price
    }

