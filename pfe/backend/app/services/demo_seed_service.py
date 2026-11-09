"""
Demo seed data for a stable CI/demo walkthrough.

Goal:
- deterministic sample dataset (products, internal_products, competitors, competitor_products)
- product_matches + missing_products + price history
- alert_rules seeded so the CI alert engine generates alerts reliably
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash
from app.models.competitor import Competitor
from app.models.internal_product import InternalProduct
from app.models.competitor_product import CompetitorProduct
from app.models.product_match import ProductMatch
from app.models.missing_detection import MissingProduct
from app.models.product import Product
from app.models.price import Price
from app.models.alert_rule import AlertRule
from app.services.competitive_alert_engine import CompetitiveAlertEngine


@dataclass(frozen=True)
class SeedUser:
    email: str
    password: str
    role: str
    full_name: str


DEMO_ADMIN = SeedUser(
    email="admin@platform.com",
    password="Admin123!",
    role="admin",
    full_name="Admin",
)

DEMO_ANALYST = SeedUser(
    email="analyst@platform.com",
    password="Analyst123!",
    role="analyst",
    full_name="Analyst",
)


def _now_anchor() -> datetime:
    # Keep pricing deterministic relative to "now", but consistent within one seed run.
    return datetime.utcnow().replace(microsecond=0)


class DemoSeedService:
    def __init__(self, db: Session):
        self.db = db

    def seed(self, *, reset: bool = True) -> dict:
        anchor = _now_anchor()

        admin = self._upsert_user(DEMO_ADMIN)
        analyst = self._upsert_user(DEMO_ANALYST)

        # For demo stability, remove previous demo rows if asked.
        if reset:
            self._reset_for_user(analyst.id)
            self._reset_demo_competitors()

        competitors = self._seed_competitors()
        internal = self._seed_internal_and_legacy_products(analyst.id)
        competitor_products = self._seed_competitor_products(competitors, internal)

        self._seed_matches_and_missing(analyst.id, internal, competitors, competitor_products)
        self._seed_price_history(analyst.id, internal, competitors, competitor_products, anchor)
        self._seed_alert_rules(analyst.id, competitors)

        # Generate alerts immediately for demo UX.
        alert_engine = CompetitiveAlertEngine(self.db)
        alerts_result = alert_engine.evaluate_user(analyst.id)

        return {
            "success": True,
            "seeded_user": {"id": analyst.id, "email": analyst.email, "role": analyst.role},
            "anchor": anchor.isoformat(),
            "alerts": alerts_result,
        }

    def _upsert_user(self, user: SeedUser) -> User:
        existing = self.db.query(User).filter(User.email == user.email).first()
        if existing:
            existing.hashed_password = get_password_hash(user.password)
            existing.role = user.role
            existing.full_name = user.full_name
            existing.is_active = True
            existing.is_superuser = user.role == "admin"
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        row = User(
            email=user.email,
            hashed_password=get_password_hash(user.password),
            full_name=user.full_name,
            is_active=True,
            is_superuser=user.role == "admin",
            role=user.role,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _reset_for_user(self, user_id: int) -> None:
        # Historical prices tied to Product ids (must be deleted before Product deletion).
        product_ids = [r.id for r in self.db.query(Product.id).filter(Product.user_id == user_id).all()]
        if product_ids:
            self.db.query(Price).filter(Price.product_id.in_(product_ids)).delete(synchronize_session=False)

        # CI tables
        self.db.query(ProductMatch).filter(ProductMatch.user_id == user_id).delete(synchronize_session=False)
        self.db.query(MissingProduct).filter(MissingProduct.user_id == user_id).delete(synchronize_session=False)
        self.db.query(InternalProduct).filter(InternalProduct.user_id == user_id).delete(synchronize_session=False)
        self.db.query(Product).filter(Product.user_id == user_id).delete(synchronize_session=False)

        # Legacy alerts (price threshold) not required for CI demo.
        self.db.commit()

        # Competitive alerts for user
        try:
            from app.models.competitive_alert import CompetitiveAlert

            self.db.query(CompetitiveAlert).filter(CompetitiveAlert.user_id == user_id).delete(synchronize_session=False)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def _reset_demo_competitors(self) -> None:
        demo_names = {"Demo Competitor A", "Demo Competitor B", "Demo Competitor C"}
        comps = self.db.query(Competitor).filter(Competitor.name.in_(list(demo_names))).all()
        for c in comps:
            self.db.query(CompetitorProduct).filter(CompetitorProduct.competitor_id == c.id).delete(synchronize_session=False)
            self.db.commit()

    def _seed_competitors(self) -> list[Competitor]:
        competitors = []
        for name, base_url in [
            ("Demo Competitor A", "https://example-a.test"),
            ("Demo Competitor B", "https://example-b.test"),
            ("Demo Competitor C", "https://example-c.test"),
        ]:
            row = self.db.query(Competitor).filter(Competitor.name == name).first()
            if not row:
                row = Competitor(
                    name=name,
                    website_url=base_url,
                    base_url=base_url,
                    description="demo competitor",
                    is_active=True,
                    scraping_config=json.dumps(
                        {
                            "platform": "generic",
                            "catalog": {
                                "base_url": base_url,
                                "product_link_selector": "a[href]",
                                "product_link_attr": "href",
                                "max_pages": 1,
                            },
                        }
                    ),
                    rate_limit_per_minute=10,
                )
                self.db.add(row)
                self.db.commit()
                self.db.refresh(row)
            competitors.append(row)
        return competitors

    def _seed_internal_and_legacy_products(self, user_id: int) -> dict:
        # internal + legacy (products) must share same sku and gtin for stable mapping.
        items = [
            {
                "sku": "SKU-1001",
                "gtin": "EAN-1001",
                "name": "Wireless Mouse Pro",
                "brand": "LogiDemo",
                "category": "Accessories",
                "url": "https://shop.example.com/products/wireless-mouse-pro",
                "image_url": "https://shop.example.com/img/mouse.jpg",
                "price": 100.0,
            },
            {
                "sku": "SKU-1002",
                "gtin": "EAN-1002",
                "name": "Mechanical Keyboard TKL",
                "brand": "KeyDemo",
                "category": "Accessories",
                "url": "https://shop.example.com/products/mech-keyboard-tkl",
                "image_url": "https://shop.example.com/img/keyboard.jpg",
                "price": 140.0,
            },
            {
                "sku": "SKU-1003",
                "gtin": "EAN-1003",
                "name": "27-inch Monitor QHD",
                "brand": "ViewDemo",
                "category": "Monitors",
                "url": "https://shop.example.com/products/monitor-27-qhd",
                "image_url": "https://shop.example.com/img/monitor.jpg",
                "price": 260.0,
            },
            {
                "sku": "SKU-2001",
                "gtin": "EAN-2001",
                "name": "USB-C Hub 7-in-1",
                "brand": "HubDemo",
                "category": "Accessories",
                "url": "https://shop.example.com/products/usb-c-hub-7-in-1",
                "image_url": "https://shop.example.com/img/hub.jpg",
                "price": 45.0,
            },
            {
                "sku": "SKU-2002",
                "gtin": "EAN-2002",
                "name": "Noise-Canceling Headphones",
                "brand": "SoundDemo",
                "category": "Audio",
                "url": "https://shop.example.com/products/nc-headphones",
                "image_url": "https://shop.example.com/img/headphones.jpg",
                "price": 180.0,
            },
        ]

        rows = {}
        for it in items:
            ip = (
                self.db.query(InternalProduct)
                .filter(InternalProduct.user_id == user_id, InternalProduct.sku == it["sku"])
                .first()
            )
            if not ip:
                ip = InternalProduct(
                    user_id=user_id,
                    name=it["name"],
                    brand=it["brand"],
                    sku=it["sku"],
                    gtin=it["gtin"],
                    category=it["category"],
                    url=it["url"],
                    image_url=it["image_url"],
                    price=it["price"],
                    currency="EUR",
                    availability="in_stock",
                    description=None,
                )
                self.db.add(ip)
                self.db.commit()
                self.db.refresh(ip)

            # Legacy products for Price history.
            legacy = self.db.query(Product).filter(Product.sku == it["sku"]).first()
            if not legacy:
                legacy = Product(
                    user_id=user_id,
                    name=it["name"],
                    description=None,
                    sku=it["sku"],
                    gtin=it["gtin"],
                    category=it["category"],
                    brand=it["brand"],
                    image_url=it["image_url"],
                    target_price=None,
                    min_price_threshold=None,
                    max_price_threshold=None,
                )
                self.db.add(legacy)
                self.db.commit()
                self.db.refresh(legacy)

            rows[it["sku"]] = {"internal": ip, "legacy": legacy}
        return rows

    def _seed_competitor_products(self, competitors: list[Competitor], internal_rows: dict) -> dict:
        # Map sku -> competitor_id -> competitor_product
        out = {}
        for comp in competitors:
            out[comp.id] = {}
            for sku, pair in internal_rows.items():
                ip = pair["internal"]
                # Create product on all competitors except intentionally missing ones for demo.
                # Missing: competitor C has only 2 products; competitor B misses SKU-2001 and SKU-2002
                if comp.name == "Demo Competitor C" and sku in {"SKU-1001", "SKU-1002", "SKU-1003"}:
                    continue
                if comp.name == "Demo Competitor B" and sku in {"SKU-2001", "SKU-2002"}:
                    continue

                url = f"{comp.base_url}/products/{sku.lower()}"
                existing = (
                    self.db.query(CompetitorProduct)
                    .filter(CompetitorProduct.competitor_id == comp.id, CompetitorProduct.url == url)
                    .first()
                )
                if not existing:
                    # Align `competitor_products.price` with what the alert/matrix logic expects.
                    our = float(ip.price or 0.0)
                    if comp.name == "Demo Competitor A":
                        competitor_price = our - 5.0
                    elif comp.name == "Demo Competitor B":
                        competitor_price = our - 20.0
                    else:
                        competitor_price = our + 15.0

                    existing = CompetitorProduct(
                        competitor_id=comp.id,
                        title=ip.name,
                        brand=ip.brand,
                        sku=ip.sku,
                        gtin=ip.gtin,
                        category=ip.category,
                        url=url,
                        image_url=ip.image_url,
                        price=competitor_price,
                        currency="EUR",
                        availability="in_stock" if not (comp.name == "Demo Competitor B" and sku == "SKU-1002") else "out_of_stock",
                        raw=None,
                    )
                    self.db.add(existing)
                    self.db.commit()
                    self.db.refresh(existing)
                out[comp.id][sku] = existing
        return out

    def _seed_matches_and_missing(self, user_id: int, internal_rows: dict, competitors: list[Competitor], competitor_products: dict) -> None:
        # Determine matched competitors by SKU:
        # - SKU-1001,1002,1003 matched in A and B
        # - SKU-2001,2002 matched only in A (B missing -> missing opportunity)
        compA = next(c for c in competitors if c.name == "Demo Competitor A")
        compB = next(c for c in competitors if c.name == "Demo Competitor B")
        compC = next(c for c in competitors if c.name == "Demo Competitor C")

        def upsert_match(internal_obj: InternalProduct, competitor_product: CompetitorProduct, competitor_id: int, conf: float, method: str) -> None:
            existing = (
                self.db.query(ProductMatch)
                .filter(
                    ProductMatch.internal_product_id == internal_obj.id,
                    ProductMatch.competitor_product_id == competitor_product.id,
                )
                .first()
            )
            if existing:
                existing.confidence_score = conf
                existing.matching_method = method
            else:
                self.db.add(
                    ProductMatch(
                        internal_product_id=internal_obj.id,
                        competitor_product_id=competitor_product.id,
                        competitor_id=competitor_id,
                        user_id=user_id,
                        confidence_score=conf,
                        matching_method=method,
                        explanation={"demo": True},
                        review_status="auto",
                    )
                )

        for sku, pair in internal_rows.items():
            internal_obj = pair["internal"]
            # Competitor A matches all
            cpA = competitor_products.get(compA.id, {}).get(sku)
            if cpA:
                upsert_match(internal_obj, cpA, compA.id, 0.96, "gtin")

            # Competitor B matches only first 3
            cpB = competitor_products.get(compB.id, {}).get(sku)
            if cpB:
                upsert_match(internal_obj, cpB, compB.id, 0.91, "sku")

            # Competitor C will be missing for all to create opportunity cards
            # Seed MissingProduct rows separately.

        # Clear and reinsert missing products for demo competitor C (those competitor products without match)
        self.db.query(MissingProduct).filter(MissingProduct.user_id == user_id).delete(synchronize_session=False)
        self.db.commit()

        # Create missing for competitor C for every competitor product we created.
        for sku, pair in internal_rows.items():
            internal_obj = pair["internal"]
            cpC = competitor_products.get(compC.id, {}).get(sku)
            if not cpC:
                continue
            # If there is no match on cpC, register missing.
            has_match = (
                self.db.query(ProductMatch)
                .filter(
                    ProductMatch.user_id == user_id,
                    ProductMatch.competitor_product_id == cpC.id,
                )
                .first()
            )
            if not has_match:
                self.db.add(
                    MissingProduct(
                        competitor_id=compC.id,
                        user_id=user_id,
                        competitor_product_id=cpC.id,
                        opportunity_score=0.8,
                        reason="no_match",
                        notes="demo missing internal product opportunity",
                        details={"demo": True},
                    )
                )

        self.db.commit()

    def _seed_price_history(self, user_id: int, internal_rows: dict, competitors: list[Competitor], competitor_products: dict, anchor: datetime) -> None:
        # Ensure we delete previous Price rows for our legacy products.
        product_ids = [pair["legacy"].id for pair in internal_rows.values()]
        self.db.query(Price).filter(Price.product_id.in_(product_ids)).delete(synchronize_session=False)
        self.db.commit()

        compA = next(c for c in competitors if c.name == "Demo Competitor A")
        compB = next(c for c in competitors if c.name == "Demo Competitor B")
        compC = next(c for c in competitors if c.name == "Demo Competitor C")

        # Pricing patterns:
        # - Competitor A slightly below our price
        # - Competitor B: sudden drop on last day for matched SKUs
        for idx in range(6, -1, -1):
            # idx runs 6..0, so day_ago = idx
            day_ago = idx
            day = anchor - timedelta(days=day_ago)
            for sku, pair in internal_rows.items():
                legacy = pair["legacy"]
                our = float(pair["internal"].price or 0.0)

                # A exists for all skus
                priceA = (our - 5.0) - (day_ago * 0.2)
                self.db.add(
                    Price(
                        product_id=legacy.id,
                        competitor_id=compA.id,
                        price=round(priceA, 2),
                        currency="EUR",
                        availability="in_stock",
                        url=(competitor_products.get(compA.id, {}).get(sku).url if competitor_products.get(compA.id, {}).get(sku) else None),
                        scraped_at=day,
                        created_at=day,
                    )
                )

                # B exists for first 3 SKUs only
                if sku in {"SKU-1001", "SKU-1002", "SKU-1003"}:
                    # Create a sudden drop between day_ago=1 (prev) and day_ago=0 (current).
                    if day_ago == 0:
                        priceB = our - 20.0
                    elif day_ago == 1:
                        priceB = our - 5.0
                    else:
                        priceB = our - 7.0
                    self.db.add(
                        Price(
                            product_id=legacy.id,
                            competitor_id=compB.id,
                            price=round(priceB, 2),
                            currency="EUR",
                            availability="in_stock" if sku != "SKU-1002" else "out_of_stock" if day_ago == 0 else "in_stock",
                            url=(competitor_products.get(compB.id, {}).get(sku).url if competitor_products.get(compB.id, {}).get(sku) else None),
                            scraped_at=day,
                            created_at=day,
                        )
                    )

                # C exists for missing opportunity SKUs; we seed its price history too for realism
                if sku in {"SKU-2001", "SKU-2002"}:
                    priceC = our + 15.0 + (day_ago * 0.2)
                    self.db.add(
                        Price(
                            product_id=legacy.id,
                            competitor_id=compC.id,
                            price=round(priceC, 2),
                            currency="EUR",
                            availability="in_stock",
                            url=(competitor_products.get(compC.id, {}).get(sku).url if competitor_products.get(compC.id, {}).get(sku) else None),
                            scraped_at=day,
                            created_at=day,
                        )
                    )

        self.db.commit()

    def _seed_alert_rules(self, user_id: int, competitors: list[Competitor]) -> None:
        compB = next(c for c in competitors if c.name == "Demo Competitor B")
        compC = next(c for c in competitors if c.name == "Demo Competitor C")

        # Recreate rules deterministically
        self.db.query(AlertRule).filter(AlertRule.user_id == user_id).delete(synchronize_session=False)
        self.db.commit()

        self.db.add(
            AlertRule(
                user_id=user_id,
                competitor_id=compB.id,
                name="Demo undercut (B vs ours)",
                rule_type="competitor_undercut",
                is_active=True,
                threshold_value=10.0,
                config={"demo": True},
            )
        )
        self.db.add(
            AlertRule(
                user_id=user_id,
                competitor_id=compB.id,
                name="Demo sudden drop (B)",
                rule_type="sudden_price_drop",
                is_active=True,
                threshold_value=10.0,
                config={"demo": True},
            )
        )
        self.db.add(
            AlertRule(
                user_id=user_id,
                competitor_id=compC.id,
                name="Demo missing opportunity (C)",
                rule_type="missing_internal_opportunity",
                is_active=True,
                threshold_value=None,
                config={"demo": True},
            )
        )
        self.db.commit()

