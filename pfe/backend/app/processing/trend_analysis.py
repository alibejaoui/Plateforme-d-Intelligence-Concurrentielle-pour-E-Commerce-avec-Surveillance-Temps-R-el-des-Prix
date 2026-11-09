"""
Trend analysis utilities
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics


def calculate_trend(prices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate price trend from historical data"""
    if len(prices) < 2:
        return {
            "trend": "insufficient_data",
            "slope": 0,
            "volatility": 0
        }
    
    # Sort by date
    sorted_prices = sorted(prices, key=lambda x: x.get("date", datetime.min))
    price_values = [p["price"] for p in sorted_prices if p.get("price")]
    
    if len(price_values) < 2:
        return {
            "trend": "insufficient_data",
            "slope": 0,
            "volatility": 0
        }
    
    # Calculate slope (simple linear regression)
    n = len(price_values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(price_values) / n
    
    numerator = sum((x[i] - x_mean) * (price_values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator != 0 else 0
    
    # Calculate volatility (standard deviation)
    volatility = statistics.stdev(price_values) if len(price_values) > 1 else 0
    
    # Determine trend direction
    if slope > 0.01:
        trend = "increasing"
    elif slope < -0.01:
        trend = "decreasing"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "slope": slope,
        "volatility": volatility,
        "current_price": price_values[-1],
        "first_price": price_values[0],
        "price_change": price_values[-1] - price_values[0],
        "price_change_percent": ((price_values[-1] - price_values[0]) / price_values[0]) * 100 if price_values[0] != 0 else 0
    }


def detect_anomalies(prices: List[Dict[str, Any]], threshold: float = 2.0) -> List[Dict[str, Any]]:
    """Detect price anomalies using statistical methods"""
    if len(prices) < 3:
        return []
    
    price_values = [p["price"] for p in prices if p.get("price")]
    if len(price_values) < 3:
        return []
    
    mean = statistics.mean(price_values)
    stdev = statistics.stdev(price_values) if len(price_values) > 1 else 0
    
    if stdev == 0:
        return []
    
    anomalies = []
    for i, price in enumerate(price_values):
        z_score = abs((price - mean) / stdev)
        if z_score > threshold:
            anomalies.append({
                "index": i,
                "price": price,
                "z_score": z_score,
                "date": prices[i].get("date")
            })
    
    return anomalies

