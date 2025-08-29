'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { 
  PlusIcon, 
  SparklesIcon, 
  ArrowLeftIcon,
  PhotoIcon,
  CurrencyDollarIcon,
  HomeIcon,
  MapPinIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { propertySchema, PropertyFormData, getFieldError, getFieldErrorClass } from '@/lib/validation'
import { apiService, APIError } from '@/lib/api'

interface PropertyFormProps {
  onSuccess?: () => void
}

export default function PropertyForm({ onSuccess }: PropertyFormProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [isAILoading, setIsAILoading] = useState(false)
  
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors }
  } = useForm<PropertyFormData>({
    resolver: zodResolver(propertySchema),
    mode: 'onBlur'
  })

  const onSubmit = async (data: PropertyFormData) => {
    setIsLoading(true)
    try {
      // Transform form data to match backend Property interface
      const propertyData = {
        user_id: '1', // TODO: Get from auth context
        title: data.title,
        type: 'Apartment', // Default type
        bedrooms: data.bedrooms,
        price: parseFloat(data.price.replace(/[₹,]/g, '')),
        price_unit: 'INR',
        city: 'Mumbai', // Default city
        area: data.area,
        address: data.address,
        description: data.description,
        amenities: data.amenities ? data.amenities.split(',').map(a => a.trim()) : []
      }

      const response = await apiService.createProperty(propertyData)
      
      // If we get here without an error, the property was created successfully
      toast.success('Property added successfully!')
      onSuccess?.()
    } catch (error) {
      console.error('Property creation error:', error)
      if (error instanceof APIError) {
        toast.error(`Failed to add property: ${error.message}`)
      } else {
        toast.error('Failed to add property. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const autoFillWithAI = async () => {
    setIsAILoading(true)
    try {
      const response = await apiService.getAIPropertySuggestions({
        property_type: 'Apartment',
        location: 'City Center',
        budget: '₹75,00,000',
        requirements: 'Modern amenities'
      })

      if (response.success && response.data && response.data.length > 0) {
        const suggestion = response.data[0]
        setValue('title', suggestion.title)
        setValue('price', suggestion.price)
        setValue('address', '123 Main Street, City Center')
        setValue('description', suggestion.description)
        setValue('amenities', suggestion.amenities)
        toast.success('Property form auto-filled with AI content!')
      } else {
        throw new Error('No suggestions received')
      }
    } catch (error) {
      console.error('AI Suggest error:', error)
      if (error instanceof APIError) {
        toast.error(`Failed to generate AI content: ${error.message}`)
      } else {
        toast.error('Failed to generate AI content. Please try again.')
      }
    } finally {
      setIsAILoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="min-h-screen bg-gray-50 dark:bg-slate-900 p-4 sm:p-6 lg:p-8"
    >
      <div className="max-w-4xl mx-auto animate-fade-in">
        {/* Header */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-200 dark:border-slate-700 mb-6 card-hover">
          <div className="p-6 sm:p-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <PlusIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">Add New Property</h1>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">Create a detailed property listing</p>
                </div>
              </div>
              <button
                  type="button"
                  onClick={autoFillWithAI}
                  disabled={isAILoading}
                  className="hidden sm:flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-4 py-2 rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] hover-glow click-shrink"
                >
                {isAILoading ? (
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
            
            {/* Progress Steps */}
            <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                <span>Basic Info</span>
              </div>
              <div className="w-4 h-px bg-gray-300 dark:bg-slate-600"></div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-300 dark:bg-slate-600 rounded-full"></div>
                <span>Details</span>
              </div>
              <div className="w-4 h-px bg-gray-300 dark:bg-slate-600"></div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-300 dark:bg-slate-600 rounded-full"></div>
                <span>Description</span>
              </div>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
                  <div className="relative">
                    <input
                      type="text"
                      {...register('title', { required: 'Title is required' })}
                      className={`w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${
                        errors.title ? 'border-red-300 dark:border-red-600' : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500'
                      }`}
                      placeholder="e.g., Luxury 3BHK Apartment in Downtown"
                    />
                  </div>
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
                      className={`w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${
                        getFieldError(errors, 'price') ? 'border-red-300 dark:border-red-600' : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500'
                      }`}
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
                    className={`w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${
                      getFieldError(errors, 'address') ? 'border-red-300 dark:border-red-600' : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500'
                    }`}
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
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                    Bedrooms
                  </label>
                  <select 
                    {...register('bedrooms')} 
                    className={`w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${
                      getFieldError(errors, 'bedrooms') ? 'border-red-300 dark:border-red-600' : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500'
                    }`}
                  >
                    <option value="" className="text-gray-500">Select bedrooms</option>
                    <option value="1">1 Bedroom</option>
                    <option value="2">2 Bedrooms</option>
                    <option value="3">3 Bedrooms</option>
                    <option value="4">4+ Bedrooms</option>
                  </select>
                  {getFieldError(errors, 'bedrooms') && (
                    <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                      <InformationCircleIcon className="w-4 h-4" />
                      <span>{getFieldError(errors, 'bedrooms')}</span>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                    Bathrooms
                  </label>
                  <select 
                    {...register('bathrooms')} 
                    className={`w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${
                      getFieldError(errors, 'bathrooms') ? 'border-red-300 dark:border-red-600' : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500'
                    }`}
                  >
                    <option value="" className="text-gray-500">Select bathrooms</option>
                    <option value="1">1 Bathroom</option>
                    <option value="2">2 Bathrooms</option>
                    <option value="3">3 Bathrooms</option>
                    <option value="4">4+ Bathrooms</option>
                  </select>
                  {getFieldError(errors, 'bathrooms') && (
                    <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                      <InformationCircleIcon className="w-4 h-4" />
                      <span>{getFieldError(errors, 'bathrooms')}</span>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                    Area (sq ft)
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      {...register('area')}
                      className={`w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${
                        getFieldError(errors, 'area') ? 'border-red-300 dark:border-red-600' : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500'
                      }`}
                      placeholder="e.g., 1200"
                      min="1"
                    />
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <span className="text-gray-400 text-sm">sq ft</span>
                    </div>
                  </div>
                  {getFieldError(errors, 'area') && (
                    <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                      <InformationCircleIcon className="w-4 h-4" />
                      <span>{getFieldError(errors, 'area')}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Description & Amenities Card */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700 card-hover">
            <div className="p-6 sm:p-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <InformationCircleIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Description & Amenities</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Detailed property information and features</p>
                </div>
              </div>
              
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                    Property Description *
                  </label>
                  <div className="relative">
                    <textarea
                      {...register('description')}
                      rows={5}
                      className={`w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 resize-none ${
                        getFieldError(errors, 'description') ? 'border-red-300 dark:border-red-600' : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500'
                      }`}
                      placeholder="Describe the property in detail... Include features like modern kitchen, spacious living areas, natural lighting, nearby amenities, transportation links, etc."
                    />
                    <div className="absolute bottom-3 right-3 text-xs text-gray-400 pointer-events-none">
                      Min 50 characters
                    </div>
                  </div>
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
                  <div className="relative">
                    <input
                      type="text"
                      {...register('amenities')}
                      className={`w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border-2 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${
                        getFieldError(errors, 'amenities') ? 'border-red-300 dark:border-red-600' : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500'
                      }`}
                      placeholder="e.g., Swimming Pool, Gym, Parking, Security, Garden, Balcony"
                    />
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <span className="text-xs text-gray-400">Comma separated</span>
                    </div>
                  </div>
                  {getFieldError(errors, 'amenities') && (
                    <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                      <InformationCircleIcon className="w-4 h-4" />
                      <span>{getFieldError(errors, 'amenities')}</span>
                    </div>
                  )}
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    💡 Tip: List key features that make your property stand out
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-200 dark:border-slate-700 card-hover">
            <div className="p-6 sm:p-8">
              <div className="flex flex-col sm:flex-row gap-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-4 px-6 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none disabled:hover:shadow-lg hover-lift click-shrink"
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
                  onClick={autoFillWithAI}
                  disabled={isAILoading}
                  className="sm:hidden bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-3 px-6 rounded-xl font-medium flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none hover-glow click-shrink"
                >
                  {isAILoading ? (
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

                <button
                  type="button"
                  onClick={onSuccess}
                  className="bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 py-4 px-6 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200 border border-gray-200 dark:border-slate-600 hover-lift click-shrink"
                >
                  <ArrowLeftIcon className="w-5 h-5" />
                  <span>Back to Dashboard</span>
                </button>
              </div>
              
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  💡 Use AI Auto-Fill to generate property details automatically
                </p>
              </div>
            </div>
          </div>
        </form>
      </div>
    </motion.div>
  )
}
