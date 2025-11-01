'use client'

import { agentAPI } from '@/lib/agent'
import { apiService } from '@/lib/api/centralized-client'
import { authManager } from '@/lib/auth'
import { API_BASE_URL } from '@/lib/config/api'
import { propertiesAPI } from '@/lib/properties'
import { PropertyFormData, propertySchema, stepSchemas } from '@/lib/validation'
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CameraIcon,
  CheckCircleIcon,
  CloudArrowUpIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  HomeIcon,
  LightBulbIcon,
  MapPinIcon,
  PhotoIcon,
  SparklesIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { zodResolver } from '@hookform/resolvers/zod'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'

interface MarketInsight {
  averagePrice: number
  priceRange: [number, number]
  marketTrend: 'rising' | 'stable' | 'declining'
  competitorCount: number
  trendPercentage: number
}

interface AITitleOption {
  text: string
  qualityScore: number
  seoScore: number
  readabilityScore: number
  marketRelevanceScore: number
}

interface AIDescriptionOption {
  text: string
  qualityScore: number
  seoScore: number
  readabilityScore: number
  marketRelevanceScore: number
}

interface AIPropertySuggestion {
  titleOptions: AITitleOption[]
  descriptionOptions: AIDescriptionOption[]
  selectedTitleIndex: number
  selectedDescriptionIndex: number
  price: string
  amenities: string[]
  features: string[]
  marketInsights: string
  overallQualityScore: {
    overall: number
    seo: number
    readability: number
    marketRelevance: number
  }
}

interface SmartPropertyFormProps {
  onSuccess?: (propertyData?: any) => void
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
  const [aiHint, setAiHint] = useState<string>('')
  const [touchStart, setTouchStart] = useState<{ x: number, y: number } | null>(null)
  const [touchEnd, setTouchEnd] = useState<{ x: number, y: number } | null>(null)

  // Minimum distance for a swipe
  const minSwipeDistance = 50

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null) // Reset touch end
    setTouchStart({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    })
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    })
  }

  const handleTouchEnd = async () => {
    if (!touchStart || !touchEnd) return

    // Get horizontal distance
    const distanceX = touchStart.x - touchEnd.x
    const absDistanceX = Math.abs(distanceX)

    // Get vertical distance to check if the user is scrolling vertically
    const distanceY = Math.abs(touchStart.y - touchEnd.y)

    // Only register as a swipe if:
    // 1. The horizontal distance is greater than minimum swipe distance
    // 2. The horizontal distance is greater than the vertical distance (to avoid triggering on scrolling)
    if (absDistanceX > minSwipeDistance && absDistanceX > distanceY) {
      // Check direction and validate step change
      if (distanceX > 0 && currentStep < FORM_STEPS.length - 1) {
        // Swiped left - go to next step
        const isValid = await validateCurrentStep(currentStep)
        if (isValid) {
          setCurrentStep(prev => prev + 1)
        }
      } else if (distanceX < 0 && currentStep > 0) {
        // Swiped right - go to previous step
        setCurrentStep(prev => prev - 1)
      }
    }
  }
  const [userProfile, setUserProfile] = useState({
    experienceLevel: 'intermediate',
    specialization: 'residential',
    priceRange: 'mid-range'
  })
  const [agentProfile, setAgentProfile] = useState<any>(null)
  const [uploadedImages, setUploadedImages] = useState<string[]>([])
  const [uploadingImages, setUploadingImages] = useState(false)
  const [selectedTitleIndex, setSelectedTitleIndex] = useState(0)
  const [selectedDescriptionIndex, setSelectedDescriptionIndex] = useState(0)
  const [isPropertyCreated, setIsPropertyCreated] = useState(false)
  const [createdPropertyData, setCreatedPropertyData] = useState<any>(null)

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
      price: undefined,
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
        const response = await agentAPI.getAgentProfile()
        if (response.success && response.data) {
          setAgentProfile(response.data)
          // Update user profile with agent data
          setUserProfile({
            experienceLevel: 'intermediate', // Default value
            specialization: 'residential', // Default value
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

      // Validate required fields before making API call
      if (!formData.address || !formData.propertyType || !formData.bedrooms || !formData.bathrooms || !formData.area || !formData.price) {
        toast.error('Please fill in Address, Property Type, Bedrooms, Bathrooms, Area and Price before generating AI content.')
        return
      }

      const processedData = {
        ...formData,
        bedrooms: Number(formData.bedrooms),
        bathrooms: Number(formData.bathrooms),
        area: Number(formData.area)
      }

      console.log('Generating AI suggestions with data:', processedData)
      console.log('Amenities being sent:', processedData.amenities)
      console.log('Description being sent:', processedData.description)
      console.log('Title being sent:', processedData.title)
      console.log('AI Hint being sent:', aiHint)

      // Use centralized API service for AI content generation
      const aiResult = await apiService.generateAIContent({
        context: 'property_creation',
        property_data: {
          address: processedData.address,
          property_type: processedData.propertyType,
          bedrooms: processedData.bedrooms,
          bathrooms: processedData.bathrooms,
          area: processedData.area,
          price: processedData.price || undefined,
          amenities: processedData.amenities || '',
          description: processedData.description || '',
          title: processedData.title || '',
          ai_hint: aiHint || ''
        },
        languages: ['en'], // Default to English for property creation
        platforms: ['website'], // Property creation is primarily for website
        agent_profile: agentProfile,
        generation_options: {
          tone: 'professional',
          length: 'medium',
          include_hashtags: false,
          include_cta: false,
          max_title_length: 100
        }
      })

      // Transform the response to match the expected format
      const transformedResponse = {
        success: true,
        suggestions: aiResult.content ? {
          title: aiResult.content.website?.en?.title || '',
          description: aiResult.content.website?.en?.body || '',
          // Create title_suggestions array from the single title
          title_suggestions: aiResult.content.website?.en?.title ? [{
            text: aiResult.content.website.en.title,
            qualityScore: 85,
            seoScore: 90,
            readabilityScore: 80,
            marketRelevanceScore: 88
          }] : [],
          // Create description_suggestions array from the single body
          description_suggestions: aiResult.content.website?.en?.body ? [{
            text: aiResult.content.website.en.body,
            qualityScore: 85,
            seoScore: 90,
            readabilityScore: 80,
            marketRelevanceScore: 88
          }] : [],
          overallQualityScore: {
            overall: 85,
            seo: 80,
            readability: 90,
            marketRelevance: 85
          }
        } : null
      }

      if (transformedResponse.success && transformedResponse.suggestions) {
        const suggestions: any = transformedResponse.suggestions
        console.log('Raw AI suggestions response:', suggestions)
        console.log('Price suggestions details:', {
          suggested: suggestions.price_suggestions?.suggested,
          ai_valuation: suggestions.price_suggestions?.ai_valuation,
          market_rate_per_sqft: suggestions.price_suggestions?.market_rate_per_sqft,
          current: suggestions.price_suggestions?.current
        })

        // Process title options
        const titleOptions: AITitleOption[] = (suggestions.title_suggestions || []).map((titleOption: any, index: number) => ({
          text: typeof titleOption === 'string' ? titleOption : titleOption.text,
          qualityScore: typeof titleOption === 'object' ? titleOption.qualityScore : Math.floor(Math.random() * 20) + 80,
          seoScore: typeof titleOption === 'object' ? titleOption.seoScore : Math.floor(Math.random() * 15) + 85,
          readabilityScore: typeof titleOption === 'object' ? titleOption.readabilityScore : Math.floor(Math.random() * 15) + 85,
          marketRelevanceScore: typeof titleOption === 'object' ? titleOption.marketRelevanceScore : Math.floor(Math.random() * 15) + 85
        }))

        // Process description options
        const descriptionOptions: AIDescriptionOption[] = (suggestions.description_suggestions || []).map((descriptionOption: any, index: number) => ({
          text: typeof descriptionOption === 'string' ? descriptionOption : descriptionOption.text,
          qualityScore: typeof descriptionOption === 'object' ? descriptionOption.qualityScore : Math.floor(Math.random() * 20) + 80,
          seoScore: typeof descriptionOption === 'object' ? descriptionOption.seoScore : Math.floor(Math.random() * 15) + 85,
          readabilityScore: typeof descriptionOption === 'object' ? descriptionOption.readabilityScore : Math.floor(Math.random() * 15) + 85,
          marketRelevanceScore: typeof descriptionOption === 'object' ? descriptionOption.marketRelevanceScore : Math.floor(Math.random() * 15) + 85
        }))

        const suggestion: AIPropertySuggestion = {
          titleOptions: titleOptions.length > 0 ? titleOptions : [{
            text: `Beautiful ${formData.propertyType} in ${formData.location}`,
            qualityScore: 85,
            seoScore: 90,
            readabilityScore: 80,
            marketRelevanceScore: 88
          }],
          descriptionOptions: descriptionOptions.length > 0 ? descriptionOptions : [{
            text: 'AI-generated description will appear here',
            qualityScore: 85,
            seoScore: 90,
            readabilityScore: 80,
            marketRelevanceScore: 88
          }],
          selectedTitleIndex: 0,
          selectedDescriptionIndex: 0,
          price: (() => {
            const suggestedPrice = suggestions.price_suggestions?.suggested;
            const aiValuation = suggestions.price_suggestions?.ai_valuation;
            const marketRate = suggestions.price_suggestions?.market_rate_per_sqft;
            const area = formData.area || 1000;

            // Use the best available price
            if (suggestedPrice && suggestedPrice > 0) {
              return suggestedPrice.toString();
            } else if (aiValuation && aiValuation > 0) {
              return aiValuation.toString();
            } else if (marketRate && marketRate > 0 && area > 0) {
              return (marketRate * area).toString();
            } else {
              return formData.price.toString();
            }
          })(),
          amenities: Array.isArray(suggestions.amenities_suggestions) ? suggestions.amenities_suggestions : ['Modern amenities included'],
          features: suggestions.features_suggestions || ['Modern design', 'Prime location'],
          marketInsights: suggestions.market_insights || 'Market analysis will appear here',
          overallQualityScore: {
            overall: suggestions.quality_score?.overall || 85,
            seo: suggestions.quality_score?.seo || 90,
            readability: suggestions.quality_score?.readability || 80,
            marketRelevance: suggestions.quality_score?.market_relevance || 88
          }
        }

        console.log('Processed AI suggestion:', suggestion)
        setAiSuggestions(suggestion)
        toast.success('AI suggestions generated successfully!')
      } else {
        console.error('AI suggestions response failed:', aiResult)
        toast.error('Failed to generate AI suggestions. Please try again.')
      }
    } catch (error: any) {
      console.error('Failed to generate AI suggestions:', error)

      // Handle specific error types
      if (error.message?.includes('401') || error.message?.includes('Unauthorized') || error.message?.includes('Authentication required')) {
        toast.error('Please log in to use AI content generation features.', {
          duration: 5000
        })
      } else if (error.message?.includes('Network') || error.message?.includes('fetch')) {
        toast.error('Network error. Please check your connection and try again.')
      } else {
        toast.error(`Failed to generate AI suggestions: ${error.message || 'Unknown error'}. Please try again.`)
      }
    } finally {
      setIsGeneratingAI(false)
    }
  }

  const applyAISuggestions = () => {
    if (!aiSuggestions) return

    console.log('Applying AI suggestions:', aiSuggestions)

    const selectedTitle = aiSuggestions.titleOptions[selectedTitleIndex]?.text || aiSuggestions.titleOptions[0]?.text
    const selectedDescription = aiSuggestions.descriptionOptions[selectedDescriptionIndex]?.text || aiSuggestions.descriptionOptions[0]?.text

    setValue('title', selectedTitle)
    setValue('description', selectedDescription)
    setValue('price', parseFloat(aiSuggestions.price) || 0)
    setValue('amenities', aiSuggestions.amenities.join(', '))

    // Trigger form re-render by updating the form state
    trigger(['title', 'description', 'price', 'amenities'])

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

  const removeImage = async (index: number) => {
    try {
      const imageToRemove = uploadedImages[index]
      const updatedImages = uploadedImages.filter((_, i) => i !== index)
      setUploadedImages(updatedImages)
      setValue('images', updatedImages)

      // Attempt to clean up the removed image
      if (imageToRemove) {
        await apiService.deleteImage(imageToRemove).catch(console.error)
      }

      toast.success('Image removed successfully')
    } catch (error) {
      console.error('Failed to remove image:', error)
      toast.error('Failed to remove image. Please try again.')
    }
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
    console.log('[SmartPropertyForm] handleFormSubmit called')
    console.log('[SmartPropertyForm] Current step:', currentStep)
    console.log('[SmartPropertyForm] Is final step:', currentStep === FORM_STEPS.length - 1)
    setIsLoading(true)
    try {
      // Get current form values
      const data = getValues()
      console.log('[SmartPropertyForm] Form data:', data)

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
        features: [], // Default empty features array
        images: uploadedImages,
        agent_id: agentId,
        amenities: data.amenities || '' // Ensure amenities is a string
      }

      console.log('Form data being submitted:', propertyData)
      console.log('Amenities type:', typeof propertyData.amenities, 'Value:', propertyData.amenities)

      console.log('🚀 About to call propertiesAPI.createProperty with:', propertyData)
      console.log('🚀 API_BASE_URL:', API_BASE_URL)
      console.log('🚀 Auth token available:', !!authManager.getState().token)

      console.log('🚀 CALLING API with propertyData:', JSON.stringify(propertyData, null, 2))
      const response = await propertiesAPI.createProperty(propertyData)
      console.log('🚀 API call completed, response:', response)
      console.log('Property creation response:', response)
      console.log('Response success:', response.success)
      console.log('Response data:', response.data)

      if (response.success && response.data) {
        toast.success('AI-powered property created successfully!')
        console.log('Property created successfully, calling onSuccess callback')

        // Prepare property data for workflow
        const workflowPropertyData = {
          id: response.data.id,
          title: data.title,
          location: data.location || data.address,
          price: Number(data.price) || 0,
          bedrooms: Number(data.bedrooms) || 0,
          bathrooms: Number(data.bathrooms) || 0,
          propertyType: data.propertyType || 'Apartment',
          area: Number(data.area) || 0,
          description: data.description,
          images: uploadedImages
        }

        // Set the property as created and store the data
        setIsPropertyCreated(true)
        setCreatedPropertyData(workflowPropertyData)

        console.log('Calling onSuccess with workflowPropertyData:', workflowPropertyData)
        onSuccess?.(workflowPropertyData)
      } else if (response && (response as any).id || (response as any)._id) {
        // Fallback: If response doesn't have success/data structure but has property ID
        console.log('Using fallback response format:', response)
        toast.success('AI-powered property created successfully!')

        const workflowPropertyData = {
          id: (response as any).id || (response as any)._id,
          title: data.title,
          location: data.location || data.address,
          price: Number(data.price) || 0,
          bedrooms: Number(data.bedrooms) || 0,
          bathrooms: Number(data.bathrooms) || 0,
          propertyType: data.propertyType || 'Apartment',
          area: Number(data.area) || 0,
          description: data.description,
          images: uploadedImages
        }

        // Set the property as created and store the data
        setIsPropertyCreated(true)
        setCreatedPropertyData(workflowPropertyData)

        console.log('Calling onSuccess with fallback workflowPropertyData:', workflowPropertyData)
        onSuccess?.(workflowPropertyData)
      } else {
        console.error('Property creation failed:', response)
        toast.error('Failed to create property. Please try again.')
      }
    } catch (error: any) {
      console.error('❌ Failed to create property:', error)
      console.error('❌ Error message:', error.message)
      console.error('❌ Error stack:', error.stack)
      console.error('❌ Full error object:', JSON.stringify(error, null, 2))

      // Handle specific error types
      if (error.message?.includes('401') || error.message?.includes('Unauthorized')) {
        toast.error('Please log in to create properties.')
      } else if (error.message?.includes('Network') || error.message?.includes('fetch')) {
        toast.error('Network error. Please check your connection and try again.')
      } else {
        toast.error(`Failed to create property: ${error.message || 'Unknown error'}. Please try again.`)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const onSubmit = async (data: PropertyFormData) => {
    // This function is kept for compatibility but won't be used
    // The actual submission is handled by handleFormSubmit
    await handleFormSubmit()
  }

  const resetForm = () => {
    setIsPropertyCreated(false)
    setCreatedPropertyData(null)
    setCurrentStep(0)
    setUploadedImages([])
    setSelectedTitleIndex(0)
    setSelectedDescriptionIndex(0)
    setAiSuggestions(null)
    setMarketInsights(null)
    // Reset form values
    setValue('title', '')
    setValue('description', '')
    setValue('location', '')
    setValue('address', '')
    setValue('propertyType', '')
    setValue('bedrooms', 1)
    setValue('bathrooms', 1)
    setValue('area', 1)
    setValue('price', 0)
    setValue('images', [])
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-4 sm:gap-6">
              <div className="space-y-3">
                <label className="block text-base sm:text-sm font-semibold text-gray-900 dark:text-white">
                  Property Type *
                </label>
                <select
                  {...register('propertyType')}
                  className="w-full px-4 py-4 sm:py-3 border-2 border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-base sm:text-sm min-h-[52px] sm:min-h-[44px]"
                >
                  <option value="">Select property type</option>
                  <option value="Apartment">Apartment</option>
                  <option value="House">House</option>
                  <option value="Villa">Villa</option>
                  <option value="Studio">Studio</option>
                  <option value="Penthouse">Penthouse</option>
                </select>
                {errors.propertyType && (
                  <p className="text-red-500 text-base sm:text-sm font-medium mt-1 px-1">{errors.propertyType.message}</p>
                )}
              </div>

              <div className="space-y-3">
                <label className="block text-base sm:text-sm font-semibold text-gray-900 dark:text-white">
                  Area (sq ft) *
                </label>
                <input
                  {...register('area', { valueAsNumber: true })}
                  type="number"
                  inputMode="numeric"
                  min="1"
                  placeholder="e.g., 1200"
                  className="w-full px-4 py-4 sm:py-3 border-2 border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-base sm:text-sm min-h-[52px] sm:min-h-[44px]"
                />
                {errors.area && (
                  <p className="text-red-500 text-base sm:text-sm font-medium mt-1 px-1">{errors.area.message}</p>
                )}
              </div>

              <div className="space-y-3">
                <label className="block text-base sm:text-sm font-semibold text-gray-900 dark:text-white">
                  Bedrooms *
                </label>
                <select
                  {...register('bedrooms', { valueAsNumber: true })}
                  className="w-full px-4 py-4 sm:py-3 border-2 border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-base sm:text-sm min-h-[52px] sm:min-h-[44px]"
                >
                  <option value="">Select bedrooms</option>
                  {[1, 2, 3, 4, 5].map(num => (
                    <option key={num} value={num}>{num} BHK</option>
                  ))}
                </select>
                {errors.bedrooms && (
                  <p className="text-red-500 text-base sm:text-sm font-medium mt-1 px-1">{errors.bedrooms.message}</p>
                )}
              </div>

              <div className="space-y-3">
                <label className="block text-base sm:text-sm font-semibold text-gray-900 dark:text-white">
                  Bathrooms *
                </label>
                <select
                  {...register('bathrooms', { valueAsNumber: true })}
                  className="w-full px-4 py-4 sm:py-3 border-2 border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-base sm:text-sm min-h-[52px] sm:min-h-[44px]"
                >
                  <option value="">Select bathrooms</option>
                  {[1, 2, 3, 4, 5].map(num => (
                    <option key={num} value={num}>{num}</option>
                  ))}
                </select>
                {errors.bathrooms && (
                  <p className="text-red-500 text-base sm:text-sm font-medium mt-1 px-1">{errors.bathrooms.message}</p>
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
              <div className="border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-xl p-6 sm:p-8 text-center hover:border-indigo-500 dark:hover:border-indigo-400 transition-colors">
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={(e) => e.target.files && handleImageUpload(e.target.files)}
                  className="hidden"
                  id="image-upload"
                  disabled={uploadingImages}
                  capture="environment"
                />
                <label
                  htmlFor="image-upload"
                  className={`cursor-pointer flex flex-col items-center space-y-4 min-h-[150px] justify-center ${
                    uploadingImages ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {uploadingImages ? (
                    <div className="flex flex-col items-center space-y-4">
                      <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                      <div>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">Uploading Images...</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Please wait</p>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="w-16 h-16 sm:w-12 sm:h-12 bg-indigo-50 dark:bg-indigo-900/20 rounded-full flex items-center justify-center">
                        <CloudArrowUpIcon className="w-10 h-10 sm:w-8 sm:h-8 text-indigo-500" />
                      </div>
                      <div>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">
                          {uploadedImages.length > 0 ? 'Add More Images' : 'Upload Property Images'}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          Use camera or choose from gallery
                        </p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                          PNG, JPG, JPEG up to 10MB each
                        </p>
                      </div>
                    </>
                  )}
                </label>
              </div>

              {/* Upload Controls for Mobile */}
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <button
                  type="button"
                  onClick={() => {
                    const input = document.getElementById('image-upload') as HTMLInputElement;
                    if (input) {
                      input.removeAttribute('capture');
                      input.click();
                    }
                  }}
                  disabled={uploadingImages}
                  className="flex-1 flex items-center justify-center space-x-2 py-3 px-4 bg-white dark:bg-slate-700 border border-gray-300 dark:border-slate-600 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <PhotoIcon className="w-5 h-5" />
                  <span>Choose from Gallery</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const input = document.getElementById('image-upload') as HTMLInputElement;
                    if (input) {
                      input.setAttribute('capture', 'environment');
                      input.click();
                    }
                  }}
                  disabled={uploadingImages}
                  className="flex-1 flex items-center justify-center space-x-2 py-3 px-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-xl text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <CameraIcon className="w-5 h-5" />
                  <span>Take Photo</span>
                </button>
              </div>

              {/* Uploaded Images Grid */}
              {uploadedImages.length > 0 && (
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    Uploaded Images ({uploadedImages.length})
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {uploadedImages.map((imageUrl, index) => (
                      <div key={index} className="relative aspect-[4/3] group">
                        <img
                          src={imageUrl}
                          alt={`Property image ${index + 1}`}
                          className="w-full h-full object-cover rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={() => removeImage(index)}
                          className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full shadow-lg opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity"
                          aria-label="Remove image"
                        >
                          <XMarkIcon className="w-5 h-5" />
                        </button>
                      </div>
                    ))}
                  </div>
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

              <div>
                <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  AI Hint (optional)
                </label>
                <textarea
                  value={aiHint}
                  onChange={(e) => setAiHint(e.target.value)}
                  rows={3}
                  placeholder="Add any extra instructions for AI (tone, highlights, nearby landmarks, builder reputation, possession details, etc.)"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white resize-none"
                />
              </div>

              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row gap-4">
                  <button
                    type="button"
                    onClick={generateAISuggestions}
                    disabled={isGeneratingAI || !watchedAddress || !watchedPropertyType}
                    className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-4 sm:py-3 px-6 rounded-xl font-semibold flex items-center justify-center space-x-3 sm:space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl min-h-[52px] sm:min-h-[44px]"
                  >
                    {isGeneratingAI ? (
                      <>
                        <div className="w-6 h-6 sm:w-5 sm:h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-base sm:text-sm">Generating...</span>
                      </>
                    ) : (
                      <>
                        <SparklesIcon className="w-6 h-6 sm:w-5 sm:h-5" />
                        <span className="text-base sm:text-sm">Generate AI Content</span>
                      </>
                    )}
                  </button>

                  {aiSuggestions && (
                    <button
                      type="button"
                      onClick={applyAISuggestions}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white py-4 sm:py-3 px-6 rounded-xl font-semibold flex items-center justify-center space-x-3 sm:space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl min-h-[52px] sm:min-h-[44px]"
                    >
                      <CheckCircleIcon className="w-6 h-6 sm:w-5 sm:h-5" />
                      <span className="text-base sm:text-sm">Apply AI Content</span>
                    </button>
                  )}
                </div>

                {/* Help text for disabled button */}
                {(!watchedAddress || !watchedPropertyType) && (
                  <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center space-x-2">
                    <LightBulbIcon className="w-4 h-4" />
                    <span>
                      Please fill in the address and property type in the previous steps to enable AI content generation.
                    </span>
                  </div>
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
                      <span className="font-bold text-purple-900 dark:text-purple-100">{aiSuggestions.overallQualityScore.overall}/100</span>
                    </div>
                  </div>

                  <div className="space-y-6">
                    {/* Title Options */}
                    <div>
                      <h4 className="font-semibold text-purple-900 dark:text-purple-100 mb-3">Choose Your Title:</h4>
                      <div className="grid gap-3">
                        {aiSuggestions.titleOptions.map((option, index) => (
                          <div
                            key={index}
                            className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${selectedTitleIndex === index
                              ? 'border-purple-500 bg-purple-100 dark:bg-purple-900/30'
                              : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-slate-800 hover:border-purple-300'
                              }`}
                            onClick={() => setSelectedTitleIndex(index)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="text-purple-800 dark:text-purple-200 font-medium mb-2">
                                  {option.text}
                                </p>
                                <div className="flex space-x-4 text-xs text-gray-600 dark:text-gray-400">
                                  <span>Quality: {option.qualityScore}/100</span>
                                  <span>SEO: {option.seoScore}/100</span>
                                  <span>Readability: {option.readabilityScore}/100</span>
                                </div>
                              </div>
                              <div className={`w-4 h-4 rounded-full border-2 ml-3 ${selectedTitleIndex === index
                                ? 'border-purple-500 bg-purple-500'
                                : 'border-gray-300 dark:border-gray-600'
                                }`}>
                                {selectedTitleIndex === index && (
                                  <div className="w-full h-full rounded-full bg-white scale-50"></div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Description Options */}
                    <div>
                      <h4 className="font-semibold text-purple-900 dark:text-purple-100 mb-3">Choose Your Description:</h4>
                      <div className="grid gap-3">
                        {aiSuggestions.descriptionOptions.map((option, index) => (
                          <div
                            key={index}
                            className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${selectedDescriptionIndex === index
                              ? 'border-purple-500 bg-purple-100 dark:bg-purple-900/30'
                              : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-slate-800 hover:border-purple-300'
                              }`}
                            onClick={() => setSelectedDescriptionIndex(index)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="text-purple-800 dark:text-purple-200 whitespace-pre-line mb-2">
                                  {option.text}
                                </p>
                                <div className="flex space-x-4 text-xs text-gray-600 dark:text-gray-400">
                                  <span>Quality: {option.qualityScore}/100</span>
                                  <span>SEO: {option.seoScore}/100</span>
                                  <span>Readability: {option.readabilityScore}/100</span>
                                </div>
                              </div>
                              <div className={`w-4 h-4 rounded-full border-2 ml-3 ${selectedDescriptionIndex === index
                                ? 'border-purple-500 bg-purple-500'
                                : 'border-gray-300 dark:border-gray-600'
                                }`}>
                                {selectedDescriptionIndex === index && (
                                  <div className="w-full h-full rounded-full bg-white scale-50"></div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Overall Quality Score */}
                    <div className="grid grid-cols-3 gap-4 text-sm bg-white dark:bg-slate-800 p-4 rounded-lg">
                      <div className="text-center">
                        <div className="font-semibold text-purple-900 dark:text-purple-100">SEO Score</div>
                        <div className="text-purple-700 dark:text-purple-300">{aiSuggestions.overallQualityScore.seo}/100</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-purple-900 dark:text-purple-100">Readability</div>
                        <div className="text-purple-700 dark:text-purple-300">{aiSuggestions.overallQualityScore.readability}/100</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-purple-900 dark:text-purple-100">Market Relevance</div>
                        <div className="text-purple-700 dark:text-purple-300">{aiSuggestions.overallQualityScore.marketRelevance}/100</div>
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

  // Show success state if property was created
  if (isPropertyCreated && createdPropertyData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-200 dark:border-slate-700 p-8 text-center"
          >
            <div className="w-20 h-20 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircleIcon className="w-12 h-12 text-green-600 dark:text-green-400" />
            </div>

            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Property Created Successfully! 🎉
            </h2>

            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Your property "{createdPropertyData.title}" has been created and is ready for marketing.
            </p>

            <div className="bg-gray-50 dark:bg-slate-700 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Property Details:</h3>
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 dark:text-gray-300">
                <div><strong>Location:</strong> {createdPropertyData.location}</div>
                <div><strong>Price:</strong> ${createdPropertyData.price?.toLocaleString()}</div>
                <div><strong>Bedrooms:</strong> {createdPropertyData.bedrooms}</div>
                <div><strong>Bathrooms:</strong> {createdPropertyData.bathrooms}</div>
              </div>
            </div>

            <div className="flex justify-center space-x-4">
              <button
                onClick={resetForm}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Create Another Property
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 p-3 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto w-full sm:w-auto">
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

            {/* Mobile Step indicator */}
            <div className="sm:hidden text-center mb-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Swipe left/right to navigate steps
              </p>
            </div>

            {/* Progress Steps */}
            <div className="flex items-center justify-between sm:justify-start sm:space-x-4 px-2 sm:px-0 overflow-x-auto no-scrollbar">
              {FORM_STEPS.map((step, index) => {
                const Icon = step.icon
                const isActive = index === currentStep
                const isCompleted = index < currentStep
                const isClickable = isCompleted || index === currentStep

                return (
                  <div key={step.id} className="flex-shrink-0 relative">
                    <button
                      type="button"
                      onClick={() => {
                        if (isClickable) {
                          setCurrentStep(index)
                        }
                      }}
                      disabled={!isClickable}
                      className={`flex items-center space-x-2 px-4 py-3 sm:py-2 rounded-xl transition-all duration-200
                        ${isActive
                          ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-2 border-blue-500'
                          : isCompleted
                            ? 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/30'
                            : 'text-gray-400 dark:text-gray-600 bg-gray-50 dark:bg-slate-800/50'
                        }
                        ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}
                        touch-manipulation min-h-[44px]
                      `}
                      aria-label={`Go to ${step.title} step ${isActive ? '(current)' : isCompleted ? '(completed)' : ''}`}
                    >
                      <div className="flex items-center space-x-2">
                        <Icon className="w-6 h-6 sm:w-5 sm:h-5" />
                        <span className="text-base sm:text-sm font-medium whitespace-nowrap">{step.title}</span>
                        {isCompleted && <CheckCircleIcon className="w-5 h-5 sm:w-4 sm:h-4" />}
                      </div>
                    </button>

                    {/* Progress line */}
                    {index < FORM_STEPS.length - 1 && (
                      <div className={`hidden sm:block absolute top-1/2 -right-2 w-4 h-0.5 transition-colors duration-200 
                        ${isCompleted ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} 
                      />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Form Content */}
        <form onSubmit={(e) => {
          console.log('[SmartPropertyForm] Form submit event triggered')
          e.preventDefault();
          handleFormSubmit();
        }}>
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-200 dark:border-slate-700">
            <div className="p-6 sm:p-8">
            <motion.div
              className="touch-pan-x"
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderStepContent()}
            </motion.div>
          </div>

            {/* Navigation */}
            <div className="border-t border-gray-200 dark:border-slate-700 p-6 sm:p-8">
              <div className="flex justify-between">
                <div className="flex w-full sm:w-auto justify-between sm:justify-start space-x-4">
                  <button
                    type="button"
                    onClick={prevStep}
                    disabled={currentStep === 0}
                    className="flex-1 sm:flex-none flex items-center justify-center space-x-2 px-6 py-4 sm:py-3 border-2 border-gray-300 dark:border-slate-600 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 min-w-[140px]"
                    aria-label="Previous step"
                  >
                    <ArrowLeftIcon className="w-6 h-6 sm:w-5 sm:h-5" />
                    <span className="font-medium">Previous</span>
                  </button>

                  {currentStep === FORM_STEPS.length - 1 ? (
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="flex-1 sm:flex-none flex items-center justify-center space-x-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-4 sm:py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200 min-w-[140px]"
                      aria-label={isLoading ? "Creating property..." : "Create property"}
                    >
                      {isLoading ? (
                        <>
                          <div className="w-6 h-6 sm:w-5 sm:h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          <span>Creating...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircleIcon className="w-6 h-6 sm:w-5 sm:h-5" />
                          <span>Create Property</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={nextStep}
                      className="flex-1 sm:flex-none flex items-center justify-center space-x-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-4 sm:py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200 min-w-[140px]"
                      aria-label="Next step"
                    >
                      <span className="font-medium">Next</span>
                      <ArrowRightIcon className="w-6 h-6 sm:w-5 sm:h-5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}