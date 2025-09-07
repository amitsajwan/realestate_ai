/**
 * Add Property Page
 * ================
 * 
 * This page uses the PropertyFormWrapper to render the appropriate
 * form variant based on feature flags and A/B testing.
 */

'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import PropertyFormWrapper from '../../../components/property/PropertyFormWrapper'
import { PropertyFormData } from '../../../lib/validation'
import { useAnalytics } from '../../../utils/analytics'

export default function AddPropertyPage() {
  const router = useRouter()
  const { trackPage } = useAnalytics()

  // Track page view
  React.useEffect(() => {
    trackPage('Add Property Page', {
      timestamp: new Date().toISOString()
    })
  }, [trackPage])

  const handleSuccess = (data: PropertyFormData) => {
    console.log('Property created successfully:', data)
    
    // Track successful property creation
    trackPage('Property Created Success', {
      propertyId: data.title, // Use title as identifier for now
      timestamp: new Date().toISOString()
    })
    
    // Redirect to properties list or property detail page
    router.push('/properties')
  }

  const handleError = (error: Error) => {
    console.error('Property creation failed:', error)
    
    // Track property creation error
    trackPage('Property Creation Error', {
      error: error.message,
      timestamp: new Date().toISOString()
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <PropertyFormWrapper
        variant="simple"
        onSuccess={handleSuccess}
        onError={handleError}
        className="py-8"
      />
    </div>
  )
}