/**
 * Smart Property Form Demo Page
 * =============================
 * 
 * This page demonstrates our consolidated AI-powered smart property form.
 */

'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  SparklesIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import SmartPropertyForm from '@/components/SmartPropertyForm'
import toast from 'react-hot-toast'

export default function SmartFormDemo() {
  const [showForm, setShowForm] = useState(false)
  const [formResults, setFormResults] = useState<any[]>([])

  const handleFormSuccess = (data: any) => {
    const result = {
      id: Date.now(),
      data,
      timestamp: new Date().toISOString()
    }
    setFormResults(prev => [result, ...prev])
    toast.success('Property created successfully!')
  }

  const resetDemo = () => {
    setFormResults([])
    setShowForm(false)
    toast.success('Demo reset successfully!')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Smart Property Form Demo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience our AI-powered smart property form with market insights and intelligent suggestions.
          </p>
        </div>

        {/* Features */}
        <div className="mb-8 bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
            <SparklesIcon className="h-6 w-6 text-blue-600 mr-2" />
            AI-Powered Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              <span>AI-Generated Descriptions</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              <span>Market Insights</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              <span>Smart Price Suggestions</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              <span>Quality Scoring</span>
            </div>
          </div>
        </div>

        {/* Form Controls */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <SparklesIcon className="h-5 w-5" />
              <span>{showForm ? 'Hide Form' : 'Try Smart Form'}</span>
            </button>
            
            {showForm && formResults.length > 0 && (
              <button
                onClick={resetDemo}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Reset Demo
              </button>
            )}
          </div>
        </div>

        {/* Form Display */}
        {showForm && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="bg-white rounded-lg shadow-lg p-6">
              <SmartPropertyForm onSuccess={handleFormSuccess} />
            </div>
          </motion.div>
        )}

        {/* Results Display */}
        {formResults.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Created Properties ({formResults.length})
            </h3>
            
            <div className="space-y-4">
              {formResults.map((result) => (
                <motion.div
                  key={result.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        AI-Generated
                      </span>
                      <span className="text-sm text-gray-500">
                        {new Date(result.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  </div>
                  
                  <div className="text-sm text-gray-700">
                    <p><strong>Title:</strong> {result.data.title || 'Generated Property'}</p>
                    <p><strong>Location:</strong> {result.data.location || result.data.address}</p>
                    <p><strong>Price:</strong> ₹{result.data.price}</p>
                    <p><strong>Type:</strong> {result.data.propertyType}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}