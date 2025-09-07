/**
 * Add Property Page - AI-First Approach
 * ====================================
 * 
 * This page uses the AI-first property form that provides intelligent
 * analysis and suggestions for quick property listing.
 */

'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import AIFirstPropertyForm from '../../../components/property/AIFirstPropertyForm'
import { useAnalytics } from '../../../utils/analytics'

export default function AddPropertyPage() {
  const router = useRouter()
  const { trackPage } = useAnalytics()

  // Track page view
  React.useEffect(() => {
    trackPage('Add Property Page - AI First', {
      timestamp: new Date().toISOString(),
      form_type: 'ai_first'
    })
  }, [trackPage])

  const handleSuccess = () => {
    // Track successful property creation
    trackPage('Property Created Success - AI First', {
      method: 'ai_analysis',
      completion_time: 'under_2_minutes',
      timestamp: new Date().toISOString()
    })
    
    // Redirect to properties list
    router.push('/properties')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AIFirstPropertyForm />
    </div>
  )
}