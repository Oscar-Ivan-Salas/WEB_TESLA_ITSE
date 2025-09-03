"""
Dashboard endpoints for Tesla CRM API.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta

from ....database import get_db
from ....models import Lead, User, ActivityLog
from ....schemas.dashboard import DashboardStats

router = APIRouter()

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard statistics including lead counts, recent activities, and metrics.
    """
    try:
        # Get total leads count
        total_leads = db.query(Lead).count()
        
        # Get new leads (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_leads = db.query(Lead).filter(Lead.created_at >= week_ago).count()
        
        # Get active users count
        active_users = db.query(User).filter(User.is_active == True).count()  # noqa: E712
        
        # Get recent activities
        recent_activities = db.query(ActivityLog)\
            .order_by(ActivityLog.created_at.desc())\
            .limit(5)\
            .all()
            
        # Calculate conversion rate (example: leads to customers)
        converted_leads = db.query(Lead).filter(Lead.status == "converted").count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "active_users": active_users,
            "conversion_rate": round(conversion_rate, 2),
            "recent_activities": [
                {
                    "id": activity.id,
                    "action": activity.action,
                    "created_at": activity.created_at.isoformat(),
                    "user_id": activity.user_id
                }
                for activity in recent_activities
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving dashboard stats: {str(e)}"
        )
