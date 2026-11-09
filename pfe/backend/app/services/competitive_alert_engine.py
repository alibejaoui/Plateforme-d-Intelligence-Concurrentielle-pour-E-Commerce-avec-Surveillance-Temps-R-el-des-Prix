"""
Competitive alert rules engine + scheduled evaluation.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.alert_rule import AlertRule
from app.models.competitive_alert import CompetitiveAlert
from app.models.product_match import ProductMatch
from app.models.internal_product import InternalProduct
from app.models.competitor_product import CompetitorProduct
from app.models.missing_detection import MissingProduct
from app.models.price import Price
from app.models.product import Product


class CompetitiveAlertEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_user(self, user_id: int) -> dict:
        rules = self.db.query(AlertRule).filter(AlertRule.user_id == user_id, AlertRule.is_active == True).all()
        created = 0
        for rule in rules:
            if rule.rule_type == "competitor_undercut":
                created += self._rule_undercut(rule)
            elif rule.rule_type == "missing_internal_opportunity":
                created += self._rule_missing(rule)
            elif rule.rule_type == "sudden_price_drop":
                created += self._rule_sudden_drop(rule)
        self.db.commit()
        return {"success": True, "rules_evaluated": len(rules), "alerts_created": created}

    def _create_alert_if_new(self, **kwargs) -> int:
        recent = self.db.query(CompetitiveAlert).filter(
            CompetitiveAlert.user_id == kwargs["user_id"],
            CompetitiveAlert.alert_type == kwargs["alert_type"],
            CompetitiveAlert.internal_product_id == kwargs.get("internal_product_id"),
            CompetitiveAlert.competitor_product_id == kwargs.get("competitor_product_id"),
            CompetitiveAlert.created_at >= datetime.utcnow() - timedelta(hours=12),
        ).first()
        if recent:
            return 0
        self.db.add(CompetitiveAlert(**kwargs, detected_at=datetime.utcnow(), status="open"))
        return 1

    def _rule_undercut(self, rule: AlertRule) -> int:
        created = 0
        threshold = rule.threshold_value if rule.threshold_value is not None else 0.0
        q = (
            self.db.query(ProductMatch, InternalProduct, CompetitorProduct)
            .join(InternalProduct, ProductMatch.internal_product_id == InternalProduct.id)
            .join(CompetitorProduct, ProductMatch.competitor_product_id == CompetitorProduct.id)
            .filter(ProductMatch.user_id == rule.user_id)
        )
        if rule.competitor_id:
            q = q.filter(ProductMatch.competitor_id == rule.competitor_id)
        for m, ip, cp in q.all():
            if ip.price is None or cp.price is None:
                continue
            if cp.price < ip.price - threshold:
                created += self._create_alert_if_new(
                    user_id=rule.user_id,
                    competitor_id=m.competitor_id,
                    internal_product_id=ip.id,
                    competitor_product_id=cp.id,
                    alert_rule_id=rule.id,
                    alert_type="competitor_undercut",
                    title="Competitor undercut detected",
                    message=f"{cp.title} is cheaper than your product {ip.name}",
                    severity="high",
                    signal_score=((ip.price - cp.price) / ip.price) if ip.price else None,
                    payload={"our_price": ip.price, "their_price": cp.price, "confidence": m.confidence_score},
                )
        return created

    def _rule_missing(self, rule: AlertRule) -> int:
        created = 0
        q = self.db.query(MissingProduct).filter(MissingProduct.user_id == rule.user_id)
        if rule.competitor_id:
            q = q.filter(MissingProduct.competitor_id == rule.competitor_id)
        for mp in q.limit(2000).all():
            created += self._create_alert_if_new(
                user_id=rule.user_id,
                competitor_id=mp.competitor_id,
                competitor_product_id=mp.competitor_product_id,
                alert_rule_id=rule.id,
                alert_type="missing_internal_opportunity",
                title="Missing product opportunity",
                message="Competitor product exists but is missing in your internal catalog",
                severity="medium",
                signal_score=mp.opportunity_score,
                payload={"missing_id": mp.id},
            )
        return created

    def _rule_sudden_drop(self, rule: AlertRule) -> int:
        created = 0
        threshold_pct = rule.threshold_value if rule.threshold_value is not None else 10.0
        q = self.db.query(ProductMatch).filter(ProductMatch.user_id == rule.user_id)
        if rule.competitor_id:
            q = q.filter(ProductMatch.competitor_id == rule.competitor_id)
        for m in q.all():
            ip = (
                self.db.query(InternalProduct)
                .filter(InternalProduct.user_id == rule.user_id, InternalProduct.id == m.internal_product_id)
                .first()
            )
            if not ip:
                continue
            product_id = None
            if ip.sku:
                p = self.db.query(Product).filter(Product.user_id == rule.user_id, Product.sku == ip.sku).first()
                if p:
                    product_id = p.id
            if product_id is None and ip.gtin:
                p2 = self.db.query(Product).filter(Product.user_id == rule.user_id, Product.gtin == ip.gtin).first()
                if p2:
                    product_id = p2.id
            if not product_id:
                continue
            prices = (
                self.db.query(Price)
                .filter(Price.product_id == product_id, Price.competitor_id == m.competitor_id)
                .order_by(Price.created_at.desc())
                .limit(2)
                .all()
            )
            if len(prices) < 2:
                continue
            cur = float(prices[0].price)
            prev = float(prices[1].price)
            if prev <= 0:
                continue
            drop_pct = (prev - cur) / prev * 100.0
            if drop_pct >= threshold_pct:
                created += self._create_alert_if_new(
                    user_id=rule.user_id,
                    competitor_id=m.competitor_id,
                    internal_product_id=m.internal_product_id,
                    alert_rule_id=rule.id,
                    alert_type="sudden_price_drop",
                    title="Sudden competitor price drop",
                    message=f"Competitor price dropped by {drop_pct:.1f}%",
                    severity="high",
                    signal_score=drop_pct,
                    payload={"prev": prev, "cur": cur},
                )
        return created

