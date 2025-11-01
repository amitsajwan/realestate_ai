/**
 * Property Field Input Component
 * ==============================
 * 
 * A reusable form field component for property forms with consistent styling,
 * validation, and accessibility features.
 */

'use client'

import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import React, { forwardRef } from 'react';

type InputTypes = 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
type FieldTypes = InputTypes | 'textarea' | 'select';

interface PropertyFieldInputProps {
  name: string
  label: string
  type?: FieldTypes
  placeholder?: string
  required?: boolean
  error?: string
  touched?: boolean
  value?: any
  onChange?: (value: any) => void
  onBlur?: () => void
  options?: Array<{ value: string | number; label: string }>
  helpText?: string
  disabled?: boolean
  className?: string
  rows?: number
  min?: number
  max?: number
  step?: number
  pattern?: string
  autoComplete?: string
  'data-testid'?: string
}

const PropertyFieldInput = forwardRef<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement, PropertyFieldInputProps>(
  ({
    name,
    label,
    type = 'text',
    placeholder,
    required = false,
    error,
    touched,
    value,
    onChange,
    onBlur,
    options = [],
    helpText,
    disabled = false,
    className = '',
    rows = 3,
    min,
    max,
    step,
    pattern,
    autoComplete,
    'data-testid': testId,
    ...props
  }, ref) => {
    const fieldId = `field-${name}`
    const hasError = error && touched
    const isValid = !error && touched && value

    const baseClasses = `
      w-full px-4 py-3 border rounded-lg shadow-sm transition-all duration-200 
      text-base sm:text-sm font-normal
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
      disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
      touch-manipulation min-h-[44px] sm:min-h-[38px]
      ${hasError
        ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
        : isValid
          ? 'border-green-500 focus:ring-green-500 focus:border-green-500'
          : 'border-gray-300 hover:border-gray-400'
      }
      ${className}
    `.trim()

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      if (type === 'number') {
        const value = e.target.value
        // More robust number handling for mobile
        if (value === '' || value === null || value === undefined || value === '-') {
          onChange?.('')
        } else {
          const numValue = Number(value)
          if (!isNaN(numValue)) {
            // Only update if it's a valid number
            onChange?.(numValue)
          }
        }
      } else {
        onChange?.(e.target.value)
      }
    }

    const renderInput = () => {
      switch (type) {
        case 'textarea':
          return (
            <textarea
              ref={ref as React.Ref<HTMLTextAreaElement>}
              id={fieldId}
              name={name}
              value={value || ''}
              onChange={handleChange}
              onBlur={onBlur}
              placeholder={placeholder}
              disabled={disabled}
              rows={rows}
              className={`${baseClasses} min-h-[120px] sm:min-h-[100px]`}
              data-testid={testId}
              aria-describedby={helpText ? `${fieldId}-help` : undefined}
              aria-invalid={!!hasError}
              aria-required={required}
              enterKeyHint="next"
              {...props}
            />
          )

        case 'select':
          return (
            <select
              ref={ref as React.Ref<HTMLSelectElement>}
              id={fieldId}
              name={name}
              value={value || ''}
              onChange={handleChange}
              onBlur={onBlur}
              disabled={disabled}
              className={`${baseClasses} pr-10 appearance-none`}
              data-testid={testId}
              aria-describedby={helpText ? `${fieldId}-help` : undefined}
              aria-invalid={!!hasError}
              aria-required={required}
              {...props}
            >
              <option value="">{placeholder || 'Select an option'}</option>
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          )

        default:
          const getInputMode = () => {
            switch (type) {
              case 'tel':
                return 'tel'
              case 'number':
                return 'numeric'
              case 'email':
                return 'email'
              case 'url':
                return 'url'
              default:
                return 'text'
            }
          }

          const getKeyboardType = () => {
            switch (type) {
              case 'tel':
                return 'tel'
              case 'number':
                return 'decimal'
              case 'email':
                return 'email'
              case 'url':
                return 'url'
              default:
                return undefined
            }
          }

          return (
            <input
              ref={ref as React.Ref<HTMLInputElement>}
              id={fieldId}
              name={name}
              type={type}
              value={value || ''}
              onChange={handleChange}
              onBlur={onBlur}
              placeholder={placeholder}
              disabled={disabled}
              min={min}
              max={max}
              step={step}
              pattern={pattern}
              autoComplete={autoComplete || name}
              className={baseClasses}
              data-testid={testId}
              aria-describedby={helpText ? `${fieldId}-help` : undefined}
              aria-invalid={!!hasError}
              aria-required={required}
              inputMode={getInputMode()}
              enterKeyHint={type === 'number' ? 'next' : 'done'}
              {...(type === 'number' ? { 'data-type': 'numeric' } : {})}
              {...props}
            />
          )
      }
    }

    return (
      <div className="space-y-3">
        <label 
          htmlFor={fieldId} 
          className="block text-base sm:text-sm font-medium text-gray-700 dark:text-gray-300 min-h-[32px] flex items-center"
        >
          {label}
          {required && <span className="text-red-500 ml-1 text-lg" aria-label="required">*</span>}
        </label>

        <div className="relative">
          {renderInput()}

          {/* Status Icons */}
          {hasError && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none" aria-hidden="true">
              <ExclamationTriangleIcon className="h-6 w-6 sm:h-5 sm:w-5 text-red-500" />
            </div>
          )}
          {isValid && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none" aria-hidden="true">
              <CheckCircleIcon className="h-6 w-6 sm:h-5 sm:w-5 text-green-500" />
            </div>
          )}
        </div>

        {/* Help Text */}
        {helpText && !hasError && (
          <p id={`${fieldId}-help`} className="text-base sm:text-sm text-gray-500 dark:text-gray-400 min-h-[24px] px-1">
            {helpText}
          </p>
        )}

        {/* Error Message */}
        {hasError && (
          <p 
            className="text-base sm:text-sm text-red-600 flex items-center space-x-2 min-h-[24px] bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg" 
            role="alert"
          >
            <ExclamationTriangleIcon className="h-5 w-5 sm:h-4 sm:w-4 flex-shrink-0" />
            <span>{error}</span>
          </p>
        )}
      </div>
    )
  }
)

PropertyFieldInput.displayName = 'PropertyFieldInput'

export default PropertyFieldInput