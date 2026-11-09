"""
Competitor service
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from fastapi import HTTPException, status

from app.models.competitor import Competitor
from app.api.schemas.competitor_schema import CompetitorCreate, CompetitorUpdate
from app.core.exceptions import not_found_exception


class CompetitorService:
    """Service for competitor operations"""
    
    @staticmethod
    def create_competitor(db: Session, competitor_data: CompetitorCreate) -> Competitor:
        """Create a new competitor"""
        # Check if competitor with same name exists
        existing = db.query(Competitor).filter(Competitor.name == competitor_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Competitor with this name already exists"
            )
        
        new_competitor = Competitor(**competitor_data.model_dump())
        db.add(new_competitor)
        db.commit()
        db.refresh(new_competitor)
        return new_competitor
    
    @staticmethod
    def get_competitor(db: Session, competitor_id: int) -> Competitor:
        """Get a competitor by ID"""
        competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
        
        if not competitor:
            raise not_found_exception("Competitor", competitor_id)
        
        return competitor
    
    @staticmethod
    def get_competitors(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> tuple[list[Competitor], int]:
        """Get competitors with pagination and filters"""
        query = db.query(Competitor)
        
        if is_active is not None:
            query = query.filter(Competitor.is_active == is_active)
        
        if search:
            query = query.filter(
                Competitor.name.contains(search) |
                Competitor.description.contains(search)
            )
        
        total = query.count()
        competitors = query.order_by(desc(Competitor.created_at)).offset(skip).limit(limit).all()
        
        return competitors, total
    
    @staticmethod
    def update_competitor(
        db: Session,
        competitor_id: int,
        competitor_data: CompetitorUpdate
    ) -> Competitor:
        """Update a competitor"""
        competitor = CompetitorService.get_competitor(db, competitor_id)
        
        update_data = competitor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(competitor, field, value)
        
        db.commit()
        db.refresh(competitor)
        return competitor
    
    @staticmethod
    def delete_competitor(db: Session, competitor_id: int) -> None:
        """Delete a competitor"""
        competitor = CompetitorService.get_competitor(db, competitor_id)
        db.delete(competitor)
        db.commit()

