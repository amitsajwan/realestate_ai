"""
Analytics Data Schemas
=====================
Pydantic schemas for analytics data and metrics
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId

class MetricType(str, Enum):
    """Metric type enumeration"""
    VIEWS = "views"
    CLICKS = "clicks"
    ENGAGEMENT = "engagement"
    SHARES = "shares"
    LIKES = "likes"
    COMMENTS = "comments"
    LEADS = "leads"
    CONVERSIONS = "conversions"
    REVENUE = "revenue"
    IMPRESSIONS = "impressions"

class AnalyticsDataBase(BaseModel):
    """Base analytics data schema"""
    property_id: str = Field(..., description="Property ID")
    content_id: Optional[str] = Field(None, description="Content ID (if applicable)")
    metric_type: MetricType = Field(..., description="Type of metric")
    value: float = Field(..., description="Metric value")
    date: datetime = Field(..., description="Date of the metric")
    channel: Optional[str] = Field(None, description="Channel where metric was collected")
    source: Optional[str] = Field(None, description="Source of the metric")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class AnalyticsDataCreate(AnalyticsDataBase):
    """Schema for creating analytics data"""
    pass

class AnalyticsDataUpdate(BaseModel):
    """Schema for updating analytics data"""
    value: Optional[float] = None
    date: Optional[datetime] = None
    channel: Optional[str] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AnalyticsData(AnalyticsDataBase):
    """Complete analytics data schema"""
    id: str = Field(..., alias="_id", description="Analytics data ID")
    data_id: str = Field(..., description="Unique data identifier")
    user_id: str = Field(..., description="User who owns this data")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class AnalyticsDataResponse(BaseModel):
    """Response schema for analytics data"""
    id: str = Field(..., alias="_id")
    data_id: str
    property_id: str
    content_id: Optional[str]
    metric_type: MetricType
    value: float
    date: datetime
    channel: Optional[str]
    source: Optional[str]
    metadata: Dict[str, Any] = Field(default={})
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class AnalyticsSummary(BaseModel):
    """Analytics summary schema"""
    total_views: int
    total_clicks: int
    total_engagement: int
    total_leads: int
    total_revenue: float
    top_performing_content: List[Dict[str, Any]]
    channel_performance: Dict[str, Dict[str, Any]]
    date_range: Dict[str, datetime]
    growth_metrics: Dict[str, float]

class AnalyticsChartData(BaseModel):
    """Chart data for analytics visualization"""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    total: float
    period: str
