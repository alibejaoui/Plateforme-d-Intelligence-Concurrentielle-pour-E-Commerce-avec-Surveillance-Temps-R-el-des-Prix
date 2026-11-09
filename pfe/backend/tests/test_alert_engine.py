from app.models.alert_rule import AlertRule
from app.models.competitive_alert import CompetitiveAlert
from app.models.missing_detection import MissingProduct
from app.models.product_match import ProductMatch
from app.services.competitive_alert_engine import CompetitiveAlertEngine
from tests.conftest import make_competitor_product, make_internal, make_product_with_prices


def test_aggressive_competitor_undercut_alert(db, user, competitor):
    internal = make_internal(db, user, price=100.0)
    competitor_product = make_competitor_product(db, competitor, price=80.0)
    db.add(ProductMatch(user_id=user.id, competitor_id=competitor.id, internal_product_id=internal.id, competitor_product_id=competitor_product.id, confidence_score=0.95, matching_method="sku"))
    db.add(AlertRule(user_id=user.id, competitor_id=competitor.id, name="Undercut", rule_type="competitor_undercut", threshold_value=5.0))
    db.commit()

    result = CompetitiveAlertEngine(db).evaluate_user(user.id)

    assert result["alerts_created"] == 1
    assert db.query(CompetitiveAlert).first().alert_type == "competitor_undercut"


def test_missing_product_alert(db, user, competitor):
    competitor_product = make_competitor_product(db, competitor, sku="NEW")
    db.add(MissingProduct(user_id=user.id, competitor_id=competitor.id, competitor_product_id=competitor_product.id, opportunity_score=0.7))
    db.add(AlertRule(user_id=user.id, competitor_id=competitor.id, name="Missing", rule_type="missing_internal_opportunity"))
    db.commit()

    result = CompetitiveAlertEngine(db).evaluate_user(user.id)

    assert result["alerts_created"] == 1
    assert db.query(CompetitiveAlert).first().alert_type == "missing_internal_opportunity"


def test_sudden_price_drop_alert(db, user, competitor):
    internal = make_internal(db, user, sku="DROP", gtin=None, price=120.0)
    competitor_product = make_competitor_product(db, competitor, sku="DROP", gtin=None, price=80.0)
    product = make_product_with_prices(db, user, competitor, sku="DROP", gtin=None, prices=[120.0, 80.0], target_price=120.0)
    db.add(ProductMatch(user_id=user.id, competitor_id=competitor.id, internal_product_id=internal.id, competitor_product_id=competitor_product.id, confidence_score=0.95, matching_method="sku"))
    db.add(AlertRule(user_id=user.id, competitor_id=competitor.id, name="Drop", rule_type="sudden_price_drop", threshold_value=10.0))
    db.commit()

    result = CompetitiveAlertEngine(db).evaluate_user(user.id)

    assert result["alerts_created"] == 1
    assert db.query(CompetitiveAlert).first().alert_type == "sudden_price_drop"
