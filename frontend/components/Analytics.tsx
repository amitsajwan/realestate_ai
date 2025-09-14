'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
// import '@/styles/components/analytics.css' // Temporarily disabled for tests
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  HomeIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  EyeIcon,
  CalendarIcon,
  MapPinIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { crmApi, DashboardMetrics, AnalyticsMetric } from '@/lib/crm-api'
import { transformPropertiesToAnalytics, safePropertyAccess, calculatePercentage, formatCurrency, type Property } from '@/lib/data-transformers'

interface AnalyticsProps {
  properties?: Property[]
}

interface StatCard {
  title: string
  value: string | number
  change?: string
  changeType?: 'increase' | 'decrease' | 'neutral'
  icon: React.ComponentType<{ className?: string }>
  color: string
}

export default function Analytics({ properties = [] }: AnalyticsProps) {
  const [dashboardData, setDashboardData] = useState<DashboardMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPeriod, setSelectedPeriod] = useState('this_month')
  
  // Memoize properties to prevent infinite re-renders
  const memoizedProperties = useMemo(() => properties, [properties.length, JSON.stringify(properties)])

  useEffect(() => {
    loadAnalyticsData()
  }, [selectedPeriod])

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const data = await crmApi.getDashboardMetrics(selectedPeriod)
      setDashboardData(data)

    } catch (err) {
      console.error('Error loading analytics:', err)
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
      
      // Fallback to mock data
      loadMockData()
    } finally {
      setIsLoading(false)
    }
  }

  const loadMockData = () => {
    // Mock data fallback
    const mockData: DashboardMetrics = {
      overview_metrics: [
        {
          name: 'Total Properties',
          value: 4,
          type: 'count',
          description: 'Total number of properties'
        },
        {
          name: 'Total Leads',
          value: 12,
          type: 'count',
          description: 'Total number of leads'
        },
        {
          name: 'Conversion Rate',
          value: 25.0,
          type: 'percentage',
          unit: '%',
          description: 'Lead conversion rate'
        },
        {
          name: 'Average Deal Value',
          value: 475000,
          type: 'sum',
          unit: '$',
          description: 'Average value of converted deals'
        }
      ],
      property_analytics: {
        total_properties: 4,
        published_properties: 3,
        draft_properties: 1,
        archived_properties: 0,
        average_price: 475000,
        total_value: 1900000,
        price_range_distribution: {},
        property_type_distribution: {},
        location_distribution: {},
        status_distribution: {},
        average_days_on_market: 30,
        conversion_rate: 25,
        top_performing_properties: [],
        recent_activity: []
      },
      lead_analytics: {
        total_leads: 12,
        new_leads: 3,
        contacted_leads: 4,
        qualified_leads: 3,
        converted_leads: 2,
        lost_leads: 0,
        conversion_rate: 16.67,
        average_lead_score: 75,
        lead_source_distribution: {},
        urgency_distribution: {},
        budget_distribution: {},
        average_deal_value: 475000,
        total_pipeline_value: 1900000,
        lead_response_time: 2.5,
        follow_up_completion_rate: 85,
        top_performing_sources: [],
        recent_activities: []
      },
      generated_at: new Date().toISOString(),
      period: selectedPeriod,
      date_range: {
        start: new Date().toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
      }
    }
    
    setDashboardData(mockData)
  }

  // Transform properties data using our robust transformer
  const transformedAnalytics = useMemo(() => {
    return transformPropertiesToAnalytics(memoizedProperties)
  }, [memoizedProperties])

  // Use dashboard data or fallback to transformed properties data
  const analyticsData = dashboardData || {
    overview_metrics: [],
    property_analytics: transformedAnalytics,
    lead_analytics: {
      total_leads: 0,
      new_leads: 0,
      contacted_leads: 0,
      qualified_leads: 0,
      converted_leads: 0,
      lost_leads: 0,
      conversion_rate: 0,
      average_lead_score: 0,
      lead_source_distribution: {},
      urgency_distribution: {},
      budget_distribution: {},
      average_deal_value: 0,
      total_pipeline_value: 0,
      lead_response_time: 0,
      follow_up_completion_rate: 0,
      top_performing_sources: [],
      recent_activities: []
    }
  }

  const stats: StatCard[] = analyticsData.overview_metrics.map(metric => ({
    title: metric.name,
    value: metric.unit ? `${metric.value}${metric.unit}` : metric.value,
    change: metric.change_percentage ? `${metric.change_percentage > 0 ? '+' : ''}${metric.change_percentage}%` : undefined,
    changeType: metric.change_direction === 'up' ? 'increase' : metric.change_direction === 'down' ? 'decrease' : 'neutral',
    icon: getIconForMetric(metric.name),
    color: getColorForMetric(metric.name)
  }))

  const statusBreakdown = [
    { 
      label: 'Published', 
      value: analyticsData.property_analytics.published_properties, 
      color: 'bg-blue-500', 
      percentage: analyticsData.property_analytics.total_properties > 0 ? Math.round((analyticsData.property_analytics.published_properties / analyticsData.property_analytics.total_properties) * 100) : 0 
    },
    { 
      label: 'Draft', 
      value: analyticsData.property_analytics.draft_properties, 
      color: 'bg-yellow-500', 
      percentage: analyticsData.property_analytics.total_properties > 0 ? Math.round((analyticsData.property_analytics.draft_properties / analyticsData.property_analytics.total_properties) * 100) : 0 
    },
    { 
      label: 'Archived', 
      value: analyticsData.property_analytics.archived_properties, 
      color: 'bg-gray-500', 
      percentage: analyticsData.property_analytics.total_properties > 0 ? Math.round((analyticsData.property_analytics.archived_properties / analyticsData.property_analytics.total_properties) * 100) : 0 
    }
  ]

  function getIconForMetric(name: string) {
    switch (name.toLowerCase()) {
      case 'total properties': return HomeIcon
      case 'total leads': return ChartBarIcon
      case 'conversion rate': return ArrowTrendingUpIcon
      case 'average deal value': return CurrencyDollarIcon
      default: return ChartBarIcon
    }
  }

  function getColorForMetric(name: string) {
    switch (name.toLowerCase()) {
      case 'total properties': return 'bg-blue-500'
      case 'total leads': return 'bg-green-500'
      case 'conversion rate': return 'bg-purple-500'
      case 'average deal value': return 'bg-orange-500'
      default: return 'bg-gray-500'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <ExclamationTriangleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button 
            onClick={loadAnalyticsData}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 mx-auto"
          >
            <ArrowPathIcon className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
          <p className="text-gray-300">Track your property portfolio performance and insights</p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-300">
          <CalendarIcon className="w-4 h-4" />
          <span>Last updated: {new Date().toLocaleDateString()}</span>
        </div>
      </div>

      {/* Key Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          const isIncrease = stat.changeType === 'increase'
          const ChangeIcon = isIncrease ? ArrowTrendingUpIcon : ArrowTrendingDownIcon
          
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                {stat.change && (
                  <div className={`flex items-center space-x-1 text-sm ${
                    isIncrease ? 'text-green-400' : 'text-red-400'
                  }`}>
                    <ChangeIcon className="w-4 h-4" />
                    <span>{stat.change}</span>
                  </div>
                )}
              </div>
              <div>
                <p className="text-2xl font-bold text-white mb-1">{stat.value}</p>
                <p className="text-gray-300 text-sm">{stat.title}</p>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Charts and Breakdowns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Property Status Breakdown */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
        >
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
            <ChartBarIcon className="w-5 h-5 mr-2" />
            Property Status Breakdown
          </h3>
          <div className="space-y-4">
            {statusBreakdown.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-4 h-4 rounded ${item.color}`}></div>
                  <span className="text-white">{item.label}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-white font-semibold">{item.value}</span>
                  <span className="text-gray-300 text-sm">({item.percentage}%)</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Property Types */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
        >
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
            <HomeIcon className="w-5 h-5 mr-2" />
            Property Types
          </h3>
          <div className="space-y-4">
            {Object.entries(safePropertyAccess(analyticsData, 'property_analytics.property_type_distribution', {})).map(([type, count], index) => {
              const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500']
              const countNum = Number(count)
              const totalProperties = safePropertyAccess(analyticsData, 'property_analytics.total_properties', 0)
              const percentage = calculatePercentage(countNum, totalProperties)
              
              return (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded ${colors[index % colors.length]}`}></div>
                    <span className="text-white">{type}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-white font-semibold">{countNum}</span>
                    <span className="text-gray-300 text-sm">({percentage}%)</span>
                  </div>
                </div>
              )
            })}
          </div>
        </motion.div>
      </div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
      >
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
          <EyeIcon className="w-5 h-5 mr-2" />
          Recent Activity
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-white/10">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-white">New property added: Modern Downtown Condo</span>
            </div>
            <span className="text-gray-300 text-sm">2 hours ago</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-white/10">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-white">Property status updated: Luxury Villa marked as sold</span>
            </div>
            <span className="text-gray-300 text-sm">5 hours ago</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-white/10">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-white">Price updated: Suburban House reduced by $10,000</span>
            </div>
            <span className="text-gray-300 text-sm">1 day ago</span>
          </div>
        </div>
      </motion.div>

      {/* Market Insights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
      >
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
          <ArrowTrendingUpIcon className="w-5 h-5 mr-2" />
          Market Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400 mb-1">+12.5%</div>
            <div className="text-gray-300 text-sm">Average Price Growth</div>
            <div className="text-xs text-gray-400 mt-1">vs last quarter</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400 mb-1">18 days</div>
            <div className="text-gray-300 text-sm">Average Time on Market</div>
            <div className="text-xs text-gray-400 mt-1">for sold properties</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400 mb-1">94%</div>
            <div className="text-gray-300 text-sm">Portfolio Occupancy</div>
            <div className="text-xs text-gray-400 mt-1">rental properties</div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
