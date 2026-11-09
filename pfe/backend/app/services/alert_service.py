"""
Alert service for price alerts
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from app.models.alert import Alert, AlertType, AlertStatus
from app.models.product import Product
from app.models.price import Price


class AlertService:
    """Service for alert operations"""
    
    @staticmethod
    def create_alert(
        db: Session,
        user_id: int,
        product_id: int,
        alert_type: AlertType,
        message: str,
        old_price: Optional[str] = None,
        new_price: Optional[str] = None
    ) -> Alert:
        """Create a new alert"""
        new_alert = Alert(
            user_id=user_id,
            product_id=product_id,
            alert_type=alert_type,
            message=message,
            old_price=old_price,
            new_price=new_price,
            status=AlertStatus.PENDING
        )
        
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        return new_alert
    
    @staticmethod
    def get_user_alerts(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[AlertStatus] = None
    ) -> tuple[list[Alert], int]:
        """Get alerts for a user"""
        query = db.query(Alert).filter(Alert.user_id == user_id)
        
        if status:
            query = query.filter(Alert.status == status)
        
        total = query.count()
        alerts = query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
        
        return alerts, total
    
    @staticmethod
    def mark_alert_as_read(db: Session, alert_id: int, user_id: int) -> Alert:
        """Mark an alert as read"""
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user_id
        ).first()
        
        if not alert:
            from app.core.exceptions import not_found_exception
            raise not_found_exception("Alert", alert_id)
        
        alert.status = AlertStatus.READ
        alert.read_at = datetime.utcnow()
        
        db.commit()
        db.refresh(alert)
        return alert
    
    @staticmethod
    def check_price_thresholds(
        db: Session,
        product_id: int,
        new_price: float
    ) -> list[Alert]:
        """Check if new price triggers any alerts"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []
        
        alerts = []
        
        # Check min threshold
        if product.min_price_threshold and new_price <= product.min_price_threshold:
            alert = AlertService.create_alert(
                db=db,
                user_id=product.user_id,
                product_id=product_id,
                alert_type=AlertType.THRESHOLD_BELOW,
                message=f"Price dropped below minimum threshold: {new_price}",
                new_price=str(new_price)
            )
            alerts.append(alert)
        
        # Check max threshold
        if product.max_price_threshold and new_price >= product.max_price_threshold:
            alert = AlertService.create_alert(
                db=db,
                user_id=product.user_id,
                product_id=product_id,
                alert_type=AlertType.THRESHOLD_ABOVE,
                message=f"Price exceeded maximum threshold: {new_price}",
                new_price=str(new_price)
            )
            alerts.append(alert)
        
        return alerts

