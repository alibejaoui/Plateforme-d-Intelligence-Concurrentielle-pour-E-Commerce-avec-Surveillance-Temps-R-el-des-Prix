"""
Celery tasks for competitor catalog crawling.

Two phases:
1) Discovery: crawl listing/category pages, collect product URLs
2) Extraction: scrape each product URL and store competitor_products fields
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

from celery import Task, chord, group
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.competitor import Competitor
from app.models.crawl_session import CrawlSession, CrawlSessionStatus, CrawlError, CrawlSessionItem
from app.models.competitor_product import CompetitorProduct
from app.scraping.adapters import get_adapter

logger = get_logger(__name__)


def _safe_json_loads(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        val = json.loads(raw)
        return val if isinstance(val, dict) else {}
    except Exception:
        return {}


def _normalize_absolute_url(base_url: str, url: str | None) -> str | None:
    if not url:
        return None
    raw = str(url).strip()
    if not raw:
        return None
    abs_url = urljoin(base_url, raw)
    p = urlparse(abs_url)
    if p.scheme not in {"http", "https"} or not p.netloc:
        return None
    return abs_url


from app.scheduler.celery_app import celery_app  # noqa: E402


@celery_app.task(bind=True, name="competitors.catalog.discover_urls")
def discover_competitor_catalog_urls(self: Task, crawl_session_id: int) -> dict:
    db: Session = SessionLocal()
    try:
        session = db.query(CrawlSession).filter(CrawlSession.id == crawl_session_id).first()
        if not session:
            raise ValueError("CrawlSession not found")

        competitor = db.query(Competitor).filter(Competitor.id == session.competitor_id).first()
        if not competitor:
            raise ValueError("Competitor not found")

        cfg = _safe_json_loads(session.config_snapshot or competitor.scraping_config)
        cfg.setdefault("catalog", {})
        cfg["catalog"].setdefault("rate_limit_per_minute", competitor.rate_limit_per_minute)
        cat_cfg = (cfg.get("catalog") or {}) if isinstance(cfg, dict) else {}
        max_urls = int(cat_cfg.get("max_urls", 50_000))
        platform = cat_cfg.get("platform") or ((cfg or {}).get("platform")) or "generic"
        adapter = get_adapter(platform, cfg)
        base_url = (cat_cfg.get("base_url") or competitor.base_url or competitor.website_url or "").rstrip("/") + "/"

        seed_urls = cat_cfg.get("category_urls") or []
        if session.seed_url:
            seed_urls = [session.seed_url] + [u for u in seed_urls if u != session.seed_url]
        if not seed_urls:
            # fallback: try base_url as listing
            seed_urls = [base_url]
        normalized_seed_urls = [u for u in (_normalize_absolute_url(base_url, s) for s in seed_urls) if u]
        if not normalized_seed_urls:
            raise ValueError("No valid seed URLs after normalization")

        session.mark_started(CrawlSessionStatus.DISCOVERING)
        db.commit()
        try:
            discovered = set(adapter.discover_product_urls(normalized_seed_urls)) if normalized_seed_urls else set()
        except Exception as e:
            db.add(
                CrawlError(
                    crawl_session_id=session.id,
                    stage="discovery",
                    url=normalized_seed_urls[0] if normalized_seed_urls else base_url,
                    message=str(e),
                )
            )
            db.commit()
            raise

        # Create CompetitorProduct stubs (URL-only) for extraction phase
        created = 0
        invalid_urls = 0
        for u in list(discovered)[:max_urls]:
            abs_u = _normalize_absolute_url(base_url, u)
            if not abs_u:
                invalid_urls += 1
                db.add(
                    CrawlError(
                        crawl_session_id=session.id,
                        stage="discovery",
                        url=str(u),
                        message="Discarded invalid/relative product URL",
                    )
                )
                continue
            exists = (
                db.query(CompetitorProduct)
                .filter(CompetitorProduct.competitor_id == competitor.id, CompetitorProduct.url == abs_u)
                .first()
            )
            if exists:
                continue
            row = CompetitorProduct(
                competitor_id=competitor.id,
                title=abs_u,
                url=abs_u,
            )
            db.add(row)
            db.flush()
            db.add(CrawlSessionItem(crawl_session_id=session.id, competitor_product_id=row.id, discovered_url=abs_u))
            created += 1

        session.stats = {
            **(session.stats or {}),
            "discovered_urls": len(discovered),
            "created_stubs": created,
            "invalid_urls": invalid_urls,
            "scraper_health": adapter.health_status(),
        }
        db.commit()

        return {"success": True, "crawl_session_id": session.id, "discovered_urls": len(discovered)}
    finally:
        db.close()


@celery_app.task(bind=True, name="competitors.catalog.extract_product")
def extract_competitor_product(self: Task, crawl_session_id: int, competitor_product_id: int) -> dict:
    db: Session = SessionLocal()
    try:
        session = db.query(CrawlSession).filter(CrawlSession.id == crawl_session_id).first()
        if not session:
            raise ValueError("CrawlSession not found")
        competitor_product = db.query(CompetitorProduct).filter(CompetitorProduct.id == competitor_product_id).first()
        if not competitor_product:
            raise ValueError("CompetitorProduct not found")
        competitor = db.query(Competitor).filter(Competitor.id == session.competitor_id).first()
        if not competitor:
            raise ValueError("Competitor not found")

        cfg = _safe_json_loads(session.config_snapshot or competitor.scraping_config)
        cfg.setdefault("catalog", {})
        cfg["catalog"].setdefault("rate_limit_per_minute", competitor.rate_limit_per_minute)
        platform = ((cfg.get("catalog") or {}).get("platform") if isinstance(cfg, dict) else None) or ((cfg or {}).get("platform")) or "generic"
        adapter = get_adapter(platform, cfg)
        cat_cfg = (cfg.get("catalog") or {}) if isinstance(cfg, dict) else {}
        base_url = (cat_cfg.get("base_url") or competitor.base_url or competitor.website_url or "").rstrip("/") + "/"
        product_url = _normalize_absolute_url(base_url, competitor_product.url)
        if not product_url:
            raise ValueError(f"Invalid competitor product URL: {competitor_product.url!r}")
        if competitor_product.url != product_url:
            competitor_product.url = product_url
            db.flush()
        data = adapter.extract_product(product_url)

        competitor_product.title = data.get("title") or competitor_product.title
        competitor_product.price = data.get("price")
        competitor_product.currency = data.get("currency")
        competitor_product.availability = data.get("availability")
        competitor_product.image_url = data.get("image_url")
        competitor_product.brand = data.get("brand")
        competitor_product.sku = data.get("sku")
        competitor_product.gtin = data.get("gtin")
        competitor_product.category = data.get("category")
        competitor_product.raw = json.dumps({"fetched_at": datetime.utcnow().isoformat()}, ensure_ascii=False)

        db.commit()
        return {"success": True, "competitor_product_id": competitor_product.id, "scraper_health": adapter.health_status()}
    except Exception as e:
        error_msg = str(e)
        try:
            db.add(CrawlError(crawl_session_id=crawl_session_id, stage="extraction", url=None, message=error_msg))
            db.commit()
        except Exception:
            db.rollback()
        return {"success": False, "competitor_product_id": competitor_product_id, "error": error_msg}
    finally:
        db.close()


@celery_app.task(bind=True, name="competitors.catalog.finalize_crawl_session")
def finalize_crawl_session(self: Task, results: list[dict] | None, crawl_session_id: int) -> dict:
    """
    Finalize crawl session after extraction group finishes.
    Idempotent and retry-safe: repeated calls keep stable terminal state/stats.
    """
    db: Session = SessionLocal()
    try:
        session = db.query(CrawlSession).filter(CrawlSession.id == crawl_session_id).first()
        if not session:
            raise ValueError("CrawlSession not found")

        # Idempotency: if already finalized, return existing state.
        if session.status in {
            CrawlSessionStatus.COMPLETED,
            CrawlSessionStatus.COMPLETED_WITH_ERRORS,
            CrawlSessionStatus.FAILED,
            CrawlSessionStatus.CANCELLED,
        } and session.completed_at is not None:
            return {"success": True, "crawl_session_id": crawl_session_id, "status": str(session.status)}

        safe_results = results or []
        success_count = sum(
            1 for r in safe_results if isinstance(r, dict) and r.get("success") is True
        )
        failed_count = max(0, len(safe_results) - success_count)

        extraction_errors = (
            db.query(CrawlError)
            .filter(CrawlError.crawl_session_id == crawl_session_id, CrawlError.stage == "extraction")
            .count()
        )
        discovery_errors = (
            db.query(CrawlError)
            .filter(CrawlError.crawl_session_id == crawl_session_id, CrawlError.stage == "discovery")
            .count()
        )
        item_count = (
            db.query(CrawlSessionItem)
            .filter(CrawlSessionItem.crawl_session_id == crawl_session_id)
            .count()
        )

        prior_stats = session.stats or {}
        invalid_urls = int(prior_stats.get("invalid_urls", 0))

        final_stats = {
            **prior_stats,
            "session_items": item_count,
            "extracted_success": success_count,
            "extracted_failed": failed_count,
            "discovery_errors": discovery_errors,
            "extraction_errors": extraction_errors,
            "invalid_urls": invalid_urls,
        }

        has_errors = (failed_count > 0) or (extraction_errors > 0) or (discovery_errors > 0) or (invalid_urls > 0)
        session.status = (
            CrawlSessionStatus.COMPLETED_WITH_ERRORS if has_errors else CrawlSessionStatus.COMPLETED
        )
        session.completed_at = datetime.utcnow()
        session.stats = final_stats
        db.commit()
        return {
            "success": True,
            "crawl_session_id": crawl_session_id,
            "status": str(session.status),
            "stats": final_stats,
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="competitors.catalog.run_sync")
def run_competitor_catalog_sync(self: Task, crawl_session_id: int) -> dict:
    """
    Orchestrates discovery then extraction (fan-out).
    """
    db: Session = SessionLocal()
    try:
        session = db.query(CrawlSession).filter(CrawlSession.id == crawl_session_id).first()
        if not session:
            raise ValueError("CrawlSession not found")
        session.mark_started(CrawlSessionStatus.DISCOVERING)
        db.commit()
    finally:
        db.close()

    # Discovery first; if it fails, finalize as FAILED.
    try:
        discover_competitor_catalog_urls(crawl_session_id)
    except Exception as e:
        db_fail: Session = SessionLocal()
        try:
            s = db_fail.query(CrawlSession).filter(CrawlSession.id == crawl_session_id).first()
            if s:
                s.mark_failed(str(e))
                db_fail.commit()
        finally:
            db_fail.close()
        raise

    db2: Session = SessionLocal()
    try:
        session2 = db2.query(CrawlSession).filter(CrawlSession.id == crawl_session_id).first()
        if not session2:
            raise ValueError("CrawlSession not found")
        session2.status = CrawlSessionStatus.EXTRACTING
        db2.commit()

        product_ids = [
            r[0]
            for r in db2.query(CrawlSessionItem.competitor_product_id)
            .filter(CrawlSessionItem.crawl_session_id == crawl_session_id)
            .all()
        ]
        # Fan-out extraction
        cfg2 = _safe_json_loads(session2.config_snapshot) or {}
        max_extract = int(((cfg2.get("catalog") or {}).get("max_extract", 5000)))
        selected_ids = product_ids[:max_extract]
        if not selected_ids:
            # Nothing to extract; finalize immediately.
            res = finalize_crawl_session.delay([], crawl_session_id)
            session2.celery_group_id = res.id
            db2.commit()
            return {
                "success": True,
                "crawl_session_id": crawl_session_id,
                "extraction_group_id": res.id,
                "enqueued": 0,
            }
        jobs = group(extract_competitor_product.s(crawl_session_id, pid) for pid in selected_ids)
        # Run finalizer after all extract tasks finish (deterministic terminal state).
        callback = finalize_crawl_session.s(crawl_session_id)
        async_result = chord(jobs)(callback)
        session2.celery_group_id = async_result.id
        db2.commit()
        return {
            "success": True,
            "crawl_session_id": crawl_session_id,
            "extraction_group_id": async_result.id,
            "enqueued": len(selected_ids),
        }
    finally:
        db2.close()

