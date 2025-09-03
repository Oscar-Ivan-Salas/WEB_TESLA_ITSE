"""
Metrics API endpoints for the Tesla CRM application.
"""
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.schemas.metrics import (
    DashboardMetrics, TimeRange, MetricType,
    TimeSeriesData, ActivityLog, MetricFilter
)
from app.database import get_db
from app.services import metrics_service

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    time_range: TimeRange = Query(
        TimeRange.THIS_MONTH,
        description="Time range for the metrics"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom range (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom range (YYYY-MM-DD)"
    ),
    user_id: Optional[int] = Query(
        None,
        description="Filter by user ID"
    ),
    db: Session = Depends(get_db)
):
    """
    Get a complete set of metrics for the dashboard.
    
    This endpoint returns various metrics including lead counts, conversion rates,
    activity counts, and time series data for visualization.
    """
    # Validate date range
    if time_range == TimeRange.CUSTOM and (not start_date or not end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date and end_date are required for custom range"
        )
    
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date"
        )
    
    filter_params = MetricFilter(
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    
    return await metrics_service.get_dashboard_metrics(db, filter_params)

@router.get("/time-series", response_model=TimeSeriesData)
async def get_time_series_metrics(
    metric_type: MetricType = Query(..., description="Type of metric to retrieve"),
    time_range: TimeRange = Query(
        TimeRange.THIS_MONTH,
        description="Time range for the metrics"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom range (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom range (YYYY-MM-DD)"
    ),
    user_id: Optional[int] = Query(
        None,
        description="Filter by user ID"
    ),
    db: Session = Depends(get_db)
):
    """
    Get time series data for a specific metric type.
    
    This endpoint returns data points over time for various metrics,
    suitable for creating charts and trend analysis.
    """
    # Validate date range
    if time_range == TimeRange.CUSTOM and (not start_date or not end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date and end_date are required for custom range"
        )
    
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date"
        )
    
    filter_params = MetricFilter(
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    
    return await metrics_service.get_time_series_data(db, metric_type, filter_params)

@router.get("/activity", response_model=List[ActivityLog])
async def get_activity_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, le=1000, description="Maximum number of records to return"),
    action: Optional[str] = Query(
        None,
        description="Filter by action type (e.g., 'user.login', 'lead.created')"
    ),
    entity_type: Optional[str] = Query(
        None,
        description="Filter by entity type (e.g., 'lead', 'conversation')"
    ),
    entity_id: Optional[int] = Query(
        None,
        description="Filter by entity ID"
    ),
    user_id: Optional[int] = Query(
        None,
        description="Filter by user ID"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Filter by start date (inclusive)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="Filter by end date (inclusive)"
    ),
    db: Session = Depends(get_db)
):
    """
    Get activity logs with filtering and pagination.
    
    This endpoint returns a list of user and system activities,
    which can be filtered by various criteria.
    """
    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date"
        )
    
    return await metrics_service.get_activity_logs(
        db,
        skip=skip,
        limit=limit,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/leaderboard")
async def get_leaderboard(
    time_range: TimeRange = Query(
        TimeRange.THIS_MONTH,
        description="Time range for the leaderboard"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom range (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom range (YYYY-MM-DD)"
    ),
    limit: int = Query(10, le=100, description="Number of top performers to return"),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard of top-performing users.
    
    This endpoint returns a ranked list of users based on various metrics
    such as leads converted, activities completed, etc.
    """
    # Validate date range
    if time_range == TimeRange.CUSTOM and (not start_date or not end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date and end_date are required for custom range"
        )
    
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date"
        )
    
    filter_params = MetricFilter(
        time_range=time_range,
        start_date=start_date,
        end_date=end_date
    )
    
    return await metrics_service.get_leaderboard(db, filter_params, limit=limit)
