'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  message?: string
  className?: string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  message,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  }

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div 
        className={`${sizeClasses[size]} border-4 border-blue-500 border-t-transparent rounded-full animate-spin`}
      />
      {message && (
        <p className="mt-4 text-gray-600 text-sm">{message}</p>
      )}
    </div>
  )
}

interface LoadingSkeletonProps {
  lines?: number
  className?: string
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ 
  lines = 3,
  className = ''
}) => {
  return (
    <div className={`animate-pulse ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={`h-4 bg-gray-200 rounded mb-2 ${
            i === lines - 1 ? 'w-3/4' : 'w-full'
          }`}
        />
      ))}
    </div>
  )
}

interface LoadingCardProps {
  count?: number
  className?: string
}

export const LoadingCard: React.FC<LoadingCardProps> = ({ 
  count = 1,
  className = ''
}) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`bg-white rounded-lg shadow-md p-6 animate-pulse ${className}`}
        >
          <div className="h-6 bg-gray-200 rounded w-3/4 mb-4" />
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded" />
            <div className="h-4 bg-gray-200 rounded" />
            <div className="h-4 bg-gray-200 rounded w-5/6" />
          </div>
          <div className="mt-4 flex space-x-2">
            <div className="h-8 bg-gray-200 rounded w-20" />
            <div className="h-8 bg-gray-200 rounded w-20" />
          </div>
        </div>
      ))}
    </>
  )
}

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
  className?: string
}

export const ErrorState: React.FC<ErrorStateProps> = ({ 
  title = 'Something went wrong',
  message = 'An error occurred while loading the data.',
  onRetry,
  className = ''
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}
    >
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-center max-w-md mb-6">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <ArrowPathIcon className="w-5 h-5 mr-2" />
          Try Again
        </button>
      )}
    </motion.div>
  )
}

interface EmptyStateProps {
  title?: string
  message?: string
  icon?: React.ReactNode
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
  title = 'No data found',
  message = 'There is no data to display at the moment.',
  icon,
  action,
  className = ''
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}
    >
      {icon && (
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-center max-w-md mb-6">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          {action.label}
        </button>
      )}
    </motion.div>
  )
}

interface LoadingOverlayProps {
  isLoading: boolean
  message?: string
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ 
  isLoading,
  message = 'Loading...'
}) => {
  if (!isLoading) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 shadow-xl">
        <LoadingSpinner size="lg" message={message} />
      </div>
    </div>
  )
}