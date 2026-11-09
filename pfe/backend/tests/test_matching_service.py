from app.models.product_match import ProductMatch
from app.services.matching_service import MatchingService
from tests.conftest import make_competitor_product, make_internal


def test_gtin_exact_match(db, user, competitor):
    internal = make_internal(db, user, sku="A1", gtin="1234567890123")
    competitor_product = make_competitor_product(db, competitor, sku="ZZ", gtin="1234567890123")

    result = MatchingService(db).run_for_competitor(user_id=user.id, competitor_id=competitor.id)

    match = db.query(ProductMatch).first()
    assert result["created"] == 1
    assert match.internal_product_id == internal.id
    assert match.competitor_product_id == competitor_product.id
    assert match.matching_method == "gtin"
    assert match.confidence_score >= 0.98


def test_sku_exact_match_when_gtin_absent(db, user, competitor):
    make_internal(db, user, sku="SKU-42", gtin=None)
    make_competitor_product(db, competitor, sku="sku-42", gtin=None)

    MatchingService(db).run_for_competitor(user_id=user.id, competitor_id=competitor.id)

    match = db.query(ProductMatch).first()
    assert match.matching_method == "sku"
    assert match.confidence_score >= 0.96


def test_fuzzy_name_and_category_match(db, user, competitor):
    make_internal(db, user, name="Samsung Galaxy S24 Ultra 256GB", brand="Samsung", sku=None, gtin=None, category="Phones")
    make_competitor_product(db, competitor, title="Samsung S24 Ultra Smartphone 256 Go", brand="Samsung", sku=None, gtin=None, category="Phones")

    MatchingService(db).run_for_competitor(user_id=user.id, competitor_id=competitor.id, min_confidence=0.55)

    match = db.query(ProductMatch).first()
    assert match is not None
    assert match.confidence_score >= 0.55
    assert match.matching_method in {"brand_tokens", "fuzzy_tfidf", "fuzzy"}


def test_brand_mismatch_rejection_prevents_false_positive(db, user, competitor):
    make_internal(db, user, name="Apple iPhone 15 128GB", brand="Apple", sku=None, gtin=None, category="Phones")
    make_competitor_product(db, competitor, title="Samsung Galaxy A15 128GB", brand="Samsung", sku=None, gtin=None, category="Phones")

    result = MatchingService(db).run_for_competitor(user_id=user.id, competitor_id=competitor.id, min_confidence=0.85)

    assert result["created"] == 0
    assert db.query(ProductMatch).count() == 0


def test_confidence_scoring_updates_existing_match(db, user, competitor):
    internal = make_internal(db, user, sku="SKU-100", gtin=None)
    competitor_product = make_competitor_product(db, competitor, sku="SKU-100", gtin=None)
    service = MatchingService(db)

    service.run_for_competitor(user_id=user.id, competitor_id=competitor.id)
    competitor_product.title = "Apple iPhone 15 Black 128GB"
    db.commit()
    result = service.run_for_competitor(user_id=user.id, competitor_id=competitor.id)

    assert result["created"] == 0
    assert db.query(ProductMatch).filter(ProductMatch.internal_product_id == internal.id).count() == 1
