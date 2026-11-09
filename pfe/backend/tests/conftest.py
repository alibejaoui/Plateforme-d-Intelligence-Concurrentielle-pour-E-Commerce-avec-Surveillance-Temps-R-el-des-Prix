import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DEBUG", "false")
if os.environ.get("DEBUG") == "release":
    os.environ["DEBUG"] = "false"

from app.models.base import Base
from app.models import (  # noqa: F401
    alert,
    alert_rule,
    catalog_source,
    competitive_alert,
    competitor,
    competitor_product,
    crawl_session,
    import_job,
    internal_product,
    missing_detection,
    price,
    product,
    product_match,
    scraping_job,
    source,
    user,
)
from app.models.user import User
from app.models.competitor import Competitor
from app.models.internal_product import InternalProduct
from app.models.competitor_product import CompetitorProduct
from app.models.product import Product
from app.models.price import Price


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def user(db):
    row = User(email="analyst@example.com", hashed_password="x", full_name="Analyst")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@pytest.fixture()
def competitor(db):
    row = Competitor(
        name="CompA",
        website_url="https://comp.example",
        base_url="https://comp.example",
        scraping_config="{}",
        rate_limit_per_minute=120,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def make_internal(db, user, **kwargs):
    defaults = {
        "user_id": user.id,
        "name": "Apple iPhone 15 128GB Black",
        "brand": "Apple",
        "sku": "IP15-128-BLK",
        "gtin": "0001112223334",
        "category": "Phones",
        "url": "https://shop.example/iphone-15",
        "price": 999.0,
        "currency": "EUR",
        "availability": "in_stock",
    }
    defaults.update(kwargs)
    row = InternalProduct(**defaults)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def make_competitor_product(db, competitor, **kwargs):
    defaults = {
        "competitor_id": competitor.id,
        "title": "Apple iPhone 15 128 Go Noir",
        "brand": "Apple",
        "sku": "IP15-128-BLK",
        "gtin": "0001112223334",
        "category": "Phones",
        "url": "https://comp.example/iphone-15",
        "price": 949.0,
        "currency": "EUR",
        "availability": "in_stock",
    }
    defaults.update(kwargs)
    row = CompetitorProduct(**defaults)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def make_product_with_prices(db, user, competitor, **kwargs):
    product = Product(
        user_id=user.id,
        name=kwargs.get("name", "Apple iPhone 15"),
        sku=kwargs.get("sku", "IP15-128-BLK"),
        gtin=kwargs.get("gtin", "0001112223334"),
        category="Phones",
        brand="Apple",
        target_price=kwargs.get("target_price", 999.0),
    )
    db.add(product)
    db.flush()
    now = datetime.utcnow()
    for idx, value in enumerate(kwargs.get("prices", [990.0, 970.0, 950.0])):
        db.add(
            Price(
                product_id=product.id,
                competitor_id=competitor.id,
                price=value,
                currency="EUR",
                availability="in_stock",
                url="https://comp.example/iphone-15",
                scraped_at=now - timedelta(days=3 - idx),
                created_at=now - timedelta(days=3 - idx),
            )
        )
    db.commit()
    db.refresh(product)
    return product
