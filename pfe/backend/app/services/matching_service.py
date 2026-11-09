"""
Product matching engine between internal_products and competitor_products.

Pipeline priority:
1) Exact: GTIN/EAN, SKU/MPN
2) Semi-exact: brand + normalized title tokens + category similarity
3) Fuzzy fallback: token similarity (Jaccard) + Levenshtein/ratio + TF-IDF cosine

All matches store an explanation payload for auditability.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable

try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover - exercised only when optional dependency is unavailable
    from difflib import SequenceMatcher

    class _FuzzFallback:
        @staticmethod
        def token_set_ratio(a: str, b: str) -> float:
            a_tokens = set(a.split())
            b_tokens = set(b.split())
            token_score = (len(a_tokens & b_tokens) / len(a_tokens | b_tokens) * 100.0) if (a_tokens and b_tokens) else 0.0
            seq_score = SequenceMatcher(None, a, b).ratio() * 100.0
            return max(token_score, seq_score)

    fuzz = _FuzzFallback()
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.internal_product import InternalProduct
from app.models.competitor_product import CompetitorProduct
from app.models.product_match import ProductMatch

logger = get_logger(__name__)


STOPWORDS = {
    "the",
    "and",
    "or",
    "a",
    "an",
    "de",
    "des",
    "du",
    "la",
    "le",
    "les",
    "pour",
    "avec",
    "sans",
    "et",
    "ou",
}


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def _normalize_text(s: str) -> str:
    s = _strip_accents((s or "").lower())
    s = re.sub(r"[^a-z0-9\s\-_/]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokenize(s: str) -> list[str]:
    s = _normalize_text(s)
    toks = [t for t in re.split(r"[\s\-_\/]+", s) if t and t not in STOPWORDS]
    return toks


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _safe_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


@dataclass(frozen=True)
class MatchResult:
    internal_id: int
    competitor_product_id: int
    competitor_id: int
    score: float
    method: str
    explanation: dict[str, Any]


class MatchingService:
    def __init__(self, db: Session):
        self.db = db

    def run_for_competitor(self, *, user_id: int, competitor_id: int, min_confidence: float = 0.75) -> dict:
        internal = (
            self.db.query(InternalProduct)
            .filter(InternalProduct.user_id == user_id)
            .all()
        )
        competitor_products = (
            self.db.query(CompetitorProduct)
            .filter(CompetitorProduct.competitor_id == competitor_id)
            .all()
        )

        # Build lookup maps for exact matching
        by_gtin: dict[str, list[InternalProduct]] = {}
        by_sku: dict[str, list[InternalProduct]] = {}
        for p in internal:
            if p.gtin:
                by_gtin.setdefault(p.gtin.strip(), []).append(p)
            if p.sku:
                by_sku.setdefault(p.sku.strip().upper(), []).append(p)

        created = 0
        updated = 0
        matched_competitor_ids: set[int] = set()
        matched_internal_ids: set[int] = set()

        # 1) Exact matching
        exact_results: list[MatchResult] = []
        for cp in competitor_products:
            best: MatchResult | None = None
            if cp.gtin and cp.gtin.strip() in by_gtin:
                candidates = by_gtin[cp.gtin.strip()]
                best = self._pick_best_name_similarity(
                    candidates=candidates,
                    competitor_title=cp.title,
                    competitor_product_id=cp.id,
                    competitor_id=competitor_id,
                    method="gtin",
                    base_score=0.98,
                    matched_fields={"gtin": cp.gtin.strip()},
                )
            if best is None and cp.sku and cp.sku.strip().upper() in by_sku:
                candidates = by_sku[cp.sku.strip().upper()]
                best = self._pick_best_name_similarity(
                    candidates=candidates,
                    competitor_title=cp.title,
                    competitor_product_id=cp.id,
                    competitor_id=competitor_id,
                    method="sku",
                    base_score=0.96,
                    matched_fields={"sku": cp.sku.strip().upper()},
                )
            if best:
                exact_results.append(best)

        for r in exact_results:
            c, u = self._upsert_match(user_id=user_id, result=r)
            created += c
            updated += u
            matched_competitor_ids.add(r.competitor_product_id)
            matched_internal_ids.add(r.internal_id)

        # 2) Semi-exact (brand + token overlap + category)
        remaining_competitors = [cp for cp in competitor_products if cp.id not in matched_competitor_ids]
        remaining_internal = [p for p in internal if p.id not in matched_internal_ids]
        semi_results: list[MatchResult] = []
        internal_by_brand: dict[str, list[InternalProduct]] = {}
        for p in remaining_internal:
            if p.brand:
                internal_by_brand.setdefault(_normalize_text(p.brand), []).append(p)

        for cp in remaining_competitors:
            cp_brand = _normalize_text(cp.brand) if cp.brand else None
            cp_tokens = set(_tokenize(cp.title))
            candidates = internal_by_brand.get(cp_brand, remaining_internal) if cp_brand else remaining_internal
            best = self._best_by_tokens(
                candidates=candidates,
                competitor=cp,
                competitor_id=competitor_id,
                method="brand_tokens",
            )
            if best and best.score >= min_confidence:
                semi_results.append(best)

        for r in semi_results:
            c, u = self._upsert_match(user_id=user_id, result=r)
            created += c
            updated += u
            matched_competitor_ids.add(r.competitor_product_id)
            matched_internal_ids.add(r.internal_id)

        # 3) Fuzzy fallback using TF-IDF cosine + rapidfuzz ratio
        remaining_competitors = [cp for cp in competitor_products if cp.id not in matched_competitor_ids]
        remaining_internal = [p for p in internal if p.id not in matched_internal_ids]
        fuzzy_results = self._fuzzy_tfidf_batch(
            candidates=remaining_internal,
            competitor_products=remaining_competitors,
            competitor_id=competitor_id,
            min_confidence=min_confidence,
        )
        for r in fuzzy_results:
            c, u = self._upsert_match(user_id=user_id, result=r)
            created += c
            updated += u
            matched_competitor_ids.add(r.competitor_product_id)
            matched_internal_ids.add(r.internal_id)

        return {
            "success": True,
            "created": created,
            "updated": updated,
            "matched_competitor_products": len(matched_competitor_ids),
            "matched_internal_products": len(matched_internal_ids),
            "total_competitor_products": len(competitor_products),
            "total_internal_products": len(internal),
        }

    def _pick_best_name_similarity(
        self,
        *,
        candidates: list[InternalProduct],
        competitor_title: str,
        competitor_product_id: int,
        competitor_id: int,
        method: str,
        base_score: float,
        matched_fields: dict[str, Any],
    ) -> MatchResult | None:
        best_p: InternalProduct | None = None
        best_ratio = -1.0
        comp_norm = _normalize_text(competitor_title)
        for p in candidates:
            ratio = fuzz.token_set_ratio(_normalize_text(p.name), comp_norm) / 100.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_p = p
        if not best_p:
            return None
        score = min(0.999, base_score + 0.02 * best_ratio)
        return MatchResult(
            internal_id=best_p.id,
            competitor_product_id=competitor_product_id,
            competitor_id=competitor_id,
            score=float(score),
            method=method,
            explanation={
                "matched_fields": matched_fields,
                "name_similarity": best_ratio,
                "competitor_title": competitor_title,
                "internal_name": best_p.name,
            },
        )

    def _best_by_tokens(
        self,
        *,
        candidates: list[InternalProduct],
        competitor: CompetitorProduct,
        competitor_id: int,
        method: str,
    ) -> MatchResult | None:
        comp_tokens = set(_tokenize(competitor.title))
        comp_cat = _normalize_text(competitor.category) if competitor.category else None
        comp_brand = _normalize_text(competitor.brand) if competitor.brand else None

        best: tuple[float, InternalProduct, dict[str, Any]] | None = None
        for p in candidates[: 20_000]:
            p_tokens = set(_tokenize(p.name))
            j = _jaccard(p_tokens, comp_tokens)
            brand_bonus = 0.08 if (comp_brand and p.brand and _normalize_text(p.brand) == comp_brand) else 0.0
            cat_bonus = 0.05 if (comp_cat and p.category and _normalize_text(p.category) == comp_cat) else 0.0
            ratio = fuzz.token_set_ratio(_normalize_text(p.name), _normalize_text(competitor.title)) / 100.0
            score = (0.55 * ratio) + (0.35 * j) + brand_bonus + cat_bonus

            if best is None or score > best[0]:
                best = (
                    score,
                    p,
                    {
                        "token_jaccard": j,
                        "token_set_ratio": ratio,
                        "brand_bonus": brand_bonus,
                        "category_bonus": cat_bonus,
                        "internal_tokens": sorted(list(p_tokens))[:30],
                        "competitor_tokens": sorted(list(comp_tokens))[:30],
                    },
                )
        if not best:
            return None
        score, p, details = best
        return MatchResult(
            internal_id=p.id,
            competitor_product_id=competitor.id,
            competitor_id=competitor_id,
            score=float(min(0.99, max(0.0, score))),
            method=method,
            explanation={
                **details,
                "competitor_title": competitor.title,
                "internal_name": p.name,
                "brand": {"internal": p.brand, "competitor": competitor.brand},
                "category": {"internal": p.category, "competitor": competitor.category},
            },
        )

    def _fuzzy_tfidf_batch(
        self,
        *,
        candidates: list[InternalProduct],
        competitor_products: list[CompetitorProduct],
        competitor_id: int,
        min_confidence: float,
    ) -> list[MatchResult]:
        if not candidates or not competitor_products:
            return []

        # Try TF-IDF, fallback to rapidfuzz-only when sklearn not available.
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except Exception:
            return self._fuzzy_rapidfuzz_only(
                candidates=candidates,
                competitor_products=competitor_products,
                competitor_id=competitor_id,
                min_confidence=min_confidence,
            )

        cand_texts = [_normalize_text(p.name) for p in candidates]
        comp_texts = [_normalize_text(cp.title) for cp in competitor_products]

        vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            max_features=50_000,
        )
        X = vectorizer.fit_transform(cand_texts + comp_texts)
        X_cand = X[: len(cand_texts)]
        X_comp = X[len(cand_texts) :]

        # Compute top-1 match per competitor product
        sims = cosine_similarity(X_comp, X_cand)  # shape [comp, cand]
        results: list[MatchResult] = []
        for i, cp in enumerate(competitor_products):
            row = sims[i]
            best_idx = int(row.argmax())
            tfidf_score = float(row[best_idx])
            cand = candidates[best_idx]

            ratio = fuzz.token_set_ratio(_normalize_text(cand.name), _normalize_text(cp.title)) / 100.0
            tokens_j = _jaccard(set(_tokenize(cand.name)), set(_tokenize(cp.title)))
            score = (0.50 * tfidf_score) + (0.35 * ratio) + (0.15 * tokens_j)

            if score >= min_confidence:
                results.append(
                    MatchResult(
                        internal_id=cand.id,
                        competitor_product_id=cp.id,
                        competitor_id=competitor_id,
                        score=float(min(0.98, score)),
                        method="fuzzy_tfidf",
                        explanation={
                            "tfidf_cosine": tfidf_score,
                            "token_set_ratio": ratio,
                            "token_jaccard": tokens_j,
                            "competitor_title": cp.title,
                            "internal_name": cand.name,
                        },
                    )
                )

        return results

    def _fuzzy_rapidfuzz_only(
        self,
        *,
        candidates: list[InternalProduct],
        competitor_products: list[CompetitorProduct],
        competitor_id: int,
        min_confidence: float,
    ) -> list[MatchResult]:
        results: list[MatchResult] = []
        for cp in competitor_products[: 20_000]:
            best: tuple[float, InternalProduct, dict[str, Any]] | None = None
            for p in candidates[: 20_000]:
                ratio = fuzz.token_set_ratio(_normalize_text(p.name), _normalize_text(cp.title)) / 100.0
                j = _jaccard(set(_tokenize(p.name)), set(_tokenize(cp.title)))
                score = 0.7 * ratio + 0.3 * j
                if best is None or score > best[0]:
                    best = (score, p, {"token_set_ratio": ratio, "token_jaccard": j})
            if best and best[0] >= min_confidence:
                score, p, details = best
                results.append(
                    MatchResult(
                        internal_id=p.id,
                        competitor_product_id=cp.id,
                        competitor_id=competitor_id,
                        score=float(min(0.95, score)),
                        method="fuzzy",
                        explanation={**details, "competitor_title": cp.title, "internal_name": p.name},
                    )
                )
        return results

    def _upsert_match(self, *, user_id: int, result: MatchResult) -> tuple[int, int]:
        existing = (
            self.db.query(ProductMatch)
            .filter(
                ProductMatch.internal_product_id == result.internal_id,
                ProductMatch.competitor_product_id == result.competitor_product_id,
            )
            .first()
        )
        if existing:
            changed = False
            if existing.confidence_score != result.score:
                existing.confidence_score = result.score
                changed = True
            if existing.matching_method != result.method:
                existing.matching_method = result.method
                changed = True
            existing.explanation = result.explanation
            existing.competitor_id = result.competitor_id
            existing.user_id = user_id
            if changed:
                self.db.flush()
                return (0, 1)
            return (0, 0)

        row = ProductMatch(
            internal_product_id=result.internal_id,
            competitor_product_id=result.competitor_product_id,
            competitor_id=result.competitor_id,
            user_id=user_id,
            confidence_score=result.score,
            matching_method=result.method,
            explanation=result.explanation,
        )
        self.db.add(row)
        self.db.flush()
        return (1, 0)

