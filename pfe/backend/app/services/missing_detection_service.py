"""
Missing / unmatched detection service.

- MissingProduct: competitor product has no match internally
- UnmatchedInternalProduct: internal product has no match at competitor
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.internal_product import InternalProduct
from app.models.competitor_product import CompetitorProduct
from app.models.product_match import ProductMatch
from app.models.missing_detection import MissingProduct, UnmatchedInternalProduct

logger = get_logger(__name__)


class MissingDetectionService:
    def __init__(self, db: Session):
        self.db = db

    def recompute_for_competitor(self, *, user_id: int, competitor_id: int) -> dict:
        internal_ids = [
            r[0]
            for r in self.db.query(InternalProduct.id)
            .filter(InternalProduct.user_id == user_id)
            .all()
        ]
        competitor_ids = [
            r[0]
            for r in self.db.query(CompetitorProduct.id)
            .filter(CompetitorProduct.competitor_id == competitor_id)
            .all()
        ]

        match_internal = set(
            r[0]
            for r in self.db.query(ProductMatch.internal_product_id)
            .filter(ProductMatch.competitor_id == competitor_id, ProductMatch.user_id == user_id)
            .all()
        )
        match_comp = set(
            r[0]
            for r in self.db.query(ProductMatch.competitor_product_id)
            .filter(ProductMatch.competitor_id == competitor_id, ProductMatch.user_id == user_id)
            .all()
        )

        missing_competitor = [pid for pid in competitor_ids if pid not in match_comp]
        unmatched_internal = [pid for pid in internal_ids if pid not in match_internal]

        # Clear previous computed rows
        self.db.query(MissingProduct).filter(
            MissingProduct.competitor_id == competitor_id,
            MissingProduct.user_id == user_id,
        ).delete(synchronize_session=False)
        self.db.query(UnmatchedInternalProduct).filter(
            UnmatchedInternalProduct.competitor_id == competitor_id,
            UnmatchedInternalProduct.user_id == user_id,
        ).delete(synchronize_session=False)
        self.db.flush()

        # Insert missing competitor products
        for cp_id in missing_competitor:
            self.db.add(
                MissingProduct(
                    competitor_id=competitor_id,
                    user_id=user_id,
                    competitor_product_id=cp_id,
                    opportunity_score=None,
                    reason="no_match",
                )
            )

        # Insert unmatched internal products
        for ip_id in unmatched_internal:
            self.db.add(
                UnmatchedInternalProduct(
                    competitor_id=competitor_id,
                    user_id=user_id,
                    internal_product_id=ip_id,
                    coverage_status="not_found",
                )
            )

        self.db.commit()
        return {
            "success": True,
            "missing_competitor_products": len(missing_competitor),
            "unmatched_internal_products": len(unmatched_internal),
        }

