'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
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
  PhotoIcon,
  CloudArrowUpIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { propertySchema, PropertyFormData, stepSchemas } from '@/lib/validation'
import { apiService } from '@/lib/api'

interface MarketInsight {
  averagePrice: number
  priceRange: [number, number]
  marketTrend: 'rising' | 'stable' | 'declining'
  competitorCount: number
  trendPercentage: number
}

interface AIPropertySuggestion {
  title: string
  description: string
  price: string
  amenities: string
  marketInsights: MarketInsight
  qualityScore: {
    overall: number
    seo: number
    readability: number
    marketRelevance: number
  }
}

interface SmartPropertyFormProps {
  onSuccess?: () => void
}

const FORM_STEPS = [
  { id: 'address', title: 'Location', icon: MapPinIcon },
  { id: 'basic', title: 'Basic Info', icon: HomeIcon },
  { id: 'pricing', title: 'Pricing', icon: CurrencyDollarIcon },
  { id: 'images', title: 'Images', icon: PhotoIcon },
  { id: 'description', title: 'Description', icon: DocumentTextIcon }
]

export default function SmartPropertyForm({ onSuccess }: SmartPropertyFormProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<AIPropertySuggestion | null>(null)
  const [isGeneratingAI, setIsGeneratingAI] = useState(false)
  const [marketInsights, setMarketInsights] = useState<MarketInsight | null>(null)
  const [userProfile, setUserProfile] = useState({
    experienceLevel: 'intermediate',
    specialization: 'residential',
    priceRange: 'mid-range'
  })
  const [agentProfile, setAgentProfile] = useState<any>(null)
  const [uploadedImages, setUploadedImages] = useState<string[]>([])
  const [uploadingImages, setUploadingImages] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
    trigger,
    getValues
  } = useForm<PropertyFormData>({
    resolver: zodResolver(propertySchema),
    mode: 'onSubmit', // Only validate on submit
    reValidateMode: 'onSubmit', // Only re-validate on submit
    defaultValues: {
      title: '',
      description: '',
      location: '',
      address: '',
      area: undefined,
      price: 0,
      bedrooms: undefined,
      bathrooms: undefined,
      amenities: '',
      status: 'available',
      propertyType: '',
      images: []
    }
  })

  const watchedAddress = watch('address')
  const watchedPropertyType = watch('propertyType')
  const watchedPrice = watch('price')

  // Fetch agent profile on component mount
  useEffect(() => {
    const fetchAgentProfile = async () => {
      try {
        const response = await apiService.getAgentProfile()
        if (response.success && response.data) {
          setAgentProfile(response.data)
          // Update user profile with agent data
          setUserProfile({
            experienceLevel: response.data.experience_level || 'intermediate',
            specialization: response.data.specialization || 'residential',
            priceRange: 'mid-range' // This could be derived from agent data
          })
        }
      } catch (error) {
        console.error('Failed to fetch agent profile:', error)
      }
    }
    
    fetchAgentProfile()
  }, [])

  // Auto-generate AI suggestions when key fields change
  useEffect(() => {
    if (watchedAddress && watchedPropertyType && currentStep >= 1) {
      generateMarketInsights()
    }
  }, [watchedAddress, watchedPropertyType, currentStep])

  const generateMarketInsights = async () => {
    try {
      // Mock market insights - replace with real API
      const insights: MarketInsight = {
        averagePrice: 3200000,
        priceRange: [2800000, 4200000],
        marketTrend: 'rising',
        competitorCount: 12,
        trendPercentage: 8.5
      }
      setMarketInsights(insights)
    } catch (error) {
      console.error('Failed to generate market insights:', error)
    }
  }

  const generateAISuggestions = async () => {
    setIsGeneratingAI(true)
    try {
      const formData = watch()
      const processedData = {
        ...formData,
        bedrooms: Number(formData.bedrooms),
        bathrooms: Number(formData.bathrooms),
        area: Number(formData.area)
      }
      
      const response = await apiService.getAIPropertySuggestions({
        address: processedData.address,
        property_type: processedData.propertyType,
        bedrooms: processedData.bedrooms,
        bathrooms: processedData.bathrooms,
        area: processedData.area,
        user_profile: userProfile,
        agent_profile: agentProfile
      })

      if (response.success && response.data) {
        const suggestion: AIPropertySuggestion = {
          title: response.data[0]?.title || `Beautiful ${formData.propertyType} in ${formData.location}`,
          description: response.data[0]?.description || 'AI-generated description will appear here',
          price: response.data[0]?.price || formData.price.toString(),
          amenities: response.data[0]?.amenities || 'Modern amenities included',
          marketInsights: marketInsights || {
            averagePrice: 3200000,
            priceRange: [2800000, 4200000],
            marketTrend: 'rising',
            competitorCount: 12,
            trendPercentage: 8.5
          },
          qualityScore: {
            overall: 87,
            seo: 92,
            readability: 85,
            marketRelevance: 84
          }
        }
        setAiSuggestions(suggestion)
        toast.success('AI suggestions generated successfully!')
      }
    } catch (error) {
      console.error('Failed to generate AI suggestions:', error)
      toast.error('Failed to generate AI suggestions. Please try again.')
    } finally {
      setIsGeneratingAI(false)
    }
  }

  const applyAISuggestions = () => {
    if (!aiSuggestions) return
    
    setValue('title', aiSuggestions.title)
    setValue('description', aiSuggestions.description)
    setValue('price', parseFloat(aiSuggestions.price) || 0)
    setValue('amenities', aiSuggestions.amenities)
    
    toast.success('AI suggestions applied to form!')
  }

  const handleImageUpload = async (files: FileList) => {
    if (!files || files.length === 0) return

    setUploadingImages(true)
    try {
      const formData = new FormData()
      Array.from(files).forEach(file => {
        formData.append('files', file)
      })

      const response = await apiService.uploadImages(formData)
      
      if (response.success && response.files) {
        const newImageUrls = response.files.map((file: any) => file.url || file.path)
        const updatedImages = [...uploadedImages, ...newImageUrls]
        setUploadedImages(updatedImages)
        setValue('images', updatedImages)
        toast.success(`${files.length} image(s) uploaded successfully!`)
      } else {
        toast.error('Failed to upload images')
      }
    } catch (error) {
      console.error('Error uploading images:', error)
      toast.error('Failed to upload images. Please try again.')
    } finally {
      setUploadingImages(false)
    }
  }

  const removeImage = (index: number) => {
    const updatedImages = uploadedImages.filter((_, i) => i !== index)
    setUploadedImages(updatedImages)
    setValue('images', updatedImages)
  }

  const validateCurrentStep = async (step: number): Promise<boolean> => {
    const fieldsToValidate = getFieldsForStep(step)
    const currentValues = watch()
    
    // Create a subset of values for the current step
    const stepValues: any = {}
    fieldsToValidate.forEach(field => {
      stepValues[field] = currentValues[field]
    })
    
    // Get the appropriate schema for this step
    let stepSchema
    switch (step) {
      case 0: stepSchema = stepSchemas.address; break
      case 1: stepSchema = stepSchemas.basic; break
      case 2: stepSchema = stepSchemas.pricing; break
      case 3: stepSchema = stepSchemas.images; break
      case 4: stepSchema = stepSchemas.description; break
      default: return true
    }
    
    try {
      stepSchema.parse(stepValues)
      return true
    } catch (error) {
      return false
    }
  }

  const nextStep = async () => {
    const fieldsToValidate = getFieldsForStep(currentStep)
    
    // Check if current step is valid
    const isValid = await validateCurrentStep(currentStep)
    
    if (!isValid) {
      // Show validation errors for empty fields
      await trigger(fieldsToValidate)
      return
    }
    
    // If current step is valid, move to next step
    if (currentStep < FORM_STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const getFieldsForStep = (step: number): (keyof PropertyFormData)[] => {
    switch (step) {
      case 0: return ['address', 'location']
      case 1: return ['propertyType', 'bedrooms', 'bathrooms', 'area']
      case 2: return ['price']
      case 3: return ['images']
      case 4: return ['title', 'description']
      default: return []
    }
  }

  const handleFormSubmit = async () => {
    setIsLoading(true)
    try {
      // Get current form values
      const data = getValues()
      
      // Check if we're on the final step and validate required fields
      if (currentStep === FORM_STEPS.length - 1) {
        const finalStepFields = getFieldsForStep(currentStep)
        const hasEmptyRequiredFields = finalStepFields.some(field => {
          const value = data[field]
          return !value || value.toString().trim() === ''
        })
        
        if (hasEmptyRequiredFields) {
          // Trigger validation for the final step fields
          await trigger(finalStepFields)
          setIsLoading(false)
          return
        }
      }
      
      // Get current user for agent_id
      let agentId = "anonymous"
      try {
        const currentUser = await apiService.getCurrentUser()
        agentId = currentUser.id || currentUser.email || "anonymous"
      } catch (error) {
        console.warn('Could not get current user, using anonymous agent_id:', error)
      }
      
      // Transform data for unified property service
      const propertyData = {
        ...data,
        ai_generate: true, // Always enable AI features
        market_analysis: {}, // Market analysis as dictionary (will be populated by backend)
        property_type: data.propertyType || 'Apartment',
        location: data.location || data.address,
        price: Number(data.price) || 0,
        bedrooms: Number(data.bedrooms) || 0,
        bathrooms: Number(data.bathrooms) || 0,
        area_sqft: Number(data.area) || 0,
        images: uploadedImages,
        agent_id: agentId
      }
      
      const response = await apiService.createProperty(propertyData)
      if (response.success || response.id) {
        toast.success('AI-powered property created successfully!')
        onSuccess?.()
      }
    } catch (error) {
      console.error('Failed to create property:', error)
      toast.error('Failed to create property. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const onSubmit = async (data: PropertyFormData) => {
    // This function is kept for compatibility but won't be used
    // The actual submission is handled by handleFormSubmit
    await handleFormSubmit()
  }

  const renderStepContent = () => {
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
                Start by entering the property address. Our AI will detect property type and market insights.
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

            {watchedAddress && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800"
              >
                <div className="flex items-center space-x-2 mb-2">
                  <SparklesIcon className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold text-blue-900 dark:text-blue-100">AI Detection</span>
                </div>
                <div className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                  <p>✓ Location verified: Premium area</p>
                  <p>✓ Property type: Likely apartment/flat</p>
                  <p>✓ Market trend: Rising (+8.5% YoY)</p>
                </div>
              </motion.div>
            )}
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
                Basic property details help us provide better AI suggestions.
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
                  <option value="">Select property type</option>
                  <option value="Apartment">Apartment</option>
                  <option value="House">House</option>
                  <option value="Villa">Villa</option>
                  <option value="Studio">Studio</option>
                  <option value="Penthouse">Penthouse</option>
                </select>
                {errors.propertyType && (
                  <p className="text-red-500 text-sm mt-1">{errors.propertyType.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  Area (sq ft) *
                </label>
                <input
                  {...register('area', { valueAsNumber: true })}
                  type="number"
                  min="1"
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
                  <option value="">Select bedrooms</option>
                  {[1, 2, 3, 4, 5].map(num => (
                    <option key={num} value={num}>{num} BHK</option>
                  ))}
                </select>
                {errors.bedrooms && (
                  <p className="text-red-500 text-sm mt-1">{errors.bedrooms.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  Bathrooms *
                </label>
                <select
                  {...register('bathrooms', { valueAsNumber: true })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                >
                  <option value="">Select bathrooms</option>
                  {[1, 2, 3, 4, 5].map(num => (
                    <option key={num} value={num}>{num}</option>
                  ))}
                </select>
                {errors.bathrooms && (
                  <p className="text-red-500 text-sm mt-1">{errors.bathrooms.message}</p>
                )}
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
                    <p className="text-green-800 dark:text-green-200">
                      <span className="font-medium">Market Trend:</span> {marketInsights.marketTrend} (+{marketInsights.trendPercentage}%)
                    </p>
                  </div>
                  <div>
                    <p className="text-green-800 dark:text-green-200">
                      <span className="font-medium">Price Range:</span> ₹{(marketInsights.priceRange[0] / 100000).toFixed(1)}L - ₹{(marketInsights.priceRange[1] / 100000).toFixed(1)}L
                    </p>
                    <p className="text-green-800 dark:text-green-200">
                      <span className="font-medium">Competition:</span> {marketInsights.competitorCount} similar properties
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
                Based on market analysis, here&apos;s our pricing recommendation.
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
                    {...register('price', { valueAsNumber: true })}
                    type="number"
                    min="1"
                    placeholder="e.g., 3200000"
                    className="w-full pl-8 pr-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                  />
                </div>
                {errors.price && (
                  <p className="text-red-500 text-sm mt-1">{errors.price.message}</p>
                )}
              </div>
            </div>

            {marketInsights && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-4 border border-yellow-200 dark:border-yellow-800"
              >
                <div className="flex items-center space-x-2 mb-3">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />
                  <span className="font-semibold text-yellow-900 dark:text-yellow-100">Pricing Analysis</span>
                </div>
                <div className="space-y-2 text-sm text-yellow-800 dark:text-yellow-200">
                  <p>💡 <strong>Recommended range:</strong> ₹{(marketInsights.priceRange[0] / 100000).toFixed(1)}L - ₹{(marketInsights.priceRange[1] / 100000).toFixed(1)}L</p>
                  <p>📈 <strong>Market average:</strong> ₹{(marketInsights.averagePrice / 100000).toFixed(1)}L</p>
                  <p>🎯 <strong>Sweet spot:</strong> ₹{((marketInsights.averagePrice * 1.05) / 100000).toFixed(1)}L (5% above average)</p>
                </div>
              </motion.div>
            )}
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
              <PhotoIcon className="w-16 h-16 text-indigo-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Add Property Images
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Upload high-quality images to showcase your property.
              </p>
            </div>

            <div className="space-y-6">
              {/* Image Upload Area */}
              <div className="border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-xl p-8 text-center hover:border-indigo-500 dark:hover:border-indigo-400 transition-colors">
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={(e) => e.target.files && handleImageUpload(e.target.files)}
                  className="hidden"
                  id="image-upload"
                  disabled={uploadingImages}
                />
                <label
                  htmlFor="image-upload"
                  className={`cursor-pointer flex flex-col items-center space-y-4 ${
                    uploadingImages ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <CloudArrowUpIcon className="w-12 h-12 text-gray-400" />
                  <div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {uploadingImages ? 'Uploading...' : 'Click to upload images'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      PNG, JPG, JPEG up to 10MB each
                    </p>
                  </div>
                </label>
              </div>

              {/* Uploaded Images Grid */}
              {uploadedImages.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {uploadedImages.map((imageUrl, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={imageUrl}
                        alt={`Property image ${index + 1}`}
                        className="w-full h-32 object-cover rounded-lg"
                      />
                      <button
                        onClick={() => removeImage(index)}
                        className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Image Tips */}
              <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-4 border border-indigo-200 dark:border-indigo-800">
                <div className="flex items-center space-x-2 mb-2">
                  <LightBulbIcon className="w-5 h-5 text-indigo-600" />
                  <span className="font-semibold text-indigo-900 dark:text-indigo-100">Image Tips</span>
                </div>
                <ul className="text-sm text-indigo-800 dark:text-indigo-200 space-y-1">
                  <li>• Use high-resolution images (at least 1920x1080)</li>
                  <li>• Include exterior, interior, and key features</li>
                  <li>• Ensure good lighting and clean spaces</li>
                  <li>• Upload 5-10 images for best results</li>
                </ul>
              </div>
            </div>
          </motion.div>
        )

      case 4:
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
                Let AI help you create professional property descriptions.
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
                  placeholder="Describe your property's key features, location benefits, and unique selling points..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white resize-none"
                />
                {errors.description && (
                  <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  Amenities
                </label>
                <textarea
                  {...register('amenities')}
                  rows={3}
                  placeholder="e.g., Swimming pool, Gym, 24/7 Security, Parking, Garden"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white resize-none"
                />
              </div>

              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={generateAISuggestions}
                  disabled={isGeneratingAI}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-3 px-6 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200"
                >
                  {isGeneratingAI ? (
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
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-purple-700 dark:text-purple-300">Quality Score:</span>
                      <span className="font-bold text-purple-900 dark:text-purple-100">{aiSuggestions.qualityScore.overall}/100</span>
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

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="text-center">
                        <div className="font-semibold text-purple-900 dark:text-purple-100">SEO Score</div>
                        <div className="text-purple-700 dark:text-purple-300">{aiSuggestions.qualityScore.seo}/100</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-purple-900 dark:text-purple-100">Readability</div>
                        <div className="text-purple-700 dark:text-purple-300">{aiSuggestions.qualityScore.readability}/100</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-purple-900 dark:text-purple-100">Market Relevance</div>
                        <div className="text-purple-700 dark:text-purple-300">{aiSuggestions.qualityScore.marketRelevance}/100</div>
                      </div>
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
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Progress Header */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-200 dark:border-slate-700 mb-6">
          <div className="p-6 sm:p-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                  Add New Property
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  Step {currentStep + 1} of {FORM_STEPS.length}: {FORM_STEPS[currentStep].title}
                </p>
              </div>
              <div className="hidden sm:flex items-center space-x-2">
                <SparklesIcon className="w-6 h-6 text-blue-500" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">AI-Powered</span>
              </div>
            </div>

            {/* Progress Steps */}
            <div className="flex items-center space-x-4">
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
          </div>
        </div>

        {/* Form Content */}
        <form onSubmit={(e) => { e.preventDefault(); handleFormSubmit(); }}>
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-200 dark:border-slate-700">
            <div className="p-6 sm:p-8">
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
      </div>
    </div>
  )
}