/**
 * Refactored Property Form Hook
 * =============================
 * 
 * Simplified, focused hook that separates concerns:
 * - Form management
 * - AI integration
 * - Market insights
 * - Analytics
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import toast from 'react-hot-toast'

import { propertySchema, PropertyFormData } from '@/lib/validation'
import { apiService, APIError } from '@/lib/api'

// Types
interface FormState {
  isLoading: boolean
  isSubmitting: boolean
  isValid: boolean
  isDirty: boolean
}

interface AISuggestions {
  title?: string
  description?: string
  price?: string
  amenities?: string
  qualityScore?: number
}

interface MarketInsights {
  averagePrice: number
  priceRange: [number, number]
  marketTrend: 'rising' | 'stable' | 'declining'
  competitorCount: number
}

interface UsePropertyFormOptions {
  enableAI?: boolean
  enableMarketInsights?: boolean
  autoSave?: boolean
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
}

interface UsePropertyFormReturn {
  // Form methods
  register: ReturnType<typeof useForm<PropertyFormData>>['register']
  handleSubmit: ReturnType<typeof useForm<PropertyFormData>>['handleSubmit']
  setValue: ReturnType<typeof useForm<PropertyFormData>>['setValue']
  watch: ReturnType<typeof useForm<PropertyFormData>>['watch']
  formState: ReturnType<typeof useForm<PropertyFormData>>['formState']
  
  // Form state
  state: FormState
  
  // AI features
  aiSuggestions: AISuggestions | null
  isAILoading: boolean
  generateAISuggestions: () => Promise<void>
  applyAISuggestions: () => void
  
  // Market insights
  marketInsights: MarketInsights | null
  generateMarketInsights: () => Promise<void>
  
  // Form submission
  onSubmit: (data: PropertyFormData) => Promise<void>
}

export function usePropertyFormRefactored(options: UsePropertyFormOptions = {}): UsePropertyFormReturn {
  const {
    enableAI = false,
    enableMarketInsights = false,
    autoSave = false,
    onSuccess,
    onError
  } = options

  // Form setup
  const form = useForm<PropertyFormData>({
    resolver: zodResolver(propertySchema),
    mode: 'onBlur'
  })

  const { register, handleSubmit, setValue, watch, formState } = form

  // State management
  const [state, setState] = useState<FormState>({
    isLoading: false,
    isSubmitting: false,
    isValid: false,
    isDirty: false
  })

  const [aiSuggestions, setAiSuggestions] = useState<AISuggestions | null>(null)
  const [isAILoading, setIsAILoading] = useState(false)
  const [marketInsights, setMarketInsights] = useState<MarketInsights | null>(null)

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave) return

    const subscription = watch((data) => {
      const timeoutId = setTimeout(() => {
        localStorage.setItem('property-form-draft', JSON.stringify(data))
      }, 1000)
      
      return () => clearTimeout(timeoutId)
    })
    
    return subscription.unsubscribe
  }, [watch, autoSave])

  // Load draft on mount
  useEffect(() => {
    if (autoSave && typeof window !== 'undefined') {
      const draft = localStorage.getItem('property-form-draft')
      if (draft) {
        try {
          const draftData = JSON.parse(draft)
          Object.entries(draftData).forEach(([key, value]) => {
            setValue(key as keyof PropertyFormData, value)
          })
        } catch (error) {
          console.error('Failed to load draft:', error)
        }
      }
    }
  }, [autoSave, setValue])

  // Generate AI suggestions
  const generateAISuggestions = useCallback(async () => {
    if (!enableAI) return
    
    setIsAILoading(true)
    try {
      const formData = watch()
      const response = await apiService.getAIPropertySuggestions({
        address: formData.address,
        property_type: formData.propertyType,
        bedrooms: formData.bedrooms,
        bathrooms: formData.bathrooms,
        area: formData.area
      })

      if (response.success && response.data && response.data.length > 0) {
        const suggestion = response.data[0]
        setAiSuggestions({
          title: suggestion.title,
          description: suggestion.description,
          price: suggestion.price,
          amenities: suggestion.amenities,
          qualityScore: 85 // Mock score
        })
        toast.success('AI suggestions generated successfully!')
      }
    } catch (error) {
      console.error('Failed to generate AI suggestions:', error)
      toast.error('Failed to generate AI suggestions. Please try again.')
    } finally {
      setIsAILoading(false)
    }
  }, [enableAI, watch])

  // Apply AI suggestions
  const applyAISuggestions = useCallback(() => {
    if (!aiSuggestions) return
    
    const currentValues = watch()
    const fieldsToOverwrite = []
    
    // Check which fields have existing content
    if (currentValues.title?.trim()) fieldsToOverwrite.push('title')
    if (currentValues.description?.trim()) fieldsToOverwrite.push('description')
    if (currentValues.price) fieldsToOverwrite.push('price')
    if (currentValues.amenities?.trim()) fieldsToOverwrite.push('amenities')
    
    // Ask for confirmation if overwriting
    if (fieldsToOverwrite.length > 0) {
      const confirmMessage = `This will overwrite your existing content in: ${fieldsToOverwrite.join(', ')}. Are you sure?`
      if (!window.confirm(confirmMessage)) return
    }
    
    // Apply suggestions
    if (aiSuggestions.title) setValue('title', aiSuggestions.title)
    if (aiSuggestions.description) setValue('description', aiSuggestions.description)
    if (aiSuggestions.price) setValue('price', aiSuggestions.price)
    if (aiSuggestions.amenities) setValue('amenities', aiSuggestions.amenities)
    
    toast.success('AI suggestions applied!')
  }, [aiSuggestions, watch, setValue])

  // Generate market insights
  const generateMarketInsights = useCallback(async () => {
    if (!enableMarketInsights) return
    
    try {
      const formData = watch()
      // Mock implementation - replace with real API
      const insights: MarketInsights = {
        averagePrice: 3200000,
        priceRange: [2800000, 4200000],
        marketTrend: 'rising',
        competitorCount: 12
      }
      setMarketInsights(insights)
    } catch (error) {
      console.error('Failed to generate market insights:', error)
    }
  }, [enableMarketInsights, watch])

  // Form submission
  const onSubmit = useCallback(async (data: PropertyFormData) => {
    setState(prev => ({ ...prev, isSubmitting: true }))
    
    try {
      const propertyData = {
        user_id: '1', // TODO: Get from auth context
        title: data.title,
        type: data.propertyType || 'Apartment',
        bedrooms: Number(data.bedrooms),
        bathrooms: Number(data.bathrooms),
        price: typeof data.price === 'string' 
          ? parseFloat(data.price.replace(/[₹,]/g, '')) 
          : data.price,
        price_unit: 'INR',
        city: 'Mumbai', // TODO: Extract from address
        area: Number(data.area),
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
      const errorMessage = error instanceof APIError ? error.message : 'Failed to add property'
      toast.error(errorMessage)
      onError?.(error instanceof Error ? error : new Error(errorMessage))
    } finally {
      setState(prev => ({ ...prev, isSubmitting: false }))
    }
  }, [autoSave, onSuccess, onError])

  return {
    // Form methods
    register,
    handleSubmit,
    setValue,
    watch,
    formState,
    
    // Form state
    state,
    
    // AI features
    aiSuggestions,
    isAILoading,
    generateAISuggestions,
    applyAISuggestions,
    
    // Market insights
    marketInsights,
    generateMarketInsights,
    
    // Form submission
    onSubmit: handleSubmit(onSubmit)
  }
}