'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { PlusIcon, SparklesIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface PropertyFormData {
  title: string
  price: string
  address: string
  bedrooms: string
  bathrooms: string
  area: string
  description: string
  amenities: string
}

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
  } = useForm<PropertyFormData>()

  const onSubmit = async (data: PropertyFormData) => {
    setIsLoading(true)
    try {
      // Here you would typically send the data to your API
      console.log('Property data:', data)
      toast.success('Property added successfully!')
      onSuccess?.()
    } catch (error) {
      toast.error('Failed to add property')
    } finally {
      setIsLoading(false)
    }
  }

  const autoFillWithAI = async () => {
    setIsAILoading(true)
    try {
      const response = await fetch('/api/v1/property/ai_suggest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_type: 'Apartment',
          location: 'City Center',
          budget: '₹75,00,000',
          requirements: 'Modern amenities'
        })
      })

      const result = await response.json()

      if (result.success && result.suggestions && result.suggestions.length > 0) {
        const suggestion = result.suggestions[0]
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
      toast.error('Failed to generate AI content. Please try again.')
    } finally {
      setIsAILoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="glass-card">
        <div className="flex items-center space-x-3 mb-6">
          <PlusIcon className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-gray-800">Add Property</h2>
        </div>
        
        <p className="text-gray-600 mb-6">
          Create a new property listing with all the details.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title *
              </label>
              <input
                type="text"
                {...register('title', { required: 'Title is required' })}
                className="form-input"
                placeholder="Enter property title"
              />
              {errors.title && (
                <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Price *
              </label>
              <input
                type="text"
                {...register('price', { required: 'Price is required' })}
                className="form-input"
                placeholder="₹50,00,000"
              />
              {errors.price && (
                <p className="text-red-500 text-sm mt-1">{errors.price.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address *
            </label>
            <input
              type="text"
              {...register('address', { required: 'Address is required' })}
              className="form-input"
              placeholder="Enter property address"
            />
            {errors.address && (
              <p className="text-red-500 text-sm mt-1">{errors.address.message}</p>
            )}
          </div>

          {/* Property Details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bedrooms
              </label>
              <select {...register('bedrooms')} className="form-input">
                <option value="">Select</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4+</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bathrooms
              </label>
              <select {...register('bathrooms')} className="form-input">
                <option value="">Select</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4+</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Area (sq ft)
              </label>
              <input
                type="number"
                {...register('area')}
                className="form-input"
                placeholder="1200"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              {...register('description', { required: 'Description is required' })}
              rows={4}
              className="form-input"
              placeholder="Describe the property features, location, amenities..."
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amenities
            </label>
            <input
              type="text"
              {...register('amenities')}
              className="form-input"
              placeholder="Parking, Gym, Pool, etc."
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4">
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Adding Property...</span>
                </>
              ) : (
                <>
                  <PlusIcon className="w-5 h-5" />
                  <span>Add Property</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={autoFillWithAI}
              disabled={isAILoading}
              className="btn-secondary flex items-center space-x-2"
            >
              {isAILoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Generating AI Content...</span>
                </>
              ) : (
                <>
                  <SparklesIcon className="w-5 h-5" />
                  <span>Auto-Fill with AI</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="btn-outline flex items-center space-x-2"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span>Back to Dashboard</span>
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  )
}
