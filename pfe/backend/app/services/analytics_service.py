"""
Analytics service for price trends and analysis
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta
import statistics

from app.models.price import Price
from app.models.product import Product
from app.models.competitor import Competitor
from app.models.internal_product import InternalProduct
from app.cache.cache_service import CacheService


class AnalyticsService:
    """Service for analytics operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = CacheService()
    
    def get_price_trends(
        self,
        product_id: int,
        days: int = 30,
        competitor_id: Optional[int] = None
    ) -> dict:
        """Get price trends for a product"""
        cache_key = f"trends:product:{product_id}:days:{days}:competitor:{competitor_id}"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(
            func.date(Price.created_at).label('date'),
            func.avg(Price.price).label('avg_price'),
            func.min(Price.price).label('min_price'),
            func.max(Price.price).label('max_price'),
            func.count(Price.id).label('count')
        ).filter(
            Price.product_id == product_id,
            Price.created_at >= start_date
        )
        
        if competitor_id:
            query = query.filter(Price.competitor_id == competitor_id)
        
        trends = query.group_by(func.date(Price.created_at)).order_by(
            func.date(Price.created_at)
        ).all()
        
        result = {
            "product_id": product_id,
            "period_days": days,
            "trends": [
                {
                    "date": str(trend.date),
                    "avg_price": float(trend.avg_price),
                    "min_price": float(trend.min_price),
                    "max_price": float(trend.max_price),
                    "count": trend.count
                }
                for trend in trends
            ]
        }
        
        # Cache for 5 minutes
        self.cache.set(cache_key, result, ttl=300)
        
        return result
    
    def get_competitor_comparison(self, product_id: int, days: int = 30) -> dict:
        """Compare latest and historical prices across competitors.

        The original response keys are preserved (`competitors`, `best_price`,
        `price_range`) and enriched with defense-ready analytics.
        """
        cache_key = f"comparison:product:{product_id}:days:{days}"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        product = self.db.query(Product).filter(Product.id == product_id).first()

        # Get latest price from each competitor
        subquery = self.db.query(
            Price.competitor_id,
            func.max(Price.created_at).label('max_date')
        ).filter(
            Price.product_id == product_id
        ).group_by(Price.competitor_id).subquery()
        
        prices = self.db.query(
            Price,
            Competitor.name.label('competitor_name')
        ).join(
            Competitor, Price.competitor_id == Competitor.id
        ).join(
            subquery,
            (Price.competitor_id == subquery.c.competitor_id) &
            (Price.created_at == subquery.c.max_date)
        ).filter(Price.product_id == product_id).all()
        
        if not prices:
            return {
                "product_id": product_id,
                "competitors": [],
                "best_price": None,
                "historical_gap_evolution": [],
                "historical_snapshots": [],
                "competitor_ranking": [],
                "average_market_price": None,
                "price_position": "unknown",
                "volatility_score": 0.0,
                "trend_direction": "stable",
                "gain_loss_estimation": {
                    "potential_revenue_loss": 0.0,
                    "estimated_competitiveness_risk": "unknown",
                },
            }
        
        competitor_prices = [
            {
                "competitor_id": price.Price.competitor_id,
                "competitor_name": price.competitor_name,
                "price": float(price.Price.price),
                "currency": price.Price.currency,
                "availability": price.Price.availability,
                "url": price.Price.url,
                "scraped_at": price.Price.scraped_at.isoformat() if price.Price.scraped_at else None
            }
            for price in prices
        ]
        
        best_price = min(competitor_prices, key=lambda x: x["price"])
        worst_price = max(competitor_prices, key=lambda x: x["price"])
        market_avg = sum(p["price"] for p in competitor_prices) / len(competitor_prices)
        our_price = self._resolve_reference_price(product)
        historical = self._build_historical_comparison(product_id, our_price, days=days)
        ranking = self._rank_competitors(product_id, days=days, our_price=our_price)
        all_hist_prices = [
            point["price"]
            for series in historical["historical_gap_evolution"]
            for point in series["points"]
            if point.get("price") is not None
        ]
        volatility = self._volatility_score(all_hist_prices)
        trend = self._trend_direction(all_hist_prices)
        price_position = self._price_position(our_price, market_avg)
        risk_score = self._risk_score(our_price, market_avg, best_price["price"], volatility, trend)
        
        result = {
            "product_id": product_id,
            "competitors": competitor_prices,
            "best_price": best_price,
            "cheapest_competitor": best_price,
            "most_expensive_competitor": worst_price,
            "average_market_price": market_avg,
            "reference_price": our_price,
            "price_position": price_position,
            "volatility_score": volatility,
            "trend_direction": trend,
            "historical_gap_evolution": historical["historical_gap_evolution"],
            "historical_snapshots": historical["historical_snapshots"],
            "competitor_ranking": ranking,
            "gain_loss_estimation": {
                "potential_revenue_loss": self._potential_loss(our_price, best_price["price"]),
                "estimated_competitiveness_risk": risk_score,
                "explanation": "Risk increases when our reference price is above market and competitors are frequently cheaper.",
            },
            "price_range": {
                "min": min(p["price"] for p in competitor_prices),
                "max": max(p["price"] for p in competitor_prices),
                "difference": max(p["price"] for p in competitor_prices) - min(p["price"] for p in competitor_prices)
            }
        }
        
        # Cache for 2 minutes
        self.cache.set(cache_key, result, ttl=120)
        
        return result

    def _resolve_reference_price(self, product: Product | None) -> Optional[float]:
        if not product:
            return None
        if product.target_price is not None:
            return float(product.target_price)
        latest = (
            self.db.query(Price)
            .filter(Price.product_id == product.id)
            .order_by(desc(Price.created_at))
            .first()
        )
        return float(latest.price) if latest else None

    def _build_historical_comparison(self, product_id: int, our_price: Optional[float], days: int) -> dict:
        start = datetime.utcnow() - timedelta(days=days)
        rows = (
            self.db.query(Price, Competitor.name.label("competitor_name"))
            .join(Competitor, Price.competitor_id == Competitor.id)
            .filter(Price.product_id == product_id, Price.created_at >= start)
            .order_by(Price.created_at.asc())
            .all()
        )
        grouped: dict[int, dict] = {}
        snapshots_by_day: dict[str, list[float]] = {}
        for row in rows:
            price = row.Price
            cid = price.competitor_id
            rec = grouped.setdefault(
                cid,
                {
                    "competitor_id": cid,
                    "competitor_name": row.competitor_name,
                    "points": [],
                },
            )
            ts = price.scraped_at or price.created_at
            day_key = ts.date().isoformat()
            price_value = float(price.price)
            snapshots_by_day.setdefault(day_key, []).append(price_value)
            rec["points"].append(
                {
                    "date": ts.isoformat(),
                    "price": price_value,
                    "gap": (price_value - our_price) if our_price is not None else None,
                    "gap_pct": ((price_value - our_price) / our_price * 100.0)
                    if our_price
                    else None,
                    "availability": price.availability,
                }
            )

        snapshots = []
        for day, values in sorted(snapshots_by_day.items()):
            snapshots.append(
                {
                    "date": day,
                    "market_average": sum(values) / len(values),
                    "market_min": min(values),
                    "market_max": max(values),
                    "reference_price": our_price,
                    "reference_gap": (sum(values) / len(values) - our_price)
                    if our_price is not None
                    else None,
                }
            )
        return {
            "historical_gap_evolution": list(grouped.values()),
            "historical_snapshots": snapshots,
        }

    def _rank_competitors(self, product_id: int, days: int, our_price: Optional[float]) -> list[dict]:
        start = datetime.utcnow() - timedelta(days=days)
        rows = (
            self.db.query(Price, Competitor.name.label("competitor_name"))
            .join(Competitor, Price.competitor_id == Competitor.id)
            .filter(Price.product_id == product_id, Price.created_at >= start)
            .all()
        )
        by_comp: dict[int, dict] = {}
        all_by_date: dict[str, list[tuple[int, float]]] = {}
        for row in rows:
            price = row.Price
            cid = price.competitor_id
            value = float(price.price)
            by_comp.setdefault(
                cid,
                {
                    "competitor_id": cid,
                    "competitor_name": row.competitor_name,
                    "prices": [],
                    "below_reference": 0,
                },
            )
            by_comp[cid]["prices"].append(value)
            if our_price is not None and value < our_price:
                by_comp[cid]["below_reference"] += 1
            all_by_date.setdefault(price.created_at.date().isoformat(), []).append((cid, value))

        lowest_counts: dict[int, int] = {cid: 0 for cid in by_comp}
        for values in all_by_date.values():
            if not values:
                continue
            min_price = min(v for _, v in values)
            for cid, value in values:
                if value == min_price:
                    lowest_counts[cid] = lowest_counts.get(cid, 0) + 1

        ranking = []
        for cid, rec in by_comp.items():
            prices = rec["prices"]
            avg_price = sum(prices) / len(prices)
            avg_gap = (avg_price - our_price) if our_price is not None else None
            below_rate = rec["below_reference"] / len(prices) if prices else 0.0
            lowest_freq = lowest_counts.get(cid, 0)
            aggressiveness = round((below_rate * 0.7) + (lowest_freq / max(1, len(all_by_date)) * 0.3), 4)
            ranking.append(
                {
                    "competitor_id": cid,
                    "competitor_name": rec["competitor_name"],
                    "average_price": avg_price,
                    "average_gap": avg_gap,
                    "lowest_price_frequency": lowest_freq,
                    "below_reference_rate": below_rate,
                    "aggressiveness_score": aggressiveness,
                }
            )
        ranking.sort(key=lambda item: (-item["aggressiveness_score"], item["average_price"]))
        return ranking

    def _volatility_score(self, values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        avg = sum(values) / len(values)
        if avg <= 0:
            return 0.0
        changes = sum(1 for prev, cur in zip(values, values[1:]) if prev != cur)
        dispersion = statistics.pstdev(values) / avg
        return round(min(1.0, dispersion + (changes / max(1, len(values) - 1) * 0.25)), 4)

    def _trend_direction(self, values: list[float]) -> str:
        if len(values) < 3:
            return "stable"
        first = values[0]
        if first <= 0:
            return "stable"
        pct = (values[-1] - first) / first * 100.0
        if pct >= 3:
            return "rising"
        if pct <= -3:
            return "decreasing"
        return "stable"

    def _price_position(self, our_price: Optional[float], market_avg: Optional[float]) -> str:
        if our_price is None or market_avg is None or market_avg <= 0:
            return "unknown"
        diff_pct = (our_price - market_avg) / market_avg * 100.0
        if diff_pct <= -3:
            return "below market"
        if diff_pct >= 3:
            return "above market"
        return "aligned"

    def _potential_loss(self, our_price: Optional[float], best_competitor_price: Optional[float]) -> float:
        if our_price is None or best_competitor_price is None or best_competitor_price >= our_price:
            return 0.0
        return round(our_price - best_competitor_price, 4)

    def _risk_score(
        self,
        our_price: Optional[float],
        market_avg: Optional[float],
        best_price: Optional[float],
        volatility: float,
        trend: str,
    ) -> str:
        if our_price is None or market_avg is None or best_price is None:
            return "unknown"
        score = 0.0
        if our_price > market_avg:
            score += min(0.45, (our_price - market_avg) / market_avg)
        if best_price < our_price:
            score += min(0.35, (our_price - best_price) / our_price)
        score += min(0.2, volatility * 0.2)
        if trend == "decreasing":
            score += 0.1
        if score >= 0.45:
            return "high"
        if score >= 0.2:
            return "medium"
        return "low"
    
    def get_market_insights(
        self,
        user_id: int,
        days: int = 7
    ) -> dict:
        """Get market insights for user's products"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get products with price changes
        products = self.db.query(Product).filter(Product.user_id == user_id).all()
        
        insights = []
        for product in products:
            recent_prices = self.db.query(Price).filter(
                Price.product_id == product.id,
                Price.created_at >= start_date
            ).order_by(desc(Price.created_at)).limit(2).all()
            
            if len(recent_prices) >= 2:
                price_change = recent_prices[0].price - recent_prices[1].price
                price_change_percent = (price_change / recent_prices[1].price) * 100
                
                insights.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "current_price": float(recent_prices[0].price),
                    "previous_price": float(recent_prices[1].price),
                    "price_change": float(price_change),
                    "price_change_percent": float(price_change_percent),
                    "trend": "up" if price_change > 0 else "down" if price_change < 0 else "stable"
                })
        
        return {
            "period_days": days,
            "insights": insights,
            "total_products": len(products)
        }

