import { z } from 'zod'
import { ValidationErrors } from '@/types/user'

// Base validation schemas
const emailSchema = z.string().email('Please enter a valid email address')
const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/\d/, 'Password must contain at least one number')
  .regex(/[^\w\s]/, 'Password must contain at least one special character')

const nameSchema = z.string()
  .min(2, 'Name must be at least 2 characters')
  .max(50, 'Name must be less than 50 characters')
  .regex(/^[a-zA-Z\s'-]+$/, 'Name can only contain letters, spaces, hyphens, and apostrophes')

const phoneSchema = z.string()
  .regex(/^[\+]?[1-9]\d{9,14}$/, 'Please enter a valid phone number')
  .optional()

// New: Allow empty-string for optional phone fields in forms where phone is not required
const optionalPhoneEmptySchema = z.union([
  z.string().regex(/^[\+]?[1-9]\d{9,14}$/, 'Please enter a valid phone number'),
  z.literal('')
]).optional()

const companyNameSchema = z.string()
  .min(2, 'Company name must be at least 2 characters')
  .max(100, 'Company name must be less than 100 characters')

const businessTypeSchema = z.string()
  .min(2, 'Business type must be at least 2 characters')
  .max(50, 'Business type must be less than 50 characters')

const targetAudienceSchema = z.string()
  .min(5, 'Target audience description must be at least 5 characters')
  .max(200, 'Target audience description must be less than 200 characters')

// Composite schemas for different forms
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required')
})

export const registerSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  firstName: nameSchema,
  lastName: nameSchema,
  phone: optionalPhoneEmptySchema,
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword']
})

export const profileSchema = z.object({
  firstName: nameSchema,
  lastName: nameSchema,
  email: emailSchema,
  companyName: companyNameSchema.optional(),
  businessType: businessTypeSchema.optional(),
  targetAudience: targetAudienceSchema.optional()
})

export const onboardingStepSchemas = {
  1: z.object({
    firstName: nameSchema,
    lastName: nameSchema,
    email: emailSchema
  }),
  2: z.object({
    companyName: companyNameSchema,
    businessType: businessTypeSchema
  }),
  3: z.object({
    targetAudience: targetAudienceSchema
  }),
  4: z.object({
    // Branding step - no required fields as it's AI-generated
  }),
  5: z.object({
    // Review step - no additional validation needed
  }),
  6: z.object({
    // Completion step - no additional validation needed
  })
}

export const brandingSuggestionSchema = z.object({
  companyName: companyNameSchema,
  businessType: businessTypeSchema,
  targetAudience: targetAudienceSchema
})

export const profileSettingsSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  phone: optionalPhoneEmptySchema,
  whatsapp: optionalPhoneEmptySchema,
  company: z.string().optional(),
  experience_years: z.string().optional(),
  specialization_areas: z.string().optional(),
  tagline: z.string().max(100, 'Tagline must be less than 100 characters').optional(),
  social_bio: z.string().max(200, 'Social bio must be less than 200 characters').optional(),
  about: z.string().max(500, 'About section must be less than 500 characters').optional(),
  address: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  pincode: z.string().regex(/^\d{6}$/, 'Pincode must be 6 digits').optional().or(z.literal('')),
  languages: z.array(z.string()).optional()
})

// Validation helper functions
export function validateField<T>(schema: z.ZodSchema<T>, value: T): { isValid: boolean; error?: string } {
  try {
    schema.parse(value)
    return { isValid: true }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const zodError = error as z.ZodError;
      if (zodError.issues && zodError.issues.length > 0) {
        return { isValid: false, error: zodError.issues[0]?.message || 'Invalid value' }
      }
    }
    return { isValid: false, error: 'Validation failed' }
  }
}

export function validateForm<T>(schema: z.ZodSchema<T>, data: T): { isValid: boolean; errors: ValidationErrors } {
  try {
    schema.parse(data)
    return { isValid: true, errors: {} }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const zodError = error as z.ZodError;
      const errors: ValidationErrors = {}
      zodError.issues.forEach((err) => {
        const path = err.path.join('.')
        errors[path] = err.message
      })
      return { isValid: false, errors }
    }
    return { isValid: false, errors: { general: 'Validation failed' } }
  }
}

export function validateOnboardingStep(step: number, data: any): { isValid: boolean; errors: ValidationErrors } {
  const schema = onboardingStepSchemas[step as keyof typeof onboardingStepSchemas]
  if (!schema) {
    return { isValid: true, errors: {} }
  }
  return validateForm(schema, data)
}

// Password strength calculator
export interface PasswordStrength {
  score: number
  feedback: string[]
  color: string
  label: string
}

export function calculatePasswordStrength(password: string): PasswordStrength {
  let score = 0
  const feedback: string[] = []

  const hasLength = password.length >= 8
  const hasLower = /[a-z]/.test(password)
  const hasUpper = /[A-Z]/.test(password)
  const hasNumber = /\d/.test(password)
  const hasSpecial = /[^\w\s]/.test(password)

  // Calculate score based on individual criteria
  if (hasLength) score += 1
  if (hasLower) score += 1
  if (hasUpper) score += 1
  if (hasNumber) score += 1
  if (hasSpecial) score += 1

  // Add feedback for missing criteria
  if (!hasLength) feedback.push('At least 8 characters')
  if (!hasLower) feedback.push('One lowercase letter')
  if (!hasUpper) feedback.push('One uppercase letter')
  if (!hasNumber) feedback.push('One number')
  if (!hasSpecial) feedback.push('One special character')

  const strengthMap = {
    0: { color: 'bg-gray-200', label: 'Very Weak' },
    1: { color: 'bg-red-500', label: 'Weak' },
    2: { color: 'bg-orange-500', label: 'Fair' },
    3: { color: 'bg-yellow-500', label: 'Good' },
    4: { color: 'bg-green-500', label: 'Strong' },
    5: { color: 'bg-green-600', label: 'Very Strong' }
  }

  return {
    score,
    feedback,
    ...strengthMap[score as keyof typeof strengthMap]
  }
}

// Real-time validation hook
export function useFormValidation<T>(schema: z.ZodSchema<T>) {
  return {
    validateField: (fieldName: string, value: any) => {
      try {
        const fieldSchema = (schema as any).shape[fieldName]
        if (fieldSchema) {
          fieldSchema.parse(value)
          return { isValid: true }
        }
        return { isValid: true }
      } catch (error) {
        if (error instanceof z.ZodError) {
          const zodError = error as z.ZodError;
          return { isValid: false, error: zodError.issues[0]?.message || 'Invalid value' }
        }
        return { isValid: false, error: 'Validation failed' }
      }
    },
    validateForm: (data: T) => validateForm(schema, data)
  }
}

// Export individual field validators for backward compatibility
export const validateEmail = (email: string) => validateField(emailSchema, email)
export const validatePassword = (password: string) => validateField(passwordSchema, password)
export const validateName = (name: string) => validateField(nameSchema, name)
export const validatePhone = (phone: string) => validateField(phoneSchema, phone)
export const validateCompanyName = (name: string) => validateField(companyNameSchema, name)
export const validateBusinessType = (type: string) => validateField(businessTypeSchema, type)
export const validateTargetAudience = (audience: string) => validateField(targetAudienceSchema, audience)

// Form validation utilities
export class FormValidator {
  private schema: z.ZodSchema<any>
  private errors: ValidationErrors = {}
  private touched: Record<string, boolean> = {}

  constructor(schema: z.ZodSchema<any>) {
    this.schema = schema
  }

  validateField(fieldName: string, value: any): boolean {
    // Check if the field exists in the schema
    if (!(this.schema as any).shape || !(this.schema as any).shape[fieldName]) {
      this.errors[fieldName] = 'Field not defined in schema'
      this.touched[fieldName] = true
      return false
    }
    
    try {
      const result = validateField((this.schema as any).shape[fieldName], value)
      
      if (result.isValid) {
        delete this.errors[fieldName]
      } else {
        this.errors[fieldName] = result.error || 'Invalid value'
      }
      
      this.touched[fieldName] = true
      return result.isValid
    } catch (error) {
      this.errors[fieldName] = 'Validation error occurred'
      this.touched[fieldName] = true
      return false
    }
  }

  validateAll(data: any): boolean {
    if (!data || typeof data !== 'object') {
      return false
    }
    
    const result = validateForm(this.schema, data)
    this.errors = result.errors
    
    // Mark all fields as touched
    Object.keys(data).forEach(key => {
      this.touched[key] = true
    })
    
    return result.isValid
  }

  getErrors(): ValidationErrors {
    return this.errors
  }

  getFieldError(fieldName: string): string | undefined {
    return this.touched[fieldName] ? this.errors[fieldName] : undefined
  }

  hasFieldError(fieldName: string): boolean {
    return !!this.errors[fieldName]
  }

  isFieldValid(fieldName: string): boolean {
    return this.touched[fieldName] && !this.errors[fieldName]
  }

  reset(): void {
    this.errors = {}
    this.touched = {}
  }

  touch(fieldName: string): void {
    this.touched[fieldName] = true
  }

  isTouched(fieldName: string): boolean {
    return !!this.touched[fieldName]
  }
}