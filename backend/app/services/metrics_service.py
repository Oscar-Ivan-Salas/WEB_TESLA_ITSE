"""
Metrics service for handling analytics and reporting.
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, extract

from app.models import Lead, User, ActivityLog, Conversation, Message
from app.schemas.metrics import (
    DashboardMetrics, TimeRange, MetricType,
    TimeSeriesData, TimeSeriesPoint, MetricValue, MetricFilter
)

class MetricsService:
    """Service class for metrics and analytics operations."""
    
    @staticmethod
    async def get_dashboard_metrics(
        db: Session,
        filter_params: MetricFilter
    ) -> DashboardMetrics:
        """
        Get a complete set of metrics for the dashboard.
        
        This includes lead counts, conversion rates, activity counts,
        and time series data for visualization.
        """
        # Get date range
        start_date, end_date = MetricsService._get_date_range(
            filter_params.time_range,
            filter_params.start_date,
            filter_params.end_date
        )
        
        # Initialize metrics
        metrics = DashboardMetrics()
        
        # Get lead metrics
        lead_metrics = await MetricsService._get_lead_metrics(
            db, start_date, end_date, filter_params.user_id
        )
        metrics.leads = lead_metrics
        
        # Get conversion metrics
        conversion_metrics = await MetricsService._get_conversion_metrics(
            db, start_date, end_date, filter_params.user_id
        )
        metrics.conversions = conversion_metrics
        
        # Get activity metrics
        activity_metrics = await MetricsService._get_activity_metrics(
            db, start_date, end_date, filter_params.user_id
        )
        metrics.activities = activity_metrics
        
        # Get time series data
        time_series = await MetricsService._get_time_series_data(
            db, start_date, end_date, filter_params.user_id
        )
        metrics.time_series = time_series
        
        return metrics
    
    @staticmethod
    async def get_time_series_data(
        db: Session,
        metric_type: MetricType,
        filter_params: MetricFilter
    ) -> TimeSeriesData:
        """
        Get time series data for a specific metric type.
        
        This is used for generating charts and trend analysis.
        """
        # Get date range
        start_date, end_date = MetricsService._get_date_range(
            filter_params.time_range,
            filter_params.start_date,
            filter_params.end_date
        )
        
        # Get the appropriate data based on metric type
        if metric_type == MetricType.LEAD_COUNT:
            return await MetricsService._get_lead_time_series(
                db, start_date, end_date, filter_params.user_id
            )
        elif metric_type == MetricType.CONVERSION_RATE:
            return await MetricsService._get_conversion_time_series(
                db, start_date, end_date, filter_params.user_id
            )
        elif metric_type == MetricType.RESPONSE_TIME:
            return await MetricsService._get_response_time_series(
                db, start_date, end_date, filter_params.user_id
            )
        elif metric_type == MetricType.ACTIVITY_COUNT:
            return await MetricsService._get_activity_time_series(
                db, start_date, end_date, filter_params.user_id
            )
        elif metric_type == MetricType.REVENUE:
            return await MetricsService._get_revenue_time_series(
                db, start_date, end_date, filter_params.user_id
            )
        else:
            raise ValueError(f"Unsupported metric type: {metric_type}")
    
    @staticmethod
    async def get_activity_logs(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[ActivityLog]:
        """
        Get activity logs with filtering and pagination.
        """
        query = db.query(ActivityLog)
        
        # Apply filters
        if action:
            query = query.filter(ActivityLog.action == action)
        
        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)
        
        if entity_id is not None:
            query = query.filter(ActivityLog.entity_id == entity_id)
        
        if user_id is not None:
            query = query.filter(ActivityLog.user_id == user_id)
        
        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)
        
        if end_date:
            # Include the entire end date
            next_day = end_date + timedelta(days=1)
            query = query.filter(ActivityLog.created_at < next_day)
        
        # Apply pagination and order
        return (
            query.order_by(ActivityLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    async def get_leaderboard(
        db: Session,
        filter_params: MetricFilter,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard of top-performing users.
        
        Returns a ranked list of users based on various metrics.
        """
        # Get date range
        start_date, end_date = MetricsService._get_date_range(
            filter_params.time_range,
            filter_params.start_date,
            filter_params.end_date
        )
        
        # Base query for user metrics
        query = (
            db.query(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                func.count(case([(Lead.id.isnot(None), 1)])).label("lead_count"),
                func.count(case([(Lead.status == "won", 1)])).label("converted_leads"),
                func.count(case([(ActivityLog.action == "lead.contacted", 1)])).label("contacts_made"),
                func.count(case([(ActivityLog.action == "meeting.scheduled", 1)])).label("meetings_scheduled"),
            )
            .outerjoin(Lead, Lead.assigned_to == User.id)
            .outerjoin(ActivityLog, ActivityLog.user_id == User.id)
            .group_by(User.id, User.first_name, User.last_name, User.email)
        )
        
        # Apply date filters to activities
        if start_date or end_date:
            if start_date:
                query = query.filter(
                    or_(
                        Lead.created_at >= start_date,
                        ActivityLog.created_at >= start_date
                    )
                )
            if end_date:
                next_day = end_date + timedelta(days=1)
                query = query.filter(
                    or_(
                        Lead.created_at < next_day,
                        ActivityLog.created_at < next_day
                    )
                )
        
        # Apply user filter if provided
        if filter_params.user_id:
            query = query.filter(User.id == filter_params.user_id)
        
        # Order by converted leads (primary) and leads (secondary)
        results = (
            query.order_by(
                func.count(case([(Lead.status == "won", 1)])).desc(),
                func.count(Lead.id).desc()
            )
            .limit(limit)
            .all()
        )
        
        # Format results
        leaderboard = []
        for i, row in enumerate(results, 1):
            leaderboard.append({
                "rank": i,
                "user_id": row.id,
                "name": f"{row.first_name} {row.last_name}",
                "email": row.email,
                "lead_count": row.lead_count or 0,
                "converted_leads": row.converted_leads or 0,
                "conversion_rate": (
                    (row.converted_leads / row.lead_count * 100)
                    if row.lead_count > 0 else 0
                ),
                "contacts_made": row.contacts_made or 0,
                "meetings_scheduled": row.meetings_scheduled or 0,
            })
        
        return leaderboard
    
    # Helper methods for getting specific metrics
    
    @staticmethod
    async def _get_lead_metrics(
        db: Session,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: Optional[int] = None
    ) -> Dict[str, MetricValue]:
        """Get lead-related metrics."""
        query = db.query(Lead)
        
        # Apply filters
        if start_date:
            query = query.filter(Lead.created_at >= start_date)
        if end_date:
            next_day = end_date + timedelta(days=1)
            query = query.filter(Lead.created_at < next_day)
        if user_id is not None:
            query = query.filter(Lead.assigned_to == user_id)
        
        # Get total leads
        total_leads = query.count()
        
        # Get leads by status
        status_query = query.with_entities(
            Lead.status,
            func.count(Lead.id).label("count")
        ).group_by(Lead.status)
        
        status_counts = {status: count for status, count in status_query.all()}
        
        # Get leads by source
        source_query = query.with_entities(
            Lead.source,
            func.count(Lead.id).label("count")
        ).group_by(Lead.source)
        
        source_counts = {source: count for source, count in source_query.all()}
        
        # Calculate trend (compare with previous period)
        trend = 0  # Default to 0% change
        if start_date and end_date:
            # Calculate previous period
            period_days = (end_date - start_date).days + 1
            prev_start_date = start_date - timedelta(days=period_days)
            prev_end_date = start_date - timedelta(days=1)
            
            # Get count for previous period
            prev_count = db.query(Lead).filter(
                Lead.created_at >= prev_start_date,
                Lead.created_at < start_date
            ).count()
            
            # Calculate percentage change
            if prev_count > 0:
                trend = ((total_leads - prev_count) / prev_count) * 100
        
        return {
            "total": MetricValue(
                value=total_leads,
                label="Total Leads",
                change_percentage=trend,
                trend="up" if trend > 0 else "down" if trend < 0 else "neutral"
            ),
            "new": MetricValue(
                value=status_counts.get("new", 0),
                label="New Leads",
                description=f"{status_counts.get('new', 0)} of {total_leads} total leads"
            ),
            "converted": MetricValue(
                value=status_counts.get("won", 0),
                label="Converted Leads",
                description=f"{status_counts.get('won', 0)} of {total_leads} total leads"
            ),
            "top_source": MetricValue(
                value=max(source_counts.values()) if source_counts else 0,
                label=(
                    f"Top Source: {max(source_counts, key=source_counts.get) if source_counts else 'N/A'}",
                ),
                description=f"{len(source_counts)} sources total"
            )
        }
    
    @staticmethod
    async def _get_conversion_metrics(
        db: Session,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: Optional[int] = None
    ) -> Dict[str, MetricValue]:
        """Get conversion-related metrics."""
        query = db.query(Lead)
        
        # Apply filters
        if start_date:
            query = query.filter(Lead.created_at >= start_date)
        if end_date:
            next_day = end_date + timedelta(days=1)
            query = query.filter(Lead.created_at < next_day)
        if user_id is not None:
            query = query.filter(Lead.assigned_to == user_id)
        
        # Get total leads and converted leads
        total_leads = query.count()
        converted_leads = query.filter(Lead.status == "won").count()
        
        # Calculate conversion rate
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Calculate trend (compare with previous period)
        trend = 0  # Default to 0% change
        if start_date and end_date and total_leads > 0:
            # Calculate previous period
            period_days = (end_date - start_date).days + 1
            prev_start_date = start_date - timedelta(days=period_days)
            prev_end_date = start_date - timedelta(days=1)
            
            # Get counts for previous period
            prev_query = db.query(Lead).filter(
                Lead.created_at >= prev_start_date,
                Lead.created_at < start_date
            )
            
            if user_id is not None:
                prev_query = prev_query.filter(Lead.assigned_to == user_id)
            
            prev_total = prev_query.count()
            prev_converted = prev_query.filter(Lead.status == "won").count()
            prev_rate = (prev_converted / prev_total * 100) if prev_total > 0 else 0
            
            # Calculate percentage change
            if prev_rate > 0:
                trend = ((conversion_rate - prev_rate) / prev_rate) * 100
        
        return {
            "rate": MetricValue(
                value=conversion_rate,
                label="Conversion Rate",
                format="{:.1f}%",
                change_percentage=trend,
                trend="up" if trend > 0 else "down" if trend < 0 else "neutral"
            ),
            "converted": MetricValue(
                value=converted_leads,
                label="Converted Leads",
                description=f"{converted_leads} of {total_leads} total leads"
            ),
            "value": MetricValue(
                value=converted_leads * 1000,  # Assuming $1000 average deal value
                label="Total Value",
                format="${:,.2f}",
                description="Estimated based on average deal value"
            )
        }
    
    @staticmethod
    async def _get_activity_metrics(
        db: Session,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: Optional[int] = None
    ) -> Dict[str, MetricValue]:
        """Get activity-related metrics."""
        query = db.query(ActivityLog)
        
        # Apply filters
        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)
        if end_date:
            next_day = end_date + timedelta(days=1)
            query = query.filter(ActivityLog.created_at < next_day)
        if user_id is not None:
            query = query.filter(ActivityLog.user_id == user_id)
        
        # Get total activities
        total_activities = query.count()
        
        # Get activities by type
        activities_by_type = (
            query.with_entities(
                ActivityLog.action,
                func.count(ActivityLog.id).label("count")
            )
            .group_by(ActivityLog.action)
            .all()
        )
        
        # Count different types of activities
        emails_sent = 0
        calls_made = 0
        meetings_scheduled = 0
        
        for action, count in activities_by_type:
            if "email" in action:
                emails_sent += count
            elif "call" in action:
                calls_made += count
            elif "meeting" in action and "scheduled" in action:
                meetings_scheduled += count
        
        # Calculate trend (compare with previous period)
        trend = 0  # Default to 0% change
        if start_date and end_date and total_activities > 0:
            # Calculate previous period
            period_days = (end_date - start_date).days + 1
            prev_start_date = start_date - timedelta(days=period_days)
            prev_end_date = start_date - timedelta(days=1)
            
            # Get count for previous period
            prev_query = db.query(ActivityLog).filter(
                ActivityLog.created_at >= prev_start_date,
                ActivityLog.created_at < start_date
            )
            
            if user_id is not None:
                prev_query = prev_query.filter(ActivityLog.user_id == user_id)
            
            prev_count = prev_query.count()
            
            # Calculate percentage change
            if prev_count > 0:
                trend = ((total_activities - prev_count) / prev_count) * 100
        
        return {
            "total": MetricValue(
                value=total_activities,
                label="Total Activities",
                change_percentage=trend,
                trend="up" if trend > 0 else "down" if trend < 0 else "neutral"
            ),
            "emails": MetricValue(
                value=emails_sent,
                label="Emails Sent",
                description=f"{emails_sent} of {total_activities} total activities"
            ),
            "calls": MetricValue(
                value=calls_made,
                label="Calls Made",
                description=f"{calls_made} of {total_activities} total activities"
            ),
            "meetings": MetricValue(
                value=meetings_scheduled,
                label="Meetings Scheduled",
                description=f"{meetings_scheduled} of {total_activities} total activities"
            )
        }
    
    # Helper methods for time series data
    
    @staticmethod
    async def _get_lead_time_series(
        db: Session,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> TimeSeriesData:
        """Get time series data for lead counts."""
        # Generate date range
        date_range = MetricsService._generate_date_range(start_date, end_date)
        
        # Build query to get leads by day
        query = (
            db.query(
                func.date(Lead.created_at).label("date"),
                func.count(Lead.id).label("count")
            )
            .filter(Lead.created_at >= start_date)
            .filter(Lead.created_at < end_date + timedelta(days=1))
            .group_by(func.date(Lead.created_at))
        )
        
        if user_id is not None:
            query = query.filter(Lead.assigned_to == user_id)
        
        # Get results as dictionary for easy lookup
        results = {row.date: row.count for row in query.all()}
        
        # Build time series points
        series = []
        total = 0
        
        for current_date in date_range:
            count = results.get(current_date, 0)
            total += count
            
            series.append(TimeSeriesPoint(
                date=current_date,
                value=count,
                label=f"{count} leads"
            ))
        
        # Calculate average per day
        avg_per_day = total / len(date_range) if date_range else 0
        
        return TimeSeriesData(
            series=series,
            total=total,
            average=avg_per_day,
            change_percentage=0  # Would need previous period data to calculate
        )
    
    @staticmethod
    async def _get_conversion_time_series(
        db: Session,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> TimeSeriesData:
        """Get time series data for conversion rates."""
        # This is a simplified version - in a real app, you'd want to calculate
        # conversion rates over time, which requires tracking when leads were created
        # and when they were converted.
        
        # For now, we'll return a placeholder implementation
        date_range = MetricsService._generate_date_range(start_date, end_date)
        
        # In a real implementation, you would calculate actual conversion rates
        # This is just a placeholder with random data
        import random
        
        series = []
        total_conversions = 0
        total_leads = 0
        
        for current_date in date_range:
            # Simulate some random data
            leads = random.randint(1, 10)
            conversions = random.randint(0, leads)
            
            total_leads += leads
            total_conversions += conversions
            
            rate = (conversions / leads * 100) if leads > 0 else 0
            
            series.append(TimeSeriesPoint(
                date=current_date,
                value=rate,
                label=f"{rate:.1f}% conversion"
            ))
        
        # Calculate overall conversion rate
        overall_rate = (total_conversions / total_leads * 100) if total_leads > 0 else 0
        
        return TimeSeriesData(
            series=series,
            total=total_conversions,
            average=overall_rate,
            change_percentage=0  # Would need previous period data to calculate
        )
    
    @staticmethod
    async def _get_response_time_series(
        db: Session,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> TimeSeriesData:
        """Get time series data for response times."""
        # This would track how quickly the team responds to leads over time
        # For now, we'll return a placeholder implementation
        
        date_range = MetricsService._generate_date_range(start_date, end_date)
        
        # In a real implementation, you would calculate actual response times
        # This is just a placeholder with random data
        import random
        
        series = []
        total_time = 0
        count = 0
        
        for current_date in date_range:
            # Simulate some random data (response time in hours)
            response_time = random.uniform(0.5, 24.0)
            total_time += response_time
            count += 1
            
            series.append(TimeSeriesPoint(
                date=current_date,
                value=response_time,
                label=f"{response_time:.1f} hours"
            ))
        
        # Calculate average response time
        avg_response_time = total_time / count if count > 0 else 0
        
        return TimeSeriesData(
            series=series,
            total=total_time,
            average=avg_response_time,
            change_percentage=0  # Would need previous period data to calculate
        )
    
    @staticmethod
    async def _get_activity_time_series(
        db: Session,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> TimeSeriesData:
        """Get time series data for activity counts."""
        # Generate date range
        date_range = MetricsService._generate_date_range(start_date, end_date)
        
        # Build query to get activities by day
        query = (
            db.query(
                func.date(ActivityLog.created_at).label("date"),
                func.count(ActivityLog.id).label("count")
            )
            .filter(ActivityLog.created_at >= start_date)
            .filter(ActivityLog.created_at < end_date + timedelta(days=1))
            .group_by(func.date(ActivityLog.created_at))
        )
        
        if user_id is not None:
            query = query.filter(ActivityLog.user_id == user_id)
        
        # Get results as dictionary for easy lookup
        results = {row.date: row.count for row in query.all()}
        
        # Build time series points
        series = []
        total = 0
        
        for current_date in date_range:
            count = results.get(current_date, 0)
            total += count
            
            series.append(TimeSeriesPoint(
                date=current_date,
                value=count,
                label=f"{count} activities"
            ))
        
        # Calculate average per day
        avg_per_day = total / len(date_range) if date_range else 0
        
        return TimeSeriesData(
            series=series,
            total=total,
            average=avg_per_day,
            change_percentage=0  # Would need previous period data to calculate
        )
    
    @staticmethod
    async def _get_revenue_time_series(
        db: Session,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> TimeSeriesData:
        """Get time series data for revenue."""
        # This would track revenue over time
        # For now, we'll return a placeholder implementation
        
        date_range = MetricsService._generate_date_range(start_date, end_date)
        
        # In a real implementation, you would query actual revenue data
        # This is just a placeholder with random data
        import random
        
        series = []
        total_revenue = 0
        
        for current_date in date_range:
            # Simulate some random revenue data
            revenue = random.uniform(100, 5000)
            total_revenue += revenue
            
            series.append(TimeSeriesPoint(
                date=current_date,
                value=revenue,
                label=f"${revenue:,.2f}"
            ))
        
        # Calculate average revenue per day
        avg_per_day = total_revenue / len(date_range) if date_range else 0
        
        return TimeSeriesData(
            series=series,
            total=total_revenue,
            average=avg_per_day,
            change_percentage=0  # Would need previous period data to calculate
        )
    
    # Helper methods
    
    @staticmethod
    def _get_date_range(
        time_range: TimeRange,
        custom_start: Optional[date] = None,
        custom_end: Optional[date] = None
    ) -> tuple[Optional[date], Optional[date]]:
        """Get start and end dates based on time range."""
        today = date.today()
        
        if time_range == TimeRange.TODAY:
            return today, today
        elif time_range == TimeRange.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif time_range == TimeRange.THIS_WEEK:
            # Start of week (Monday)
            start = today - timedelta(days=today.weekday())
            return start, today
        elif time_range == TimeRange.LAST_WEEK:
            # Start of last week (Monday)
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            return start, end
        elif time_range == TimeRange.THIS_MONTH:
            # Start of month
            start = date(today.year, today.month, 1)
            return start, today
        elif time_range == TimeRange.LAST_MONTH:
            # Start of last month
            if today.month == 1:
                start = date(today.year - 1, 12, 1)
            else:
                start = date(today.year, today.month - 1, 1)
            
            # End of last month
            if today.month == 1:
                end = date(today.year - 1, 12, 31)
            else:
                # Get the last day of the previous month
                next_month = date(today.year, today.month, 1)
                end = next_month - timedelta(days=1)
            
            return start, end
        elif time_range == TimeRange.THIS_QUARTER:
            # Start of quarter
            quarter_start_month = 3 * ((today.month - 1) // 3) + 1
            start = date(today.year, quarter_start_month, 1)
            return start, today
        elif time_range == TimeRange.LAST_QUARTER:
            # Calculate current quarter (1-4)
            current_quarter = (today.month - 1) // 3 + 1
            
            # Get previous quarter and year
            if current_quarter == 1:
                prev_quarter = 4
                prev_year = today.year - 1
            else:
                prev_quarter = current_quarter - 1
                prev_year = today.year
            
            # Start month of previous quarter
            start_month = 3 * (prev_quarter - 1) + 1
            start = date(prev_year, start_month, 1)
            
            # End month of previous quarter
            end_month = start_month + 2
            
            # Handle December (end of year)
            if end_month == 12:
                end = date(prev_year, 12, 31)
            else:
                # Get the last day of the end month
                next_month = date(prev_year, end_month + 1, 1)
                end = next_month - timedelta(days=1)
            
            return start, end
        elif time_range == TimeRange.THIS_YEAR:
            # Start of year
            start = date(today.year, 1, 1)
            return start, today
        elif time_range == TimeRange.LAST_YEAR:
            # Last year
            start = date(today.year - 1, 1, 1)
            end = date(today.year - 1, 12, 31)
            return start, end
        elif time_range == TimeRange.CUSTOM:
            if not custom_start or not custom_end:
                raise ValueError("start_date and end_date are required for custom range")
            return custom_start, custom_end
        else:
            raise ValueError(f"Unsupported time range: {time_range}")
    
    @staticmethod
    def _generate_date_range(
        start_date: date,
        end_date: date
    ) -> List[date]:
        """Generate a list of dates from start_date to end_date (inclusive)."""
        date_list = []
        current_date = start_date
        
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        
        return date_list

# Create a singleton instance
metrics_service = MetricsService()
