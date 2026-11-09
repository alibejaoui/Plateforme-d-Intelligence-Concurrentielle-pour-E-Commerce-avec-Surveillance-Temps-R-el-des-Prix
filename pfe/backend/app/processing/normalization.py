"""
Data normalization utilities
"""
from typing import Dict, Any, Optional


def normalize_product_data(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize product data from different sources"""
    normalized = {}
    
    # Normalize name
    if "name" in product_data:
        normalized["name"] = product_data["name"].strip()
    
    # Normalize price
    if "price" in product_data:
        price = product_data["price"]
        if isinstance(price, str):
            # Remove currency symbols
            price = price.replace("€", "").replace("$", "").replace("£", "").strip()
            price = price.replace(",", ".")
        normalized["price"] = float(price) if price else None
    
    # Normalize currency
    normalized["currency"] = product_data.get("currency", "EUR").upper()
    
    # Normalize availability
    if "availability" in product_data:
        normalized["availability"] = normalize_availability(product_data["availability"])
    
    # Normalize SKU
    if "sku" in product_data:
        normalized["sku"] = product_data["sku"].strip().upper() if product_data["sku"] else None
    
    return normalized


def normalize_availability(availability: str) -> str:
    """Normalize availability status"""
    if not availability:
        return "unknown"
    
    availability_lower = availability.lower()
    
    if any(word in availability_lower for word in ["in stock", "available", "en stock", "disponible"]):
        return "in_stock"
    elif any(word in availability_lower for word in ["out of stock", "unavailable", "rupture", "épuisé"]):
        return "out_of_stock"
    elif any(word in availability_lower for word in ["preorder", "pre-order", "précommande"]):
        return "preorder"
    else:
        return "unknown"

