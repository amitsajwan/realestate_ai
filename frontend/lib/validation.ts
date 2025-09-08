/**
 * Validation utilities for form inputs
 */

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

/**
 * Validate email format
 */
export const validateEmail = (email: string): ValidationResult => {
  if (!email) {
    return { isValid: false, error: 'Email is required' };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Please enter a valid email address' };
  }

  return { isValid: true };
};

/**
 * Validate password strength
 */
export const validatePasswordStrength = (password: string): ValidationResult => {
  if (!password) {
    return { isValid: false, error: 'Password is required' };
  }

  if (password.length < 8) {
    return { isValid: false, error: 'Password must be at least 8 characters long' };
  }

  if (!/[a-z]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one lowercase letter' };
  }

  if (!/[A-Z]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one uppercase letter' };
  }

  if (!/\d/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one number' };
  }

  if (!/[^\w\s]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one special character' };
  }

  return { isValid: true };
};

export const validatePassword = validatePasswordStrength;
/**
 * Validate phone number (international format)
 */
export const validatePhone = (phone: string): ValidationResult => {
  if (!phone) {
    return { isValid: true }; // Phone is optional
  }

  // Remove all non-digit characters for validation
  const cleanPhone = phone.replace(/\D/g, '');
  
  if (cleanPhone.length < 10) {
    return { isValid: false, error: 'Phone number must be at least 10 digits' };
  }

  if (cleanPhone.length > 15) {
    return { isValid: false, error: 'Phone number cannot exceed 15 digits' };
  }

  // Basic international phone format validation
  const phoneRegex = /^[+]?[1-9]\d{1,14}$|^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$/;
  if (!phoneRegex.test(phone.replace(/\s/g, ''))) {
    return { isValid: false, error: 'Please enter a valid phone number' };
  }

  return { isValid: true };
};

/**
 * Validate name (first name, last name)
 */
export const validateName = (name: string): ValidationResult => {
  if (!name) {
    return { isValid: false, error: 'Name is required' };
  }

  if (name.trim().length < 2) {
    return { isValid: false, error: 'Name must be at least 2 characters long' };
  }

  if (name.trim().length > 50) {
    return { isValid: false, error: 'Name cannot exceed 50 characters' };
  }

  // Only allow letters, spaces, hyphens, and apostrophes
  const nameRegex = /^[a-zA-Z\s\-']+$/;
  if (!nameRegex.test(name)) {
    return { isValid: false, error: 'Name can only contain letters, spaces, hyphens, and apostrophes' };
  }

  return { isValid: true };
};

/**
 * Validate confirm password
 */
export const validateConfirmPassword = (password: string, confirmPassword: string): ValidationResult => {
  if (!confirmPassword) {
    return { isValid: false, error: 'Please confirm your password' };
  }

  if (password !== confirmPassword) {
    return { isValid: false, error: 'Passwords do not match' };
  }

  return { isValid: true };
};

/**
 * Validate required field
 */
export const validateRequired = (value: string, fieldName: string): ValidationResult => {
  if (!value || value.trim().length === 0) {
    return { isValid: false, error: `${fieldName} is required` };
  }

  return { isValid: true };
};

/**
 * Sanitize input to prevent XSS
 */
export const sanitizeInput = (input: string): string => {
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
};

export const getFieldError = (errors: Record<string, any>, fieldName: string): string | undefined => {
  return errors[fieldName]?.message;
};

export const getFieldErrorClass = (errors: Record<string, any>, fieldName: string): string => {
  return errors[fieldName] ? 'border-red-500' : '';
};

import { z } from 'zod';

// Step-by-step validation schemas
export const stepSchemas = {
  address: z.object({
    address: z.string().min(1, 'Address is required'),
    location: z.string().min(1, 'Location is required')
  }),
  basic: z.object({
    propertyType: z.string().min(1, 'Property type is required'),
    bedrooms: z.coerce.number().min(1, 'At least 1 bedroom is required').refine(val => !isNaN(val) && val > 0, 'Bedrooms must be a valid number greater than 0'),
    bathrooms: z.coerce.number().min(1, 'At least 1 bathroom is required').refine(val => !isNaN(val) && val > 0, 'Bathrooms must be a valid number greater than 0'),
    area: z.coerce.number().min(1, 'Area is required').refine(val => !isNaN(val) && val > 0, 'Area must be a valid number greater than 0')
  }),
  pricing: z.object({
    price: z.coerce.number().min(1, 'Price is required').refine(val => !isNaN(val) && val > 0, 'Price must be a valid number greater than 0')
  }),
  images: z.object({
    images: z.array(z.string()).optional()
  }),
  description: z.object({
    title: z.string().min(1, 'Title is required'),
    description: z.string().min(1, 'Description is required')
  })
};

export const propertySchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(1, 'Description is required'),
  location: z.string().min(1, 'Location is required'),
  address: z.string().min(1, 'Address is required'),
  area: z.coerce.number().min(1, 'Area is required').refine(val => !isNaN(val) && val > 0, 'Area must be a valid number greater than 0'),
  price: z.coerce.number().min(1, 'Price is required').refine(val => !isNaN(val) && val > 0, 'Price must be a valid number greater than 0'),
  bedrooms: z.coerce.number().min(1, 'At least 1 bedroom is required').refine(val => !isNaN(val) && val > 0, 'Bedrooms must be a valid number greater than 0'),
  bathrooms: z.coerce.number().min(1, 'At least 1 bathroom is required').refine(val => !isNaN(val) && val > 0, 'Bathrooms must be a valid number greater than 0'),
  amenities: z.string().optional(),
  status: z.string().default('available'),
  propertyType: z.string().min(1, 'Property type is required'),
  images: z.array(z.string()).optional()
});

export type PropertyFormData = z.infer<typeof propertySchema>;
