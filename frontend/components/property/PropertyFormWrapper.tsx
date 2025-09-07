/**
 * Property Form Wrapper Component
 * ===============================
 * 
 * This component handles feature flags and A/B testing to determine
 * which form variant to render.
 */

'use client'

import React from 'react'
import { useFeatureFlags, useABTesting } from '../../utils/featureFlags'
import UnifiedPropertyForm from './UnifiedPropertyForm'
import PropertyForm from '../PropertyForm'
import SmartPropertyForm from '../SmartPropertyForm'
import GenAIPropertyForm from '../GenAIPropertyForm'
import ConsolidatedPropertyForm from './ConsolidatedPropertyForm'
import { UnifiedPropertyFormProps } from '../../types/PropertyFormTypes'

interface PropertyFormWrapperProps extends UnifiedPropertyFormProps {
  fallbackVariant?: 'simple' | 'wizard' | 'ai-first' | 'consolidated'
  userId?: string
}

/**
 * Property Form Wrapper Component
 * 
 * This component acts as a router that determines which form to render
 * based on feature flags and A/B testing configuration.
 */
export default function PropertyFormWrapper({
  variant = 'simple',
  fallbackVariant = 'simple',
  userId,
  ...props
}: PropertyFormWrapperProps) {
  const featureFlags = useFeatureFlags()
  const { variant: abVariant, trackEvent } = useABTesting(userId)

  // Track form selection
  React.useEffect(() => {
    trackEvent('form_selected', {
      variant: abVariant,
      formVariant: variant,
      useUnifiedForm: featureFlags.USE_UNIFIED_FORM
    })
  }, [abVariant, variant, featureFlags.USE_UNIFIED_FORM, trackEvent])

  // If unified form is enabled and user is in new variant, use unified form
  if (featureFlags.USE_UNIFIED_FORM && abVariant === 'new') {
    return (
      <UnifiedPropertyForm
        variant={variant}
        userId={userId}
        {...props}
      />
    )
  }

  // Fallback to existing forms based on variant
  switch (variant) {
    case 'simple':
      return <PropertyForm {...props} />
    
    case 'wizard':
      return <SmartPropertyForm {...props} />
    
    case 'ai-first':
      return <GenAIPropertyForm {...props} />
    
    case 'consolidated':
      return <ConsolidatedPropertyForm {...props} />
    
    default:
      // Use fallback variant if specified variant is not supported
      return <PropertyFormWrapper variant={fallbackVariant} {...props} />
  }
}

/**
 * Hook to get the appropriate form component based on feature flags
 */
export function useFormComponent() {
  const featureFlags = useFeatureFlags()
  const { variant: abVariant } = useABTesting()

  return {
    shouldUseUnifiedForm: featureFlags.USE_UNIFIED_FORM && abVariant === 'new',
    abVariant,
    featureFlags
  }
}