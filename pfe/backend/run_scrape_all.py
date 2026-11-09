import json
from sqlalchemy import text
from app.core.database import SessionLocal
from app.scraping.scraping_manager import ScrapingManager

DEFAULT_CFG = {
    "base_url": "https://webscraper.io/test-sites/e-commerce/allinone",
    "search_url_template": "{base_url}",
    "link_selector": "a.title",
    "price_selector": "h4.price",
    "currency": "USD",
}

db = SessionLocal()
manager = ScrapingManager(db)

try:
    competitors = db.execute(text("SELECT id FROM competitors")).fetchall()
    products = db.execute(text("SELECT id FROM products")).fetchall()

    for competitor in competitors:
        competitor_id = competitor.id

        db.execute(
            text(
                "UPDATE competitors "
                "SET base_url=:base_url, scraping_config=:scraping_config "
                "WHERE id=:id"
            ),
            {
                "id": competitor_id,
                "base_url": DEFAULT_CFG["base_url"],
                "scraping_config": json.dumps(DEFAULT_CFG),
            },
        )
        db.commit()

        for product in products:
            product_id = product.id

            result = manager.scrape_product(
                competitor_id=competitor_id,
                product_id=product_id,
            )
            print(f"[competitor={competitor_id} product={product_id}] {result}")

finally:
    db.close()