"""
Leads API endpoints for the Tesla CRM application.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.schemas.lead import Lead, LeadCreate, LeadUpdate, LeadListResponse, LeadStatus, LeadSource
from app.database import get_db
from app.services import lead_service

router = APIRouter(prefix="/leads", tags=["leads"])

@router.post("/", response_model=Lead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead: LeadCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new lead.
    
    - **first_name**: Lead's first name (required)
    - **last_name**: Lead's last name (required)
    - **email**: Lead's email address (optional)
    - **phone**: Lead's phone number (required)
    - **company**: Lead's company (optional)
    - **job_title**: Lead's job title (optional)
    - **status**: Lead status (default: new)
    - **source**: Lead source (default: website)
    - **assigned_to**: ID of the user this lead is assigned to (optional)
    - **notes**: Additional notes about the lead (optional)
    """
    try:
        return await lead_service.create_lead(db, lead)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=LeadListResponse)
async def list_leads(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, le=1000, description="Maximum number of records to return"),
    status: Optional[LeadStatus] = None,
    source: Optional[LeadSource] = None,
    assigned_to: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all leads with optional filtering and pagination.
    """
    result = await lead_service.get_leads(
        db,
        skip=skip,
        limit=limit,
        status=status,
        source=source,
        assigned_to=assigned_to,
        search=search
    )
    
    return {
        "items": result["items"],
        "total": result["total"],
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": (result["total"] + limit - 1) // limit if limit > 0 else 0
    }

@router.get("/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific lead by ID.
    """
    lead = await lead_service.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return lead

@router.put("/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a lead's information.
    
    Only the fields provided in the request will be updated.
    """
    updated_lead = await lead_service.update_lead(db, lead_id, lead_update)
    if not updated_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return updated_lead

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a lead.
    
    This will also delete all associated conversations and messages.
    """
    success = await lead_service.delete_lead(db, lead_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return None

@router.post("/{lead_id}/convert-to-customer", response_model=Lead)
async def convert_lead_to_customer(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Convert a lead to a customer.
    
    This will change the lead's status to 'won' and create a new customer record.
    """
    try:
        return await lead_service.convert_to_customer(db, lead_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

@router.get("/sources/stats/")
async def get_lead_source_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get statistics about lead sources.
    
    Returns a breakdown of leads by source, with counts and conversion rates.
    """
    return await lead_service.get_lead_source_stats(db, start_date, end_date)

@router.get("/status/stats/")
async def get_lead_status_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get statistics about lead statuses.
    
    Returns a breakdown of leads by status, with counts and trends.
    """
    return await lead_service.get_lead_status_stats(db, start_date, end_date)
