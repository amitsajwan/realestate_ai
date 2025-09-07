'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  HomeIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  EyeIcon,
  CalendarIcon,
  MapPinIcon
} from '@heroicons/react/24/outline'

interface AnalyticsProps {
  properties?: any[]
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
  const [mockProperties, setMockProperties] = useState<any[]>([])
  
  // Memoize properties to prevent infinite re-renders
  const memoizedProperties = useMemo(() => properties, [properties.length, JSON.stringify(properties)])
  
  // Use provided properties or load mock data
  const activeProperties = memoizedProperties.length > 0 ? memoizedProperties : mockProperties

  useEffect(() => {
    // Load mock properties if none provided
    if (memoizedProperties.length === 0) {
      const mockData = [
        {
          id: 1,
          title: 'Modern Downtown Condo',
          price: 450000,
          status: 'for-sale',
          type: 'Condo',
          dateAdded: '2024-01-15'
        },
        {
          id: 2,
          title: 'Luxury Villa',
          price: 850000,
          status: 'sold',
          type: 'House',
          dateAdded: '2024-01-10'
        },
        {
          id: 3,
          title: 'Suburban House',
          price: 320000,
          status: 'for-rent',
          type: 'House',
          dateAdded: '2024-01-20'
        },
        {
          id: 4,
          title: 'City Apartment',
          price: 280000,
          status: 'for-sale',
          type: 'Apartment',
          dateAdded: '2024-01-25'
        }
      ]
      setMockProperties(mockData)
    }
  }, [memoizedProperties.length])

  // Calculate analytics from properties data
  const totalProperties = activeProperties.length
  const forSaleProperties = activeProperties.filter(p => p.status === 'for-sale').length
  const forRentProperties = activeProperties.filter(p => p.status === 'for-rent').length
  const soldProperties = activeProperties.filter(p => p.status === 'sold').length
  
  const averagePrice = activeProperties.length > 0 
    ? Math.round(activeProperties.reduce((sum, p) => sum + p.price, 0) / activeProperties.length)
    : 0
  
  const totalValue = activeProperties.reduce((sum, p) => sum + p.price, 0)
  
  const propertyTypes = activeProperties.reduce((acc, p) => {
    acc[p.type] = (acc[p.type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const stats: StatCard[] = [
    {
      title: 'Total Properties',
      value: totalProperties,
      change: '+12%',
      changeType: 'increase',
      icon: HomeIcon,
      color: 'bg-blue-500'
    },
    {
      title: 'Total Portfolio Value',
      value: `$${totalValue.toLocaleString()}`,
      change: '+8.2%',
      changeType: 'increase',
      icon: CurrencyDollarIcon,
      color: 'bg-green-500'
    },
    {
      title: 'Average Property Value',
      value: `$${averagePrice.toLocaleString()}`,
      change: '+5.1%',
      changeType: 'increase',
      icon: ArrowTrendingUpIcon,
      color: 'bg-purple-500'
    },
    {
      title: 'Properties Sold',
      value: soldProperties,
      change: '+15%',
      changeType: 'increase',
      icon: ChartBarIcon,
      color: 'bg-orange-500'
    }
  ]

  const statusBreakdown = [
    { label: 'For Sale', value: forSaleProperties, color: 'bg-blue-500', percentage: totalProperties > 0 ? Math.round((forSaleProperties / totalProperties) * 100) : 0 },
    { label: 'For Rent', value: forRentProperties, color: 'bg-green-500', percentage: totalProperties > 0 ? Math.round((forRentProperties / totalProperties) * 100) : 0 },
    { label: 'Sold', value: soldProperties, color: 'bg-gray-500', percentage: totalProperties > 0 ? Math.round((soldProperties / totalProperties) * 100) : 0 }
  ]

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
            {Object.entries(propertyTypes).map(([type, count], index) => {
              const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500']
              const countNum = Number(count)
              const percentage = totalProperties > 0 ? Math.round((countNum / totalProperties) * 100) : 0
              
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
