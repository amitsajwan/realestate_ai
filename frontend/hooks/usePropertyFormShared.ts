'use client'

import { useState, useEffect, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { propertySchema, PropertyFormData } from '@/lib/validation'
import { apiService } from '@/lib/api'
import { toast } from 'react-hot-toast'
import { useRouter } from 'next/navigation'

export interface PropertyFormOptions {
  onSuccess?: (propertyId?: string) => void
  variant?: 'basic' | 'smart' | 'genai'
  enableAI?: boolean
  enableMultiStep?: boolean
}

export interface AIPropertySuggestion {
  title: string
  description: string
  price: string
  amenities: string
  marketInsights?: {
    averagePrice: number
    priceRange: [number, number]
    marketTrend: 'rising' | 'stable' | 'declining'
    competitorCount: number
    trendPercentage: number
  }
  qualityScore?: {
    overall: number
    seo: number
    readability: number
    marketRelevance: number
  }
}

export function usePropertyFormShared(options: PropertyFormOptions = {}) {
  const { onSuccess, variant = 'basic', enableAI = true, enableMultiStep = false } = options
  const router = useRouter()
  
  const [isLoading, setIsLoading] = useState(false)
  const [isAILoading, setIsAILoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [aiSuggestions, setAiSuggestions] = useState<AIPropertySuggestion | null>(null)
  const [agentProfile, setAgentProfile] = useState<any>(null)
  const [marketInsights, setMarketInsights] = useState<any>(null)

  const form = useForm<PropertyFormData>({
    resolver: zodResolver(propertySchema),
    mode: 'onSubmit',
    defaultValues: {
      propertyType: 'Apartment',
      bedrooms: 2,
      bathrooms: 2,
      area: 1000,
      price: '',
      title: '',
      description: '',
      address: '',
      location: '',
      amenities: ''
    }
  })

  const { handleSubmit, setValue, watch, trigger, formState: { errors } } = form

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

  // Get current user from auth context (placeholder for now)
  const getCurrentUserId = useCallback(() => {
    // TODO: Replace with actual auth context
    return '1'
  }, [])

  // Get city from address
  const getCityFromAddress = useCallback((address: string) => {
    // TODO: Implement proper address parsing
    const cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune']
    const foundCity = cities.find(city => address.toLowerCase().includes(city.toLowerCase()))
    return foundCity || 'Mumbai'
  }, [])

  // Transform form data to API format
  const transformFormData = useCallback((data: PropertyFormData) => {
    const priceValue = typeof data.price === 'string' 
      ? parseFloat(data.price.replace(/[₹,]/g, '')) 
      : data.price

    return {
      user_id: getCurrentUserId(),
      title: data.title,
      type: data.propertyType || 'Apartment',
      bedrooms: Number(data.bedrooms),
      bathrooms: Number(data.bathrooms),
      price: priceValue,
      price_unit: 'INR',
      city: getCityFromAddress(data.address),
      area: Number(data.area),
      address: data.address,
      description: data.description,
      amenities: data.amenities ? data.amenities.split(',').map(a => a.trim()) : []
    }
  }, [getCurrentUserId, getCityFromAddress])

  // Handle form submission
  const onSubmit = async (data: PropertyFormData) => {
    setIsLoading(true)
    try {
      const propertyData = transformFormData(data)
      const response = await apiService.createProperty(propertyData)
      
      toast.success('Property created successfully!')
      onSuccess?.(response.data?.id)
    } catch (error: any) {
      console.error('[PropertyForm] Property creation error:', error)
      toast.error(error.message || 'Failed to create property. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  // Generate AI suggestions
  const generateAISuggestions = async () => {
    setIsAILoading(true)
    try {
      const formData = watch()
      const response = await apiService.getAIPropertySuggestions({
        property_type: formData.propertyType || 'Apartment',
        location: formData.location || formData.address,
        budget: formData.price,
        requirements: 'Modern amenities',
        agent_profile: agentProfile,
        bedrooms: Number(formData.bedrooms),
        bathrooms: Number(formData.bathrooms),
        area: Number(formData.area)
      })

      if (response.success && response.data && response.data.length > 0) {
        const suggestion = response.data[0]
        const aiSuggestion: AIPropertySuggestion = {
          title: suggestion.title,
          description: suggestion.description,
          price: suggestion.price,
          amenities: suggestion.amenities,
          marketInsights: marketInsights,
          qualityScore: {
            overall: 87,
            seo: 92,
            readability: 85,
            marketRelevance: 84
          }
        }
        setAiSuggestions(aiSuggestion)
        toast.success('AI suggestions generated successfully!')
      }
    } catch (error) {
      console.error('[PropertyForm] AI generation error:', error)
      toast.error('Failed to generate AI content. Please try again.')
    } finally {
      setIsAILoading(false)
    }
  }

  // Apply AI suggestions to form
  const applyAISuggestions = useCallback(() => {
    if (!aiSuggestions) return
    
    setValue('title', aiSuggestions.title)
    setValue('description', aiSuggestions.description)
    setValue('price', aiSuggestions.price)
    setValue('amenities', aiSuggestions.amenities)
    
    toast.success('AI suggestions applied!')
  }, [aiSuggestions, setValue])

  // Multi-step form navigation
  const nextStep = useCallback(async () => {
    if (!enableMultiStep) return
    
    const fieldsToValidate = getFieldsForStep(currentStep)
    const isValid = await trigger(fieldsToValidate)
    
    if (isValid && currentStep < 3) {
      setCurrentStep(currentStep + 1)
    }
  }, [currentStep, enableMultiStep, trigger])

  const prevStep = useCallback(() => {
    if (!enableMultiStep) return
    
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }, [currentStep, enableMultiStep])

  const getFieldsForStep = (step: number): (keyof PropertyFormData)[] => {
    switch (step) {
      case 0: return ['address', 'location']
      case 1: return ['propertyType', 'bedrooms', 'bathrooms', 'area']
      case 2: return ['price']
      case 3: return ['title', 'description']
      default: return []
    }
  }

  return {
    form,
    errors,
    isLoading,
    isAILoading,
    currentStep,
    aiSuggestions,
    agentProfile,
    marketInsights,
    handleSubmit: handleSubmit(onSubmit),
    generateAISuggestions,
    applyAISuggestions,
    nextStep,
    prevStep,
    setCurrentStep,
    variant
  }
}