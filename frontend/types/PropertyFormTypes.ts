/**
 * Unified Property Form Types
 * ===========================
 * 
 * This module defines all TypeScript types and interfaces
 * for the unified property form system.
 */

import { PropertyFormData } from '@/lib/validation'

/**
 * Form variant types
 */
export type FormVariant = 'simple' | 'wizard' | 'ai-first'

/**
 * AI suggestion types
 */
export interface AISuggestion {
  title: string
  description: string
  price: string
  amenities: string
  qualityScore?: QualityScore
  marketInsights?: MarketInsight
}

/**
 * Quality score interface
 */
export interface QualityScore {
  overall: number
  seo: number
  readability: number
  marketRelevance: number
  uniqueness: number
}

/**
 * Market insight interface
 */
export interface MarketInsight {
  averagePrice: number
  priceRange: [number, number]
  marketTrend: 'rising' | 'stable' | 'declining'
  competitorCount: number
  trendPercentage: number
  locationScore?: number
  amenitiesScore?: number
}

/**
 * Form configuration interface
 */
export interface FormConfig {
  variant: FormVariant
  features: {
    ai: boolean
    marketInsights: boolean
    qualityScoring: boolean
    multilanguage: boolean
    autoSave: boolean
    validation: 'onBlur' | 'onChange' | 'onSubmit'
  }
  ui: {
    showProgress: boolean
    showSections: boolean
    showAI: boolean
    showMarketInsights: boolean
  }
}

/**
 * Form state interface
 */
export interface FormState {
  isLoading: boolean
  isSubmitting: boolean
  isAILoading: boolean
  currentStep: number
  totalSteps: number
  errors: Record<string, string>
  touched: Record<string, boolean>
  isValid: boolean
  isDirty: boolean
}

/**
 * AI integration interface
 */
export interface AIIntegration {
  suggestions: AISuggestion | null
  marketInsights: MarketInsight | null
  isGenerating: boolean
  lastGenerated: Date | null
  error: string | null
}

/**
 * Form section interface
 */
export interface FormSection {
  id: string
  title: string
  description: string
  icon: string
  fields: string[]
  required: boolean
  completed: boolean
  visible: boolean
}

/**
 * Wizard step interface
 */
export interface WizardStep {
  id: string
  title: string
  description: string
  icon: string
  fields: (keyof PropertyFormData)[]
  validation: (data: Partial<PropertyFormData>) => boolean
  nextStep?: string
  prevStep?: string
}

/**
 * Form field interface
 */
export interface FormField {
  name: keyof PropertyFormData
  label: string
  type: 'text' | 'number' | 'select' | 'textarea' | 'checkbox' | 'radio'
  required: boolean
  placeholder?: string
  helpText?: string
  options?: Array<{ value: string | number; label: string }>
  validation?: {
    min?: number
    max?: number
    pattern?: string
    custom?: (value: any) => string | null
  }
  ai?: {
    enabled: boolean
    suggestion: string | null
    confidence: number
  }
}

/**
 * Form submission interface
 */
export interface FormSubmission {
  data: PropertyFormData
  metadata: {
    variant: FormVariant
    timestamp: Date
    userId: string
    sessionId: string
    userAgent: string
    duration: number
    steps: number
    aiUsed: boolean
    marketInsightsUsed: boolean
  }
}

/**
 * Form analytics interface
 */
export interface FormAnalytics {
  formLoadTime: number
  timeToFirstInteraction: number
  timeToComplete: number
  stepsCompleted: number
  fieldsModified: string[]
  aiSuggestionsUsed: string[]
  errorsEncountered: string[]
  abandonmentPoint?: string
  completionRate: number
}

/**
 * Multilanguage interface
 */
export interface MultilanguageConfig {
  enabled: boolean
  defaultLanguage: string
  supportedLanguages: string[]
  currentLanguage: string
  translations: Record<string, Record<string, string>>
}

/**
 * Form validation interface
 */
export interface FormValidation {
  isValid: boolean
  errors: Record<string, string>
  warnings: Record<string, string>
  touched: Record<string, boolean>
  dirty: Record<string, boolean>
}

/**
 * Form hook options interface
 */
export interface UseFormOptions {
  variant: FormVariant
  config: Partial<FormConfig>
  onSuccess?: (data: PropertyFormData) => void
  onError?: (error: Error) => void
  onStepChange?: (step: number) => void
  onFieldChange?: (field: string, value: any) => void
  autoSave?: boolean
  autoSaveInterval?: number
}

/**
 * Form hook return interface
 */
export interface UseFormReturn {
  // Form data
  data: PropertyFormData
  setData: (data: Partial<PropertyFormData>) => void
  reset: () => void
  
  // Form state
  state: FormState
  validation: FormValidation
  
  // Form actions
  submit: () => Promise<void>
  nextStep: () => void
  prevStep: () => void
  goToStep: (step: number) => void
  
  // AI integration
  ai: AIIntegration
  generateAISuggestions: () => Promise<void>
  applyAISuggestion: (suggestion: Partial<AISuggestion>) => void
  
  // Market insights
  marketInsights: MarketInsight | null
  generateMarketInsights: () => Promise<void>
  
  // Form fields
  register: (name: keyof PropertyFormData) => any
  setValue: (name: keyof PropertyFormData, value: any) => void
  getValue: (name: keyof PropertyFormData) => any
  watch: (name?: keyof PropertyFormData) => any
  
  // Validation
  validate: () => boolean
  validateField: (name: keyof PropertyFormData) => string | null
  
  // Analytics
  analytics: FormAnalytics
  trackEvent: (event: string, properties?: Record<string, any>) => void
}

/**
 * Component props interfaces
 */
export interface UnifiedPropertyFormProps {
  variant?: FormVariant
  config?: Partial<FormConfig>
  onSuccess?: (data: PropertyFormData) => void
  onError?: (error: Error) => void
  className?: string
  initialData?: Partial<PropertyFormData>
  userId?: string
  sessionId?: string
}

export interface FormSectionProps {
  section: FormSection
  children: React.ReactNode
  isActive: boolean
  isCompleted: boolean
  onToggle?: () => void
}

export interface FormFieldProps {
  field: FormField
  value: any
  onChange: (value: any) => void
  error?: string
  touched?: boolean
  disabled?: boolean
}

export interface AIAssistantProps {
  onGenerate: () => Promise<void>
  suggestions: AISuggestion | null
  isLoading: boolean
  onApply: (suggestion: Partial<AISuggestion>) => void
  onDismiss: () => void
}

export interface MarketInsightsProps {
  insights: MarketInsight | null
  isLoading: boolean
  onGenerate: () => Promise<void>
  onApply: (insight: Partial<MarketInsight>) => void
}

export interface ProgressIndicatorProps {
  currentStep: number
  totalSteps: number
  steps: WizardStep[]
  onStepClick?: (step: number) => void
}

/**
 * API interfaces
 */
export interface PropertyCreateRequest {
  data: PropertyFormData
  metadata: {
    variant: FormVariant
    userId: string
    sessionId: string
    timestamp: Date
  }
  options: {
    generateAI: boolean
    generateMarketInsights: boolean
    language: string
    template: string
  }
}

export interface PropertyCreateResponse {
  success: boolean
  data: {
    id: string
    property: PropertyFormData
    aiContent?: string
    marketInsights?: MarketInsight
    qualityScore?: QualityScore
  }
  metadata: {
    processingTime: number
    aiGenerated: boolean
    marketInsightsGenerated: boolean
  }
}

/**
 * Error interfaces
 */
export interface FormError {
  code: string
  message: string
  field?: string
  details?: any
}

export interface APIError {
  status: number
  code: string
  message: string
  details?: any
}

/**
 * Event interfaces
 */
export interface FormEvent {
  type: 'load' | 'submit' | 'step_change' | 'field_change' | 'ai_generate' | 'error'
  timestamp: Date
  data: any
  metadata: {
    variant: FormVariant
    userId: string
    sessionId: string
  }
}

/**
 * Utility types
 */
export type FormFieldName = keyof PropertyFormData
export type FormStep = number
export type FormVariantConfig = Record<FormVariant, FormConfig>
export type AISuggestionType = 'title' | 'description' | 'price' | 'amenities' | 'all'
export type MarketInsightType = 'price' | 'location' | 'amenities' | 'competition' | 'all'