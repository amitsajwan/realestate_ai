'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { SparklesIcon, HomeIcon, MapPinIcon } from '@heroicons/react/24/outline'
import { LoadingButton } from '@/components/LoadingStates'
import { useAsyncOperation } from '@/hooks/useLoading'
import { apiService } from '@/lib/api'
import { logger } from '@/lib/logger'
import { toast } from 'react-hot-toast'

interface PropertyFormData {
  title: string
  description: string
  price: string
  location: string
  bedrooms: string
  bathrooms: string
  area: string
  propertyType: string
  language: string
}

interface GenAIPropertyFormProps {
  onSuccess?: (propertyId: string) => void
}

export default function GenAIPropertyForm({ onSuccess }: GenAIPropertyFormProps) {
  const [formData, setFormData] = useState<PropertyFormData>({
    title: '',
    description: '',
    price: '',
    location: '',
    bedrooms: '2',
    bathrooms: '2',
    area: '',
    propertyType: 'apartment',
    language: 'English'
  })

  const generateOperation = useAsyncOperation()

  const handleInputChange = (field: keyof PropertyFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleGenerate = async () => {
    try {
      logger.info('Starting AI property generation', {
        component: 'GenAIPropertyForm',
        action: 'generate_property',
        metadata: { language: formData.language, propertyType: formData.propertyType }
      })

      const response = await apiService.generatePropertyContent({
        property_id: `prop_${Date.now()}`,
        language: formData.language,
        basic_info: {
          title: formData.title,
          description: formData.description,
          price: formData.price,
          location: formData.location,
          bedrooms: parseInt(formData.bedrooms),
          bathrooms: parseInt(formData.bathrooms),
          area: formData.area,
          property_type: formData.propertyType
        }
      })

      if (response) {
        logger.info('AI property generation successful', {
          component: 'GenAIPropertyForm',
          action: 'generate_success'
        })
        
        toast.success('Property content generated successfully!')
        onSuccess?.(response.property_id || `prop_${Date.now()}`)
      }
    } catch (error) {
      logger.error('AI property generation failed', {
        component: 'GenAIPropertyForm',
        action: 'generate_error',
        errorDetails: error
      })
      
      toast.error('Failed to generate property content')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto p-6"
    >
      <div className="glass-card p-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl">
            <SparklesIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">AI Property Generator</h2>
            <p className="text-gray-400">Create compelling property listings with AI</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Property Title
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              className="form-input"
              placeholder="Enter property title"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Location
            </label>
            <div className="relative">
              <MapPinIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={formData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                className="form-input pl-10"
                placeholder="Enter location"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Price
            </label>
            <input
              type="text"
              value={formData.price}
              onChange={(e) => handleInputChange('price', e.target.value)}
              className="form-input"
              placeholder="Enter price"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Property Type
            </label>
            <select
              value={formData.propertyType}
              onChange={(e) => handleInputChange('propertyType', e.target.value)}
              className="form-input"
            >
              <option value="apartment">Apartment</option>
              <option value="house">House</option>
              <option value="villa">Villa</option>
              <option value="commercial">Commercial</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Bedrooms
            </label>
            <select
              value={formData.bedrooms}
              onChange={(e) => handleInputChange('bedrooms', e.target.value)}
              className="form-input"
            >
              {[1, 2, 3, 4, 5].map(num => (
                <option key={num} value={num.toString()}>{num}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Bathrooms
            </label>
            <select
              value={formData.bathrooms}
              onChange={(e) => handleInputChange('bathrooms', e.target.value)}
              className="form-input"
            >
              {[1, 2, 3, 4, 5].map(num => (
                <option key={num} value={num.toString()}>{num}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Area (sq ft)
            </label>
            <input
              type="text"
              value={formData.area}
              onChange={(e) => handleInputChange('area', e.target.value)}
              className="form-input"
              placeholder="Enter area"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Language
            </label>
            <select
              value={formData.language}
              onChange={(e) => handleInputChange('language', e.target.value)}
              className="form-input"
            >
              <option value="English">English</option>
              <option value="Hindi">Hindi</option>
              <option value="Marathi">Marathi</option>
              <option value="Gujarati">Gujarati</option>
            </select>
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            className="form-input h-32 resize-none"
            placeholder="Enter property description"
          />
        </div>

        <div className="flex justify-center">
          <LoadingButton
            onClick={() => generateOperation.execute(handleGenerate)}
            isLoading={generateOperation.isLoading}
            className="btn-primary px-8 py-3 flex items-center gap-2"
            disabled={!formData.title || !formData.location}
          >
            <SparklesIcon className="w-5 h-5" />
            Generate AI Content
          </LoadingButton>
        </div>
      </div>
    </motion.div>
  )
}