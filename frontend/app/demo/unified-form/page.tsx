/**
 * Unified Form Demo Page
 * ======================
 * 
 * This page demonstrates all variants of the unified property form
 * with different configurations and features.
 */

'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  SparklesIcon,
  ListBulletIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import UnifiedPropertyForm from '@/components/property/UnifiedPropertyForm'
import { FormVariant, FormConfig } from '@/types/PropertyFormTypes'
import toast from 'react-hot-toast'

const FORM_VARIANTS: Array<{
  id: FormVariant
  name: string
  description: string
  icon: React.ComponentType<any>
  config: Partial<FormConfig>
}> = [
  {
    id: 'simple',
    name: 'Simple Form',
    description: 'Quick and straightforward property creation',
    icon: ListBulletIcon,
    config: {
      features: {
        ai: false,
        marketInsights: false,
        qualityScoring: false,
        multilanguage: false,
        autoSave: true,
        validation: 'onSubmit'
      },
      ui: {
        showProgress: false,
        showSections: true,
        showAI: false,
        showMarketInsights: false
      }
    }
  },
  {
    id: 'wizard',
    name: 'Wizard Form',
    description: 'Step-by-step guided property creation',
    icon: ArrowPathIcon,
    config: {
      features: {
        ai: true,
        marketInsights: true,
        qualityScoring: true,
        multilanguage: true,
        autoSave: true,
        validation: 'onBlur'
      },
      ui: {
        showProgress: true,
        showSections: false,
        showAI: true,
        showMarketInsights: true
      }
    }
  },
  {
    id: 'ai-first',
    name: 'AI-First Form',
    description: 'AI-powered property creation with smart suggestions',
    icon: SparklesIcon,
    config: {
      features: {
        ai: true,
        marketInsights: true,
        qualityScoring: true,
        multilanguage: true,
        autoSave: true,
        validation: 'onChange'
      },
      ui: {
        showProgress: false,
        showSections: true,
        showAI: true,
        showMarketInsights: true
      }
    }
  }
]

export default function UnifiedFormDemo() {
  const [selectedVariant, setSelectedVariant] = useState<FormVariant>('simple')
  const [showForm, setShowForm] = useState(false)
  const [formResults, setFormResults] = useState<any[]>([])

  const selectedFormConfig = FORM_VARIANTS.find(v => v.id === selectedVariant)

  const handleFormSuccess = (data: any) => {
    const result = {
      id: Date.now(),
      variant: selectedVariant,
      data,
      timestamp: new Date().toISOString()
    }
    setFormResults(prev => [result, ...prev])
    toast.success(`Property created successfully with ${selectedVariant} form!`)
  }

  const handleFormError = (error: Error) => {
    toast.error(`Form error: ${error.message}`)
  }

  const resetDemo = () => {
    setFormResults([])
    setShowForm(false)
    toast.success('Demo reset successfully!')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Unified Property Form Demo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience different variants of our unified property form system.
            Each variant is designed for different use cases and user preferences.
          </p>
        </div>

        {/* Variant Selection */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Choose a Form Variant</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {FORM_VARIANTS.map((variant) => {
              const Icon = variant.icon
              const isSelected = selectedVariant === variant.id
              
              return (
                <motion.div
                  key={variant.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`relative cursor-pointer rounded-lg border-2 p-6 transition-all duration-200 ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 shadow-lg'
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
                  }`}
                  onClick={() => setSelectedVariant(variant.id)}
                >
                  {isSelected && (
                    <div className="absolute top-4 right-4">
                      <CheckCircleIcon className="h-6 w-6 text-blue-600" />
                    </div>
                  )}
                  
                  <div className="flex items-center space-x-3 mb-4">
                    <div className={`p-3 rounded-lg ${
                      isSelected ? 'bg-blue-100' : 'bg-gray-100'
                    }`}>
                      <Icon className={`h-6 w-6 ${
                        isSelected ? 'text-blue-600' : 'text-gray-600'
                      }`} />
                    </div>
                    <h3 className={`text-lg font-semibold ${
                      isSelected ? 'text-blue-900' : 'text-gray-900'
                    }`}>
                      {variant.name}
                    </h3>
                  </div>
                  
                  <p className={`text-sm ${
                    isSelected ? 'text-blue-700' : 'text-gray-600'
                  }`}>
                    {variant.description}
                  </p>

                  {/* Feature indicators */}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {Object.entries(variant.config.features || {}).map(([feature, enabled]) => (
                      enabled && (
                        <span
                          key={feature}
                          className={`px-2 py-1 text-xs rounded-full ${
                            isSelected
                              ? 'bg-blue-200 text-blue-800'
                              : 'bg-gray-200 text-gray-700'
                          }`}
                        >
                          {feature.replace(/([A-Z])/g, ' $1').trim()}
                        </span>
                      )
                    ))}
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>

        {/* Form Controls */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              {showForm ? 'Hide Form' : 'Show Form'}
            </button>
            
            {showForm && (
              <button
                onClick={resetDemo}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                Reset Demo
              </button>
            )}
          </div>

          {selectedFormConfig && (
            <div className="text-sm text-gray-600">
              Selected: <span className="font-medium">{selectedFormConfig.name}</span>
            </div>
          )}
        </div>

        {/* Form Display */}
        <AnimatePresence>
          {showForm && selectedFormConfig && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-8"
            >
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {selectedFormConfig.name}
                  </h3>
                  <p className="text-gray-600">{selectedFormConfig.description}</p>
                </div>
                
                <UnifiedPropertyForm
                  variant={selectedVariant}
                  config={selectedFormConfig.config}
                  onSuccess={handleFormSuccess}
                  onError={handleFormError}
                  userId="demo-user"
                  sessionId="demo-session"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Display */}
        {formResults.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Form Results ({formResults.length})
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
                        {result.variant}
                      </span>
                      <span className="text-sm text-gray-500">
                        {new Date(result.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  </div>
                  
                  <div className="text-sm text-gray-700">
                    <p><strong>Title:</strong> {result.data.title}</p>
                    <p><strong>Location:</strong> {result.data.location}</p>
                    <p><strong>Price:</strong> ₹{result.data.price}</p>
                    <p><strong>Type:</strong> {result.data.propertyType}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Feature Comparison */}
        <div className="mt-12 bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            Feature Comparison
          </h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Feature
                  </th>
                  {FORM_VARIANTS.map((variant) => (
                    <th key={variant.id} className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {variant.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {[
                  { key: 'ai', label: 'AI Suggestions' },
                  { key: 'marketInsights', label: 'Market Insights' },
                  { key: 'qualityScoring', label: 'Quality Scoring' },
                  { key: 'multilanguage', label: 'Multi-language' },
                  { key: 'autoSave', label: 'Auto-save' },
                  { key: 'showProgress', label: 'Progress Indicator' },
                  { key: 'showSections', label: 'Collapsible Sections' }
                ].map((feature) => (
                  <tr key={feature.key}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {feature.label}
                    </td>
                    {FORM_VARIANTS.map((variant) => {
                      const enabled = variant.config.features?.[feature.key as keyof typeof variant.config.features] ||
                                     variant.config.ui?.[feature.key as keyof typeof variant.config.ui]
                      
                      return (
                        <td key={variant.id} className="px-6 py-4 whitespace-nowrap text-center">
                          {enabled ? (
                            <CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" />
                          ) : (
                            <ExclamationTriangleIcon className="h-5 w-5 text-gray-400 mx-auto" />
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}