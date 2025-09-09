export type FormVariant = 'smart' | 'unified' | 'genai' | 'simple' | 'wizard' | 'ai-first'

export interface FormStep {
  id: string
  title: string
  icon: any
}

export interface FormField {
  name: string
  label: string
  type: 'text' | 'number' | 'select' | 'textarea' | 'checkbox' | 'file'
  required?: boolean
  options?: string[]
  placeholder?: string
  validation?: {
    min?: number
    max?: number
    pattern?: string
    message?: string
  }
}

export interface FormFieldProps {
  name: string
  label: string
  type: 'text' | 'number' | 'select' | 'textarea' | 'checkbox' | 'file'
  required?: boolean
  options?: string[]
  placeholder?: string
  value?: any
  onChange?: (value: any) => void
  error?: string
  validation?: {
    min?: number
    max?: number
    pattern?: string
    message?: string
  }
}

export interface FormSection {
  id: string
  title: string
  description?: string
  fields: FormField[]
}

export interface FormEvent {
  type: string
  timestamp: Date
  data: any
  metadata?: {
    variant?: string
    userId?: string
    sessionId?: string
  }
}

export interface FormAnalytics {
  formId: string
  events: FormEvent[]
  completionRate: number
  averageTime: number
  errorRate: number
  formLoadTime?: number
  timeToFirstInteraction?: number
  timeToComplete?: number
  stepsCompleted?: number
  totalSteps?: number
  errors?: number
  fieldInteractions?: number
  fieldsModified?: string[]
  aiSuggestionsUsed?: string[]
  errorsEncountered?: string[]
}