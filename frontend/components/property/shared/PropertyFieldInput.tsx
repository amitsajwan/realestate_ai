/**
 * Property Field Input Component
 * ==============================
 * 
 * A reusable form field component for property forms with consistent styling,
 * validation, and accessibility features.
 */

'use client'

import React, { forwardRef } from 'react'
import { ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline'
import { FormFieldProps } from '@/types/PropertyFormTypes'

interface PropertyFieldInputProps {
  name: string
  label: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'textarea' | 'select'
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
      w-full px-3 py-2 border rounded-md shadow-sm transition-colors duration-200
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
      disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
      ${hasError 
        ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
        : isValid 
          ? 'border-green-500 focus:ring-green-500 focus:border-green-500'
          : 'border-gray-300 hover:border-gray-400'
      }
      ${className}
    `.trim()

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const newValue = type === 'number' ? Number(e.target.value) : e.target.value
      onChange?.(newValue)
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
              className={baseClasses}
              data-testid={testId}
              aria-describedby={helpText ? `${fieldId}-help` : undefined}
              aria-invalid={hasError}
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
              className={baseClasses}
              data-testid={testId}
              aria-describedby={helpText ? `${fieldId}-help` : undefined}
              aria-invalid={hasError}
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
              autoComplete={autoComplete}
              className={baseClasses}
              data-testid={testId}
              aria-describedby={helpText ? `${fieldId}-help` : undefined}
              aria-invalid={hasError}
              {...props}
            />
          )
      }
    }

    return (
      <div className="space-y-2">
        <label htmlFor={fieldId} className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>

        <div className="relative">
          {renderInput()}
          
          {/* Status Icons */}
          {hasError && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
            </div>
          )}
          {isValid && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
            </div>
          )}
        </div>

        {/* Help Text */}
        {helpText && !hasError && (
          <p id={`${fieldId}-help`} className="text-sm text-gray-500">
            {helpText}
          </p>
        )}

        {/* Error Message */}
        {hasError && (
          <p className="text-sm text-red-600 flex items-center space-x-1">
            <ExclamationTriangleIcon className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </p>
        )}
      </div>
    )
  }
)

PropertyFieldInput.displayName = 'PropertyFieldInput'

export default PropertyFieldInput