'use client'

import React from 'react'
import { motion } from 'framer-motion'
import {
  PlusIcon,
  HomeIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline'
import PropertyFieldInput from './shared/PropertyFieldInput'
import { AIAutoFillButton, AISuggestionsButton, AIInsightsButton } from './shared/AIAssistantButton'
import { usePropertyForm } from './hooks/usePropertyForm'

interface ConsolidatedPropertyFormProps {
  variant?: 'simple' | 'wizard' | 'ai-first'
  onSuccess?: (data?: any) => void
  enableAI?: boolean
  enableMarketInsights?: boolean
  enableQualityScoring?: boolean
  className?: string
}

const propertyTypeOptions = [
  { value: 'apartment', label: 'Apartment' },
  { value: 'house', label: 'House' },
  { value: 'villa', label: 'Villa' },
  { value: 'commercial', label: 'Commercial' }
]

const bedroomOptions = Array.from({ length: 5 }, (_, i) => ({
  value: (i + 1),
  label: `${i + 1} Bedroom${i > 0 ? 's' : ''}`
}))

const bathroomOptions = Array.from({ length: 5 }, (_, i) => ({
  value: (i + 1),
  label: `${i + 1} Bathroom${i > 0 ? 's' : ''}`
}))

export default function ConsolidatedPropertyForm({
  variant = 'simple',
  onSuccess,
  enableAI = true,
  enableMarketInsights = false,
  enableQualityScoring = false,
  className = ''
}: ConsolidatedPropertyFormProps) {
  const {
    register,
    formState: { errors },
    onSubmit,
    isLoading,
    isAILoading,
    aiSuggestions,
    marketInsights,
    generateAISuggestions,
    applyAISuggestions,
    autoFillWithAI
  } = usePropertyForm({
    onSuccess,
    enableAI,
    enableMarketInsights,
    enableQualityScoring,
    mode: 'onSubmit' // Changed from default 'onBlur' to 'onSubmit' to prevent premature validation
  })

  const getVariantTitle = () => {
    switch (variant) {
      case 'wizard': return 'Smart Property Form'
      case 'ai-first': return 'AI Property Generator'
      default: return 'Add New Property'
    }
  }

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
              {enableAI && (
                <div className="hidden sm:flex items-center gap-2">
                  {variant === 'ai-first' ? (
                    <AISuggestionsButton
                      onGenerate={generateAISuggestions}
                      isLoading={isAILoading}
                      size="md"
                    />
                  ) : (
                    <AIAutoFillButton
                      onGenerate={autoFillWithAI}
                      isLoading={isAILoading}
                      size="md"
                    />
                  )}
                  
                  {enableMarketInsights && (
                    <AIInsightsButton
                      onGenerate={generateAISuggestions}
                      isLoading={isAILoading}
                      size="sm"
                    />
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        <form onSubmit={onSubmit} className="space-y-6">
          {/* Basic Information Section */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700">
            <div className="p-6 sm:p-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <HomeIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Property title, type, and basic details</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PropertyFieldInput
                  name="title"
                  label="Property Title"
                  placeholder="Enter property title"
                  icon={HomeIcon}
                  register={register}
                  errors={errors}
                  required
                  helpText="Create an attractive title for your property"
                />
                
                <PropertyFieldInput
                  name="propertyType"
                  label="Property Type"
                  type="select"
                  icon={BuildingOfficeIcon}
                  options={propertyTypeOptions}
                  register={register}
                  errors={errors}
                  required
                />
                
                <PropertyFieldInput
                  name="bedrooms"
                  label="Bedrooms"
                  type="select"
                  options={bedroomOptions}
                  register={register}
                  errors={errors}
                  required
                />
                
                <PropertyFieldInput
                  name="bathrooms"
                  label="Bathrooms"
                  type="select"
                  options={bathroomOptions}
                  register={register}
                  errors={errors}
                  required
                />
              </div>
            </div>
          </div>

          {/* Location Section */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700">
            <div className="p-6 sm:p-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <MapPinIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Location Details</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Property location and address</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PropertyFieldInput
                  name="location"
                  label="Location"
                  placeholder="Enter city or area"
                  icon={MapPinIcon}
                  register={register}
                  errors={errors}
                  required
                  className="lg:col-span-1"
                />
                
                <PropertyFieldInput
                  name="area"
                  label="Area (sq ft)"
                  type="number"
                  placeholder="Enter area in square feet"
                  register={register}
                  errors={errors}
                  required
                />
                
                <PropertyFieldInput
                  name="address"
                  label="Full Address"
                  type="textarea"
                  placeholder="Enter complete address"
                  register={register}
                  errors={errors}
                  required
                  className="lg:col-span-2"
                />
              </div>
            </div>
          </div>

          {/* Pricing Section */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700">
            <div className="p-6 sm:p-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg flex items-center justify-center">
                  <CurrencyDollarIcon className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Pricing Information</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Set your property price</p>
                </div>
              </div>
              
              <PropertyFieldInput
                name="price"
                label="Price"
                placeholder="Enter price (e.g., ₹50,00,000)"
                icon={CurrencyDollarIcon}
                register={register}
                errors={errors}
                required
                helpText="Enter the total price of the property"
              />
              
              {/* Market Insights */}
              {enableMarketInsights && marketInsights && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800"
                >
                  <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">Market Insights</h4>
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
              )}
            </div>
          </div>

          {/* Description Section */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700">
            <div className="p-6 sm:p-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <DocumentTextIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Description & Amenities</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Detailed property information</p>
                </div>
              </div>
              
              <div className="space-y-6">
                <PropertyFieldInput
                  name="description"
                  label="Property Description"
                  type="textarea"
                  placeholder="Describe your property in detail..."
                  register={register}
                  errors={errors}
                  required
                  helpText="Provide a detailed description to attract potential buyers"
                />
                
                <PropertyFieldInput
                  name="amenities"
                  label="Amenities"
                  type="textarea"
                  placeholder="List amenities (comma-separated)"
                  register={register}
                  errors={errors}
                  helpText="e.g., Swimming pool, Gym, Parking, Security"
                />
              </div>
              
              {/* AI Suggestions Display */}
              {aiSuggestions && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl border border-purple-200 dark:border-purple-800"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-purple-900 dark:text-purple-100">AI Suggestions</h4>
                    <button
                      type="button"
                      onClick={applyAISuggestions}
                      className="text-xs bg-purple-600 text-white px-3 py-1 rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      Apply All
                    </button>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium text-purple-700 dark:text-purple-300">Title:</span>
                      <span className="ml-2 text-gray-700 dark:text-gray-300">{aiSuggestions.title}</span>
                    </div>
                    <div>
                      <span className="font-medium text-purple-700 dark:text-purple-300">Description:</span>
                      <span className="ml-2 text-gray-700 dark:text-gray-300">{aiSuggestions.description.substring(0, 100)}...</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <motion.button
              type="submit"
              disabled={isLoading}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center gap-2"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isLoading ? (
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
        </form>
      </div>
    </motion.div>
  )
}