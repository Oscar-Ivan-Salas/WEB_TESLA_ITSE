"""
Lead service for handling lead-related business logic.
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models import Lead, User, ActivityLog
from app.schemas.lead import LeadCreate, LeadUpdate, LeadStatus, LeadSource
from app.core.security import get_password_hash

class LeadService:
    """Service class for lead-related operations."""
    
    @staticmethod
    async def create_lead(
        db: Session, 
        lead_in: LeadCreate
    ) -> Lead:
        """Create a new lead."""
        # Check if lead with this email already exists
        if lead_in.email:
            existing_lead = db.query(Lead).filter(
                Lead.email == lead_in.email
            ).first()
            
            if existing_lead:
                # Update existing lead instead of creating a new one
                update_data = lead_in.dict(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(existing_lead, field, value)
                
                db.add(existing_lead)
                db.commit()
                db.refresh(existing_lead)
                
                # Log the update
                await ActivityLog.log_activity(
                    db,
                    action="lead.updated",
                    entity_type="lead",
                    entity_id=existing_lead.id,
                    details={"source": "lead_creation", "updated_fields": list(update_data.keys())}
                )
                
                return existing_lead
        
        # Create new lead
        db_lead = Lead(**lead_in.dict())
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        
        # Log the creation
        await ActivityLog.log_activity(
            db,
            action="lead.created",
            entity_type="lead",
            entity_id=db_lead.id,
            details={"source": lead_in.source or LeadSource.WEBSITE}
        )
        
        return db_lead
    
    @staticmethod
    async def get_lead(
        db: Session, 
        lead_id: int
    ) -> Optional[Lead]:
        """Get a lead by ID."""
        return db.query(Lead).filter(Lead.id == lead_id).first()
    
    @staticmethod
    async def get_lead_by_email(
        db: Session, 
        email: str
    ) -> Optional[Lead]:
        """Get a lead by email."""
        return db.query(Lead).filter(Lead.email == email).first()
    
    @staticmethod
    async def get_leads(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        assigned_to: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of leads with optional filtering and search.
        
        Returns a dictionary with 'items' (list of leads) and 'total' (total count).
        """
        query = db.query(Lead)
        
        # Apply filters
        if status:
            query = query.filter(Lead.status == status)
        
        if source:
            query = query.filter(Lead.source == source)
        
        if assigned_to is not None:
            query = query.filter(Lead.assigned_to == assigned_to)
        
        # Apply search
        if search:
            search_filter = or_(
                Lead.first_name.ilike(f"%{search}%"),
                Lead.last_name.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%"),
                Lead.phone.ilike(f"%{search}%"),
                Lead.company.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        return {"items": items, "total": total}
    
    @staticmethod
    async def update_lead(
        db: Session,
        lead_id: int,
        lead_in: LeadUpdate,
    ) -> Optional[Lead]:
        """Update a lead."""
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            return None
        
        # Track changes for activity log
        changes = {}
        update_data = lead_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            old_value = getattr(db_lead, field)
            if old_value != value:
                changes[field] = {"old": old_value, "new": value}
            setattr(db_lead, field, value)
        
        if changes:
            db.add(db_lead)
            db.commit()
            db.refresh(db_lead)
            
            # Log the update
            await ActivityLog.log_activity(
                db,
                action="lead.updated",
                entity_type="lead",
                entity_id=db_lead.id,
                details={"changes": changes}
            )
        
        return db_lead
    
    @staticmethod
    async def delete_lead(
        db: Session,
        lead_id: int,
    ) -> bool:
        """Delete a lead."""
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            return False
        
        # Log the deletion
        await ActivityLog.log_activity(
            db,
            action="lead.deleted",
            entity_type="lead",
            entity_id=db_lead.id,
            details={
                "lead_data": {
                    "name": f"{db_lead.first_name} {db_lead.last_name}",
                    "email": db_lead.email,
                    "status": db_lead.status
                }
            }
        )
        
        # Delete the lead
        db.delete(db_lead)
        db.commit()
        return True
    
    @staticmethod
    async def convert_to_customer(
        db: Session,
        lead_id: int,
    ) -> Lead:
        """Convert a lead to a customer."""
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            raise ValueError("Lead not found")
        
        # Update lead status to "won" (or another appropriate status)
        db_lead.status = LeadStatus.WON
        db_lead.converted_at = datetime.utcnow()
        
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        
        # Log the conversion
        await ActivityLog.log_activity(
            db,
            action="lead.converted",
            entity_type="lead",
            entity_id=db_lead.id,
            details={
                "converted_at": db_lead.converted_at.isoformat(),
                "status": db_lead.status
            }
        )
        
        # Here you would typically create a new Customer record, send welcome email, etc.
        # For now, we'll just return the updated lead
        
        return db_lead
    
    @staticmethod
    async def get_lead_source_stats(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get lead statistics by source."""
        query = db.query(
            Lead.source,
            func.count(Lead.id).label("count"),
            func.sum(
                case([(Lead.status == LeadStatus.WON, 1)], else_=0)
            ).label("converted")
        ).group_by(Lead.source)
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(Lead.created_at >= start_date)
        if end_date:
            query = query.filter(Lead.created_at <= end_date)
        
        results = query.all()
        
        return [
            {
                "source": source,
                "total_leads": count,
                "converted_leads": converted or 0,
                "conversion_rate": (converted or 0) / count * 100 if count > 0 else 0
            }
            for source, count, converted in results
        ]
    
    @staticmethod
    async def get_lead_status_stats(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get lead statistics by status."""
        query = db.query(
            Lead.status,
            func.count(Lead.id).label("count")
        ).group_by(Lead.status)
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(Lead.created_at >= start_date)
        if end_date:
            query = query.filter(Lead.created_at <= end_date)
        
        results = query.all()
        
        return [
            {
                "status": status,
                "count": count
            }
            for status, count in results
        ]

# Create a singleton instance
lead_service = LeadService()
