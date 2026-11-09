"""
Product endpoints
"""
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.product_service import ProductService
from app.api.schemas.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse
)

router = APIRouter()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    try:
        return ProductService.create_product(db, product_data, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        # Return a clear message for debugging; avoids opaque 500s in the UI.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create product: {str(e)}",
        )


@router.get("", response_model=ProductListResponse)
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get products with pagination and filters"""
    products, total = ProductService.get_products(
        db, current_user.id, skip, limit, category, search
    )
    return ProductListResponse(
        items=products,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a product by ID"""
    return ProductService.get_product(db, product_id, current_user.id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a product"""
    return ProductService.update_product(db, product_id, product_data, current_user.id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a product"""
    ProductService.delete_product(db, product_id, current_user.id)
    return None

