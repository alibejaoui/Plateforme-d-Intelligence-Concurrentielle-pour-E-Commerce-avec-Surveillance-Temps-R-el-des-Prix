import json
from sqlalchemy import text
from app.core.database import SessionLocal
from app.scraping.scraping_manager import ScrapingManager

# Scraper configuration
cfg = {
    "base_url": "https://webscraper.io/test-sites/e-commerce/allinone",
    "search_url_template": "{base_url}",
    "link_selector": "a.title",
    "price_selector": "h4.price",
    "currency": "USD",
}

db = SessionLocal()

try:
    # Update competitor config
    db.execute(
        text(
            "UPDATE competitors "
            "SET base_url=:base_url, scraping_config=:scraping_config "
            "WHERE id=:id"
        ),
        {
            "id": 3,
            "base_url": cfg["base_url"],
            "scraping_config": json.dumps(cfg),
        },
    )
    db.commit()

    # Run scrape (this inserts into prices and checks thresholds internally)
    manager = ScrapingManager(db)
    result = manager.scrape_product(competitor_id=3, product_id=1)
    print("Scrape result:", result)

    # Optional: show latest saved price row
    latest_price = db.execute(
        text(
            "SELECT id, product_id, competitor_id, price, currency, scraped_at, created_at, updated_at "
            "FROM prices "
            "WHERE product_id=:product_id AND competitor_id=:competitor_id "
            "ORDER BY id DESC LIMIT 1"
        ),
        {"product_id": 1, "competitor_id": 3},
    ).fetchone()
    print("Latest price row:", latest_price)

    # Optional: show latest alerts for this product
    latest_alerts = db.execute(
        text(
            "SELECT id, user_id, product_id, alert_type, status, message, old_price, new_price, created_at "
            "FROM alerts "
            "WHERE product_id=:product_id "
            "ORDER BY id DESC LIMIT 5"
        ),
        {"product_id": 1},
    ).fetchall()
    print("Latest alerts:", latest_alerts)

finally:
    db.close()