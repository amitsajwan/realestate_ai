'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { ChartBarIcon } from '@heroicons/react/24/outline'

export default function Analytics() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="glass-card">
        <div className="flex items-center space-x-3 mb-6">
          <ChartBarIcon className="w-6 h-6 text-green-500" />
          <h2 className="text-2xl font-bold text-gray-800">Analytics Dashboard</h2>
        </div>
        
        <p className="text-gray-600 mb-6">
          Track your property performance and business growth.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Property Performance</h3>
            <p className="text-gray-500">Analytics data will be displayed here once connected to your data sources.</p>
          </div>
          
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Lead Conversion</h3>
            <p className="text-gray-500">Lead conversion metrics will appear here.</p>
          </div>
        </div>

        <div className="mt-6">
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Monthly Trends</h3>
            <p className="text-gray-500">Monthly performance trends will be displayed here.</p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
