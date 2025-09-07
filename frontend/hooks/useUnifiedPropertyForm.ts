/**
 * Unified Property Form Hook
 * ==========================
 * 
 * This hook provides unified form logic for all property form variants.
 * It consolidates the functionality from multiple existing form hooks.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import toast from 'react-hot-toast'

import { propertySchema, PropertyFormData } from '@/lib/validation'
import { apiService, APIError } from '@/lib/api'
import { useABTesting } from '@/utils/featureFlags'
import {
  FormVariant,
  FormConfig,
  FormState,
  FormValidation,
  AIIntegration,
  MarketInsight,
  FormAnalytics,
  UseFormOptions,
  UseFormReturn,
  AISuggestion,
  FormEvent
} from '@/types/PropertyFormTypes'

/**
 * Default form configuration
 */
const DEFAULT_CONFIG: FormConfig = {
  variant: 'simple',
  features: {
    ai: true,
    marketInsights: true,
    qualityScoring: true,
    multilanguage: true,
    autoSave: false,
    validation: 'onSubmit'
  },
  ui: {
    showProgress: true,
    showSections: true,
    showAI: true,
    showMarketInsights: true
  }
}

/**
 * Wizard steps configuration
 */
const WIZARD_STEPS = [
  {
    id: 'location',
    title: 'Location',
    description: 'Property address and location details',
    fields: ['address', 'location'] as (keyof PropertyFormData)[]
  },
  {
    id: 'details',
    title: 'Property Details',
    description: 'Basic property information',
    fields: ['propertyType', 'bedrooms', 'bathrooms', 'area'] as (keyof PropertyFormData)[]
  },
  {
    id: 'pricing',
    title: 'Pricing',
    description: 'Property price and financial details',
    fields: ['price'] as (keyof PropertyFormData)[]
  },
  {
    id: 'description',
    title: 'Description',
    description: 'Property description and amenities',
    fields: ['title', 'description', 'amenities'] as (keyof PropertyFormData)[]
  }
]

/**
 * Unified Property Form Hook
 */
export function useUnifiedPropertyForm(options: UseFormOptions): UseFormReturn {
  const {
    variant = 'simple',
    config = {},
    onSuccess,
    onError,
    onStepChange,
    onFieldChange,
    autoSave = false,
    autoSaveInterval = 5000
  } = options

  // Merge configuration
  const finalConfig: FormConfig = { ...DEFAULT_CONFIG, ...config, variant }

  // A/B testing
  const { variant: abVariant } = useABTesting()

  // Form setup
  const form = useForm<PropertyFormData>({
    resolver: zodResolver(propertySchema),
    mode: finalConfig.features.validation,
    defaultValues: {
      title: '',
      description: '',
      propertyType: '',
      bedrooms: 1,
      bathrooms: 1,
      area: 0,
      price: '',
      location: '',
      address: '',
      amenities: ''
    }
  })

  const { register, handleSubmit, setValue, watch, trigger, formState: rhfFormState, reset } = form

  // State management
  const [formState, setFormState] = useState<FormState>({
    isLoading: false,
    isSubmitting: false,
    isAILoading: false,
    currentStep: 0,
    totalSteps: variant === 'wizard' ? WIZARD_STEPS.length : 1,
    errors: {},
    touched: {},
    isValid: false,
    isDirty: false
  })

  const [aiIntegration, setAIIntegration] = useState<AIIntegration>({
    suggestions: null,
    marketInsights: null,
    isGenerating: false,
    lastGenerated: null,
    error: null
  })

  const [analytics, setAnalytics] = useState<FormAnalytics>({
    formLoadTime: 0,
    timeToFirstInteraction: 0,
    timeToComplete: 0,
    stepsCompleted: 0,
    fieldsModified: [],
    aiSuggestionsUsed: [],
    errorsEncountered: [],
    completionRate: 0
  })

  // Refs for tracking
  const formLoadTime = useRef<number>(Date.now())
  const firstInteractionTime = useRef<number | null>(null)
  const autoSaveTimeout = useRef<NodeJS.Timeout | null>(null)

  // Initialize form
  useEffect(() => {
    const loadTime = Date.now() - formLoadTime.current
    setAnalytics(prev => ({ ...prev, formLoadTime: loadTime }))
    
    // Defer to ensure trackEvent is initialized
    setTimeout(() => {
      trackEvent('form_loaded', {
        variant: abVariant,
        formVariant: variant,
        loadTime
      })
    }, 0)
  }, [variant, abVariant])

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave || !finalConfig.features.autoSave) return

    const subscription = watch((data, { name, type }) => {
      if (type === 'change' && name) {
        // Track field modification
        setAnalytics(prev => {
          const unique = Array.from(new Set<string>([...prev.fieldsModified, String(name)]))
          return { ...prev, fieldsModified: unique }
        })

        // Track first interaction
        if (!firstInteractionTime.current) {
          firstInteractionTime.current = Date.now()
          const interactionTime = firstInteractionTime.current - formLoadTime.current
          setAnalytics(prev => ({ ...prev, timeToFirstInteraction: interactionTime }))
        }

        // Clear existing timeout
        if (autoSaveTimeout.current) {
          clearTimeout(autoSaveTimeout.current)
        }

        // Set new timeout for auto-save
        autoSaveTimeout.current = setTimeout(() => {
          localStorage.setItem('property-form-draft', JSON.stringify(data))
          trackEvent('form_auto_saved', { variant: abVariant })
        }, autoSaveInterval)
      }
    })

    return () => {
      subscription.unsubscribe()
      if (autoSaveTimeout.current) {
        clearTimeout(autoSaveTimeout.current)
      }
    }
  }, [watch, autoSave, autoSaveInterval, abVariant, finalConfig.features.autoSave])

  // Load draft on mount
  useEffect(() => {
    if (autoSave && typeof window !== 'undefined') {
      const draft = localStorage.getItem('property-form-draft')
      if (draft) {
        try {
          const draftData = JSON.parse(draft) as Partial<PropertyFormData>
          (Object.entries(draftData) as [keyof PropertyFormData, any][]).forEach(([key, value]) => {
            setValue(key, value as any)
          })
          trackEvent('form_draft_loaded', { variant: abVariant })
        } catch (error) {
          console.error('Failed to load draft:', error)
        }
      }
    }
  }, [autoSave, setValue, abVariant])

  // Form validation
  const validate = useCallback(async (): Promise<boolean> => {
    const isValid = await trigger()
    setFormState(prev => ({ ...prev, isValid }))
    return isValid
  }, [trigger])

  const validateField = useCallback(async (name: keyof PropertyFormData): Promise<string | null> => {
    const result = await trigger(name)
    const errVal = formState.errors[name]
    const error = typeof errVal === 'string' ? errVal : (errVal as any)?.message
    return (error as string) || null
  }, [trigger, formState.errors])

  // Step navigation (for wizard variant)
  const nextStep = useCallback(async () => {
    if (variant !== 'wizard') return

    const currentStepData = WIZARD_STEPS[formState.currentStep]
    if (currentStepData) {
      const isValid = await trigger(currentStepData.fields)
      if (isValid && formState.currentStep < formState.totalSteps - 1) {
        const newStep = formState.currentStep + 1
        setFormState(prev => ({ ...prev, currentStep: newStep }))
        onStepChange?.(newStep)
        trackEvent('form_step_next', { 
          variant: abVariant, 
          step: newStep,
          totalSteps: formState.totalSteps
        })
      }
    }
  }, [variant, formState.currentStep, formState.totalSteps, trigger, onStepChange, abVariant])

  const prevStep = useCallback(() => {
    if (variant !== 'wizard' || formState.currentStep > 0) {
      const newStep = formState.currentStep - 1
      setFormState(prev => ({ ...prev, currentStep: newStep }))
      onStepChange?.(newStep)
      trackEvent('form_step_prev', { 
        variant: abVariant, 
        step: newStep,
        totalSteps: formState.totalSteps
      })
    }
  }, [variant, formState.currentStep, formState.totalSteps, onStepChange, abVariant])

  const goToStep = useCallback((step: number) => {
    if (variant === 'wizard' && step >= 0 && step < formState.totalSteps) {
      setFormState(prev => ({ ...prev, currentStep: step }))
      onStepChange?.(step)
      trackEvent('form_step_goto', { 
        variant: abVariant, 
        step,
        totalSteps: formState.totalSteps
      })
    }
  }, [variant, formState.totalSteps, onStepChange, abVariant])

  // AI integration
  const generateAISuggestions = useCallback(async () => {
    if (!finalConfig.features.ai) return

    setAIIntegration(prev => ({ ...prev, isGenerating: true, error: null }))
    
    try {
      const formData = watch()
      const response = await apiService.getAIPropertySuggestions({
        ...formData,
        variant: variant,
        config: finalConfig
      })

      if (response.success && response.data) {
        const suggestion: AISuggestion = {
          title: response.data.title || '',
          description: response.data.description || '',
          price: response.data.price || '',
          amenities: response.data.amenities || '',
          qualityScore: response.data.qualityScore,
          marketInsights: response.data.marketInsights
        }

        setAIIntegration(prev => ({
          ...prev,
          suggestions: suggestion,
          lastGenerated: new Date(),
          isGenerating: false
        }))

        trackEvent('ai_suggestions_generated', { 
          variant: abVariant,
          formVariant: variant,
          hasQualityScore: !!suggestion.qualityScore,
          hasMarketInsights: !!suggestion.marketInsights
        })

        toast.success('AI suggestions generated successfully!')
      }
    } catch (error) {
      const errorMessage = error instanceof APIError ? error.message : 'Failed to generate AI suggestions'
      setAIIntegration(prev => ({ 
        ...prev, 
        error: errorMessage, 
        isGenerating: false 
      }))
      
      trackEvent('ai_suggestions_error', { 
        variant: abVariant,
        error: errorMessage
      })
      
      toast.error(errorMessage)
    }
  }, [finalConfig.features.ai, watch, variant, finalConfig, abVariant])

  const applyAISuggestion = useCallback((suggestion: Partial<AISuggestion>) => {
    if (!suggestion) return

    const appliedFields: string[] = []

    if (suggestion.title) {
      setValue('title', suggestion.title)
      appliedFields.push('title')
    }
    if (suggestion.description) {
      setValue('description', suggestion.description)
      appliedFields.push('description')
    }
    if (suggestion.price) {
      setValue('price', suggestion.price)
      appliedFields.push('price')
    }
    if (suggestion.amenities) {
      setValue('amenities', suggestion.amenities)
      appliedFields.push('amenities')
    }

    setAnalytics(prev => ({
      ...prev,
      aiSuggestionsUsed: [...prev.aiSuggestionsUsed, ...appliedFields]
    }))

    trackEvent('ai_suggestion_applied', { 
      variant: abVariant,
      fields: appliedFields
    })

    toast.success(`Applied AI suggestions to ${appliedFields.length} field(s)`)
  }, [setValue, abVariant])

  // Market insights
  const generateMarketInsights = useCallback(async () => {
    if (!finalConfig.features.marketInsights) return

    try {
      const formData = watch()
      const response = await apiService.getMarketInsights({
        location: formData.location,
        propertyType: formData.propertyType,
        price: formData.price
      })

      if (response.success && response.data) {
        setAIIntegration(prev => ({
          ...prev,
          marketInsights: response.data
        }))

        trackEvent('market_insights_generated', { 
          variant: abVariant,
          location: formData.location,
          propertyType: formData.propertyType
        })
      }
    } catch (error) {
      console.error('Failed to generate market insights:', error)
      trackEvent('market_insights_error', { 
        variant: abVariant,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }, [finalConfig.features.marketInsights, watch, abVariant])

  // Form submission
  const submit = useCallback(async () => {
    setFormState(prev => ({ ...prev, isSubmitting: true }))
    
    const startTime = Date.now()
    
    try {
      const formData = watch()
      const isValid = await validate()
      
      if (!isValid) {
        throw new Error('Form validation failed')
      }

      const response = await apiService.createProperty({
        ...formData,
        metadata: {
          variant: variant,
          timestamp: new Date(),
          userId: 'current-user', // TODO: Get from auth context
          sessionId: 'current-session' // TODO: Get from session
        },
        options: {
          generateAI: finalConfig.features.ai,
          generateMarketInsights: finalConfig.features.marketInsights,
          language: 'en',
          template: 'standard'
        }
      })

      if (response.success) {
        const completionTime = Date.now() - startTime
        setAnalytics(prev => ({ 
          ...prev, 
          timeToComplete: completionTime,
          completionRate: 100
        }))

        // Clear auto-save draft
        if (autoSave && typeof window !== 'undefined') {
          localStorage.removeItem('property-form-draft')
        }

        trackEvent('form_submitted_success', { 
          variant: abVariant,
          formVariant: variant,
          completionTime,
          stepsCompleted: formState.totalSteps,
          aiUsed: aiIntegration.suggestions !== null,
          marketInsightsUsed: aiIntegration.marketInsights !== null
        })

        toast.success('Property created successfully!')
        onSuccess?.(formData)
      }
    } catch (error) {
      const errorMessage = error instanceof APIError ? error.message : 'Failed to create property'
      
      setAnalytics(prev => ({
        ...prev,
        errorsEncountered: [...prev.errorsEncountered, errorMessage]
      }))

      trackEvent('form_submitted_error', { 
        variant: abVariant,
        error: errorMessage
      })

      toast.error(errorMessage)
      onError?.(error instanceof Error ? error : new Error(errorMessage))
    } finally {
      setFormState(prev => ({ ...prev, isSubmitting: false }))
    }
  }, [
    watch, validate, variant, finalConfig, autoSave, abVariant,
    formState.totalSteps, aiIntegration.suggestions, aiIntegration.marketInsights,
    onSuccess, onError
  ])

  // Field value management
  const getValue = useCallback((name: keyof PropertyFormData) => {
    return watch(name)
  }, [watch])

  const setData = useCallback((data: Partial<PropertyFormData>) => {
    Object.entries(data).forEach(([key, value]) => {
      setValue(key as keyof PropertyFormData, value)
    })
  }, [setValue])

  // Analytics tracking
  const trackEvent = useCallback((event: string, properties?: Record<string, any>) => {
    const eventData: FormEvent = {
      type: event as any,
      timestamp: new Date(),
      data: properties || {},
      metadata: {
        variant: variant,
        userId: 'current-user', // TODO: Get from auth context
        sessionId: 'current-session' // TODO: Get from session
      }
    }

    // Send to analytics service
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', event, {
        custom_parameter_variant: abVariant,
        custom_parameter_form_variant: variant,
        ...properties
      })
    }

    // Log for debugging
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Form Analytics] ${event}`, eventData)
    }
  }, [variant, abVariant])

  // Return hook interface
  return {
    // Form data
    data: watch(),
    setData,
    reset,

    // Form state
    state: formState,
    validation: {
      isValid: formState.isValid,
      errors: formState.errors,
      warnings: {},
      touched: formState.touched,
      dirty: {}
    },

    // Form actions
    submit: handleSubmit(submit),
    nextStep,
    prevStep,
    goToStep,

    // AI integration
    ai: aiIntegration,
    generateAISuggestions,
    applyAISuggestion,

    // Market insights
    marketInsights: aiIntegration.marketInsights,
    generateMarketInsights,

    // Form fields
    register,
    setValue,
    getValue,
    watch,

    // Validation
    validate,
    validateField,

    // Analytics
    analytics,
    trackEvent
  }
}