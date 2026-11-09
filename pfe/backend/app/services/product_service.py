"""
Product service
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from fastapi import HTTPException, status

from app.models.product import Product
from app.api.schemas.product_schema import ProductCreate, ProductUpdate
from app.core.exceptions import not_found_exception


class ProductService:
    """Service for product operations"""
    
    @staticmethod
    def create_product(db: Session, product_data: ProductCreate, user_id: int) -> Product:
        """Create a new product"""
        new_product = Product(
            **product_data.model_dump(),
            user_id=user_id
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    
    @staticmethod
    def get_product(db: Session, product_id: int, user_id: int) -> Product:
        """Get a product by ID"""
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.user_id == user_id
        ).first()
        
        if not product:
            raise not_found_exception("Product", product_id)
        
        return product
    
    @staticmethod
    def get_products(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[list[Product], int]:
        """Get products with pagination and filters"""
        query = db.query(Product).filter(Product.user_id == user_id)
        
        if category:
            query = query.filter(Product.category == category)
        
        if search:
            query = query.filter(
                Product.name.contains(search) |
                Product.description.contains(search) |
                Product.sku.contains(search)
            )
        
        total = query.count()
        products = query.order_by(desc(Product.created_at)).offset(skip).limit(limit).all()
        
        return products, total
    
    @staticmethod
    def update_product(
        db: Session,
        product_id: int,
        product_data: ProductUpdate,
        user_id: int
    ) -> Product:
        """Update a product"""
        product = ProductService.get_product(db, product_id, user_id)
        
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        return product
    
    @staticmethod
    def delete_product(db: Session, product_id: int, user_id: int) -> None:
        """Delete a product"""
        product = ProductService.get_product(db, product_id, user_id)
        db.delete(product)
        db.commit()

