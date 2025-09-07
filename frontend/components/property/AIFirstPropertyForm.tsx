/**
 * AI-First Property Form
 * =====================
 * 
 * Single, intelligent property form that starts with AI analysis
 * and provides smart suggestions for quick property listing.
 */

'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MapPinIcon,
  SparklesIcon,
  CheckCircleIcon,
  PhotoIcon,
  RocketLaunchIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  HomeIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { useUnifiedPropertyForm } from '../../hooks/useUnifiedPropertyForm'
import { aiPropertyAnalysisService } from '../../services/aiPropertyAnalysis'

interface AIPropertyData {
  address: string
  propertyType: string
  suggestedPrice: {
    min: number
    max: number
    currency: string
  }
  marketTrend: {
    direction: 'rising' | 'stable' | 'declining'
    percentage: number
  }
  neighborhood: {
    walkScore: number
    amenities: string[]
    transportLinks: string[]
  }
  similarListings: Array<{
    price: number
    bedrooms: number
    area: number
    daysOnMarket: number
  }>
  aiSuggestions: {
    title: string
    description: string
    keyFeatures: string[]
    amenities: string[]
  }
}

type FormStep = 'address' | 'ai-analysis' | 'review' | 'publish'

export default function AIFirstPropertyForm() {
  const [currentStep, setCurrentStep] = useState<FormStep>('address')
  const [isLoading, setIsLoading] = useState(false)
  const [aiData, setAiData] = useState<AIPropertyData | null>(null)
  const [userEdits, setUserEdits] = useState<Partial<AIPropertyData>>({})
  
  const {
    data: formData,
    setData: updateFormData,
    submit: submitForm,
    state: { isSubmitting },
    validation: { errors }
  } = useUnifiedPropertyForm({
    variant: 'ai-first',
    autoSave: true,
    config: {
      features: {
        ai: true,
        marketInsights: true,
        qualityScoring: true,
        multilanguage: false,
        autoSave: true,
        validation: 'onSubmit'
      }
    }
  })

  // Handle address submission and AI analysis
  const handleAddressSubmit = async (address: string) => {
    setIsLoading(true)
    try {
      // Use real AI analysis service
      const analysisResult = await aiPropertyAnalysisService.analyzeProperty({
        address,
        propertyType: undefined,
        bedrooms: undefined,
        bathrooms: undefined,
        area: undefined,
        additionalContext: undefined
      })
      
      // Convert to our local format
      const aiData: AIPropertyData = {
        address: analysisResult.address,
        propertyType: analysisResult.propertyType,
        suggestedPrice: {
          min: analysisResult.marketInsight.priceRange.min,
          max: analysisResult.marketInsight.priceRange.max,
          currency: 'INR'
        },
        marketTrend: {
          direction: analysisResult.marketInsight.marketTrend.direction,
          percentage: analysisResult.marketInsight.marketTrend.percentage
        },
        neighborhood: {
          walkScore: analysisResult.neighborhoodInsight.walkScore,
          amenities: analysisResult.neighborhoodInsight.amenities.map(a => a.name),
          transportLinks: analysisResult.neighborhoodInsight.amenities
            .filter(a => a.type === 'transport')
            .map(a => a.name)
        },
        similarListings: analysisResult.similarListings.map(listing => ({
          price: listing.price,
          bedrooms: listing.bedrooms,
          area: listing.area,
          daysOnMarket: listing.daysOnMarket
        })),
        aiSuggestions: {
          title: analysisResult.aiContentSuggestion.title,
          description: analysisResult.aiContentSuggestion.description,
          keyFeatures: analysisResult.aiContentSuggestion.keyFeatures,
          amenities: analysisResult.aiContentSuggestion.amenities
        }
      }
      
      setAiData(aiData)
      setCurrentStep('ai-analysis')
      toast.success('AI analysis complete!')
    } catch (error) {
      toast.error('Failed to analyze property. Please try again.')
      console.error('AI analysis error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Accept AI suggestions
  const acceptAISuggestions = () => {
    if (aiData) {
      updateFormData({
        title: aiData.aiSuggestions.title,
        description: aiData.aiSuggestions.description,
        propertyType: aiData.propertyType,
        price: aiData.suggestedPrice.max.toString(),
        location: aiData.address,
        amenities: aiData.aiSuggestions.amenities.join(', ')
      })
      setCurrentStep('review')
    }
  }

  // Edit AI suggestions
  const editAISuggestions = () => {
    setCurrentStep('review')
  }

  // Publish property
  const handlePublish = async () => {
    try {
      await submitForm()
      toast.success('Property published successfully!')
      setCurrentStep('publish')
    } catch (error) {
      toast.error('Failed to publish property. Please try again.')
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[
            { id: 'address', label: 'Address', icon: MapPinIcon },
            { id: 'ai-analysis', label: 'AI Analysis', icon: SparklesIcon },
            { id: 'review', label: 'Review', icon: DocumentTextIcon },
            { id: 'publish', label: 'Publish', icon: RocketLaunchIcon }
          ].map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`
                flex items-center justify-center w-10 h-10 rounded-full border-2
                ${currentStep === step.id ? 'bg-blue-600 border-blue-600 text-white' : 
                  ['address', 'ai-analysis', 'review', 'publish'].indexOf(currentStep) > index ? 
                  'bg-green-600 border-green-600 text-white' : 
                  'bg-gray-200 border-gray-300 text-gray-500'}
              `}>
                <step.icon className="w-5 h-5" />
              </div>
              <span className={`ml-2 text-sm font-medium ${
                currentStep === step.id ? 'text-blue-600' : 
                ['address', 'ai-analysis', 'review', 'publish'].indexOf(currentStep) > index ? 
                'text-green-600' : 'text-gray-500'
              }`}>
                {step.label}
              </span>
              {index < 3 && (
                <div className={`w-16 h-0.5 mx-4 ${
                  ['address', 'ai-analysis', 'review', 'publish'].indexOf(currentStep) > index ? 
                  'bg-green-600' : 'bg-gray-300'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {/* Step 1: Address Input */}
        {currentStep === 'address' && (
          <motion.div
            key="address"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="text-center"
          >
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                🏠 Add New Property
              </h1>
              <p className="text-lg text-gray-600">
                Start by entering the property address. Our AI will analyze the market and provide smart suggestions.
              </p>
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-8 max-w-2xl mx-auto">
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📍 Property Address
                </label>
                <input
                  type="text"
                  placeholder="Enter full property address..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const address = (e.target as HTMLInputElement).value
                      if (address.trim()) {
                        handleAddressSubmit(address.trim())
                      }
                    }
                  }}
                />
              </div>

              <div className="bg-blue-50 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-blue-900 mb-2 flex items-center">
                  <SparklesIcon className="w-5 h-5 mr-2" />
                  AI will analyze:
                </h3>
                <ul className="text-blue-800 space-y-1">
                  <li>• Market value and pricing trends</li>
                  <li>• Property type and characteristics</li>
                  <li>• Neighborhood insights and amenities</li>
                  <li>• Similar listings and competition</li>
                </ul>
              </div>

              <button
                onClick={() => {
                  const input = document.querySelector('input[type="text"]') as HTMLInputElement
                  if (input?.value.trim()) {
                    handleAddressSubmit(input.value.trim())
                  }
                }}
                disabled={isLoading}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Analyzing Property...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-5 h-5 mr-2" />
                    Analyze with AI
                  </>
                )}
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 2: AI Analysis Results */}
        {currentStep === 'ai-analysis' && aiData && (
          <motion.div
            key="ai-analysis"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                ✨ AI Analysis Complete!
              </h1>
              <p className="text-lg text-gray-600">
                Here's what our AI found about your property:
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Market Analysis */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center">
                  <CurrencyDollarIcon className="w-6 h-6 mr-2 text-green-600" />
                  Market Analysis
                </h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-gray-600">Suggested Price Range:</span>
                    <p className="text-2xl font-bold text-green-600">
                      ₹{aiData.suggestedPrice.min.toLocaleString()} - ₹{aiData.suggestedPrice.max.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Market Trend:</span>
                    <p className={`font-semibold ${
                      aiData.marketTrend.direction === 'rising' ? 'text-green-600' :
                      aiData.marketTrend.direction === 'declining' ? 'text-red-600' : 'text-yellow-600'
                    }`}>
                      {aiData.marketTrend.direction === 'rising' ? '↗️' : 
                       aiData.marketTrend.direction === 'declining' ? '↘️' : '→'} 
                      {aiData.marketTrend.percentage}% {aiData.marketTrend.direction}
                    </p>
                  </div>
                </div>
              </div>

              {/* Property Details */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center">
                  <HomeIcon className="w-6 h-6 mr-2 text-blue-600" />
                  Property Details
                </h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-gray-600">Type:</span>
                    <p className="font-semibold">{aiData.propertyType}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Location:</span>
                    <p className="font-semibold">{aiData.address}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Walk Score:</span>
                    <p className="font-semibold">{aiData.neighborhood.walkScore}/100</p>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Suggestions */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
              <h3 className="text-xl font-semibold mb-4 flex items-center">
                <SparklesIcon className="w-6 h-6 mr-2 text-purple-600" />
                AI-Generated Content
              </h3>
              <div className="space-y-4">
                <div>
                  <span className="text-sm text-gray-600">Suggested Title:</span>
                  <p className="font-semibold text-lg">{aiData.aiSuggestions.title}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Description:</span>
                  <p className="text-gray-800">{aiData.aiSuggestions.description}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Key Features:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {aiData.aiSuggestions.keyFeatures.map((feature, index) => (
                      <span key={index} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 justify-center">
              <button
                onClick={acceptAISuggestions}
                className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 flex items-center"
              >
                <CheckCircleIcon className="w-5 h-5 mr-2" />
                Use AI Suggestions
              </button>
              <button
                onClick={editAISuggestions}
                className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 flex items-center"
              >
                <DocumentTextIcon className="w-5 h-5 mr-2" />
                Edit Details
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Review & Edit */}
        {currentStep === 'review' && (
          <motion.div
            key="review"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                📋 Review & Finalize
              </h1>
              <p className="text-lg text-gray-600">
                Review the property details and make any final adjustments before publishing.
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Basic Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                      <input
                        type="text"
                        value={formData.title || ''}
                        onChange={(e) => updateFormData({ title: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Property Type</label>
                      <select
                        value={formData.propertyType || ''}
                        onChange={(e) => updateFormData({ propertyType: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select type</option>
                        <option value="apartment">Apartment</option>
                        <option value="house">House</option>
                        <option value="villa">Villa</option>
                        <option value="commercial">Commercial</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Price (₹)</label>
                      <input
                        type="text"
                        value={formData.price || ''}
                        onChange={(e) => updateFormData({ price: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Additional Details */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Additional Details</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Bedrooms</label>
                      <input
                        type="number"
                        value={formData.bedrooms || ''}
                        onChange={(e) => updateFormData({ bedrooms: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Bathrooms</label>
                      <input
                        type="number"
                        value={formData.bathrooms || ''}
                        onChange={(e) => updateFormData({ bathrooms: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Area (sq ft)</label>
                      <input
                        type="number"
                        value={formData.area || ''}
                        onChange={(e) => updateFormData({ area: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description || ''}
                  onChange={(e) => updateFormData({ description: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">Amenities</label>
                <input
                  type="text"
                  value={formData.amenities || ''}
                  onChange={(e) => updateFormData({ amenities: e.target.value })}
                  placeholder="Swimming Pool, Gym, Parking..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Image Upload */}
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Property Images</label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <PhotoIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600">Click to upload or drag and drop</p>
                  <p className="text-sm text-gray-500">PNG, JPG up to 10MB each</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 justify-center mt-8">
                <button
                  onClick={() => setCurrentStep('ai-analysis')}
                  className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700 flex items-center"
                >
                  <ArrowLeftIcon className="w-5 h-5 mr-2" />
                  Back to Analysis
                </button>
                <button
                  onClick={handlePublish}
                  disabled={isSubmitting}
                  className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 flex items-center"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Publishing...
                    </>
                  ) : (
                    <>
                      <RocketLaunchIcon className="w-5 h-5 mr-2" />
                      Publish Property
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Step 4: Success */}
        {currentStep === 'publish' && (
          <motion.div
            key="publish"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <div className="mb-8">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircleIcon className="w-12 h-12 text-green-600" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                🎉 Property Published Successfully!
              </h1>
              <p className="text-lg text-gray-600">
                Your property is now live and visible to potential buyers.
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 max-w-2xl mx-auto">
              <h3 className="text-xl font-semibold mb-4">What's Next?</h3>
              <div className="space-y-3 text-left">
                <div className="flex items-center">
                  <CheckCircleIcon className="w-5 h-5 text-green-600 mr-3" />
                  <span>Property is live on the platform</span>
                </div>
                <div className="flex items-center">
                  <CheckCircleIcon className="w-5 h-5 text-green-600 mr-3" />
                  <span>SEO-optimized for better visibility</span>
                </div>
                <div className="flex items-center">
                  <CheckCircleIcon className="w-5 h-5 text-green-600 mr-3" />
                  <span>Market insights and analytics enabled</span>
                </div>
                <div className="flex items-center">
                  <CheckCircleIcon className="w-5 h-5 text-green-600 mr-3" />
                  <span>Lead notifications will be sent to you</span>
                </div>
              </div>

              <div className="flex gap-4 justify-center mt-8">
                <button
                  onClick={() => {
                    setCurrentStep('address')
                    setAiData(null)
                    setUserEdits({})
                  }}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700"
                >
                  Add Another Property
                </button>
                <button
                  onClick={() => window.location.href = '/properties'}
                  className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700"
                >
                  View All Properties
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
