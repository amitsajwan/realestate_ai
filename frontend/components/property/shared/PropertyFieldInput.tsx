'use client'

import React from 'react'
import { UseFormRegister, FieldErrors } from 'react-hook-form'
import { PropertyFormData } from '@/lib/validation'
import { ExclamationCircleIcon } from '@heroicons/react/24/outline'

interface PropertyFieldInputProps {
  name: keyof PropertyFormData
  label: string
  type?: 'text' | 'number' | 'select' | 'textarea'
  placeholder?: string
  icon?: React.ComponentType<{ className?: string }>
  options?: Array<{ value: string | number; label: string }>
  register: UseFormRegister<PropertyFormData>
  errors: FieldErrors<PropertyFormData>
  required?: boolean
  helpText?: string
  className?: string
}

export default function PropertyFieldInput({
  name,
  label,
  type = 'text',
  placeholder,
  icon: Icon,
  options,
  register,
  errors,
  required = false,
  helpText,
  className = ''
}: PropertyFieldInputProps) {
  const error = errors[name]?.message as string | undefined
  const hasError = !!error

  const baseInputClasses = `
    w-full px-4 py-3 rounded-xl border transition-all duration-200
    bg-white dark:bg-slate-800
    text-gray-900 dark:text-white
    placeholder-gray-500 dark:placeholder-gray-400
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
    ${hasError 
      ? 'border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/10' 
      : 'border-gray-300 dark:border-slate-600 hover:border-gray-400 dark:hover:border-slate-500'
    }
    ${Icon ? 'pl-12' : ''}
  `

  const renderInput = () => {
    const commonProps = {
      ...register(name, { 
        valueAsNumber: (type === 'number' || name === 'bedrooms' || name === 'bathrooms' || name === 'area') ? true : false 
      }),
      className: baseInputClasses,
      placeholder,
      'aria-invalid': hasError,
      'aria-describedby': hasError ? `${name}-error` : undefined
    }

    switch (type) {
      case 'textarea':
        return (
          <textarea
            {...commonProps}
            rows={4}
            className={`${baseInputClasses} resize-none`}
          />
        )
      
      case 'select':
        return (
          <select {...commonProps}>
            <option value="">Select {label.toLowerCase()}</option>
            {options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        )
      
      case 'number':
        return (
          <input
            {...commonProps}
            type="number"
            min="0"
            step="1"
          />
        )
      
      default:
        return (
          <input
            {...commonProps}
            type="text"
          />
        )
    }
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <label 
        htmlFor={name}
        className="block text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        )}
        
        {renderInput()}
        
        {hasError && (
          <ExclamationCircleIcon className="absolute right-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-red-500" />
        )}
      </div>
      
      {helpText && !hasError && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {helpText}
        </p>
      )}
      
      {hasError && (
        <p 
          id={`${name}-error`}
          className="text-sm text-red-600 dark:text-red-400 flex items-center gap-1"
          role="alert"
        >
          <ExclamationCircleIcon className="w-4 h-4" />
          {error}
        </p>
      )}
    </div>
  )
}