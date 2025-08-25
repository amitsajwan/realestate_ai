'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { UsersIcon } from '@heroicons/react/24/outline'

export default function CRM() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="glass-card">
        <div className="flex items-center space-x-3 mb-6">
          <UsersIcon className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-gray-800">Customer Relationship Management</h2>
        </div>
        
        <p className="text-gray-600 mb-6">
          Manage your leads and customer relationships effectively.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="stat-card">
            <div className="stat-number">24</div>
            <div className="stat-label">New Leads</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">12</div>
            <div className="stat-label">Pending</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">8</div>
            <div className="stat-label">Converted</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">15</div>
            <div className="stat-label">Calls Today</div>
          </div>
        </div>

        <div className="glass-card">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Leads</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Interest</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Rahul Sharma</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">+91 98765 43210</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">3 BHK Apartment</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">New</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-2">Call</button>
                    <button className="text-green-600 hover:text-green-900">Message</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
