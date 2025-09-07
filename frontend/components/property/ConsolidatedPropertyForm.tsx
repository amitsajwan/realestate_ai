'use client'

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PlusIcon,
  SparklesIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  PhotoIcon,
  CurrencyDollarIcon,
  HomeIcon,
  MapPinIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  LightBulbIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { usePropertyFormShared, PropertyFormOptions } from '@/hooks/usePropertyFormShared'
import { getFieldError, getFieldErrorClass } from '@/lib/validation'
import toast from 'react-hot-toast'

interface ConsolidatedPropertyFormProps extends PropertyFormOptions {
  className?: string
}

const FORM_STEPS = [
  { id: 'address', title: 'Location', icon: MapPinIcon },
  { id: 'basic', title: 'Basic Info', icon: HomeIcon },
  { id: 'pricing', title: 'Pricing', icon: CurrencyDollarIcon },
  { id: 'description', title: 'Description', icon: DocumentTextIcon }
]

export default function ConsolidatedPropertyForm({
  onSuccess,
  variant = 'basic',
  enableAI = true,
  enableMultiStep = false,
  className = ''
}: ConsolidatedPropertyFormProps) {
  const {
    form: { register, formState: { errors }, watch },
    isLoading,
    isAILoading,
    currentStep,
    aiSuggestions,
    marketInsights,
    handleSubmit,
    generateAISuggestions,
    applyAISuggestions,
    nextStep,
    prevStep
  } = usePropertyFormShared({ onSuccess, variant, enableAI, enableMultiStep })

  const renderBasicForm = () => (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information Card */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700 card-hover">
        <div className="p-6 sm:p-8">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
              <HomeIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Property title, price, and location</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                Property Title *
              </label>
              <input
                type="text"
                {...register('title')}
                className={`w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${getFieldErrorClass(errors, 'title')}`}
                placeholder="e.g., Luxury 3BHK Apartment in Downtown"
              />
              {errors.title && (
                <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                  <InformationCircleIcon className="w-4 h-4" />
                  <span>{errors.title.message}</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                Price *
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <CurrencyDollarIcon className="w-5 h-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  {...register('price')}
                  className={`w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${getFieldErrorClass(errors, 'price')}`}
                  placeholder="₹50,00,000"
                />
              </div>
              {getFieldError(errors, 'price') && (
                <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                  <InformationCircleIcon className="w-4 h-4" />
                  <span>{getFieldError(errors, 'price')}</span>
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 space-y-2">
            <label className="block text-sm font-semibold text-gray-900 dark:text-white">
              Address *
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MapPinIcon className="w-5 h-5 text-gray-400" />
              </div>
              <input
                type="text"
                {...register('address')}
                className={`w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${getFieldErrorClass(errors, 'address')}`}
                placeholder="123 Main Street, Downtown, City - 400001"
              />
            </div>
            {getFieldError(errors, 'address') && (
              <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                <InformationCircleIcon className="w-4 h-4" />
                <span>{getFieldError(errors, 'address')}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Property Details Card */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700 card-hover">
        <div className="p-6 sm:p-8">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Property Details</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Bedrooms, bathrooms, and area specifications</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                Property Type
              </label>
              <select
                {...register('propertyType')}
                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 border-gray-200 dark:border-slate-600"
              >
                <option value="Apartment">Apartment</option>
                <option value="House">House</option>
                <option value="Villa">Villa</option>
                <option value="Studio">Studio</option>
                <option value="Penthouse">Penthouse</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                Bedrooms
              </label>
              <select 
                {...register('bedrooms', { valueAsNumber: true })} 
                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 border-gray-200 dark:border-slate-600"
              >
                <option value="1">1 Bedroom</option>
                <option value="2">2 Bedrooms</option>
                <option value="3">3 Bedrooms</option>
                <option value="4">4+ Bedrooms</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                Bathrooms
              </label>
              <select 
                {...register('bathrooms', { valueAsNumber: true })} 
                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 border-gray-200 dark:border-slate-600"
              >
                <option value="1">1 Bathroom</option>
                <option value="2">2 Bathrooms</option>
                <option value="3">3 Bathrooms</option>
                <option value="4">4+ Bathrooms</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                Area (sq ft)
              </label>
              <input
                type="number"
                {...register('area', { valueAsNumber: true })}
                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 border-gray-200 dark:border-slate-600"
                placeholder="e.g., 1200"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Description & Amenities Card */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700 card-hover">
        <div className="p-6 sm:p-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                <InformationCircleIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Description & Amenities</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Detailed property information</p>
              </div>
            </div>
            {enableAI && (
              <button
                type="button"
                onClick={generateAISuggestions}
                disabled={isAILoading}
                className="hidden sm:flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-4 py-2 rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
              >
                {isAILoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-5 h-5" />
                    <span>AI Suggest</span>
                  </>
                )}
              </button>
            )}
          </div>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                Property Description *
              </label>
              <textarea
                {...register('description')}
                rows={5}
                className={`w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 resize-none ${getFieldErrorClass(errors, 'description')}`}
                placeholder="Describe the property in detail..."
              />
              {getFieldError(errors, 'description') && (
                <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                  <InformationCircleIcon className="w-4 h-4" />
                  <span>{getFieldError(errors, 'description')}</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                Amenities & Features
              </label>
              <input
                type="text"
                {...register('amenities')}
                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 border-gray-200 dark:border-slate-600"
                placeholder="e.g., Swimming Pool, Gym, Parking, Security"
              />
            </div>
          </div>

          {/* AI Suggestions Display */}
          <AnimatePresence>
            {aiSuggestions && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-6 bg-purple-50 dark:bg-purple-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <SparklesIcon className="w-5 h-5 text-purple-600" />
                    <span className="font-semibold text-purple-900 dark:text-purple-100">AI Suggestions</span>
                  </div>
                  <button
                    type="button"
                    onClick={applyAISuggestions}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded-lg text-sm font-medium transition-colors"
                  >
                    Apply All
                  </button>
                </div>
                <div className="space-y-3 text-sm text-purple-800 dark:text-purple-200">
                  <div>
                    <span className="font-medium">Title:</span> {aiSuggestions.title}
                  </div>
                  <div>
                    <span className="font-medium">Description:</span> {aiSuggestions.description}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700 p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-4 px-6 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Creating Property...</span>
              </>
            ) : (
              <>
                <PlusIcon className="w-5 h-5" />
                <span>Create Property Listing</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => onSuccess?.()}
            className="bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 py-4 px-6 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            <span>Back to Dashboard</span>
          </button>
        </div>
      </div>
    </form>
  )

  const renderMultiStepForm = () => {
    const renderStepContent = () => {
      const watchedData = watch()
      
      switch (currentStep) {
        case 0:
          return (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <div className="text-center mb-8">
                <MapPinIcon className="w-16 h-16 text-blue-500 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  Where is your property located?
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Start by entering the property address
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Property Address *
                  </label>
                  <input
                    {...register('address')}
                    type="text"
                    placeholder="e.g., 123 Marine Drive, Mumbai"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                  />
                  {errors.address && (
                    <p className="text-red-500 text-sm mt-1">{errors.address.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Area/Locality *
                  </label>
                  <input
                    {...register('location')}
                    type="text"
                    placeholder="e.g., Bandra West, Mumbai"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                  />
                  {errors.location && (
                    <p className="text-red-500 text-sm mt-1">{errors.location.message}</p>
                  )}
                </div>
              </div>
            </motion.div>
          )

        case 1:
          return (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <div className="text-center mb-8">
                <HomeIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  Tell us about your property
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Basic property details
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Property Type *
                  </label>
                  <select
                    {...register('propertyType')}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                  >
                    <option value="Apartment">Apartment</option>
                    <option value="House">House</option>
                    <option value="Villa">Villa</option>
                    <option value="Studio">Studio</option>
                    <option value="Penthouse">Penthouse</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Area (sq ft) *
                  </label>
                  <input
                    {...register('area', { valueAsNumber: true })}
                    type="number"
                    placeholder="e.g., 1200"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                  />
                  {errors.area && (
                    <p className="text-red-500 text-sm mt-1">{errors.area.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Bedrooms *
                  </label>
                  <select
                    {...register('bedrooms', { valueAsNumber: true })}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                  >
                    {[1, 2, 3, 4, 5].map(num => (
                      <option key={num} value={num}>{num} BHK</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Bathrooms *
                  </label>
                  <select
                    {...register('bathrooms', { valueAsNumber: true })}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                  >
                    {[1, 2, 3, 4, 5].map(num => (
                      <option key={num} value={num}>{num}</option>
                    ))}
                  </select>
                </div>
              </div>

              {marketInsights && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4 border border-green-200 dark:border-green-800"
                >
                  <div className="flex items-center space-x-2 mb-3">
                    <LightBulbIcon className="w-5 h-5 text-green-600" />
                    <span className="font-semibold text-green-900 dark:text-green-100">Market Insights</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-green-800 dark:text-green-200">
                        <span className="font-medium">Average Price:</span> ₹{(marketInsights.averagePrice / 100000).toFixed(1)}L
                      </p>
                    </div>
                    <div>
                      <p className="text-green-800 dark:text-green-200">
                        <span className="font-medium">Market Trend:</span> {marketInsights.marketTrend}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          )

        case 2:
          return (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <div className="text-center mb-8">
                <CurrencyDollarIcon className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  Set your price
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Based on market analysis
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Property Price *
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">₹</span>
                    <input
                      {...register('price')}
                      type="text"
                      placeholder="e.g., 3,20,00,000"
                      className="w-full pl-8 pr-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  {errors.price && (
                    <p className="text-red-500 text-sm mt-1">{errors.price.message}</p>
                  )}
                </div>
              </div>
            </motion.div>
          )

        case 3:
          return (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <div className="text-center mb-8">
                <DocumentTextIcon className="w-16 h-16 text-purple-500 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  Create compelling content
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Let AI help you create professional descriptions
                </p>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Property Title *
                  </label>
                  <input
                    {...register('title')}
                    type="text"
                    placeholder="e.g., Beautiful 3BHK Apartment in Bandra West"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                  />
                  {errors.title && (
                    <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Property Description *
                  </label>
                  <textarea
                    {...register('description')}
                    rows={6}
                    placeholder="Describe your property's key features..."
                    className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white resize-none"
                  />
                  {errors.description && (
                    <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
                  )}
                </div>

                {enableAI && (
                  <div className="flex space-x-4">
                    <button
                      type="button"
                      onClick={generateAISuggestions}
                      disabled={isAILoading}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-3 px-6 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200"
                    >
                      {isAILoading ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          <span>Generating...</span>
                        </>
                      ) : (
                        <>
                          <SparklesIcon className="w-5 h-5" />
                          <span>Generate AI Content</span>
                        </>
                      )}
                    </button>

                    {aiSuggestions && (
                      <button
                        type="button"
                        onClick={applyAISuggestions}
                        className="bg-green-600 hover:bg-green-700 text-white py-3 px-6 rounded-xl font-semibold flex items-center space-x-2 transition-all duration-200"
                      >
                        <CheckCircleIcon className="w-5 h-5" />
                        <span>Apply</span>
                      </button>
                    )}
                  </div>
                )}
              </div>

              <AnimatePresence>
                {aiSuggestions && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-2">
                        <SparklesIcon className="w-5 h-5 text-purple-600" />
                        <span className="font-semibold text-purple-900 dark:text-purple-100">AI Generated Content</span>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-purple-900 dark:text-purple-100 mb-2">Suggested Title:</h4>
                        <p className="text-purple-800 dark:text-purple-200 bg-white dark:bg-slate-800 p-3 rounded-lg">
                          {aiSuggestions.title}
                        </p>
                      </div>
                      <div>
                        <h4 className="font-semibold text-purple-900 dark:text-purple-100 mb-2">Suggested Description:</h4>
                        <p className="text-purple-800 dark:text-purple-200 bg-white dark:bg-slate-800 p-3 rounded-lg whitespace-pre-line">
                          {aiSuggestions.description}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )

        default:
          return null
      }
    }

    return (
      <form onSubmit={handleSubmit}>
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-200 dark:border-slate-700">
          <div className="p-6 sm:p-8">
            {/* Progress Steps */}
            <div className="flex items-center space-x-4 mb-8">
              {FORM_STEPS.map((step, index) => {
                const Icon = step.icon
                const isActive = index === currentStep
                const isCompleted = index < currentStep
                
                return (
                  <div key={step.id} className="flex items-center">
                    <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 ${
                      isActive 
                        ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' 
                        : isCompleted 
                        ? 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400'
                        : 'text-gray-400 dark:text-gray-600'
                    }`}>
                      <Icon className="w-4 h-4" />
                      <span className="text-sm font-medium hidden sm:inline">{step.title}</span>
                      {isCompleted && <CheckCircleIcon className="w-4 h-4" />}
                    </div>
                    {index < FORM_STEPS.length - 1 && (
                      <ArrowRightIcon className="w-4 h-4 text-gray-300 dark:text-gray-600 mx-2" />
                    )}
                  </div>
                )
              })}
            </div>

            {renderStepContent()}
          </div>

          {/* Navigation */}
          <div className="border-t border-gray-200 dark:border-slate-700 p-6 sm:p-8">
            <div className="flex justify-between">
              <button
                type="button"
                onClick={prevStep}
                disabled={currentStep === 0}
                className="flex items-center space-x-2 px-6 py-3 border border-gray-300 dark:border-slate-600 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <ArrowLeftIcon className="w-5 h-5" />
                <span>Previous</span>
              </button>

              {currentStep === FORM_STEPS.length - 1 ? (
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-3 rounded-xl font-semibold transition-all duration-200"
                >
                  {isLoading ? (
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
          </div>
        </div>
      </form>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`min-h-screen bg-gray-50 dark:bg-slate-900 p-4 sm:p-6 lg:p-8 ${className}`}
    >
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-200 dark:border-slate-700 mb-6 card-hover">
          <div className="p-6 sm:p-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <PlusIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                    {variant === 'smart' ? 'Smart Property' : variant === 'genai' ? 'AI Property Generator' : 'Add New Property'}
                  </h1>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    {enableMultiStep ? `Step ${currentStep + 1} of ${FORM_STEPS.length}` : 'Create a detailed property listing'}
                  </p>
                </div>
              </div>
              {enableAI && !enableMultiStep && (
                <div className="hidden sm:flex items-center space-x-2">
                  <SparklesIcon className="w-6 h-6 text-blue-500" />
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">AI-Powered</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Form Content */}
        {enableMultiStep ? renderMultiStepForm() : renderBasicForm()}
      </div>
    </motion.div>
  )
}