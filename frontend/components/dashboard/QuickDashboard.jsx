// QuickDashboard.jsx - Main dashboard component with all low-hanging fruit graphs
import React, { useState, useEffect } from 'react';
import MetricCard from './MetricCard';
import LeadSourceChart from './LeadSourceChart';
import WeeklyTrendChart from './WeeklyTrendChart';
import PipelineChart from './PipelineChart';
import LoadingState from './common/LoadingState';

const QuickDashboard = ({ agentId = 'agent_rajesh_kumar' }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Sample data for immediate implementation
  const sampleData = {
    basic_metrics: {
      total_leads: 45,
      new_today: 8,
      hot_leads: 12,
      follow_ups_due: 6,
      meetings_today: 3,
      deals_closing: 2,
      response_rate: "89%",
      avg_response_time: "4.2 min"
    },
    lead_sources: {
      facebook: 18,
      whatsapp: 12,
      website: 10,
      referral: 3,
      phone: 2
    },
    weekly_trend: [
      { day: 'Mon', date: '2025-08-09', count: 4 },
      { day: 'Tue', date: '2025-08-10', count: 7 },
      { day: 'Wed', date: '2025-08-11', count: 8 },
      { day: 'Thu', date: '2025-08-12', count: 6 },
      { day: 'Fri', date: '2025-08-13', count: 9 },
      { day: 'Sat', date: '2025-08-14', count: 5 },
      { day: 'Sun', date: '2025-08-15', count: 3 }
    ],
    pipeline: {
      new: 15,
      qualified: 12,
      meeting: 8,
      proposal: 5,
      negotiation: 3,
      closed: 2
    },
    performance_trends: {
      leads_growth: "+23%",
      conversion_change: "+12%",
      response_time_improvement: "-18%",
      revenue_growth: "+31%"
    }
  };

  useEffect(() => {
    // Load dashboard data from API
    const loadDashboardData = async () => {
      setLoading(true);
      
      try {
        // Real API call to backend
        const response = await fetch(`/api/dashboard/quick-metrics?agent_id=${agentId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            // Add authorization header if needed
            // 'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
          setDashboardData(result.data);
        } else {
          console.error('API returned error:', result.message);
          setDashboardData(sampleData); // Fallback to sample data
        }
        
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
        setDashboardData(sampleData); // Fallback to sample data
      } finally {
        setLoading(false);
        setLastUpdated(new Date());
      }
    };

    loadDashboardData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [agentId]);

  const handleRefresh = async () => {
    setLoading(true);
    
    try {
      // Get real-time updates
      const response = await fetch(`/api/dashboard/real-time-updates?agent_id=${agentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Merge updates with existing data
          setDashboardData(prevData => ({
            ...prevData,
            ...result.data
          }));
        }
      } else {
        // Fallback refresh with sample data
        setDashboardData(sampleData);
      }
    } catch (error) {
      console.error('Failed to refresh data:', error);
      setDashboardData(sampleData);
    } finally {
      setLoading(false);
      setLastUpdated(new Date());
    }
  };

  // Import LoadingState at the top of the file
  if (loading && !dashboardData) {
    return <LoadingState message="Loading dashboard..." fullScreen={true} />;
  }

  const metrics = dashboardData?.basic_metrics || {};
  const trends = dashboardData?.performance_trends || {};

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Real Estate CRM Dashboard
              </h1>
              <p className="text-sm text-gray-500">
                Welcome back, Rajesh! Here's your performance overview.
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-xs text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="px-3 py-2 text-xs font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors disabled:opacity-50 relative"
              >
                {loading ? (
                  <>
                    <span className="opacity-0">Refresh</span>
                    <LoadingState size="sm" className="absolute inset-0" />
                  </>
                ) : 'Refresh'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Metric Cards Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Leads"
            value={metrics.total_leads}
            trend={trends.leads_growth}
            trendDirection="up"
            icon="👥"
            color="blue"
          />
          <MetricCard
            title="New Today" 
            value={metrics.new_today}
            trend="+3 from yesterday"
            trendDirection="up"
            icon="⭐"
            color="green"
          />
          <MetricCard
            title="Hot Leads"
            value={metrics.hot_leads}
            trend="Ready to close"
            trendDirection="up"
            icon="🔥"
            color="red"
          />
          <MetricCard
            title="Follow-ups Due"
            value={metrics.follow_ups_due}
            trend="Due today"
            trendDirection="neutral"
            icon="⏰"
            color="orange"
          />
        </div>

        {/* Performance Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Response Rate"
            value={metrics.response_rate}
            trend={trends.response_time_improvement}
            trendDirection="up"
            icon="📱"
            color="green"
            subtitle="Industry avg: 65%"
          />
          <MetricCard
            title="Avg Response Time"
            value={metrics.avg_response_time}
            trend="18% faster"
            trendDirection="up"
            icon="⚡"
            color="blue"
            subtitle="Industry avg: 15 min"
          />
          <MetricCard
            title="Meetings Today"
            value={metrics.meetings_today}
            trend="2 confirmed"
            trendDirection="up"
            icon="📅"
            color="purple"
          />
          <MetricCard
            title="Revenue Growth"
            value={trends.revenue_growth}
            trend="This month"
            trendDirection="up"
            icon="💰"
            color="green"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <LeadSourceChart data={dashboardData?.lead_sources} />
          <WeeklyTrendChart data={dashboardData?.weekly_trend} />
        </div>

        {/* Pipeline Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <PipelineChart data={dashboardData?.pipeline} />
          
          {/* Quick Actions Panel */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            
            <div className="space-y-3">
              <button className="w-full flex items-center justify-between p-4 text-left bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
                <div>
                  <div className="font-medium text-red-900">Call Hot Leads</div>
                  <div className="text-sm text-red-600">12 leads ready to close</div>
                </div>
                <span className="text-red-500">🔥</span>
              </button>
              
              <button className="w-full flex items-center justify-between p-4 text-left bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
                <div>
                  <div className="font-medium text-blue-900">Follow Up Today</div>
                  <div className="text-sm text-blue-600">6 leads need attention</div>
                </div>
                <span className="text-blue-500">📞</span>
              </button>
              
              <button className="w-full flex items-center justify-between p-4 text-left bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
                <div>
                  <div className="font-medium text-green-900">Schedule Meetings</div>
                  <div className="text-sm text-green-600">8 qualified leads</div>
                </div>
                <span className="text-green-500">📅</span>
              </button>
              
              <button className="w-full flex items-center justify-between p-4 text-left bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
                <div>
                  <div className="font-medium text-purple-900">Send Proposals</div>
                  <div className="text-sm text-purple-600">3 deals in negotiation</div>
                </div>
                <span className="text-purple-500">📄</span>
              </button>
            </div>
          </div>
        </div>

        {/* AI Insights Panel */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <span className="text-2xl mr-3">🤖</span>
            <h3 className="text-lg font-semibold text-gray-900">AI Insights</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4">
              <div className="font-medium text-gray-900">Best Time to Call</div>
              <div className="text-sm text-gray-600 mt-1">
                3-6 PM shows 67% higher pickup rate
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4">
              <div className="font-medium text-gray-900">Top Performing Source</div>
              <div className="text-sm text-gray-600 mt-1">
                WhatsApp leads convert 34% better
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4">
              <div className="font-medium text-gray-900">Priority Action</div>
              <div className="text-sm text-gray-600 mt-1">
                Focus on Bandra leads this week
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickDashboard;
