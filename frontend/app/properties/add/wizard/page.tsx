/**
 * Add Property Wizard Page
 * =======================
 * 
 * This page renders the wizard variant of the property form.
 */

'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import PropertyFormWrapper from '../../../../components/property/PropertyFormWrapper'
import { PropertyFormData } from '../../../../lib/validation'
import { useAnalytics } from '../../../../utils/analytics'

export default function AddPropertyWizardPage() {
  const router = useRouter()
  const { trackPage } = useAnalytics()

  // Track page view
  React.useEffect(() => {
    trackPage('Add Property Wizard Page', {
      timestamp: new Date().toISOString()
    })
  }, [trackPage])

  const handleSuccess = (data: PropertyFormData) => {
    console.log('Property created successfully via wizard:', data)
    
    // Track successful property creation
    trackPage('Property Created Success (Wizard)', {
      propertyId: data.title,
      timestamp: new Date().toISOString()
    })
    
    // Redirect to properties list
    router.push('/properties')
  }

  const handleError = (error: Error) => {
    console.error('Property creation failed via wizard:', error)
    
    // Track property creation error
    trackPage('Property Creation Error (Wizard)', {
      error: error.message,
      timestamp: new Date().toISOString()
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <PropertyFormWrapper
        variant="wizard"
        onSuccess={handleSuccess}
        onError={handleError}
        className="py-8"
      />
    </div>
  )
}