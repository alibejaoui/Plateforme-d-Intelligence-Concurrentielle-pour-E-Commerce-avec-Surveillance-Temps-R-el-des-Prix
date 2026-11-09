"""
Schemas for matching / missing / coverage endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class MatchingRunRequest(BaseModel):
    competitor_id: int
    min_confidence: float = Field(0.75, ge=0.0, le=1.0)


class MatchingRunResponse(BaseModel):
    success: bool
    created: int
    updated: int
    matched_competitor_products: int
    matched_internal_products: int
    total_competitor_products: int
    total_internal_products: int


class MissingDetectionResponse(BaseModel):
    success: bool
    missing_competitor_products: int
    unmatched_internal_products: int


class CoverageResponse(BaseModel):
    competitor_id: int
    internal_total: int
    competitor_total: int
    matched_internal: int
    matched_competitor: int
    internal_coverage_pct: float
    competitor_coverage_pct: float


class MatchReviewRequest(BaseModel):
    review_status: str = Field(..., pattern="^(accepted|rejected|auto)$")
    review_note: Optional[str] = None


class AlertRuleCreateRequest(BaseModel):
    name: str
    rule_type: str
    competitor_id: Optional[int] = None
    is_active: bool = True
    threshold_value: Optional[float] = None
    config: Optional[dict[str, Any]] = None

