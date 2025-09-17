/**
 * Validation System
 * =================
 * Centralized validation utilities for forms and data
 */

import { ValidationError } from '../errors';

export interface ValidationRule<T = any> {
  validate: (value: T) => boolean | string;
  message: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

export class Validator<T = any> {
  private rules: Record<string, ValidationRule<T>[]> = {};

  addRule(field: string, rule: ValidationRule<T>) {
    if (!this.rules[field]) {
      this.rules[field] = [];
    }
    this.rules[field].push(rule);
    return this;
  }

  validate(data: Record<string, T>): ValidationResult {
    const errors: Record<string, string> = {};

    for (const [field, value] of Object.entries(data)) {
      const fieldRules = this.rules[field] || [];
      
      for (const rule of fieldRules) {
        const result = rule.validate(value);
        if (result !== true) {
          errors[field] = typeof result === 'string' ? result : rule.message;
          break; // Stop at first error for each field
        }
      }
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  }
}

// Common validation rules
export const commonRules = {
  required: <T>(message: string = 'This field is required'): ValidationRule<T> => ({
    validate: (value: T) => {
      if (value === null || value === undefined) return false;
      if (typeof value === 'string' && value.trim() === '') return false;
      if (Array.isArray(value) && value.length === 0) return false;
      return true;
    },
    message
  }),

  email: (message: string = 'Please enter a valid email address'): ValidationRule<string> => ({
    validate: (value: string) => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value);
    },
    message
  }),

  minLength: (min: number, message?: string): ValidationRule<string> => ({
    validate: (value: string) => value.length >= min,
    message: message || `Must be at least ${min} characters long`
  }),

  maxLength: (max: number, message?: string): ValidationRule<string> => ({
    validate: (value: string) => value.length <= max,
    message: message || `Must be no more than ${max} characters long`
  }),

  min: (min: number, message?: string): ValidationRule<number> => ({
    validate: (value: number) => value >= min,
    message: message || `Must be at least ${min}`
  }),

  max: (max: number, message?: string): ValidationRule<number> => ({
    validate: (value: number) => value <= max,
    message: message || `Must be no more than ${max}`
  }),

  pattern: (regex: RegExp, message: string): ValidationRule<string> => ({
    validate: (value: string) => regex.test(value),
    message
  }),

  phone: (message: string = 'Please enter a valid phone number'): ValidationRule<string> => ({
    validate: (value: string) => {
      const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
      return phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''));
    },
    message
  }),

  url: (message: string = 'Please enter a valid URL'): ValidationRule<string> => ({
    validate: (value: string) => {
      try {
        new URL(value);
        return true;
      } catch {
        return false;
      }
    },
    message
  }),

  positive: (message: string = 'Must be a positive number'): ValidationRule<number> => ({
    validate: (value: number) => value > 0,
    message
  }),

  integer: (message: string = 'Must be a whole number'): ValidationRule<number> => ({
    validate: (value: number) => Number.isInteger(value),
    message
  })
};

// Form validation helpers
export function validateForm<T extends Record<string, any>>(
  data: T,
  rules: Record<string, ValidationRule<any>[]>
): ValidationResult {
  const validator = new Validator();
  
  for (const [field, fieldRules] of Object.entries(rules)) {
    for (const rule of fieldRules) {
      validator.addRule(field, rule);
    }
  }
  
  return validator.validate(data);
}

// Async validation support
export async function validateAsync<T extends Record<string, any>>(
  data: T,
  asyncRules: Record<string, (value: any) => Promise<boolean | string>>
): Promise<ValidationResult> {
  const errors: Record<string, string> = {};
  
  for (const [field, value] of Object.entries(data)) {
    const asyncRule = asyncRules[field];
    if (asyncRule) {
      try {
        const result = await asyncRule(value);
        if (result !== true) {
          errors[field] = typeof result === 'string' ? result : 'Validation failed';
        }
      } catch (error) {
        errors[field] = 'Validation error occurred';
      }
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

// Validation error formatter
export function formatValidationErrors(errors: Record<string, string>): string {
  return Object.entries(errors)
    .map(([field, message]) => `${field}: ${message}`)
    .join(', ');
}