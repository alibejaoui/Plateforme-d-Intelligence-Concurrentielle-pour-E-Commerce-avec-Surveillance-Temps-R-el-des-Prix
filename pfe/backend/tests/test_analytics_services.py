from datetime import datetime, timedelta

from app.models.missing_detection import MissingProduct
from app.models.product_match import ProductMatch
from app.models.price import Price
from app.services.analytics_service import AnalyticsService
from app.services.competitive_analytics_service import CompetitiveAnalyticsService
from app.services.historical_intelligence_service import HistoricalIntelligenceService
from tests.conftest import make_competitor_product, make_internal, make_product_with_prices


def seed_match(db, user, competitor):
    internal = make_internal(db, user, sku="IP15-128-BLK", gtin="0001112223334", price=999.0)
    competitor_product = make_competitor_product(db, competitor, sku="IP15-128-BLK", gtin="0001112223334", price=949.0)
    db.add(
        ProductMatch(
            user_id=user.id,
            competitor_id=competitor.id,
            internal_product_id=internal.id,
            competitor_product_id=competitor_product.id,
            confidence_score=0.99,
            matching_method="sku",
        )
    )
    db.commit()
    return internal, competitor_product


def test_opportunities_endpoint_service(db, user, competitor):
    competitor_product = make_competitor_product(db, competitor, sku="MISSING", price=49.0)
    db.add(MissingProduct(user_id=user.id, competitor_id=competitor.id, competitor_product_id=competitor_product.id, opportunity_score=0.8))
    db.commit()

    result = CompetitiveAnalyticsService(db).opportunities(user_id=user.id, competitor_id=competitor.id)

    assert result["total"] == 1
    assert result["items"][0]["opportunity_score"] == 0.8


def test_enriched_comparison_contains_historical_fields(db, user, competitor):
    product = make_product_with_prices(db, user, competitor, prices=[100.0, 95.0, 90.0], target_price=110.0)

    result = AnalyticsService(db).get_competitor_comparison(product.id, days=30)

    assert result["best_price"]["price"] == 90.0
    assert result["cheapest_competitor"]["price"] == 90.0
    assert result["average_market_price"] == 90.0
    assert result["historical_gap_evolution"]
    assert result["historical_snapshots"]
    assert result["competitor_ranking"]
    assert result["price_position"] in {"below market", "aligned", "above market", "unknown"}


def test_competitor_aggressiveness(db, user, competitor):
    seed_match(db, user, competitor)

    result = CompetitiveAnalyticsService(db).competitor_aggressiveness(user_id=user.id)

    assert result["total"] == 1
    assert result["items"][0]["undercut_products"] == 1


def test_historical_trend_retrieval_and_empty_history(db, user, competitor):
    internal, _ = seed_match(db, user, competitor)
    make_product_with_prices(db, user, competitor, prices=[10.0, 11.0, 12.0], target_price=13.0)

    result = HistoricalIntelligenceService(db).matched_product_history(user_id=user.id, internal_product_id=internal.id, days=30)

    assert result["series"]
    assert result["summary"]["max"] == 12.0
    empty = HistoricalIntelligenceService(db).matched_product_history(user_id=user.id, internal_product_id=999, days=30)
    assert empty["series"] == []


def test_risk_and_opportunity_products(db, user, competitor):
    seed_match(db, user, competitor)
    make_product_with_prices(db, user, competitor, prices=[1000.0, 980.0, 950.0], target_price=999.0)

    service = CompetitiveAnalyticsService(db)
    risks = service.products_at_risk(user_id=user.id)
    opps = service.opportunity_products(user_id=user.id)

    assert risks["items"]
    assert "strategic_recommendation" in risks["items"][0]
    assert opps["items"]
