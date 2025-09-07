/**
 * Unified Property Form Component
 * ===============================
 * 
 * This component consolidates all property form variants into a single,
 * maintainable component with feature flags and A/B testing support.
 */

'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PlusIcon,
  SparklesIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  HomeIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline'

import { useUnifiedPropertyForm } from '@/hooks/useUnifiedPropertyForm'
import { useFeatureFlags, useABTesting } from '@/utils/featureFlags'
import PropertyFieldInput from './shared/PropertyFieldInput'
import {
  UnifiedPropertyFormProps,
  FormVariant,
  FormConfig,
  AISuggestion,
  MarketInsight
} from '@/types/PropertyFormTypes'

/**
 * Form section configuration
 */
const FORM_SECTIONS = [
  {
    id: 'basic',
    title: 'Basic Information',
    description: 'Property title, type, and basic details',
    icon: HomeIcon,
    fields: ['title', 'propertyType', 'bedrooms', 'bathrooms']
  },
  {
    id: 'location',
    title: 'Location Details',
    description: 'Property location and address',
    icon: MapPinIcon,
    fields: ['location', 'address', 'area']
  },
  {
    id: 'pricing',
    title: 'Pricing Information',
    description: 'Property price and financial details',
    icon: CurrencyDollarIcon,
    fields: ['price']
  },
  {
    id: 'description',
    title: 'Description & Amenities',
    description: 'Detailed property information',
    icon: DocumentTextIcon,
    fields: ['description', 'amenities']
  }
]

/**
 * Property type options
 */
const PROPERTY_TYPE_OPTIONS = [
  { value: 'apartment', label: 'Apartment' },
  { value: 'house', label: 'House' },
  { value: 'villa', label: 'Villa' },
  { value: 'commercial', label: 'Commercial' }
]

/**
 * Bedroom options
 */
const BEDROOM_OPTIONS = Array.from({ length: 5 }, (_, i) => ({
  value: i + 1,
  label: `${i + 1} Bedroom${i > 0 ? 's' : ''}`
}))

/**
 * Bathroom options
 */
const BATHROOM_OPTIONS = Array.from({ length: 5 }, (_, i) => ({
  value: i + 1,
  label: `${i + 1} Bathroom${i > 0 ? 's' : ''}`
}))

/**
 * Unified Property Form Component
 */
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
  // Feature flags and A/B testing
  const featureFlags = useFeatureFlags()
  const { variant: abVariant, trackEvent } = useABTesting(userId)

  // Form configuration
  const formConfig: FormConfig = {
    variant,
    features: {
      ai: featureFlags.ENABLE_AI_FEATURES,
      marketInsights: featureFlags.ENABLE_MARKET_INSIGHTS,
      qualityScoring: featureFlags.ENABLE_QUALITY_SCORING,
      multilanguage: featureFlags.ENABLE_MULTILANGUAGE,
      autoSave: true,
      validation: 'onSubmit'
    },
    ui: {
      showProgress: variant === 'wizard',
      showSections: variant === 'simple',
      showAI: featureFlags.ENABLE_AI_FEATURES,
      showMarketInsights: featureFlags.ENABLE_MARKET_INSIGHTS
    },
    ...config
  }

  // Form hook
  const {
    data,
    setData,
    state,
    validation,
    submit,
    nextStep,
    prevStep,
    goToStep,
    ai,
    generateAISuggestions,
    applyAISuggestion,
    marketInsights,
    generateMarketInsights,
    register,
    setValue,
    getValue,
    watch,
    validate,
    trackEvent
  } = useUnifiedPropertyForm({
    variant,
    config: formConfig,
    onSuccess,
    onError
  })

  // Initialize form with initial data
  useEffect(() => {
    if (initialData) {
      setData(initialData)
    }
  }, [initialData, setData])

  // Track form interactions
  useEffect(() => {
    trackEvent('form_rendered', {
      variant: abVariant,
      formVariant: variant,
      features: formConfig.features
    })
  }, [variant, abVariant, formConfig.features, trackEvent])

  /**
   * Render form header
   */
  const renderHeader = () => (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-200 dark:border-slate-700 mb-6">
      <div className="p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <PlusIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                {getVariantTitle()}
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {getVariantDescription()}
              </p>
            </div>
          </div>
          
          {/* AI Actions */}
          {formConfig.ui.showAI && (
            <div className="hidden sm:flex items-center gap-2">
              <button
                type="button"
                onClick={generateAISuggestions}
                disabled={ai.isGenerating}
                className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-4 py-2 rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none hover-glow"
              >
                {ai.isGenerating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-5 h-5" />
                    <span>AI Auto-Fill</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
        
        {/* Progress Steps (for wizard variant) */}
        {formConfig.ui.showProgress && variant === 'wizard' && (
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            {FORM_SECTIONS.map((section, index) => {
              const isActive = index === state.currentStep
              const isCompleted = index < state.currentStep
              const Icon = section.icon
              
              return (
                <div key={section.id} className="flex items-center">
                  <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 ${
                    isActive 
                      ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' 
                      : isCompleted 
                      ? 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400'
                      : 'text-gray-400 dark:text-gray-600'
                  }`}>
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium hidden sm:inline">{section.title}</span>
                    {isCompleted && <CheckCircleIcon className="w-4 h-4" />}
                  </div>
                  {index < FORM_SECTIONS.length - 1 && (
                    <ArrowRightIcon className="w-4 h-4 text-gray-300 dark:text-gray-600 mx-2" />
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )

  /**
   * Render form section
   */
  const renderSection = (section: typeof FORM_SECTIONS[0], index: number) => {
    const isVisible = variant === 'simple' || 
                     (variant === 'wizard' && index === state.currentStep) ||
                     (variant === 'ai-first' && index === 0)

    if (!isVisible) return null

    return (
      <motion.div
        key={section.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700 mb-6"
      >
        <div className="p-6 sm:p-8">
          <div className="flex items-center space-x-3 mb-6">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              index === 0 ? 'bg-blue-100 dark:bg-blue-900/20' :
              index === 1 ? 'bg-green-100 dark:bg-green-900/20' :
              index === 2 ? 'bg-yellow-100 dark:bg-yellow-900/20' :
              'bg-purple-100 dark:bg-purple-900/20'
            }`}>
              <section.icon className={`w-5 h-5 ${
                index === 0 ? 'text-blue-600 dark:text-blue-400' :
                index === 1 ? 'text-green-600 dark:text-green-400' :
                index === 2 ? 'text-yellow-600 dark:text-yellow-400' :
                'text-purple-600 dark:text-purple-400'
              }`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {section.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {section.description}
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {section.fields.map((fieldName) => {
              switch (fieldName) {
                case 'title':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="title"
                      label="Property Title"
                      placeholder="Enter property title"
                      icon={HomeIcon}
                      register={register}
                      errors={validation.errors}
                      required
                      helpText="Create an attractive title for your property"
                    />
                  )
                
                case 'propertyType':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="propertyType"
                      label="Property Type"
                      type="select"
                      icon={BuildingOfficeIcon}
                      options={PROPERTY_TYPE_OPTIONS}
                      register={register}
                      errors={validation.errors}
                      required
                    />
                  )
                
                case 'bedrooms':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="bedrooms"
                      label="Bedrooms"
                      type="select"
                      options={BEDROOM_OPTIONS}
                      register={register}
                      errors={validation.errors}
                      required
                    />
                  )
                
                case 'bathrooms':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="bathrooms"
                      label="Bathrooms"
                      type="select"
                      options={BATHROOM_OPTIONS}
                      register={register}
                      errors={validation.errors}
                      required
                    />
                  )
                
                case 'location':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="location"
                      label="Location"
                      placeholder="Enter city or area"
                      icon={MapPinIcon}
                      register={register}
                      errors={validation.errors}
                      required
                    />
                  )
                
                case 'address':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="address"
                      label="Full Address"
                      type="textarea"
                      placeholder="Enter complete address"
                      register={register}
                      errors={validation.errors}
                      required
                      className="lg:col-span-2"
                    />
                  )
                
                case 'area':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="area"
                      label="Area (sq ft)"
                      type="number"
                      placeholder="Enter area in square feet"
                      register={register}
                      errors={validation.errors}
                      required
                    />
                  )
                
                case 'price':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="price"
                      label="Price"
                      placeholder="Enter price (e.g., ₹50,00,000)"
                      icon={CurrencyDollarIcon}
                      register={register}
                      errors={validation.errors}
                      required
                      helpText="Enter the total price of the property"
                    />
                  )
                
                case 'description':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="description"
                      label="Property Description"
                      type="textarea"
                      placeholder="Describe your property in detail..."
                      register={register}
                      errors={validation.errors}
                      required
                      helpText="Provide a detailed description to attract potential buyers"
                      className="lg:col-span-2"
                    />
                  )
                
                case 'amenities':
                  return (
                    <PropertyFieldInput
                      key={fieldName}
                      name="amenities"
                      label="Amenities"
                      type="textarea"
                      placeholder="List amenities (comma-separated)"
                      register={register}
                      errors={validation.errors}
                      helpText="e.g., Swimming pool, Gym, Parking, Security"
                      className="lg:col-span-2"
                    />
                  )
                
                default:
                  return null
              }
            })}
          </div>
        </div>
      </motion.div>
    )
  }

  /**
   * Render AI suggestions
   */
  const renderAISuggestions = () => {
    if (!ai.suggestions || !formConfig.ui.showAI) return null

    return (
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800 mb-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <SparklesIcon className="w-5 h-5 text-purple-600" />
              <span className="font-semibold text-purple-900 dark:text-purple-100">
                AI Suggestions
              </span>
            </div>
            <button
              type="button"
              onClick={() => applyAISuggestion(ai.suggestions!)}
              className="text-xs bg-purple-600 text-white px-3 py-1 rounded-lg hover:bg-purple-700 transition-colors"
            >
              Apply All
            </button>
          </div>
          
          <div className="space-y-4">
            {ai.suggestions.title && (
              <div>
                <h4 className="font-semibold text-purple-900 dark:text-purple-100 mb-2">
                  Suggested Title:
                </h4>
                <p className="text-purple-800 dark:text-purple-200 bg-white dark:bg-slate-800 p-3 rounded-lg">
                  {ai.suggestions.title}
                </p>
              </div>
            )}
            
            {ai.suggestions.description && (
              <div>
                <h4 className="font-semibold text-purple-900 dark:text-purple-100 mb-2">
                  Suggested Description:
                </h4>
                <p className="text-purple-800 dark:text-purple-200 bg-white dark:bg-slate-800 p-3 rounded-lg whitespace-pre-line">
                  {ai.suggestions.description}
                </p>
              </div>
            )}
            
            {ai.suggestions.qualityScore && (
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="text-center">
                  <div className="font-semibold text-purple-900 dark:text-purple-100">SEO Score</div>
                  <div className="text-purple-700 dark:text-purple-300">{ai.suggestions.qualityScore.seo}/100</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-purple-900 dark:text-purple-100">Readability</div>
                  <div className="text-purple-700 dark:text-purple-300">{ai.suggestions.qualityScore.readability}/100</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-purple-900 dark:text-purple-100">Market Relevance</div>
                  <div className="text-purple-700 dark:text-purple-300">{ai.suggestions.qualityScore.marketRelevance}/100</div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    )
  }

  /**
   * Render market insights
   */
  const renderMarketInsights = () => {
    if (!marketInsights || !formConfig.ui.showMarketInsights) return null

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800 mb-6"
      >
        <div className="flex items-center space-x-2 mb-3">
          <InformationCircleIcon className="w-5 h-5 text-blue-600" />
          <span className="font-semibold text-blue-900 dark:text-blue-100">Market Insights</span>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-blue-700 dark:text-blue-300">Average Price:</span>
            <span className="ml-2 font-medium">₹{marketInsights.averagePrice.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-blue-700 dark:text-blue-300">Market Trend:</span>
            <span className={`ml-2 font-medium ${
              marketInsights.marketTrend === 'rising' ? 'text-green-600' :
              marketInsights.marketTrend === 'declining' ? 'text-red-600' : 'text-yellow-600'
            }`}>
              {marketInsights.marketTrend} ({marketInsights.trendPercentage}%)
            </span>
          </div>
        </div>
      </motion.div>
    )
  }

  /**
   * Render form navigation
   */
  const renderNavigation = () => {
    if (variant !== 'wizard') return null

    return (
      <div className="flex justify-between items-center">
        <button
          type="button"
          onClick={prevStep}
          disabled={state.currentStep === 0}
          className="flex items-center space-x-2 px-6 py-3 border border-gray-300 dark:border-slate-600 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          <span>Previous</span>
        </button>

        {state.currentStep === state.totalSteps - 1 ? (
          <button
            type="button"
            onClick={submit}
            disabled={state.isSubmitting}
            className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-3 rounded-xl font-semibold transition-all duration-200"
          >
            {state.isSubmitting ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Creating...</span>
              </>
            ) : (
              <>
                <CheckCircleIcon className="w-5 h-5" />
                <span>Create Property</span>
              </>
            )}
          </button>
        ) : (
          <button
            type="button"
            onClick={nextStep}
            className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200"
          >
            <span>Next</span>
            <ArrowRightIcon className="w-5 h-5" />
          </button>
        )}
      </div>
    )
  }

  /**
   * Get variant title
   */
  const getVariantTitle = () => {
    switch (variant) {
      case 'wizard': return 'Smart Property Form'
      case 'ai-first': return 'AI Property Generator'
      default: return 'Add New Property'
    }
  }

  /**
   * Get variant description
   */
  const getVariantDescription = () => {
    switch (variant) {
      case 'wizard': return 'Step-by-step property listing with AI insights'
      case 'ai-first': return 'Create compelling property listings with AI'
      default: return 'Create a detailed property listing'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`min-h-screen bg-gray-50 dark:bg-slate-900 p-4 sm:p-6 lg:p-8 ${className}`}
    >
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        {renderHeader()}

        {/* Form */}
        <form onSubmit={submit} className="space-y-6">
          {/* Form Sections */}
          {FORM_SECTIONS.map((section, index) => renderSection(section, index))}

          {/* AI Suggestions */}
          {renderAISuggestions()}

          {/* Market Insights */}
          {renderMarketInsights()}

          {/* Navigation (for wizard) */}
          {variant === 'wizard' && (
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700 p-6">
              {renderNavigation()}
            </div>
          )}

          {/* Submit Button (for simple and ai-first variants) */}
          {variant !== 'wizard' && (
            <div className="flex justify-end">
              <motion.button
                type="submit"
                disabled={state.isSubmitting}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center gap-2"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {state.isSubmitting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Creating Property...</span>
                  </>
                ) : (
                  <>
                    <PlusIcon className="w-5 h-5" />
                    <span>Create Property</span>
                  </>
                )}
              </motion.button>
            </div>
          )}
        </form>
      </div>
    </motion.div>
  )
}