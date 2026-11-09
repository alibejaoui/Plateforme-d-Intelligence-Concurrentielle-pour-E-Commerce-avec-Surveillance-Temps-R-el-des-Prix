"""
Advanced competitor comparison matrix service.
"""

from __future__ import annotations

from collections import defaultdict
from io import StringIO
import csv
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.internal_product import InternalProduct
from app.models.competitor import Competitor
from app.models.competitor_product import CompetitorProduct
from app.models.product_match import ProductMatch


class ComparisonMatrixService:
    def __init__(self, db: Session):
        self.db = db

    def get_matrix(
        self,
        *,
        user_id: int,
        competitor_ids: list[int] | None = None,
        category: str | None = None,
        brand: str | None = None,
        search: str | None = None,
        min_confidence: float | None = None,
        skip: int = 0,
        limit: int = 50,
        sort_by: str = "name",
        sort_dir: str = "asc",
    ) -> dict[str, Any]:
        q = self.db.query(InternalProduct).filter(InternalProduct.user_id == user_id)
        if category:
            q = q.filter(InternalProduct.category == category)
        if brand:
            q = q.filter(InternalProduct.brand == brand)
        if search:
            like = f"%{search}%"
            q = q.filter((InternalProduct.name.like(like)) | (InternalProduct.sku.like(like)))

        total = q.count()
        rows = q.offset(skip).limit(limit).all()
        if not rows:
            return {"items": [], "total": total, "competitors": []}

        internal_ids = [r.id for r in rows]

        cq = self.db.query(Competitor).filter(Competitor.is_active == True)
        if competitor_ids:
            cq = cq.filter(Competitor.id.in_(competitor_ids))
        competitors = cq.all()
        competitor_ids_final = [c.id for c in competitors]

        mq = (
            self.db.query(ProductMatch, CompetitorProduct)
            .join(CompetitorProduct, ProductMatch.competitor_product_id == CompetitorProduct.id)
            .filter(
                ProductMatch.user_id == user_id,
                ProductMatch.internal_product_id.in_(internal_ids),
                ProductMatch.competitor_id.in_(competitor_ids_final),
            )
        )
        if min_confidence is not None:
            mq = mq.filter(ProductMatch.confidence_score >= min_confidence)
        pairs = mq.all()

        by_internal: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for m, cp in pairs:
            by_internal[m.internal_product_id].append(
                {
                    "competitor_id": m.competitor_id,
                    "competitor_product_id": cp.id,
                    "title": cp.title,
                    "price": cp.price,
                    "currency": cp.currency,
                    "availability": cp.availability,
                    "url": cp.url,
                    "confidence_score": m.confidence_score,
                    "review_status": m.review_status,
                }
            )

        items = []
        for ip in rows:
            cells = by_internal.get(ip.id, [])
            cheapest = None
            for c in cells:
                if c["price"] is None:
                    continue
                if cheapest is None or c["price"] < cheapest:
                    cheapest = c["price"]
            cell_map = {c["competitor_id"]: c for c in cells}
            items.append(
                {
                    "internal_product_id": ip.id,
                    "internal_name": ip.name,
                    "brand": ip.brand,
                    "category": ip.category,
                    "sku": ip.sku,
                    "gtin": ip.gtin,
                    "our_price": ip.price,
                    "availability": ip.availability,
                    "cells": cell_map,
                    "matched_competitors": len(cells),
                    "missing_competitors": max(0, len(competitor_ids_final) - len(cells)),
                    "cheapest_competitor_price": cheapest,
                }
            )

        reverse = sort_dir.lower() == "desc"
        if sort_by == "price":
            items.sort(key=lambda x: (x["our_price"] is None, x["our_price"]), reverse=reverse)
        elif sort_by == "coverage":
            items.sort(key=lambda x: x["matched_competitors"], reverse=not reverse)
        else:
            items.sort(key=lambda x: (x["internal_name"] or "").lower(), reverse=reverse)

        return {
            "items": items,
            "total": total,
            "competitors": [{"id": c.id, "name": c.name} for c in competitors],
            "page": (skip // limit + 1) if limit else 1,
            "page_size": limit,
        }

    def export_matrix_csv(self, matrix: dict[str, Any]) -> str:
        output = StringIO()
        w = csv.writer(output)
        competitors = matrix.get("competitors", [])
        header = ["internal_product_id", "name", "brand", "category", "sku", "our_price", "availability"]
        for c in competitors:
            header.extend(
                [
                    f"{c['name']}_price",
                    f"{c['name']}_availability",
                    f"{c['name']}_confidence",
                ]
            )
        w.writerow(header)
        for row in matrix.get("items", []):
            base = [
                row["internal_product_id"],
                row["internal_name"],
                row.get("brand"),
                row.get("category"),
                row.get("sku"),
                row.get("our_price"),
                row.get("availability"),
            ]
            cells = row.get("cells", {})
            for c in competitors:
                cell = cells.get(c["id"])
                if cell:
                    base.extend([cell.get("price"), cell.get("availability"), cell.get("confidence_score")])
                else:
                    base.extend(["", "", ""])
            w.writerow(base)
        return output.getvalue()

