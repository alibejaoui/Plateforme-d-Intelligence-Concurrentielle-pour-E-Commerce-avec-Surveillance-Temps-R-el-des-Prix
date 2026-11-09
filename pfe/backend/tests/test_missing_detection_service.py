from app.models.missing_detection import MissingProduct, UnmatchedInternalProduct
from app.models.product_match import ProductMatch
from app.services.missing_detection_service import MissingDetectionService
from tests.conftest import make_competitor_product, make_internal


def test_detects_missing_competitor_and_unmatched_internal(db, user, competitor):
    make_internal(db, user, sku="OUR-1")
    make_competitor_product(db, competitor, sku="THEIR-1")

    result = MissingDetectionService(db).recompute_for_competitor(user_id=user.id, competitor_id=competitor.id)

    assert result["missing_competitor_products"] == 1
    assert result["unmatched_internal_products"] == 1
    assert db.query(MissingProduct).count() == 1
    assert db.query(UnmatchedInternalProduct).count() == 1


def test_matched_products_are_not_reported_missing(db, user, competitor):
    internal = make_internal(db, user, sku="SKU-1")
    competitor_product = make_competitor_product(db, competitor, sku="SKU-1")
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

    result = MissingDetectionService(db).recompute_for_competitor(user_id=user.id, competitor_id=competitor.id)

    assert result["missing_competitor_products"] == 0
    assert result["unmatched_internal_products"] == 0


def test_handles_competitor_duplicates_without_crashing(db, user, competitor):
    make_internal(db, user, sku="OUR-1")
    make_competitor_product(db, competitor, sku="DUP", url="https://comp.example/a")
    make_competitor_product(db, competitor, sku="DUP", url="https://comp.example/b")

    result = MissingDetectionService(db).recompute_for_competitor(user_id=user.id, competitor_id=competitor.id)

    assert result["missing_competitor_products"] == 2
    assert db.query(MissingProduct).count() == 2


def test_empty_catalogs_return_zero(db, user, competitor):
    result = MissingDetectionService(db).recompute_for_competitor(user_id=user.id, competitor_id=competitor.id)

    assert result["missing_competitor_products"] == 0
    assert result["unmatched_internal_products"] == 0
