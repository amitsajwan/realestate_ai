'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import toast from 'react-hot-toast'
import { propertySchema, PropertyFormData } from '@/lib/validation'
import { apiService, APIError } from '@/lib/api'

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
  marketInsights?: MarketInsight
  qualityScore?: {
    overall: number
    seo: number
    readability: number
    marketRelevance: number
  }
}

interface UsePropertyFormOptions {
  onSuccess?: (data?: any) => void
  enableAI?: boolean
  enableMarketInsights?: boolean
  enableQualityScoring?: boolean
  autoSave?: boolean
  mode?: 'onBlur' | 'onChange' | 'onSubmit'
}

interface UsePropertyFormReturn {
  // Form methods
  register: ReturnType<typeof useForm<PropertyFormData>>['register']
  handleSubmit: ReturnType<typeof useForm<PropertyFormData>>['handleSubmit']
  setValue: ReturnType<typeof useForm<PropertyFormData>>['setValue']
  watch: ReturnType<typeof useForm<PropertyFormData>>['watch']
  trigger: ReturnType<typeof useForm<PropertyFormData>>['trigger']
  formState: ReturnType<typeof useForm<PropertyFormData>>['formState']
  
  // Form state
  isLoading: boolean
  isSubmitting: boolean
  
  // AI features
  isAILoading: boolean
  aiSuggestions: AIPropertySuggestion | null
  generateAISuggestions: () => Promise<void>
  applyAISuggestions: () => void
  autoFillWithAI: () => Promise<void>
  applyFieldSuggestion: (fieldName: keyof PropertyFormData, suggestedValue: any) => boolean
  
  // Market insights
  marketInsights: MarketInsight | null
  generateMarketInsights: () => Promise<void>
  
  // Agent profile
  agentProfile: any
  
  // Form submission
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>
}

export function usePropertyForm(options: UsePropertyFormOptions = {}): UsePropertyFormReturn {
  const {
    onSuccess,
    enableAI = false,
    enableMarketInsights = false,
    enableQualityScoring = false,
    autoSave = false,
    mode = 'onBlur'
  } = options

  // Form setup
  const form = useForm<PropertyFormData>({
    resolver: zodResolver(propertySchema),
    mode
  })

  const { register, handleSubmit, setValue, watch, trigger, formState } = form

  // State management
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isAILoading, setIsAILoading] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<AIPropertySuggestion | null>(null)
  const [marketInsights, setMarketInsights] = useState<MarketInsight | null>(null)
  const [agentProfile, setAgentProfile] = useState<any>(null)

  // Watch form values for auto-insights
  const watchedAddress = watch('address')
  const watchedPropertyType = watch('propertyType')
  const watchedPrice = watch('price')

  // Fetch agent profile on mount
  useEffect(() => {
    const fetchAgentProfile = async () => {
      try {
        const response = await apiService.getAgentProfile()
        if (response.success && response.data) {
          setAgentProfile(response.data)
        }
      } catch (error) {
        console.error('Failed to fetch agent profile:', error)
      }
    }
    
    fetchAgentProfile()
  }, [])

  // Auto-generate market insights when key fields change
  useEffect(() => {
    if (enableMarketInsights && watchedAddress && watchedPropertyType) {
      generateMarketInsights()
    }
  }, [watchedAddress, watchedPropertyType, enableMarketInsights])

  // Auto-save functionality
  useEffect(() => {
    if (autoSave) {
      const subscription = watch((data) => {
        // Debounced auto-save logic
        const timeoutId = setTimeout(() => {
          localStorage.setItem('property-form-draft', JSON.stringify(data))
        }, 1000)
        
        return () => clearTimeout(timeoutId)
      })
      
      return subscription.unsubscribe
    }
  }, [watch, autoSave])

  // Generate market insights
  const generateMarketInsights = async () => {
    if (!enableMarketInsights) return
    
    try {
      // Mock implementation - replace with real API
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

  // Generate AI suggestions
  const generateAISuggestions = async () => {
    if (!enableAI) return
    
    setIsAILoading(true)
    try {
      const formData = watch()
      const response = await apiService.getAIPropertySuggestions({
        address: formData.address,
        property_type: formData.propertyType,
        bedrooms: formData.bedrooms,
        bathrooms: formData.bathrooms,
        area: formData.area,
        agent_profile: agentProfile
      })

      if (response.success && response.data && response.data.length > 0) {
        const suggestion = response.data[0]
        const aiSuggestion: AIPropertySuggestion = {
          title: suggestion.title,
          description: suggestion.description,
          price: suggestion.price,
          amenities: suggestion.amenities,
          marketInsights: enableMarketInsights ? marketInsights || undefined : undefined,
          qualityScore: enableQualityScoring ? {
            overall: 87,
            seo: 92,
            readability: 85,
            marketRelevance: 84
          } : undefined
        }
        
        setAiSuggestions(aiSuggestion)
        toast.success('AI suggestions generated successfully!')
      } else {
        throw new Error('No suggestions received')
      }
    } catch (error) {
      console.error('Failed to generate AI suggestions:', error)
      if (error instanceof APIError) {
        toast.error(`Failed to generate AI suggestions: ${error.message}`)
      } else {
        toast.error('Failed to generate AI suggestions. Please try again.')
      }
    } finally {
      setIsAILoading(false)
    }
  }

  // Apply AI suggestions with user confirmation for existing content
  const applyAISuggestions = () => {
    if (!aiSuggestions) return
    
    const currentValues = watch()
    const fieldsToOverwrite = []
    
    // Check which fields have existing content
    if (currentValues.title?.trim()) fieldsToOverwrite.push('title')
    if (currentValues.description?.trim()) fieldsToOverwrite.push('description')
    if (currentValues.price) fieldsToOverwrite.push('price')
    if (currentValues.amenities?.trim()) fieldsToOverwrite.push('amenities')
    
    // If there are fields with content, ask for confirmation
    if (fieldsToOverwrite.length > 0) {
      const confirmMessage = `This will overwrite your existing content in: ${fieldsToOverwrite.join(', ')}. Are you sure you want to continue?`
      
      if (!window.confirm(confirmMessage)) {
        return
      }
    }
    
    // Apply suggestions
    setValue('title', aiSuggestions.title)
    setValue('description', aiSuggestions.description)
    setValue('price', aiSuggestions.price)
    setValue('amenities', aiSuggestions.amenities)
    
    const message = fieldsToOverwrite.length > 0 
      ? `AI suggestions applied! Overwrote ${fieldsToOverwrite.length} field(s).`
      : 'AI suggestions applied to form!'
    
    toast.success(message)
  }

  // Smart AI auto-fill that preserves user inputs
  const autoFillWithAI = async () => {
    setIsAILoading(true)
    try {
      // Get current form values to understand what user has already entered
      const currentValues = watch()
      
      // Build context from existing user inputs
      const context = {
        property_type: currentValues.propertyType || 'Apartment',
        location: currentValues.address || currentValues.location || 'City Center',
        bedrooms: currentValues.bedrooms,
        bathrooms: currentValues.bathrooms,
        area: currentValues.area,
        existing_title: currentValues.title,
        existing_description: currentValues.description,
        budget: currentValues.price ? `₹${currentValues.price}` : '₹75,00,000',
        requirements: 'Modern amenities',
        agent_profile: agentProfile
      }

      const response = await apiService.getAIPropertySuggestions(context)

      if (response.success && response.data && response.data.length > 0) {
        const suggestion = response.data[0]
        let filledFields = []
        
        // Only fill empty fields, preserve user inputs
        if (!currentValues.title?.trim()) {
          setValue('title', suggestion.title)
          filledFields.push('title')
        }
        
        if (!currentValues.price) {
          setValue('price', suggestion.price)
          filledFields.push('price')
        }
        
        if (!currentValues.address?.trim()) {
          setValue('address', '123 Main Street, City Center')
          filledFields.push('address')
        }
        
        if (!currentValues.description?.trim()) {
          setValue('description', suggestion.description)
          filledFields.push('description')
        }
        
        if (!currentValues.amenities?.trim()) {
          setValue('amenities', suggestion.amenities)
          filledFields.push('amenities')
        }
        
        if (filledFields.length > 0) {
          toast.success(`AI filled ${filledFields.length} empty field(s): ${filledFields.join(', ')}`)
        } else {
          toast.success('All fields already have content. Use "Generate Suggestions" to get AI recommendations.')
        }
      } else {
        throw new Error('No suggestions received')
      }
    } catch (error) {
      console.error('AI Auto-fill error:', error)
      if (error instanceof APIError) {
        toast.error(`Failed to generate AI content: ${error.message}`)
      } else {
        toast.error('Failed to generate AI content. Please try again.')
      }
    } finally {
      setIsAILoading(false)
    }
  }

  // Form submission
  const onSubmit = async (data: PropertyFormData) => {
    setIsSubmitting(true)
    setIsLoading(true)
    
    try {
      // Transform form data to match backend Property interface
      const propertyData = {
        user_id: '1', // TODO: Get from auth context
        title: data.title,
        type: data.propertyType || 'Apartment',
        bedrooms: data.bedrooms,
        bathrooms: data.bathrooms,
        price: typeof data.price === 'string' 
          ? parseFloat(data.price.replace(/[₹,]/g, '')) 
          : data.price,
        price_unit: 'INR',
        city: 'Mumbai', // TODO: Extract from address
        area: data.area,
        address: data.address,
        description: data.description,
        amenities: data.amenities ? data.amenities.split(',').map(a => a.trim()) : []
      }

      const response = await apiService.createProperty(propertyData)
      
      // Clear auto-save draft on successful submission
      if (autoSave) {
        localStorage.removeItem('property-form-draft')
      }
      
      toast.success('Property added successfully!')
      onSuccess?.(response)
    } catch (error) {
      console.error('Property creation error:', error)
      if (error instanceof APIError) {
        toast.error(`Failed to add property: ${error.message}`)
      } else {
        toast.error('Failed to add property. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
      setIsLoading(false)
    }
  }

  // Smart field suggestion - apply AI suggestion to specific field with user choice
  const applyFieldSuggestion = (fieldName: keyof PropertyFormData, suggestedValue: any) => {
    const currentValue = watch(fieldName)
    
    if (currentValue && String(currentValue).trim()) {
      const confirmMessage = `Replace "${currentValue}" with AI suggestion "${suggestedValue}"?`
      if (!window.confirm(confirmMessage)) {
        return false
      }
    }
    
    setValue(fieldName, suggestedValue)
    toast.success(`Updated ${fieldName} with AI suggestion`)
    return true
  }

  return {
    // Form methods
    register,
    handleSubmit,
    setValue,
    watch,
    trigger,
    formState,
    
    // Form state
    isLoading,
    isSubmitting,
    
    // AI features
    isAILoading,
    aiSuggestions,
    generateAISuggestions,
    applyAISuggestions,
    autoFillWithAI,
    applyFieldSuggestion,
    
    // Market insights
    marketInsights,
    generateMarketInsights,
    
    // Agent profile
    agentProfile,
    
    // Form submission
    onSubmit: handleSubmit(onSubmit)
  }
}