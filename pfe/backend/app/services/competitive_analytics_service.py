"""
Competitive Intelligence analytics built on:
- internal_products (our catalog)
- competitor_products (competitor catalogs)
- product_matches (links)
- missing_products (catalog gaps)
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.core.logging import get_logger
from app.models.internal_product import InternalProduct
from app.models.competitor_product import CompetitorProduct
from app.models.product_match import ProductMatch
from app.models.missing_detection import MissingProduct
from app.models.price import Price
from app.models.product import Product

logger = get_logger(__name__)


class CompetitiveAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def price_gaps(self, *, user_id: int, competitor_id: int, limit: int = 200) -> dict:
        q = (
            self.db.query(ProductMatch, InternalProduct, CompetitorProduct)
            .join(InternalProduct, ProductMatch.internal_product_id == InternalProduct.id)
            .join(CompetitorProduct, ProductMatch.competitor_product_id == CompetitorProduct.id)
            .filter(
                ProductMatch.user_id == user_id,
                ProductMatch.competitor_id == competitor_id,
                InternalProduct.price.isnot(None),
                CompetitorProduct.price.isnot(None),
            )
        )

        rows = q.all()
        items = []
        for m, ip, cp in rows:
            our = float(ip.price)
            their = float(cp.price)
            delta = their - our
            pct = (delta / our * 100.0) if our else None
            items.append(
                {
                    "internal_product_id": ip.id,
                    "competitor_product_id": cp.id,
                    "confidence_score": m.confidence_score,
                    "matching_method": m.matching_method,
                    "our_price": our,
                    "their_price": their,
                    "delta": delta,
                    "delta_pct": pct,
                    "internal_name": ip.name,
                    "competitor_title": cp.title,
                    "competitor_url": cp.url,
                    "availability": {"internal": ip.availability, "competitor": cp.availability},
                }
            )

        items.sort(key=lambda x: (x["delta_pct"] is None, x["delta_pct"]))
        return {"items": items[:limit], "total": len(items)}

    def opportunities(self, *, user_id: int, competitor_id: int, limit: int = 200) -> dict:
        q = (
            self.db.query(MissingProduct, CompetitorProduct)
            .join(CompetitorProduct, MissingProduct.competitor_product_id == CompetitorProduct.id)
            .filter(MissingProduct.user_id == user_id, MissingProduct.competitor_id == competitor_id)
        )
        rows = q.all()
        items = []
        for mp, cp in rows:
            # Simple scoring: prefer in-stock and cheaper items (proxy for demand); configurable later.
            stock_bonus = 0.15 if (cp.availability or "").lower() in {"in_stock", "available", "en stock"} else 0.0
            price_signal = 0.0
            if cp.price is not None:
                price_signal = min(0.85, math.log1p(float(cp.price)) / 10.0)
            score = (0.3 * price_signal) + stock_bonus
            items.append(
                {
                    "missing_id": mp.id,
                    "competitor_product_id": cp.id,
                    "opportunity_score": mp.opportunity_score if mp.opportunity_score is not None else round(score, 4),
                    "title": cp.title,
                    "url": cp.url,
                    "price": cp.price,
                    "currency": cp.currency,
                    "availability": cp.availability,
                    "brand": cp.brand,
                    "category": cp.category,
                }
            )
        items.sort(key=lambda x: (x["opportunity_score"] is None, -(x["opportunity_score"] or 0.0)))
        return {"items": items[:limit], "total": len(items)}

    def competitor_aggressiveness(self, *, user_id: int, limit: int = 50) -> dict:
        """
        Aggressiveness = how often competitor undercuts our price on matched products.
        """
        # Join matches across all competitors
        q = (
            self.db.query(ProductMatch, InternalProduct, CompetitorProduct)
            .join(InternalProduct, ProductMatch.internal_product_id == InternalProduct.id)
            .join(CompetitorProduct, ProductMatch.competitor_product_id == CompetitorProduct.id)
            .filter(
                ProductMatch.user_id == user_id,
                InternalProduct.price.isnot(None),
                CompetitorProduct.price.isnot(None),
            )
        )
        rows = q.all()
        by_comp: dict[int, dict] = {}
        for m, ip, cp in rows:
            cid = m.competitor_id
            rec = by_comp.setdefault(
                cid,
                {"competitor_id": cid, "matched": 0, "undercut": 0, "avg_undercut_pct": 0.0},
            )
            rec["matched"] += 1
            our = float(ip.price)
            their = float(cp.price)
            if our > 0 and their < our:
                rec["undercut"] += 1
                rec["avg_undercut_pct"] += (our - their) / our * 100.0

        items = []
        for cid, rec in by_comp.items():
            undercut = rec["undercut"]
            matched = rec["matched"]
            avg = (rec["avg_undercut_pct"] / undercut) if undercut else 0.0
            rate = (undercut / matched * 100.0) if matched else 0.0
            items.append(
                {
                    "competitor_id": cid,
                    "matched_products": matched,
                    "undercut_products": undercut,
                    "undercut_rate_pct": rate,
                    "avg_undercut_pct": avg,
                    "aggressiveness_score": round((rate / 100.0) * min(1.0, avg / 20.0), 4),
                }
            )
        items.sort(key=lambda x: (-x["aggressiveness_score"], -x["matched_products"]))
        return {"items": items[:limit], "total": len(items)}

    def products_at_risk(self, *, user_id: int, days: int = 30, limit: int = 50) -> dict:
        """
        Products at risk are matched products where competitors are repeatedly
        cheaper, market prices trend down, or gaps are volatile.
        """
        rows = (
            self.db.query(ProductMatch, InternalProduct, CompetitorProduct)
            .join(InternalProduct, ProductMatch.internal_product_id == InternalProduct.id)
            .join(CompetitorProduct, ProductMatch.competitor_product_id == CompetitorProduct.id)
            .filter(
                ProductMatch.user_id == user_id,
                InternalProduct.price.isnot(None),
                CompetitorProduct.price.isnot(None),
            )
            .all()
        )

        grouped: dict[int, dict] = {}
        for match, internal, competitor_product in rows:
            our = float(internal.price)
            their = float(competitor_product.price)
            gap_pct = ((their - our) / our * 100.0) if our else 0.0
            rec = grouped.setdefault(
                internal.id,
                {
                    "internal_product_id": internal.id,
                    "name": internal.name,
                    "sku": internal.sku,
                    "category": internal.category,
                    "our_price": our,
                    "competitor_count": 0,
                    "cheaper_competitors": 0,
                    "worst_gap_pct": 0.0,
                    "matches": [],
                },
            )
            rec["competitor_count"] += 1
            if their < our:
                rec["cheaper_competitors"] += 1
                rec["worst_gap_pct"] = min(rec["worst_gap_pct"], gap_pct)
            rec["matches"].append(
                {
                    "competitor_id": match.competitor_id,
                    "competitor_product_id": competitor_product.id,
                    "title": competitor_product.title,
                    "price": their,
                    "gap_pct": gap_pct,
                    "confidence_score": match.confidence_score,
                    "url": competitor_product.url,
                }
            )

        items = []
        for rec in grouped.values():
            product_id = self._map_internal_to_product(user_id=user_id, internal_product_id=rec["internal_product_id"])
            variation = self._variation_summary(product_id, days=days) if product_id else {"variation_7d_pct": None, "variation_30d_pct": None, "trend": "stable", "volatility": 0.0}
            cheaper_rate = rec["cheaper_competitors"] / max(1, rec["competitor_count"])
            volatility = variation["volatility"]
            pressure = round(min(1.0, cheaper_rate * 0.65 + min(0.25, abs(rec["worst_gap_pct"]) / 100.0) + volatility * 0.10), 4)
            recommendation = "monitor competitor"
            if pressure >= 0.65:
                recommendation = "lower price or defend value proposition"
            elif variation["trend"] == "decreasing":
                recommendation = "monitor downward market trend"
            items.append(
                {
                    **rec,
                    **variation,
                    "competitor_pressure_score": pressure,
                    "margin_risk_estimation": round(abs(rec["worst_gap_pct"]) * pressure, 4),
                    "strategic_recommendation": recommendation,
                }
            )

        items.sort(key=lambda x: (-x["competitor_pressure_score"], x["worst_gap_pct"]))
        return {"items": items[:limit], "total": len(items), "days": days}

    def opportunity_products(self, *, user_id: int, days: int = 30, limit: int = 50) -> dict:
        """
        Opportunity products combine missing competitor coverage, internal price
        advantage, rising market trend, and competitor unavailability.
        """
        rows = (
            self.db.query(ProductMatch, InternalProduct, CompetitorProduct)
            .join(InternalProduct, ProductMatch.internal_product_id == InternalProduct.id)
            .join(CompetitorProduct, ProductMatch.competitor_product_id == CompetitorProduct.id)
            .filter(ProductMatch.user_id == user_id, InternalProduct.price.isnot(None))
            .all()
        )
        grouped: dict[int, dict] = {}
        for match, internal, competitor_product in rows:
            our = float(internal.price)
            their = float(competitor_product.price) if competitor_product.price is not None else None
            rec = grouped.setdefault(
                internal.id,
                {
                    "internal_product_id": internal.id,
                    "name": internal.name,
                    "sku": internal.sku,
                    "category": internal.category,
                    "our_price": our,
                    "competitors_unavailable": 0,
                    "internal_cheaper_count": 0,
                    "matched_count": 0,
                    "matches": [],
                },
            )
            rec["matched_count"] += 1
            if (competitor_product.availability or "").lower() in {"out_of_stock", "unavailable", "rupture"}:
                rec["competitors_unavailable"] += 1
            if their is not None and our < their:
                rec["internal_cheaper_count"] += 1
            rec["matches"].append(
                {
                    "competitor_id": match.competitor_id,
                    "title": competitor_product.title,
                    "price": their,
                    "availability": competitor_product.availability,
                    "url": competitor_product.url,
                }
            )

        items = []
        for rec in grouped.values():
            product_id = self._map_internal_to_product(user_id=user_id, internal_product_id=rec["internal_product_id"])
            variation = self._variation_summary(product_id, days=days) if product_id else {"variation_7d_pct": None, "variation_30d_pct": None, "trend": "stable", "volatility": 0.0}
            unavailable_rate = rec["competitors_unavailable"] / max(1, rec["matched_count"])
            cheaper_rate = rec["internal_cheaper_count"] / max(1, rec["matched_count"])
            rising_bonus = 0.2 if variation["trend"] == "rising" else 0.0
            score = round(min(1.0, cheaper_rate * 0.45 + unavailable_rate * 0.35 + rising_bonus), 4)
            recommendation = "increase visibility"
            if unavailable_rate >= 0.5:
                recommendation = "increase visibility while competitors are unavailable"
            elif variation["trend"] == "rising":
                recommendation = "protect margin during market rise"
            items.append(
                {
                    **rec,
                    **variation,
                    "opportunity_score": score,
                    "strategic_recommendation": recommendation,
                }
            )

        items.sort(key=lambda x: (-x["opportunity_score"], -x["internal_cheaper_count"]))
        return {"items": items[:limit], "total": len(items), "days": days}

    def _map_internal_to_product(self, *, user_id: int, internal_product_id: int) -> int | None:
        internal = (
            self.db.query(InternalProduct)
            .filter(InternalProduct.user_id == user_id, InternalProduct.id == internal_product_id)
            .first()
        )
        if not internal:
            return None
        q = self.db.query(Product).filter(Product.user_id == user_id)
        if internal.sku:
            p = q.filter(Product.sku == internal.sku).first()
            if p:
                return p.id
        if internal.gtin:
            p = q.filter(Product.gtin == internal.gtin).first()
            if p:
                return p.id
        return None

    def _variation_summary(self, product_id: int, days: int) -> dict:
        prices = (
            self.db.query(Price)
            .filter(Price.product_id == product_id, Price.created_at >= datetime.utcnow() - timedelta(days=days))
            .order_by(Price.created_at.asc())
            .all()
        )
        values = [float(p.price) for p in prices]
        return {
            "variation_7d_pct": self._variation_pct(product_id, 7),
            "variation_30d_pct": self._variation_pct(product_id, 30),
            "trend": self._trend(values),
            "volatility": self._volatility(values),
        }

    def _variation_pct(self, product_id: int, days: int) -> float | None:
        prices = (
            self.db.query(Price)
            .filter(Price.product_id == product_id, Price.created_at >= datetime.utcnow() - timedelta(days=days))
            .order_by(Price.created_at.asc())
            .all()
        )
        if len(prices) < 2 or float(prices[0].price) == 0:
            return None
        return round((float(prices[-1].price) - float(prices[0].price)) / float(prices[0].price) * 100.0, 4)

    def _trend(self, values: list[float]) -> str:
        if len(values) < 3 or values[0] <= 0:
            return "stable"
        pct = (values[-1] - values[0]) / values[0] * 100.0
        if pct >= 3:
            return "rising"
        if pct <= -3:
            return "decreasing"
        return "stable"

    def _volatility(self, values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        avg = sum(values) / len(values)
        if avg <= 0:
            return 0.0
        return round(min(1.0, statistics.pstdev(values) / avg), 4)

