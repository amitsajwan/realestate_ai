'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { 
  HomeIcon, 
  EyeIcon, 
  UserGroupIcon, 
  CurrencyRupeeIcon,
  CheckCircleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

interface StatsProps {
  stats: {
    total_properties: number
    active_listings: number
    total_leads: number
    total_users: number
    total_views: number
    monthly_leads: number
    revenue: string
  }
}

const statCards = [
  {
    title: 'Total Properties',
    value: 'total_properties',
    icon: HomeIcon,
    color: 'from-blue-500 to-blue-600'
  },
  {
    title: 'Property Views',
    value: 'total_views',
    icon: EyeIcon,
    color: 'from-green-500 to-green-600'
  },
  {
    title: 'Active Leads',
    value: 'total_leads',
    icon: UserGroupIcon,
    color: 'from-purple-500 to-purple-600'
  },
  {
    title: 'Revenue',
    value: 'revenue',
    icon: CurrencyRupeeIcon,
    color: 'from-yellow-500 to-yellow-600'
  }
]

export default function DashboardStats({ stats }: StatsProps) {
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card text-center"
      >
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          🚀 Welcome to PropertyAI!
        </h1>
        <p className="text-lg text-gray-600 mb-6">
          Your AI-powered real estate assistant is ready to help you succeed!
        </p>
        
        {/* Setup Progress */}
        <div className="flex justify-center space-x-4 mb-6">
          {[1, 2, 3, 4, 5, 6, 7].map((step) => (
            <div key={step} className="flex flex-col items-center">
              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white font-bold">
                {step}
              </div>
              <span className="text-xs text-gray-500 mt-1">Step {step}</span>
            </div>
          ))}
        </div>
        
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-center space-x-2">
            <CheckCircleIcon className="w-5 h-5 text-green-500" />
            <span className="text-green-700 font-medium">Setup Complete!</span>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="stat-card"
          >
            <div className={`w-12 h-12 bg-gradient-to-r ${card.color} rounded-lg flex items-center justify-center mb-4 mx-auto`}>
              <card.icon className="w-6 h-6 text-white" />
            </div>
            <div className="stat-number">
              {card.value === 'revenue' ? stats[card.value as keyof typeof stats] : stats[card.value as keyof typeof stats].toLocaleString()}
            </div>
            <div className="stat-label">{card.title}</div>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card text-center hover:scale-105 transition-transform duration-200"
        >
          <HomeIcon className="w-12 h-12 text-blue-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Add Properties</h3>
          <p className="text-gray-600 mb-4">Start listing your properties with AI assistance</p>
          <button className="btn-primary">
            Add Property
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card text-center hover:scale-105 transition-transform duration-200"
        >
          <SparklesIcon className="w-12 h-12 text-purple-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-800 mb-2">AI Tools</h3>
          <p className="text-gray-600 mb-4">Use AI to generate content and insights</p>
          <button className="btn-secondary">
            AI Tools
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="glass-card text-center hover:scale-105 transition-transform duration-200"
        >
          <EyeIcon className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Analytics</h3>
          <p className="text-gray-600 mb-4">Track your performance and growth</p>
          <button className="btn-outline">
            View Analytics
          </button>
        </motion.div>
      </div>
    </div>
  )
}
