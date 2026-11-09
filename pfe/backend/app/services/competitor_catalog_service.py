"""
Competitor catalog crawling orchestration service.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.competitor import Competitor
from app.models.crawl_session import CrawlSession, CrawlSessionStatus

logger = get_logger(__name__)


class CompetitorCatalogService:
    def __init__(self, db: Session):
        self.db = db

    def start_sync(self, *, competitor_id: int, user_id: int | None, seed_url: str | None = None) -> CrawlSession:
        competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            raise ValueError("Competitor not found")

        snapshot = None
        if competitor.scraping_config:
            snapshot = competitor.scraping_config

        session = CrawlSession(
            competitor_id=competitor_id,
            user_id=user_id,
            status=CrawlSessionStatus.PENDING,
            seed_url=seed_url,
            config_snapshot=snapshot,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_config(self, session: CrawlSession) -> dict[str, Any]:
        raw = session.config_snapshot
        if not raw:
            return {}
        try:
            val = json.loads(raw)
            return val if isinstance(val, dict) else {}
        except Exception:
            return {}

