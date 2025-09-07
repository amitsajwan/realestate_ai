/**
 * Unified Property Form Component
 * ===============================
 * 
 * This component provides a unified interface for all property form variants,
 * supporting simple, wizard, and AI-first modes with consistent UX.
 */

'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  SparklesIcon,
  MapPinIcon,
  HomeIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline'
import { useUnifiedPropertyForm } from '@/hooks/useUnifiedPropertyForm'
import { 
  UnifiedPropertyFormProps, 
  FormVariant, 
  FormConfig,
  WizardStep,
  FormSection
} from '@/types/PropertyFormTypes'
import PropertyImageUpload from './shared/PropertyImageUpload'
import UserFeedbackModal from '../UserFeedbackModal'
import { useABTesting } from '@/utils/featureFlags'
import { useUserTesting } from '@/utils/userTesting'
import { analytics } from '@/utils/analytics'

// Form sections configuration
const FORM_SECTIONS: Record<FormVariant, FormSection[]> = {
  simple: [
    {
      id: 'basic',
      title: 'Basic Information',
      description: 'Property details and location',
      icon: 'home',
      fields: ['title', 'propertyType', 'location', 'address'],
      required: true,
      completed: false,
      visible: true
    },
    {
      id: 'details',
      title: 'Property Details',
      description: 'Size, rooms, and amenities',
      icon: 'home',
      fields: ['area', 'bedrooms', 'bathrooms', 'amenities'],
      required: true,
      completed: false,
      visible: true
    },
    {
      id: 'pricing',
      title: 'Pricing & Description',
      description: 'Price and property description',
      icon: 'currency',
      fields: ['price', 'description'],
      required: true,
      completed: false,
      visible: true
    }
  ],
  wizard: [
    {
      id: 'location',
      title: 'Location & Address',
      description: 'Where is your property located?',
      icon: 'map',
      fields: ['location', 'address'],
      required: true,
      completed: false,
      visible: true
    },
    {
      id: 'basic',
      title: 'Basic Information',
      description: 'Property type and key details',
      icon: 'home',
      fields: ['title', 'propertyType', 'area', 'bedrooms', 'bathrooms'],
      required: true,
      completed: false,
      visible: true
    },
    {
      id: 'pricing',
      title: 'Pricing & Features',
      description: 'Set your price and list amenities',
      icon: 'currency',
      fields: ['price', 'amenities'],
      required: true,
      completed: false,
      visible: true
    },
    {
      id: 'description',
      title: 'Description & Media',
      description: 'Describe your property and add images',
      icon: 'document',
      fields: ['description'],
      required: true,
      completed: false,
      visible: true
    }
  ],
  'ai-first': [
    {
      id: 'minimal',
      title: 'Basic Details',
      description: 'Just the essentials',
      icon: 'home',
      fields: ['title', 'location', 'price', 'propertyType'],
      required: true,
      completed: false,
      visible: true
    },
    {
      id: 'ai-generation',
      title: 'AI Enhancement',
      description: 'Let AI enhance your listing',
      icon: 'sparkles',
      fields: [],
      required: false,
      completed: false,
      visible: true
    }
  ]
}

// Wizard steps for wizard variant
const WIZARD_STEPS: WizardStep[] = [
  {
    id: 'location',
    title: 'Location',
    description: 'Property location and address',
    icon: 'map',
    fields: ['location', 'address'],
    validation: (data) => !!(data.location && data.address),
    nextStep: 'basic',
    prevStep: undefined
  },
  {
    id: 'basic',
    title: 'Basic Info',
    description: 'Property type and details',
    icon: 'home',
    fields: ['title', 'propertyType', 'area', 'bedrooms', 'bathrooms'],
    validation: (data) => !!(data.title && data.propertyType && data.area && data.bedrooms && data.bathrooms),
    nextStep: 'pricing',
    prevStep: 'location'
  },
  {
    id: 'pricing',
    title: 'Pricing',
    description: 'Price and amenities',
    icon: 'currency',
    fields: ['price', 'amenities'],
    validation: (data) => !!(data.price),
    nextStep: 'description',
    prevStep: 'basic'
  },
  {
    id: 'description',
    title: 'Description',
    description: 'Property description and images',
    icon: 'document',
    fields: ['description'],
    validation: (data) => !!(data.description),
    nextStep: undefined,
    prevStep: 'pricing'
  }
]

export default function UnifiedPropertyForm({
  variant = 'simple',
  config = {},
  onSuccess,
  onError,
  className = '',
  initialData,
  userId,
  sessionId
}: UnifiedPropertyFormProps) {
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set())
  const [showAI, setShowAI] = useState(true)
  const [showMarketInsights, setShowMarketInsights] = useState(true)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [abandonmentPoint, setAbandonmentPoint] = useState<string>()
  
  const { variant: abVariant, trackEvent } = useABTesting()
  const { startSession, completeSession, abandonSession, trackEvent: trackUserEvent } = useUserTesting(variant, userId)

  // Initialize form hook
  const form = useUnifiedPropertyForm({
    variant,
    config,
    onSuccess: (data) => {
      // Complete user testing session
      completeSession(form.analytics)
      setShowFeedbackModal(true)
      onSuccess?.(data)
    },
    onError: (error) => {
      // Track error in user testing
      trackUserEvent('error', { error: error.message })
      onError?.(error)
    },
    autoSave: true
  })

  // Track page view and start user testing session
  useEffect(() => {
    analytics.trackPageView('Property Form', {
      variant,
      abVariant,
      userId,
      sessionId
    })

    // Start user testing session
    startSession()
  }, [variant, abVariant, userId, sessionId, startSession])

  // Track abandonment on page unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (form.state.isDirty && !form.state.isSubmitting) {
        setAbandonmentPoint('page_unload')
        abandonSession('page_unload')
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [form.state.isDirty, form.state.isSubmitting, abandonSession])

  // Initialize with data
  useEffect(() => {
    if (initialData) {
      form.setData(initialData)
    }
  }, [initialData, form])

  // Get current sections based on variant
  const currentSections = FORM_SECTIONS[variant]
  const currentStep = form.state.currentStep
  const totalSteps = form.state.totalSteps

  // Toggle section collapse
  const toggleSection = (sectionId: string) => {
    setCollapsedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      return newSet
    })
  }

  // Render form field
  const renderField = (fieldName: string, fieldConfig: any) => {
    const value = form.getValue(fieldName as any)
    const error = form.validation.errors[fieldName]
    const touched = form.validation.touched[fieldName]

    const commonProps = {
      key: fieldName,
      className: `w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
        error ? 'border-red-500' : 'border-gray-300'
      }`,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        form.setValue(fieldName, e.target.value)
      }
    }

    switch (fieldName) {
      case 'title':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Property Title *
            </label>
            <input
              {...commonProps}
              type="text"
              placeholder="e.g., Beautiful 3BHK Apartment in Prime Location"
              value={value || ''}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'description':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Property Description *
            </label>
            <textarea
              {...commonProps}
              rows={4}
              placeholder="Describe your property in detail..."
              value={value || ''}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'location':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Location *
            </label>
            <input
              {...commonProps}
              type="text"
              placeholder="e.g., Bandra West, Mumbai"
              value={value || ''}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'address':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Full Address *
            </label>
            <input
              {...commonProps}
              type="text"
              placeholder="Complete address with landmarks"
              value={value || ''}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'price':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Price (₹) *
            </label>
            <input
              {...commonProps}
              type="text"
              placeholder="e.g., 5000000"
              value={value || ''}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'propertyType':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Property Type *
            </label>
            <select {...commonProps} value={value || ''}>
              <option value="">Select property type</option>
              <option value="apartment">Apartment</option>
              <option value="house">House</option>
              <option value="villa">Villa</option>
              <option value="plot">Plot</option>
              <option value="commercial">Commercial</option>
            </select>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'area':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Area (sq ft) *
            </label>
            <input
              {...commonProps}
              type="number"
              placeholder="e.g., 1200"
              value={value || ''}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'bedrooms':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Bedrooms *
            </label>
            <select {...commonProps} value={value || ''}>
              <option value="">Select bedrooms</option>
              {[1, 2, 3, 4, 5, 6].map(num => (
                <option key={num} value={num}>{num} BHK</option>
              ))}
            </select>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'bathrooms':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Bathrooms *
            </label>
            <select {...commonProps} value={value || ''}>
              <option value="">Select bathrooms</option>
              {[1, 2, 3, 4, 5].map(num => (
                <option key={num} value={num}>{num}</option>
              ))}
            </select>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      case 'amenities':
        return (
          <div key={fieldName} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Amenities
            </label>
            <input
              {...commonProps}
              type="text"
              placeholder="e.g., Swimming Pool, Gym, Parking, Security"
              value={value || ''}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        )

      default:
        return null
    }
  }

  // Render AI assistant
  const renderAIAssistant = () => {
    if (!config.features?.ai) return null

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="h-6 w-6 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">AI Assistant</h3>
          </div>
          <button
            onClick={() => setShowAI(!showAI)}
            className="text-gray-500 hover:text-gray-700"
          >
            {showAI ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
          </button>
        </div>

        <AnimatePresence>
          {showAI && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-4"
            >
              <div className="flex space-x-3">
                <button
                  onClick={form.generateAISuggestions}
                  disabled={form.ai.isGenerating}
                  className="flex-1 bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {form.ai.isGenerating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="h-4 w-4" />
                      <span>Generate AI Content</span>
                    </>
                  )}
                </button>

                <button
                  onClick={form.generateMarketInsights}
                  disabled={form.ai.isGenerating}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  <LightBulbIcon className="h-4 w-4" />
                  <span>Market Insights</span>
                </button>
              </div>

              {form.ai.suggestions && (
                <div className="bg-white border border-purple-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3">AI Suggestions</h4>
                  <div className="space-y-3">
                    {Object.entries(form.ai.suggestions).map(([key, value]) => (
                      <div key={key} className="flex items-start space-x-3">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-700 capitalize">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </p>
                          <p className="text-sm text-gray-600">{value}</p>
                        </div>
                        <button
                          onClick={() => form.applyAISuggestion({ [key]: value })}
                          className="text-purple-600 hover:text-purple-700 text-sm font-medium"
                        >
                          Apply
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {form.ai.error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-600">{form.ai.error}</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    )
  }

  // Render market insights
  const renderMarketInsights = () => {
    if (!config.features?.marketInsights || !form.marketInsights) return null

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <LightBulbIcon className="h-6 w-6 text-green-600" />
            <h3 className="text-lg font-semibold text-gray-900">Market Insights</h3>
          </div>
          <button
            onClick={() => setShowMarketInsights(!showMarketInsights)}
            className="text-gray-500 hover:text-gray-700"
          >
            {showMarketInsights ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
          </button>
        </div>

        <AnimatePresence>
          {showMarketInsights && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-4"
            >
              <div className="bg-white border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Average Price</h4>
                <p className="text-2xl font-bold text-green-600">
                  ₹{form.marketInsights.averagePrice.toLocaleString()}
                </p>
              </div>
              <div className="bg-white border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Market Trend</h4>
                <p className={`text-lg font-semibold ${
                  form.marketInsights.marketTrend === 'rising' ? 'text-green-600' :
                  form.marketInsights.marketTrend === 'stable' ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {form.marketInsights.marketTrend.charAt(0).toUpperCase() + form.marketInsights.marketTrend.slice(1)}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    )
  }

  // Render progress indicator for wizard
  const renderProgressIndicator = () => {
    if (variant !== 'wizard') return null

    return (
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {WIZARD_STEPS.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                index <= currentStep
                  ? 'bg-blue-600 border-blue-600 text-white'
                  : 'border-gray-300 text-gray-500'
              }`}>
                {index < currentStep ? (
                  <CheckCircleIcon className="h-6 w-6" />
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </div>
              <div className="ml-3">
                <p className={`text-sm font-medium ${
                  index <= currentStep ? 'text-blue-600' : 'text-gray-500'
                }`}>
                  {step.title}
                </p>
                <p className="text-xs text-gray-500">{step.description}</p>
              </div>
              {index < WIZARD_STEPS.length - 1 && (
                <div className={`w-16 h-0.5 mx-4 ${
                  index < currentStep ? 'bg-blue-600' : 'bg-gray-300'
                }`} />
              )}
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
          />
        </div>
      </div>
    )
  }

  // Render form sections
  const renderSections = () => {
    if (variant === 'wizard') {
      // Render current step for wizard
      const currentStepData = WIZARD_STEPS[currentStep]
      if (!currentStepData) return null

      return (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900">{currentStepData.title}</h2>
            <p className="text-gray-600 mt-2">{currentStepData.description}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {currentStepData.fields.map(field => renderField(field, {}))}
          </div>

          {currentStepData.id === 'description' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Property Images</h3>
              <PropertyImageUpload
                propertyId={userId}
                onImagesUploaded={(images) => {
                  trackEvent('images_uploaded', { count: images.length })
                }}
              />
            </div>
          )}
        </div>
      )
    }

    // Render all sections for simple and ai-first variants
    return (
      <div className="space-y-8">
        {currentSections.map((section) => (
          <motion.div
            key={section.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white border border-gray-200 rounded-lg p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  {section.icon === 'home' && <HomeIcon className="h-6 w-6 text-blue-600" />}
                  {section.icon === 'map' && <MapPinIcon className="h-6 w-6 text-blue-600" />}
                  {section.icon === 'currency' && <CurrencyDollarIcon className="h-6 w-6 text-blue-600" />}
                  {section.icon === 'document' && <DocumentTextIcon className="h-6 w-6 text-blue-600" />}
                  {section.icon === 'sparkles' && <SparklesIcon className="h-6 w-6 text-blue-600" />}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
                  <p className="text-sm text-gray-600">{section.description}</p>
                </div>
              </div>
              {variant === 'simple' && (
                <button
                  onClick={() => toggleSection(section.id)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  {collapsedSections.has(section.id) ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              )}
            </div>

            <AnimatePresence>
              {!collapsedSections.has(section.id) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="grid grid-cols-1 md:grid-cols-2 gap-6"
                >
                  {section.fields.map(field => renderField(field, {}))}
                </motion.div>
              )}
            </AnimatePresence>

            {section.id === 'description' && !collapsedSections.has(section.id) && (
              <div className="mt-6 space-y-4">
                <h4 className="text-md font-semibold text-gray-900">Property Images</h4>
                <PropertyImageUpload
                  propertyId={userId}
                  onImagesUploaded={(images) => {
                    trackEvent('images_uploaded', { count: images.length })
                  }}
                />
              </div>
            )}
          </motion.div>
        ))}
      </div>
    )
  }

  return (
    <div className={`max-w-4xl mx-auto p-6 ${className}`}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {variant === 'simple' && 'Create Property Listing'}
          {variant === 'wizard' && 'Property Listing Wizard'}
          {variant === 'ai-first' && 'AI-Powered Property Listing'}
        </h1>
        <p className="text-gray-600">
          {variant === 'simple' && 'Fill in the details to create your property listing'}
          {variant === 'wizard' && 'Follow the steps to create a comprehensive property listing'}
          {variant === 'ai-first' && 'Let AI help you create an amazing property listing'}
        </p>
      </div>

      {renderProgressIndicator()}

      <div className="space-y-8">
        {renderAIAssistant()}
        {renderMarketInsights()}
        {renderSections()}
      </div>

      {/* Form Actions */}
      <div className="mt-8 flex items-center justify-between">
        <div className="flex space-x-4">
          {variant === 'wizard' && currentStep > 0 && (
            <button
              onClick={form.prevStep}
              className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              <ArrowLeftIcon className="h-4 w-4" />
              <span>Previous</span>
            </button>
          )}
        </div>

        <div className="flex space-x-4">
          {variant === 'wizard' && currentStep < totalSteps - 1 ? (
            <button
              onClick={form.nextStep}
              className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <span>Next</span>
              <ArrowRightIcon className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={form.submit}
              disabled={form.state.isSubmitting || !form.validation.isValid}
              className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {form.state.isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Creating...</span>
                </>
              ) : (
                <>
                  <CheckCircleIcon className="h-4 w-4" />
                  <span>Create Property</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Form Status */}
      {form.state.errors && Object.keys(form.state.errors).length > 0 && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
            <h4 className="text-sm font-medium text-red-800">Please fix the following errors:</h4>
          </div>
          <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
            {Object.entries(form.state.errors).map(([field, error]) => (
              <li key={field}>{error?.message}</li>
            ))}
          </ul>
        </div>
      )}

      {/* User Feedback Modal */}
      <UserFeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        variant={variant}
        sessionId={sessionId || 'unknown'}
        completed={true}
        abandonmentPoint={abandonmentPoint}
      />
    </div>
  )
}