'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { CogIcon } from '@heroicons/react/24/outline'

export default function FacebookIntegration() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="glass-card">
        <div className="flex items-center space-x-3 mb-6">
          <CogIcon className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-gray-800">Facebook Integration</h2>
        </div>
        
        <p className="text-gray-600 mb-6">
          Connect your Facebook account to automatically post properties and engage with leads.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Connected Facebook Pages</h3>
            <p className="text-gray-500">Loading Facebook pages...</p>
          </div>
          
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Posts</h3>
            <p className="text-gray-500">No recent posts found.</p>
          </div>
        </div>

        <div className="mt-6">
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Post</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Page</label>
                <select className="form-input">
                  <option>Choose a page...</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Post Type</label>
                <select className="form-input">
                  <option>Text Post</option>
                  <option>Image Post</option>
                  <option>Link Post</option>
                </select>
              </div>
              <button className="btn-primary">Create Post</button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
