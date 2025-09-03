"""
Metrics and analytics schemas for the Tesla CRM application.
"""
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field

class TimeRange(str, Enum):
    """Time range options for metrics."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    LAST_QUARTER = "last_quarter"
    THIS_YEAR = "this_year"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"

class MetricType(str, Enum):
    """Types of metrics available."""
    LEAD_COUNT = "lead_count"
    CONVERSION_RATE = "conversion_rate"
    RESPONSE_TIME = "response_time"
    ACTIVITY_COUNT = "activity_count"
    REVENUE = "revenue"

class MetricFilter(BaseModel):
    """Filter criteria for metrics."""
    time_range: TimeRange = Field(TimeRange.THIS_MONTH, description="Time range for the metrics")
    start_date: Optional[date] = Field(None, description="Start date for custom range")
    end_date: Optional[date] = Field(None, description="End date for custom range")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    status: Optional[str] = Field(None, description="Filter by status")
    source: Optional[str] = Field(None, description="Filter by source")

class TimeSeriesPoint(BaseModel):
    """A single point in a time series."""
    date: date
    value: float
    label: Optional[str] = None

class TimeSeriesData(BaseModel):
    """Time series data for metrics."""
    series: List[TimeSeriesPoint] = []
    total: float = 0
    average: Optional[float] = None
    change_percentage: Optional[float] = Field(
        None, 
        description="Percentage change compared to previous period"
    )

class MetricValue(BaseModel):
    """A single metric value with metadata."""
    value: float
    label: str
    description: Optional[str] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = Field(
        None,
        description="Trend indicator (up, down, neutral)"
    )

class DashboardMetrics(BaseModel):
    """Complete set of metrics for the dashboard."""
    leads: Dict[str, MetricValue] = Field(
        default_factory=dict,
        description="Lead-related metrics"
    )
    conversions: Dict[str, MetricValue] = Field(
        default_factory=dict,
        description="Conversion-related metrics"
    )
    activities: Dict[str, MetricValue] = Field(
        default_factory=dict,
        description="Activity-related metrics"
    )
    revenue: Dict[str, MetricValue] = Field(
        default_factory=dict,
        description="Revenue-related metrics"
    )
    time_series: Dict[str, TimeSeriesData] = Field(
        default_factory=dict,
        description="Time series data for various metrics"
    )

class ActivityLog(BaseModel):
    """Log of user or system activities."""
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
