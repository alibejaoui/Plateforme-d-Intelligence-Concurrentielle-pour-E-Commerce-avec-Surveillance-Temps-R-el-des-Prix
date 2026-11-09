"""
Competitive intelligence endpoints:
- matching engine run
- matrix comparison
- missing/new detection
- historical intelligence
- match review workflow
- alert rules and generated alerts
- crawl monitoring
"""

import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.internal_product import InternalProduct
from app.models.competitor_product import CompetitorProduct
from app.models.competitor import Competitor
from app.models.product_match import ProductMatch
from app.models.missing_detection import MissingProduct
from app.models.alert_rule import AlertRule
from app.models.competitive_alert import CompetitiveAlert
from app.models.crawl_session import CrawlSession, CrawlError
from app.services.matching_service import MatchingService
from app.services.missing_detection_service import MissingDetectionService
from app.services.comparison_matrix_service import ComparisonMatrixService
from app.services.historical_intelligence_service import HistoricalIntelligenceService
from app.services.competitive_alert_engine import CompetitiveAlertEngine
from app.api.schemas.intelligence_schema import (
    MatchingRunRequest,
    MatchingRunResponse,
    MissingDetectionResponse,
    CoverageResponse,
    MatchReviewRequest,
    AlertRuleCreateRequest,
)

router = APIRouter()

def _alert_rule_to_dict(r: AlertRule) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "competitor_id": r.competitor_id,
        "name": r.name,
        "rule_type": r.rule_type,
        "is_active": r.is_active,
        "threshold_value": r.threshold_value,
        "config": r.config,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
    }


def _competitive_alert_to_dict(a: CompetitiveAlert) -> dict:
    return {
        "id": a.id,
        "user_id": a.user_id,
        "competitor_id": a.competitor_id,
        "internal_product_id": a.internal_product_id,
        "competitor_product_id": a.competitor_product_id,
        "alert_rule_id": a.alert_rule_id,
        "alert_type": a.alert_type,
        "title": a.title,
        "message": a.message,
        "severity": a.severity,
        "status": a.status,
        "signal_score": a.signal_score,
        "payload": a.payload,
        "detected_at": a.detected_at,
        "acknowledged_at": a.acknowledged_at,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
    }


@router.post("/matching/run", response_model=MatchingRunResponse)
async def run_matching(
    payload: MatchingRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = MatchingService(db)
    res = service.run_for_competitor(
        user_id=current_user.id,
        competitor_id=payload.competitor_id,
        min_confidence=payload.min_confidence,
    )
    return res


@router.post("/missing-products/recompute", response_model=MissingDetectionResponse)
async def recompute_missing_products(
    competitor_id: int = Query(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = MissingDetectionService(db)
    return service.recompute_for_competitor(user_id=current_user.id, competitor_id=competitor_id)


@router.get("/coverage", response_model=CoverageResponse)
async def get_coverage(
    competitor_id: int = Query(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    internal_total = (
        db.query(InternalProduct).filter(InternalProduct.user_id == current_user.id).count()
    )
    competitor_total = (
        db.query(CompetitorProduct).filter(CompetitorProduct.competitor_id == competitor_id).count()
    )
    matched_internal = (
        db.query(ProductMatch.internal_product_id)
        .filter(ProductMatch.user_id == current_user.id, ProductMatch.competitor_id == competitor_id)
        .distinct()
        .count()
    )
    matched_competitor = (
        db.query(ProductMatch.competitor_product_id)
        .filter(ProductMatch.user_id == current_user.id, ProductMatch.competitor_id == competitor_id)
        .distinct()
        .count()
    )

    internal_cov = (matched_internal / internal_total * 100.0) if internal_total else 0.0
    competitor_cov = (matched_competitor / competitor_total * 100.0) if competitor_total else 0.0

    return {
        "competitor_id": competitor_id,
        "internal_total": internal_total,
        "competitor_total": competitor_total,
        "matched_internal": matched_internal,
        "matched_competitor": matched_competitor,
        "internal_coverage_pct": internal_cov,
        "competitor_coverage_pct": competitor_cov,
    }


@router.get("/missing-products")
async def get_missing_products(
    competitor_id: int = Query(..., ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(MissingProduct, CompetitorProduct)
        .join(CompetitorProduct, MissingProduct.competitor_product_id == CompetitorProduct.id)
        .filter(
            MissingProduct.user_id == current_user.id,
            MissingProduct.competitor_id == competitor_id,
        )
        # MySQL doesn't support "NULLS LAST" reliably; emulate by sorting NULLs after values.
        .order_by(MissingProduct.opportunity_score.is_(None), MissingProduct.opportunity_score.desc(), MissingProduct.created_at.desc())
    )
    total = q.count()
    rows = q.offset(skip).limit(limit).all()

    items = []
    for mp, cp in rows:
        items.append(
            {
                "id": mp.id,
                "competitor_id": mp.competitor_id,
                "competitor_product_id": mp.competitor_product_id,
                "opportunity_score": mp.opportunity_score,
                "reason": mp.reason,
                "created_at": mp.created_at,
                "competitor_product": {
                    "title": cp.title,
                    "url": cp.url,
                    "brand": cp.brand,
                    "sku": cp.sku,
                    "gtin": cp.gtin,
                    "category": cp.category,
                    "price": cp.price,
                    "currency": cp.currency,
                    "availability": cp.availability,
                    "image_url": cp.image_url,
                },
            }
        )

    return {
        "items": items,
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "page_size": limit,
    }


@router.get("/competitor-catalog/products")
async def get_competitor_catalog_products(
    competitor_id: int | None = Query(None, ge=1),
    category: str | None = Query(None),
    availability: str | None = Query(None),
    search: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    matched: bool | None = Query(None),
    sort_by: str = Query("updated_at"),
    sort_dir: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Paginated competitor catalog viewer endpoint.

    Indexing recommendations:
    - competitor_products(competitor_id, category)
    - competitor_products(competitor_id, availability)
    - product_matches(competitor_product_id, user_id)
    Existing migrations already cover the highest-cardinality fields.
    """
    q = (
        db.query(CompetitorProduct, Competitor, ProductMatch, InternalProduct)
        .join(Competitor, CompetitorProduct.competitor_id == Competitor.id)
        .outerjoin(
            ProductMatch,
            (ProductMatch.competitor_product_id == CompetitorProduct.id)
            & (ProductMatch.user_id == current_user.id),
        )
        .outerjoin(InternalProduct, ProductMatch.internal_product_id == InternalProduct.id)
    )
    if competitor_id:
        q = q.filter(CompetitorProduct.competitor_id == competitor_id)
    if category:
        q = q.filter(CompetitorProduct.category == category)
    if availability:
        q = q.filter(CompetitorProduct.availability == availability)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (CompetitorProduct.title.like(like))
            | (CompetitorProduct.sku.like(like))
            | (CompetitorProduct.gtin.like(like))
            | (CompetitorProduct.brand.like(like))
        )
    if min_price is not None:
        q = q.filter(CompetitorProduct.price >= min_price)
    if max_price is not None:
        q = q.filter(CompetitorProduct.price <= max_price)
    if matched is True:
        q = q.filter(ProductMatch.id.isnot(None))
    elif matched is False:
        q = q.filter(ProductMatch.id.is_(None))

    total = q.count()
    sort_col = {
        "title": CompetitorProduct.title,
        "price": CompetitorProduct.price,
        "category": CompetitorProduct.category,
        "updated_at": CompetitorProduct.updated_at,
        "confidence": ProductMatch.confidence_score,
    }.get(sort_by, CompetitorProduct.updated_at)
    q = q.order_by(sort_col.asc() if sort_dir.lower() == "asc" else sort_col.desc())
    rows = q.offset(skip).limit(limit).all()

    items = []
    for cp, competitor, match, internal in rows:
        items.append(
            {
                "id": cp.id,
                "competitor_id": cp.competitor_id,
                "competitor_name": competitor.name,
                "title": cp.title,
                "brand": cp.brand,
                "sku": cp.sku,
                "gtin": cp.gtin,
                "category": cp.category,
                "url": cp.url,
                "image_url": cp.image_url,
                "price": cp.price,
                "currency": cp.currency,
                "availability": cp.availability,
                "last_seen": cp.updated_at,
                "created_at": cp.created_at,
                "matching_status": "matched" if match else "unmatched",
                "confidence_score": match.confidence_score if match else None,
                "matching_method": match.matching_method if match else None,
                "matched_internal_product": {
                    "id": internal.id,
                    "name": internal.name,
                    "sku": internal.sku,
                    "price": internal.price,
                    "url": internal.url,
                }
                if internal
                else None,
            }
        )

    facets = {
        "categories": [
            r[0]
            for r in db.query(CompetitorProduct.category)
            .filter(CompetitorProduct.category.isnot(None))
            .distinct()
            .order_by(CompetitorProduct.category.asc())
            .limit(200)
            .all()
        ],
        "availability": [
            r[0]
            for r in db.query(CompetitorProduct.availability)
            .filter(CompetitorProduct.availability.isnot(None))
            .distinct()
            .order_by(CompetitorProduct.availability.asc())
            .limit(50)
            .all()
        ],
    }
    return {"items": items, "total": total, "page": skip // limit + 1, "page_size": limit, "facets": facets}


@router.get("/matrix")
async def get_comparison_matrix(
    competitor_ids: str | None = Query(None, description="Comma-separated competitor ids"),
    category: str | None = Query(None),
    brand: str | None = Query(None),
    search: str | None = Query(None),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    sort_by: str = Query("name"),
    sort_dir: str = Query("asc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cids = [int(x) for x in competitor_ids.split(",") if x.strip().isdigit()] if competitor_ids else None
    service = ComparisonMatrixService(db)
    return service.get_matrix(
        user_id=current_user.id,
        competitor_ids=cids,
        category=category,
        brand=brand,
        search=search,
        min_confidence=min_confidence,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/matrix/export")
async def export_comparison_matrix_csv(
    competitor_ids: str | None = Query(None),
    category: str | None = Query(None),
    brand: str | None = Query(None),
    search: str | None = Query(None),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cids = [int(x) for x in competitor_ids.split(",") if x.strip().isdigit()] if competitor_ids else None
    service = ComparisonMatrixService(db)
    matrix = service.get_matrix(
        user_id=current_user.id,
        competitor_ids=cids,
        category=category,
        brand=brand,
        search=search,
        min_confidence=min_confidence,
        skip=0,
        limit=5000,
    )
    csv_data = service.export_matrix_csv(matrix)
    filename = f"comparison_matrix_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(csv_data.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/historical/matched-product/{internal_product_id}")
async def get_historical_matched_product(
    internal_product_id: int,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HistoricalIntelligenceService(db)
    return service.matched_product_history(
        user_id=current_user.id,
        internal_product_id=internal_product_id,
        days=days,
    )


@router.patch("/matches/{match_id}/review")
async def review_match(
    match_id: int,
    payload: MatchReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(ProductMatch).filter(ProductMatch.id == match_id, ProductMatch.user_id == current_user.id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    row.review_status = payload.review_status
    row.review_note = payload.review_note
    row.reviewed_at = datetime.utcnow()
    row.reviewed_by_user_id = current_user.id
    db.commit()
    db.refresh(row)
    return {"id": row.id, "review_status": row.review_status, "review_note": row.review_note}


@router.get("/matches/review-queue")
async def get_match_review_queue(
    competitor_id: int | None = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(ProductMatch, InternalProduct, CompetitorProduct)
        .join(InternalProduct, ProductMatch.internal_product_id == InternalProduct.id)
        .join(CompetitorProduct, ProductMatch.competitor_product_id == CompetitorProduct.id)
        .filter(ProductMatch.user_id == current_user.id, ProductMatch.review_status == "auto")
    )
    if competitor_id:
        q = q.filter(ProductMatch.competitor_id == competitor_id)
    total = q.count()
    rows = q.order_by(ProductMatch.confidence_score.asc()).offset(skip).limit(limit).all()
    items = [
        {
            "match_id": m.id,
            "confidence_score": m.confidence_score,
            "matching_method": m.matching_method,
            "internal": {"id": ip.id, "name": ip.name, "sku": ip.sku, "brand": ip.brand},
            "competitor": {"id": cp.id, "title": cp.title, "sku": cp.sku, "brand": cp.brand, "url": cp.url},
            "explanation": m.explanation,
        }
        for m, ip, cp in rows
    ]
    return {"items": items, "total": total, "page": skip // limit + 1, "page_size": limit}


@router.post("/ci-alert-rules")
async def create_alert_rule(
    payload: AlertRuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = AlertRule(
        user_id=current_user.id,
        competitor_id=payload.competitor_id,
        name=payload.name,
        rule_type=payload.rule_type,
        is_active=payload.is_active,
        threshold_value=payload.threshold_value,
        config=payload.config,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _alert_rule_to_dict(rule)


@router.get("/ci-alert-rules")
async def get_alert_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AlertRule)
        .filter(AlertRule.user_id == current_user.id)
        .order_by(AlertRule.created_at.desc())
        .all()
    )
    return {"items": [_alert_rule_to_dict(r) for r in rows]}


@router.post("/ci-alerts/evaluate")
async def evaluate_competitive_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = CompetitiveAlertEngine(db)
    return engine.evaluate_user(current_user.id)


@router.get("/ci-alerts")
async def get_competitive_alerts(
    status_filter: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(CompetitiveAlert).filter(CompetitiveAlert.user_id == current_user.id)
    if status_filter:
        q = q.filter(CompetitiveAlert.status == status_filter)
    total = q.count()
    rows = q.order_by(CompetitiveAlert.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "items": [_competitive_alert_to_dict(a) for a in rows],
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
    }


@router.get("/monitoring/crawls")
async def get_crawl_monitoring(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(CrawlSession).filter(CrawlSession.user_id == current_user.id)
    total = q.count()
    sessions = q.order_by(CrawlSession.created_at.desc()).offset(skip).limit(limit).all()
    items = []
    for s in sessions:
        err_count = db.query(CrawlError).filter(CrawlError.crawl_session_id == s.id).count()
        items.append(
            {
                "id": s.id,
                "competitor_id": s.competitor_id,
                "status": s.status,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
                "stats": s.stats,
                "errors_count": err_count,
            }
        )
    return {"items": items, "total": total, "page": skip // limit + 1, "page_size": limit}

