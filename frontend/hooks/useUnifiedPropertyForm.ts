/**
 * Unified Property Form Hook
 * ==========================
 * 
 * This hook provides unified form logic for all property form variants,
 * including AI integration, market insights, and analytics.
 */

import { useState, useEffect, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { propertySchema, PropertyFormData } from '@/lib/validation'
import { 
  FormVariant, 
  FormConfig, 
  FormState, 
  AIIntegration, 
  MarketInsight,
  FormAnalytics,
  UseFormOptions,
  UseFormReturn,
  AISuggestion
} from '@/types/PropertyFormTypes'
import { apiService } from '@/lib/api'
import { analytics, performanceMonitor } from '@/utils/analytics'
import { useABTesting } from '@/utils/featureFlags'
import toast from 'react-hot-toast'

const DEFAULT_CONFIG: FormConfig = {
  variant: 'simple',
  features: {
    ai: true,
    marketInsights: true,
    qualityScoring: true,
    multilanguage: true,
    autoSave: true,
    validation: 'onBlur'
  },
  ui: {
    showProgress: true,
    showSections: true,
    showAI: true,
    showMarketInsights: true
  }
}

export function useUnifiedPropertyForm(options: UseFormOptions): UseFormReturn {
  const {
    variant = 'simple',
    config = {},
    onSuccess,
    onError,
    onStepChange,
    onFieldChange,
    autoSave = true,
    autoSaveInterval = 30000
  } = options

  // Merge config with defaults
  const formConfig = { ...DEFAULT_CONFIG, ...config, variant }

  // A/B testing
  const { variant: abVariant, trackEvent } = useABTesting()

  // Form state
  const [formState, setFormState] = useState<FormState>({
    isLoading: false,
    isSubmitting: false,
    isAILoading: false,
    currentStep: 0,
    totalSteps: variant === 'wizard' ? 4 : 1,
    errors: {},
    touched: {},
    isValid: false,
    isDirty: false
  })

  // AI integration state
  const [aiIntegration, setAiIntegration] = useState<AIIntegration>({
    suggestions: null,
    marketInsights: null,
    isGenerating: false,
    lastGenerated: null,
    error: null
  })

  // Analytics state
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

  // React Hook Form
  const {
    register,
    handleSubmit,
    setValue,
    getValue,
    watch,
    reset,
    formState: { errors, touchedFields, dirtyFields, isValid }
  } = useForm<PropertyFormData>({
    resolver: zodResolver(propertySchema),
    mode: formConfig.features.validation
  })

  // Performance monitoring
  useEffect(() => {
    performanceMonitor.mark('form-load-start')
    const loadTime = performanceMonitor.measure('form-load', 'form-load-start')
    
    setAnalytics(prev => ({
      ...prev,
      formLoadTime: loadTime
    }))

    // Track form load event
    trackEvent('form_load', {
      variant: formConfig.variant,
      abVariant,
      loadTime
    })
  }, [])

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave || !formConfig.features.autoSave) return

    const interval = setInterval(() => {
      const currentData = watch()
      if (Object.keys(dirtyFields).length > 0) {
        // Auto-save to localStorage
        localStorage.setItem('property-form-draft', JSON.stringify(currentData))
        trackEvent('form_auto_save', { variant: formConfig.variant })
      }
    }, autoSaveInterval)

    return () => clearInterval(interval)
  }, [autoSave, autoSaveInterval, watch, dirtyFields, formConfig.variant, trackEvent])

  // Load draft data on mount
  useEffect(() => {
    const draftData = localStorage.getItem('property-form-draft')
    if (draftData) {
      try {
        const parsed = JSON.parse(draftData)
        Object.entries(parsed).forEach(([key, value]) => {
          setValue(key as keyof PropertyFormData, value)
        })
        trackEvent('form_draft_loaded', { variant: formConfig.variant })
      } catch (error) {
        console.error('Failed to load draft data:', error)
      }
    }
  }, [setValue, formConfig.variant, trackEvent])

  // Update form state when form changes
  useEffect(() => {
    setFormState(prev => ({
      ...prev,
      errors: errors,
      touched: touchedFields,
      isValid,
      isDirty: Object.keys(dirtyFields).length > 0
    }))
  }, [errors, touchedFields, isValid, dirtyFields])

  // Generate AI suggestions
  const generateAISuggestions = useCallback(async () => {
    if (!formConfig.features.ai) return

    setAiIntegration(prev => ({ ...prev, isGenerating: true, error: null }))
    performanceMonitor.mark('ai-generation-start')

    try {
      const currentData = watch()
      
      // Call AI service
      const response = await apiService.generateAISuggestions({
        propertyData: currentData,
        variant: formConfig.variant,
        language: 'en' // TODO: Get from user preferences
      })

      if (response.success && response.data) {
        const suggestions: AISuggestion = response.data
        
        setAiIntegration(prev => ({
          ...prev,
          suggestions,
          isGenerating: false,
          lastGenerated: new Date()
        }))

        // Track AI generation
        trackEvent('ai_suggestions_generated', {
          variant: formConfig.variant,
          suggestionsCount: Object.keys(suggestions).length
        })

        performanceMonitor.measure('ai-generation', 'ai-generation-start')
      }
    } catch (error) {
      console.error('AI generation failed:', error)
      setAiIntegration(prev => ({
        ...prev,
        isGenerating: false,
        error: 'Failed to generate AI suggestions'
      }))
      
      trackEvent('ai_generation_error', {
        variant: formConfig.variant,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }, [formConfig.features.ai, formConfig.variant, watch, trackEvent])

  // Generate market insights
  const generateMarketInsights = useCallback(async () => {
    if (!formConfig.features.marketInsights) return

    setAiIntegration(prev => ({ ...prev, isGenerating: true, error: null }))
    performanceMonitor.mark('market-insights-start')

    try {
      const currentData = watch()
      
      const response = await apiService.generateMarketInsights({
        propertyData: currentData,
        location: currentData.location
      })

      if (response.success && response.data) {
        const insights: MarketInsight = response.data
        
        setAiIntegration(prev => ({
          ...prev,
          marketInsights: insights,
          isGenerating: false
        }))

        trackEvent('market_insights_generated', {
          variant: formConfig.variant,
          location: currentData.location
        })

        performanceMonitor.measure('market-insights', 'market-insights-start')
      }
    } catch (error) {
      console.error('Market insights generation failed:', error)
      setAiIntegration(prev => ({
        ...prev,
        isGenerating: false,
        error: 'Failed to generate market insights'
      }))
      
      trackEvent('market_insights_error', {
        variant: formConfig.variant,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }, [formConfig.features.marketInsights, formConfig.variant, watch, trackEvent])

  // Apply AI suggestion
  const applyAISuggestion = useCallback((suggestion: Partial<AISuggestion>) => {
    if (!suggestion) return

    Object.entries(suggestion).forEach(([key, value]) => {
      if (key in propertySchema.shape && value) {
        setValue(key as keyof PropertyFormData, value as any)
      }
    })

    setAnalytics(prev => ({
      ...prev,
      aiSuggestionsUsed: [...prev.aiSuggestionsUsed, 'ai_suggestion_applied']
    }))

    trackEvent('ai_suggestion_applied', {
      variant: formConfig.variant,
      suggestionType: Object.keys(suggestion).join(',')
    })

    toast.success('AI suggestions applied successfully!')
  }, [setValue, formConfig.variant, trackEvent])

  // Form submission
  const submit = useCallback(async () => {
    setFormState(prev => ({ ...prev, isSubmitting: true }))
    performanceMonitor.mark('form-submit-start')

    try {
      const formData = watch()
      
      const response = await apiService.createProperty({
        ...formData,
        variant: formConfig.variant,
        aiGenerated: !!aiIntegration.suggestions,
        marketInsights: aiIntegration.marketInsights
      })

      if (response.success) {
        // Clear draft data
        localStorage.removeItem('property-form-draft')
        
        // Update analytics
        const submitTime = performanceMonitor.measure('form-submit', 'form-submit-start')
        setAnalytics(prev => ({
          ...prev,
          timeToComplete: submitTime,
          completionRate: 100
        }))

        // Track successful submission
        trackEvent('form_submit_success', {
          variant: formConfig.variant,
          completionTime: submitTime,
          aiUsed: !!aiIntegration.suggestions,
          marketInsightsUsed: !!aiIntegration.marketInsights
        })

        toast.success('Property created successfully!')
        onSuccess?.(formData)
      }
    } catch (error) {
      console.error('Form submission failed:', error)
      
      setAnalytics(prev => ({
        ...prev,
        errorsEncountered: [...prev.errorsEncountered, 'submit_error']
      }))

      trackEvent('form_submit_error', {
        variant: formConfig.variant,
        error: error instanceof Error ? error.message : 'Unknown error'
      })

      toast.error('Failed to create property. Please try again.')
      onError?.(error instanceof Error ? error : new Error('Submission failed'))
    } finally {
      setFormState(prev => ({ ...prev, isSubmitting: false }))
    }
  }, [watch, formConfig.variant, aiIntegration, onSuccess, onError, trackEvent])

  // Step navigation for wizard variant
  const nextStep = useCallback(() => {
    if (variant !== 'wizard') return
    
    const nextStepIndex = Math.min(formState.currentStep + 1, formState.totalSteps - 1)
    setFormState(prev => ({ ...prev, currentStep: nextStepIndex }))
    
    setAnalytics(prev => ({
      ...prev,
      stepsCompleted: Math.max(prev.stepsCompleted, nextStepIndex + 1)
    }))

    trackEvent('form_step_next', {
      variant: formConfig.variant,
      step: nextStepIndex
    })

    onStepChange?.(nextStepIndex)
  }, [variant, formState.currentStep, formState.totalSteps, formConfig.variant, onStepChange, trackEvent])

  const prevStep = useCallback(() => {
    if (variant !== 'wizard') return
    
    const prevStepIndex = Math.max(formState.currentStep - 1, 0)
    setFormState(prev => ({ ...prev, currentStep: prevStepIndex }))

    trackEvent('form_step_prev', {
      variant: formConfig.variant,
      step: prevStepIndex
    })

    onStepChange?.(prevStepIndex)
  }, [variant, formState.currentStep, formConfig.variant, onStepChange, trackEvent])

  const goToStep = useCallback((step: number) => {
    if (variant !== 'wizard') return
    
    const validStep = Math.max(0, Math.min(step, formState.totalSteps - 1))
    setFormState(prev => ({ ...prev, currentStep: validStep }))

    trackEvent('form_step_goto', {
      variant: formConfig.variant,
      step: validStep
    })

    onStepChange?.(validStep)
  }, [variant, formState.totalSteps, formConfig.variant, onStepChange, trackEvent])

  // Field change handler
  const handleFieldChange = useCallback((field: string, value: any) => {
    setValue(field as keyof PropertyFormData, value)
    
    // Track first interaction
    if (analytics.timeToFirstInteraction === 0) {
      const firstInteractionTime = performanceMonitor.measure('first-interaction', 'form-load-start')
      setAnalytics(prev => ({
        ...prev,
        timeToFirstInteraction: firstInteractionTime
      }))
    }

    // Track field modification
    setAnalytics(prev => ({
      ...prev,
      fieldsModified: prev.fieldsModified.includes(field) 
        ? prev.fieldsModified 
        : [...prev.fieldsModified, field]
    }))

    trackEvent('form_field_change', {
      variant: formConfig.variant,
      field,
      hasValue: !!value
    })

    onFieldChange?.(field, value)
  }, [setValue, analytics.timeToFirstInteraction, formConfig.variant, onFieldChange, trackEvent])

  // Validation
  const validate = useCallback(async (): Promise<boolean> => {
    try {
      const result = await handleSubmit(() => {})()
      return result
    } catch (error) {
      return false
    }
  }, [handleSubmit])

  const validateField = useCallback(async (name: keyof PropertyFormData): Promise<string | null> => {
    try {
      const result = await propertySchema.shape[name].safeParse(getValue(name))
      return result.success ? null : result.error.errors[0]?.message || 'Invalid value'
    } catch (error) {
      return 'Validation error'
    }
  }, [getValue])

  // Track events
  const trackEvent = useCallback((event: string, properties?: Record<string, any>) => {
    analytics.trackFormEvent({
      type: event as any,
      timestamp: new Date(),
      data: properties || {},
      metadata: {
        variant: formConfig.variant,
        userId: 'current-user', // TODO: Get from auth context
        sessionId: analytics.getSessionId()
      }
    })
  }, [formConfig.variant, analytics])

  return {
    // Form data
    data: watch(),
    setData: (data: Partial<PropertyFormData>) => {
      Object.entries(data).forEach(([key, value]) => {
        setValue(key as keyof PropertyFormData, value)
      })
    },
    reset,
    
    // Form state
    state: formState,
    validation: {
      isValid,
      errors,
      warnings: {}, // TODO: Implement warnings
      touched: touchedFields,
      dirty: dirtyFields
    },
    
    // Form actions
    submit,
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
    setValue: handleFieldChange,
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