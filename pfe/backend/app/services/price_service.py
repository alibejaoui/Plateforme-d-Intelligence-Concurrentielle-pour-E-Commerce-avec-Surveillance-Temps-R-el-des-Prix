"""
Price service
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from datetime import datetime, timedelta

from app.models.price import Price
from app.models.product import Product
from app.models.competitor import Competitor
from app.api.schemas.price_schema import PriceCreate
from app.core.exceptions import not_found_exception


class PriceService:
    """Service for price operations"""
    
    @staticmethod
    def create_price(db: Session, price_data: PriceCreate) -> Price:
        """Create a new price record"""
        # Verify product and competitor exist
        product = db.query(Product).filter(Product.id == price_data.product_id).first()
        if not product:
            raise not_found_exception("Product", price_data.product_id)
        
        competitor = db.query(Competitor).filter(Competitor.id == price_data.competitor_id).first()
        if not competitor:
            raise not_found_exception("Competitor", price_data.competitor_id)
        
        new_price = Price(
            **price_data.model_dump(),
            scraped_at=price_data.scraped_at or datetime.utcnow()
        )
        db.add(new_price)
        db.commit()
        db.refresh(new_price)
        return new_price
    
    @staticmethod
    def get_price_history(
        db: Session,
        product_id: int,
        competitor_id: Optional[int] = None,
        days: int = 30
    ) -> list[Price]:
        """Get price history for a product"""
        query = db.query(Price).filter(Price.product_id == product_id)
        
        if competitor_id:
            query = query.filter(Price.competitor_id == competitor_id)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Price.created_at >= start_date)
        
        return query.order_by(desc(Price.created_at)).all()
    
    @staticmethod
    def get_current_prices(
        db: Session,
        product_id: int
    ) -> list[Price]:
        """Get current prices for a product from all competitors"""
        # Get the most recent price for each competitor
        subquery = db.query(
            Price.competitor_id,
            func.max(Price.created_at).label('max_date')
        ).filter(
            Price.product_id == product_id
        ).group_by(Price.competitor_id).subquery()
        
        prices = db.query(Price).join(
            subquery,
            (Price.competitor_id == subquery.c.competitor_id) &
            (Price.created_at == subquery.c.max_date)
        ).filter(Price.product_id == product_id).all()
        
        return prices
    
    @staticmethod
    def get_price_statistics(
        db: Session,
        product_id: int,
        days: int = 30
    ) -> dict:
        """Get price statistics for a product"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            func.min(Price.price).label('min_price'),
            func.max(Price.price).label('max_price'),
            func.avg(Price.price).label('avg_price'),
            func.count(Price.id).label('count')
        ).filter(
            Price.product_id == product_id,
            Price.created_at >= start_date
        ).first()
        
        return {
            "min_price": float(stats.min_price) if stats.min_price else None,
            "max_price": float(stats.max_price) if stats.max_price else None,
            "avg_price": float(stats.avg_price) if stats.avg_price else None,
            "count": stats.count
        }

