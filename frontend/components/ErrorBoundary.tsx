'use client'

import React, { Component, ErrorInfo, ReactNode, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import { logger } from '../lib/logger'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
  console.error('[ErrorBoundary] ErrorBoundary caught an error:', error, errorInfo)
    this.setState({ error, errorInfo })
    
    // Log error to your error reporting service
    // Example: logErrorToService(error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

                        return (
                    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="w-full max-w-md"
                      >
                        <div className="glass-card text-center">
                          <motion.div 
                            className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4"
                            animate={{ scale: [1, 1.1, 1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                          >
                            <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
                          </motion.div>
                          <h2 className="text-2xl font-bold text-gray-800 mb-2">
                            Oops! Something went wrong
                          </h2>
                          <p className="text-gray-600 mb-6">
                            We encountered an unexpected error. Don&apos;t worry, this is usually temporary. Please try refreshing the page or contact support if the problem persists.
                          </p>
                          <div className="flex space-x-3">
                            <button
                              onClick={this.handleRetry}
                              className="btn-primary flex items-center space-x-2"
                            >
                              <ArrowPathIcon className="w-4 h-4" />
                              <span>Try Again</span>
                            </button>
                            <button
                              onClick={() => window.location.reload()}
                              className="btn-outline"
                            >
                              Refresh Page
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    </div>
              )
    }

    return this.props.children
  }
}

// Hook for functional components to handle errors
export function useErrorHandler() {
  const [error, setError] = useState<Error | null>(null)

  const handleError = useCallback((error: Error) => {
    logger.error('[ErrorBoundary] Error caught by useErrorHandler', {
      component: 'ErrorBoundary',
      action: 'error_handling',
      errorDetails: error
    }, error)
    setError(error)
  }, [])

  const clearError = React.useCallback(() => {
    setError(null)
  }, [])

  return { error, handleError, clearError }
}

// Higher-order component for error handling
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}
