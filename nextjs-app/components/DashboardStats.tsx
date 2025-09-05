'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  HomeIcon, 
  EyeIcon, 
  UserGroupIcon, 
  CurrencyRupeeIcon,
  CheckCircleIcon,
  SparklesIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  PlusIcon,
  CalendarDaysIcon,
  BellIcon,
  FireIcon
} from '@heroicons/react/24/outline'
import { 
  HomeIcon as HomeSolid,
  EyeIcon as EyeSolid,
  UserGroupIcon as UserGroupSolid,
  CurrencyRupeeIcon as CurrencyRupeeSolid
} from '@heroicons/react/24/solid'

interface DashboardStatsProps {
  stats: {
    total_properties: number
    active_listings: number
    total_leads: number
    total_users: number
    total_views: number
    monthly_leads: number
    revenue: string
  }
  onAddProperty?: () => void
  onNavigateToAI?: () => void
  onNavigateToAnalytics?: () => void
  onNavigateToSmartForm?: () => void
}

const statCards = [
  {
    title: 'Total Properties',
    value: 'total_properties',
    icon: HomeIcon,
    solidIcon: HomeSolid,
    color: 'from-blue-500 to-blue-600',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    textColor: 'text-blue-600 dark:text-blue-400',
    trend: '+12%',
    trendType: 'up' as const,
    description: 'Listed this month'
  },
  {
    title: 'Property Views',
    value: 'total_views',
    icon: EyeIcon,
    solidIcon: EyeSolid,
    color: 'from-emerald-500 to-emerald-600',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
    textColor: 'text-emerald-600 dark:text-emerald-400',
    trend: '+24%',
    trendType: 'up' as const,
    description: 'vs last month'
  },
  {
    title: 'Active Leads',
    value: 'total_leads',
    icon: UserGroupIcon,
    solidIcon: UserGroupSolid,
    color: 'from-purple-500 to-purple-600',
    bgColor: 'bg-purple-50 dark:bg-purple-900/20',
    textColor: 'text-purple-600 dark:text-purple-400',
    trend: '+8%',
    trendType: 'up' as const,
    description: 'New this week'
  },
  {
    title: 'Revenue',
    value: 'revenue',
    icon: CurrencyRupeeIcon,
    solidIcon: CurrencyRupeeSolid,
    color: 'from-amber-500 to-amber-600',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    textColor: 'text-amber-600 dark:text-amber-400',
    trend: '+18%',
    trendType: 'up' as const,
    description: 'This quarter'
  }
]

const DashboardStats = React.memo(function DashboardStats({ stats, onAddProperty, onNavigateToAI, onNavigateToAnalytics, onNavigateToSmartForm }: DashboardStatsProps) {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [isHovered, setIsHovered] = useState<string | null>(null)

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const getGreeting = () => {
    const hour = currentTime.getHours()
    if (hour < 12) return 'Good Morning'
    if (hour < 17) return 'Good Afternoon'
    return 'Good Evening'
  }

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Modern Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 rounded-3xl p-6 sm:p-8 text-white"
      >
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-40 h-40 bg-white rounded-full -translate-x-20 -translate-y-20"></div>
          <div className="absolute bottom-0 right-0 w-32 h-32 bg-white rounded-full translate-x-16 translate-y-16"></div>
          <div className="absolute top-1/2 right-1/4 w-24 h-24 bg-white rounded-full"></div>
        </div>
        
        <div className="relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <FireIcon className="w-6 h-6 text-yellow-300" data-testid="fire-icon" />
                <h1 className="text-2xl sm:text-3xl font-bold">
                  {getGreeting()}!
                </h1>
              </div>
              <p className="text-blue-100 text-sm sm:text-base">
                Ready to boost your real estate business today?
              </p>
            </div>
            
            <div className="mt-4 sm:mt-0 flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-blue-200">Today</div>
                <div className="font-semibold">
                  {currentTime.toLocaleDateString('en-US', { 
                    weekday: 'short', 
                    month: 'short', 
                    day: 'numeric' 
                  })}
                </div>
              </div>
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                <CalendarDaysIcon className="w-6 h-6" data-testid="calendar-days-icon" />
              </div>
            </div>
          </div>
          
          {/* Quick Stats Preview */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 text-center">
              <div className="text-lg sm:text-xl font-bold">{stats.total_properties}</div>
              <div className="text-xs text-blue-200">Properties</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 text-center">
              <div className="text-lg sm:text-xl font-bold">{stats.total_leads}</div>
              <div className="text-xs text-blue-200">Active Leads</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 text-center">
              <div className="text-lg sm:text-xl font-bold">{stats.total_views.toLocaleString()}</div>
              <div className="text-xs text-blue-200">Total Views</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 text-center">
              <div className="text-lg sm:text-xl font-bold">{stats.revenue}</div>
              <div className="text-xs text-blue-200">Revenue</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Enhanced Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {statCards.map((card, index) => {
          const Icon = (isHovered === card.title && card.solidIcon) ? card.solidIcon : card.icon
          const TrendIcon = card.trendType === 'up' ? ArrowTrendingUpIcon : ArrowTrendingDownIcon
          
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onHoverStart={() => setIsHovered(card.title)}
              onHoverEnd={() => setIsHovered(null)}
              className={`group relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-200 dark:border-slate-700 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:scale-[1.02] ${card.bgColor}`}
            >
              {/* Background Gradient */}
              <div className={`absolute inset-0 bg-gradient-to-br ${card.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>
              
              <div className="relative z-10">
                {/* Header with Icon and Trend */}
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-xl ${card.bgColor} ${card.textColor} group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className="w-6 h-6" data-testid={`${card.title.replace(/\s/g, '-')}-icon`} />
                  </div>
                  <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${
                    card.trendType === 'up' 
                      ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' 
                      : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                  }`}>
                    <TrendIcon className="w-3 h-3" data-testid={`${card.title.replace(/\s/g, '-')}-trend-icon`} />
                    <span>{card.trend}</span>
                  </div>
                </div>
                
                {/* Main Value */}
                <div className="mb-2">
                  <div className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:to-purple-600 transition-all duration-300">
                    {card.value === 'revenue' ? stats[card.value as keyof typeof stats] : stats[card.value as keyof typeof stats].toLocaleString()}
                  </div>
                </div>
                
                {/* Title and Description */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    {card.title}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {card.description}
                  </p>
                </div>
                
                {/* Hover Effect Bar */}
                <div className={`absolute bottom-0 left-0 h-1 bg-gradient-to-r ${card.color} transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left`}></div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Modern Quick Actions */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Quick Actions</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Get started with these essential tasks</p>
          </div>
          <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <BellIcon className="w-4 h-4" data-testid="bell-icon" />
            <span>3 pending tasks</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="group relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-200 dark:border-slate-700 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
          >
            {/* Background Pattern */}
            <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/10 rounded-full -translate-y-10 translate-x-10 group-hover:scale-150 transition-transform duration-500"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform duration-300">
                  <HomeIcon className="w-6 h-6" data-testid="add-property-icon" />
                </div>
                <div className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded-full font-medium">
                  Popular
                </div>
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300">
                Add Properties
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                Start listing your properties with AI-powered descriptions and market insights
              </p>
              
              <button 
                onClick={onAddProperty}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white py-3 px-4 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
              >
                <PlusIcon className="w-5 h-5" data-testid="plus-icon" />
                <span>Add Property</span>
              </button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="group relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-200 dark:border-slate-700 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
          >
            {/* Background Pattern */}
            <div className="absolute top-0 right-0 w-20 h-20 bg-purple-500/10 rounded-full -translate-y-10 translate-x-10 group-hover:scale-150 transition-transform duration-500"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-xl text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform duration-300">
                  <SparklesIcon className="w-6 h-6" />
                </div>
                <div className="text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 px-2 py-1 rounded-full font-medium">
                  AI Powered
                </div>
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors duration-300">
                AI Tools
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                Generate compelling content, market analysis, and property descriptions automatically
              </p>
              
              <button 
                onClick={onNavigateToAI}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white py-3 px-4 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
              >
                <SparklesIcon className="w-5 h-5" />
                <span>Explore AI</span>
              </button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="group relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-200 dark:border-slate-700 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
          >
            {/* Background Pattern */}
            <div className="absolute top-0 right-0 w-20 h-20 bg-emerald-500/10 rounded-full -translate-y-10 translate-x-10 group-hover:scale-150 transition-transform duration-500"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform duration-300">
                  <ChartBarIcon className="w-6 h-6" />
                </div>
                <div className="text-xs bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 px-2 py-1 rounded-full font-medium">
                  Insights
                </div>
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors duration-300">
                Analytics
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                Track performance metrics, lead conversion rates, and market trends
              </p>
              
              <button 
                onClick={onNavigateToAnalytics}
                className="w-full bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white py-3 px-4 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
              >
                <ChartBarIcon className="w-5 h-5" data-testid="view-analytics-icon" />
                <span>View Analytics</span>
              </button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="group relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-200 dark:border-slate-700 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
          >
            {/* Background Pattern */}
            <div className="absolute top-0 right-0 w-20 h-20 bg-orange-500/10 rounded-full -translate-y-10 translate-x-10 group-hover:scale-150 transition-transform duration-500"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-xl text-orange-600 dark:text-orange-400 group-hover:scale-110 transition-transform duration-300">
                  <SparklesIcon className="w-6 h-6" />
                </div>
                <div className="text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 px-2 py-1 rounded-full font-medium">
                  NEW
                </div>
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors duration-300">
                Smart Form Demo
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                Experience our intelligent property form with step-by-step guidance and AI assistance
              </p>
              
              <button 
                onClick={onNavigateToSmartForm}
                className="w-full bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white py-3 px-4 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
              >
                <SparklesIcon className="w-5 h-5" />
                <span>Try Demo</span>
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
})

export default DashboardStats
