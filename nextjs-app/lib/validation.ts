// Form validation schemas using Zod for type-safe validation

import { z } from 'zod'

// Property validation schema
export const propertySchema = z.object({
  title: z.string()
    .min(3, 'Title must be at least 3 characters')
    .max(100, 'Title must be less than 100 characters'),
  price: z.string()
    .min(1, 'Price is required')
    .regex(/^₹?\d{1,3}(,\d{3})*$/, 'Please enter a valid price (e.g., ₹50,00,000)'),
  address: z.string()
    .min(10, 'Address must be at least 10 characters')
    .max(200, 'Address must be less than 200 characters'),
  bedrooms: z.string()
    .min(1, 'Please select number of bedrooms'),
  bathrooms: z.string()
    .min(1, 'Please select number of bathrooms'),
  area: z.string()
    .min(1, 'Area is required')
    .regex(/^\d+$/, 'Area must be a number'),
  description: z.string()
    .min(20, 'Description must be at least 20 characters')
    .max(1000, 'Description must be less than 1000 characters'),
  amenities: z.string()
    .min(1, 'Please add at least one amenity')
    .max(500, 'Amenities must be less than 500 characters'),
})

export type PropertyFormData = z.infer<typeof propertySchema>

// User registration validation schema
export const registrationSchema = z.object({
  firstName: z.string()
    .min(2, 'First name must be at least 2 characters')
    .max(50, 'First name must be less than 50 characters')
    .regex(/^[a-zA-Z\s]+$/, 'First name can only contain letters and spaces'),
  lastName: z.string()
    .min(2, 'Last name must be at least 2 characters')
    .max(50, 'Last name must be less than 50 characters')
    .regex(/^[a-zA-Z\s]+$/, 'Last name can only contain letters and spaces'),
  email: z.string()
    .email('Please enter a valid email address')
    .min(5, 'Email must be at least 5 characters')
    .max(100, 'Email must be less than 100 characters'),
  phone: z.string()
    .refine((val) => !val || /^[\+]?[1-9][\d]{0,15}$/.test(val), {
      message: 'Please enter a valid phone number'
    })
    .optional(),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password must be less than 100 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one uppercase letter, one lowercase letter, and one number'),
  confirmPassword: z.string()
    .min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

export type RegistrationFormData = z.infer<typeof registrationSchema>

// Login validation schema
export const loginSchema = z.object({
  email: z.string()
    .email('Please enter a valid email address'),
  password: z.string()
    .min(1, 'Password is required'),
})

export type LoginFormData = z.infer<typeof loginSchema>

// Onboarding validation schemas
export const onboardingStep1Schema = z.object({
  firstName: z.string()
    .min(2, 'First name must be at least 2 characters')
    .max(50, 'First name must be less than 50 characters'),
  lastName: z.string()
    .min(2, 'Last name must be at least 2 characters')
    .max(50, 'Last name must be less than 50 characters'),
  phone: z.string()
    .refine((val) => !val || /^[\+]?[1-9][\d]{0,15}$/.test(val), {
      message: 'Please enter a valid phone number'
    })
    .optional(),
})

export const onboardingStep2Schema = z.object({
  company: z.string()
    .min(2, 'Company name must be at least 2 characters')
    .max(100, 'Company name must be less than 100 characters'),
  position: z.string()
    .min(2, 'Position must be at least 2 characters')
    .max(100, 'Position must be less than 100 characters'),
  licenseNumber: z.string()
    .refine((val) => !val || /^[A-Z]{2}\d{6}$/.test(val), {
      message: 'License number must be in format: RE123456'
    })
    .optional(),
})

export const onboardingStep3Schema = z.object({
  aiStyle: z.enum(['Professional', 'Casual', 'Luxury', 'Family-friendly']),
  aiTone: z.enum(['Friendly', 'Formal', 'Enthusiastic', 'Calm']),
})

export const onboardingStep5Schema = z.object({
  termsAccepted: z.boolean()
    .refine((val) => val === true, {
      message: 'You must accept the Terms of Service'
    }),
  privacyAccepted: z.boolean()
    .refine((val) => val === true, {
      message: 'You must accept the Privacy Policy'
    }),
})

// Lead validation schema
export const leadSchema = z.object({
  name: z.string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must be less than 100 characters'),
  email: z.string()
    .email('Please enter a valid email address'),
  phone: z.string()
    .min(10, 'Phone number must be at least 10 digits')
    .regex(/^[\+]?[1-9][\d]{0,15}$/, 'Please enter a valid phone number'),
  source: z.string()
    .min(1, 'Please select a lead source'),
  notes: z.string()
    .max(500, 'Notes must be less than 500 characters')
    .optional(),
})

export type LeadFormData = z.infer<typeof leadSchema>

// AI Content generation validation schema
export const aiContentSchema = z.object({
  propertyType: z.string()
    .min(1, 'Please select a property type'),
  contentStyle: z.string()
    .min(1, 'Please select a content style'),
  prompt: z.string()
    .min(10, 'Prompt must be at least 10 characters')
    .max(500, 'Prompt must be less than 500 characters'),
})

export type AIContentFormData = z.infer<typeof aiContentSchema>

// Profile settings validation schema
export const profileSchema = z.object({
  firstName: z.string()
    .min(2, 'First name must be at least 2 characters')
    .max(50, 'First name must be less than 50 characters'),
  lastName: z.string()
    .min(2, 'Last name must be at least 2 characters')
    .max(50, 'Last name must be less than 50 characters'),
  email: z.string()
    .email('Please enter a valid email address'),
  phone: z.string()
    .refine((val) => !val || /^[\+]?[1-9][\d]{0,15}$/.test(val), {
      message: 'Please enter a valid phone number'
    })
    .optional(),
  company: z.string()
    .min(2, 'Company name must be at least 2 characters')
    .max(100, 'Company name must be less than 100 characters'),
  position: z.string()
    .min(2, 'Position must be at least 2 characters')
    .max(100, 'Position must be less than 100 characters'),
  licenseNumber: z.string()
    .refine((val) => !val || /^[A-Z]{2}\d{6}$/.test(val), {
      message: 'License number must be in format: RE123456'
    })
    .optional(),
})

export type ProfileFormData = z.infer<typeof profileSchema>

// Utility function to get field error message
export function getFieldError(errors: any, fieldName: string): string | undefined {
  return errors[fieldName]?.message
}

// Utility function to check if field has error
export function hasFieldError(errors: any, fieldName: string): boolean {
  return !!errors[fieldName]
}

// Utility function to get field error class
export function getFieldErrorClass(errors: any, fieldName: string): string {
  return hasFieldError(errors, fieldName) 
    ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
    : 'border-gray-300 focus:border-primary-500 focus:ring-primary-500'
}
