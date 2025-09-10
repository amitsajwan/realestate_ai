from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class AnalyticsPeriod(str, Enum):
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
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    GROWTH_RATE = "growth_rate"

class AnalyticsMetric(BaseModel):
    name: str
    value: float
    type: MetricType
    unit: Optional[str] = None
    change_percentage: Optional[float] = None
    change_direction: Optional[str] = None  # "up", "down", "neutral"
    previous_value: Optional[float] = None
    target_value: Optional[float] = None
    description: Optional[str] = None

class PropertyAnalytics(BaseModel):
    total_properties: int
    published_properties: int
    draft_properties: int
    archived_properties: int
    average_price: float
    total_value: float
    price_range_distribution: Dict[str, int]
    property_type_distribution: Dict[str, int]
    location_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    average_days_on_market: float
    conversion_rate: float
    top_performing_properties: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

class LeadAnalytics(BaseModel):
    total_leads: int
    new_leads: int
    contacted_leads: int
    qualified_leads: int
    converted_leads: int
    lost_leads: int
    conversion_rate: float
    average_lead_score: float
    lead_source_distribution: Dict[str, int]
    urgency_distribution: Dict[str, int]
    budget_distribution: Dict[str, int]
    average_deal_value: float
    total_pipeline_value: float
    lead_response_time: float
    follow_up_completion_rate: float
    top_performing_sources: List[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]

class AgentPerformance(BaseModel):
    agent_id: str
    agent_name: str
    total_leads: int
    converted_leads: int
    conversion_rate: float
    total_sales: float
    average_deal_size: float
    response_time: float
    follow_up_rate: float
    properties_listed: int
    properties_sold: int
    client_satisfaction: Optional[float] = None
    performance_score: float
    rank: int

class TeamAnalytics(BaseModel):
    team_id: str
    team_name: str
    total_members: int
    active_members: int
    total_leads: int
    total_properties: int
    total_sales: float
    average_conversion_rate: float
    team_performance_score: float
    top_performers: List[AgentPerformance]
    recent_activity: List[Dict[str, Any]]

class MarketAnalytics(BaseModel):
    market_trends: Dict[str, Any]
    price_trends: Dict[str, Any]
    demand_indicators: Dict[str, Any]
    seasonal_patterns: Dict[str, Any]
    competitive_analysis: Dict[str, Any]
    market_insights: List[str]

class RevenueAnalytics(BaseModel):
    total_revenue: float
    monthly_revenue: List[Dict[str, Any]]
    revenue_by_source: Dict[str, float]
    revenue_by_agent: List[Dict[str, Any]]
    revenue_growth_rate: float
    average_deal_value: float
    revenue_forecast: List[Dict[str, Any]]

class DashboardMetrics(BaseModel):
    overview_metrics: List[AnalyticsMetric]
    property_analytics: PropertyAnalytics
    lead_analytics: LeadAnalytics
    team_analytics: Optional[TeamAnalytics] = None
    market_analytics: Optional[MarketAnalytics] = None
    revenue_analytics: Optional[RevenueAnalytics] = None
    generated_at: datetime
    period: AnalyticsPeriod
    date_range: Dict[str, date]

class AnalyticsFilter(BaseModel):
    period: AnalyticsPeriod = AnalyticsPeriod.THIS_MONTH
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    agent_ids: Optional[List[str]] = None
    team_id: Optional[str] = None
    property_types: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    lead_sources: Optional[List[str]] = None
    include_inactive: bool = False

class ChartData(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]
    type: str = "line"  # line, bar, pie, doughnut, etc.
    title: str
    description: Optional[str] = None

class AnalyticsReport(BaseModel):
    id: str
    name: str
    description: str
    report_type: str
    filters: AnalyticsFilter
    data: DashboardMetrics
    charts: List[ChartData]
    generated_by: str
    generated_at: datetime
    is_scheduled: bool = False
    schedule_frequency: Optional[str] = None
    recipients: List[str] = Field(default_factory=list)

class AnalyticsInsight(BaseModel):
    id: str
    title: str
    description: str
    insight_type: str  # "opportunity", "warning", "trend", "recommendation"
    priority: str  # "low", "medium", "high", "critical"
    metrics_affected: List[str]
    recommended_actions: List[str]
    generated_at: datetime
    is_read: bool = False
    is_actionable: bool = True

class PerformanceComparison(BaseModel):
    current_period: Dict[str, Any]
    previous_period: Dict[str, Any]
    improvement_percentage: float
    key_improvements: List[str]
    areas_for_improvement: List[str]
    recommendations: List[str]

class AnalyticsExport(BaseModel):
    format: str = "csv"  # csv, excel, pdf
    data_type: str  # leads, properties, performance, etc.
    filters: AnalyticsFilter
    columns: List[str]
    include_charts: bool = False
    email_to: Optional[str] = None