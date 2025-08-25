'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { UserIcon } from '@heroicons/react/24/outline'

export default function ProfileSettings() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="glass-card">
        <div className="flex items-center space-x-3 mb-6">
          <UserIcon className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-gray-800">Profile & Settings</h2>
        </div>
        
        <p className="text-gray-600 mb-6">
          Manage your profile, preferences, and account settings.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Personal Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">First Name *</label>
                <input type="text" className="form-input" defaultValue="John" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Last Name *</label>
                <input type="text" className="form-input" defaultValue="Doe" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
                <input type="email" className="form-input" defaultValue="john.doe@example.com" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                <input type="tel" className="form-input" defaultValue="+91 98765 43210" />
              </div>
            </div>
          </div>
          
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Company Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Company Name *</label>
                <input type="text" className="form-input" defaultValue="Real Estate Pro" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Position</label>
                <input type="text" className="form-input" defaultValue="Senior Agent" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">License Number</label>
                <input type="text" className="form-input" defaultValue="RE123456" />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <button className="btn-primary">Save Changes</button>
        </div>
      </div>
    </motion.div>
  )
}
