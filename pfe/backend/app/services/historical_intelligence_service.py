"""
Historical price intelligence for matched products.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import statistics

from sqlalchemy.orm import Session

from app.models.price import Price
from app.models.product_match import ProductMatch
from app.models.internal_product import InternalProduct
from app.models.product import Product


class HistoricalIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    def _map_internal_to_product_id(self, *, user_id: int, internal_product_id: int) -> int | None:
        ip = (
            self.db.query(InternalProduct)
            .filter(InternalProduct.user_id == user_id, InternalProduct.id == internal_product_id)
            .first()
        )
        if not ip:
            return None
        if ip.sku:
            # SKU is unique globally in this schema; ensure user ownership to avoid cross-tenant edits.
            p = self.db.query(Product).filter(Product.sku == ip.sku).first()
            if p and p.user_id == user_id:
                return p.id
        if ip.gtin:
            p2 = (
                self.db.query(Product)
                .filter(Product.user_id == user_id, Product.gtin == ip.gtin)
                .first()
            )
            if p2:
                return p2.id
        return None

    def matched_product_history(self, *, user_id: int, internal_product_id: int, days: int = 30) -> dict:
        start_date = datetime.utcnow() - timedelta(days=days)
        matches = (
            self.db.query(ProductMatch)
            .filter(ProductMatch.user_id == user_id, ProductMatch.internal_product_id == internal_product_id)
            .all()
        )
        competitor_ids = sorted({m.competitor_id for m in matches})

        product_id = self._map_internal_to_product_id(user_id=user_id, internal_product_id=internal_product_id)
        # If we can't map, return stable payload with empty series for demo robustness.
        if not product_id:
            return {
                "internal_product_id": internal_product_id,
                "days": days,
                "series": [],
                "summary": {"min": None, "max": None, "avg": None},
            }

        series = []
        all_prices = []
        for cid in competitor_ids:
            prices = (
                self.db.query(Price)
                .filter(
                    Price.product_id == product_id,
                    Price.competitor_id == cid,
                    Price.created_at >= start_date,
                )
                .order_by(Price.created_at.asc())
                .all()
            )
            points = [{"t": (p.scraped_at or p.created_at).isoformat(), "price": float(p.price)} for p in prices]
            values = [float(p.price) for p in prices]
            all_prices.extend(values)
            volatility = statistics.pstdev(values) if len(values) > 1 else 0.0
            trend = self._trend(values)
            drops = self._drops(values)
            series.append(
                {
                    "competitor_id": cid,
                    "points": points,
                    "stats": {
                        "min": min(values) if values else None,
                        "max": max(values) if values else None,
                        "avg": (sum(values) / len(values)) if values else None,
                        "volatility": volatility,
                        "trend": trend,
                        "drop_events": drops,
                    },
                }
            )
        return {
            "internal_product_id": internal_product_id,
            "days": days,
            "series": series,
            "summary": {
                "min": min(all_prices) if all_prices else None,
                "max": max(all_prices) if all_prices else None,
                "avg": (sum(all_prices) / len(all_prices)) if all_prices else None,
            },
        }

    def _trend(self, values: list[float]) -> str:
        if len(values) < 3:
            return "stable"
        delta = values[-1] - values[0]
        pct = (delta / values[0] * 100.0) if values[0] else 0.0
        if pct <= -5:
            return "down"
        if pct >= 5:
            return "up"
        return "stable"

    def _drops(self, values: list[float]) -> int:
        drops = 0
        for prev, cur in zip(values, values[1:]):
            if prev > 0 and ((prev - cur) / prev) >= 0.1:
                drops += 1
        return drops

