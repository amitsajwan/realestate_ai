'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircleIcon, SparklesIcon } from '@heroicons/react/24/outline'
import GenAIPropertyForm from '@/components/GenAIPropertyForm'
import { toast } from 'react-hot-toast'

export default function GenAIFormDemo() {
  const [completedProperties, setCompletedProperties] = useState<string[]>([])

  const handleSuccess = (propertyId: string) => {
    setCompletedProperties(prev => [...prev, propertyId])
    toast.success(`Property ${propertyId} created successfully!`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-lg border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                GenAI Property Form Demo
              </h1>
              <p className="text-blue-200">
                Test the complete three-step GenAI-enabled property creation workflow
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-green-500/20 text-green-300 px-4 py-2 rounded-lg border border-green-500/30">
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="w-5 h-5" />
                  <span className="font-medium">{completedProperties.length} Properties Created</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Demo Instructions */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card"
          >
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-lg">1</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Property Details</h3>
              <p className="text-gray-600 text-sm">
                Fill in core property information with drag & drop media upload
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card"
          >
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <SparklesIcon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Assistance</h3>
              <p className="text-gray-600 text-sm">
                Get AI-powered descriptions, pricing suggestions, and SEO content
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card"
          >
            <div className="text-center">
              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-lg">3</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Social Media</h3>
              <p className="text-gray-600 text-sm">
                Create and share property listings on social media platforms
              </p>
            </div>
          </motion.div>
        </div>

        {/* Testing Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card mb-8"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">🧪 Testing Instructions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Step 1 - Property Details</h4>
              <ul className="space-y-1 text-sm text-gray-600 list-disc list-inside">
                <li>Fill minimum required fields: Title, Type, Location, Area</li>
                <li>Test drag & drop image upload</li>
                <li>Notice AI unlock notification when ready</li>
                <li>Try form validation by leaving fields empty</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Step 2 - AI Features</h4>
              <ul className="space-y-1 text-sm text-gray-600 list-disc list-inside">
                <li>Click "Generate AI Content" button</li>
                <li>Test "Apply" buttons for each suggestion</li>
                <li>Try "Copy" functionality for generated content</li>
                <li>Notice quality scores and market insights</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Step 3 - Social Media</h4>
              <ul className="space-y-1 text-sm text-gray-600 list-disc list-inside">
                <li>Review property summary</li>
                <li>Test social media integration placeholder</li>
                <li>Save property to CRM</li>
                <li>Complete the full workflow</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Navigation & UX</h4>
              <ul className="space-y-1 text-sm text-gray-600 list-disc list-inside">
                <li>Test step navigation (Previous/Next)</li>
                <li>Notice step locking until requirements met</li>
                <li>Experience smooth animations</li>
                <li>Test responsive design on mobile</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>

      {/* GenAI Property Form */}
      <GenAIPropertyForm onSuccess={handleSuccess} />

      {/* Demo Footer */}
      <div className="bg-white/10 backdrop-blur-lg border-t border-white/20 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-white mb-4">
              🎯 Key Features Demonstrated
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
              <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                <div className="text-2xl mb-2">🧠</div>
                <h4 className="font-semibold text-white mb-2">AI-Powered UX</h4>
                <p className="text-blue-200">
                  Intelligent suggestions reduce cognitive load and improve form completion rates
                </p>
              </div>
              <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                <div className="text-2xl mb-2">📊</div>
                <h4 className="font-semibold text-white mb-2">Progressive Disclosure</h4>
                <p className="text-blue-200">
                  Step-by-step workflow prevents overwhelming users with too many fields
                </p>
              </div>
              <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                <div className="text-2xl mb-2">🚀</div>
                <h4 className="font-semibold text-white mb-2">Seamless Integration</h4>
                <p className="text-blue-200">
                  Integrates with existing APIs, validation, and social media components
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}