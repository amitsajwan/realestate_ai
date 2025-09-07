/**
 * Feature Flags for Property Forms Consolidation
 * =============================================
 * 
 * This module provides feature flag utilities for gradual rollout
 * and A/B testing of the unified property form system.
 */

export interface FeatureFlags {
  USE_UNIFIED_FORM: boolean
  ENABLE_AI_FEATURES: boolean
  ENABLE_MARKET_INSIGHTS: boolean
  ENABLE_QUALITY_SCORING: boolean
  ENABLE_MULTILANGUAGE: boolean
  FALLBACK_ON_ERROR: boolean
  ENABLE_AB_TESTING: boolean
  DEBUG_MODE: boolean
}

/**
 * Get feature flags from environment variables
 */
export function getFeatureFlags(): FeatureFlags {
  return {
    USE_UNIFIED_FORM: process.env.NEXT_PUBLIC_USE_UNIFIED_FORM === 'true',
    ENABLE_AI_FEATURES: process.env.NEXT_PUBLIC_ENABLE_AI_FEATURES === 'true',
    ENABLE_MARKET_INSIGHTS: process.env.NEXT_PUBLIC_ENABLE_MARKET_INSIGHTS === 'true',
    ENABLE_QUALITY_SCORING: process.env.NEXT_PUBLIC_ENABLE_QUALITY_SCORING === 'true',
    ENABLE_MULTILANGUAGE: process.env.NEXT_PUBLIC_ENABLE_MULTILANGUAGE === 'true',
    FALLBACK_ON_ERROR: process.env.NEXT_PUBLIC_FALLBACK_ON_ERROR === 'true',
    ENABLE_AB_TESTING: process.env.NEXT_PUBLIC_ENABLE_AB_TESTING === 'true',
    DEBUG_MODE: process.env.NODE_ENV === 'development'
  }
}

/**
 * A/B Testing utilities
 */
export class ABTesting {
  private static instance: ABTesting
  private userVariant: 'old' | 'new' | null = null

  static getInstance(): ABTesting {
    if (!ABTesting.instance) {
      ABTesting.instance = new ABTesting()
    }
    return ABTesting.instance
  }

  /**
   * Get user variant for A/B testing
   */
  getUserVariant(userId: string): 'old' | 'new' {
    if (this.userVariant) {
      return this.userVariant
    }

    // Simple hash-based assignment for consistent user experience
    const hash = this.hashUserId(userId)
    const percentage = hash % 100
    
    // Start with 10% of users getting the new form
    const rolloutPercentage = parseInt(process.env.NEXT_PUBLIC_ROLLOUT_PERCENTAGE || '10')
    
    this.userVariant = percentage < rolloutPercentage ? 'new' : 'old'
    
    // Store in localStorage for consistency
    if (typeof window !== 'undefined') {
      localStorage.setItem('property-form-variant', this.userVariant)
    }
    
    return this.userVariant
  }

  /**
   * Get variant from localStorage (for consistency)
   */
  getStoredVariant(): 'old' | 'new' | null {
    if (typeof window === 'undefined') return null
    
    const stored = localStorage.getItem('property-form-variant')
    return stored as 'old' | 'new' | null
  }

  /**
   * Simple hash function for user ID
   */
  private hashUserId(userId: string): number {
    let hash = 0
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash)
  }

  /**
   * Track A/B test events
   */
  trackEvent(event: string, variant: 'old' | 'new', properties?: Record<string, any>) {
    if (typeof window === 'undefined') return

    // Send to analytics service
    if (window.gtag) {
      window.gtag('event', event, {
        custom_parameter_variant: variant,
        ...properties
      })
    }

    // Log for debugging
    if (getFeatureFlags().DEBUG_MODE) {
      console.log(`[AB Testing] ${event}`, { variant, properties })
    }
  }
}

/**
 * Feature flag hook for React components
 */
export function useFeatureFlags(): FeatureFlags {
  return getFeatureFlags()
}

/**
 * A/B testing hook for React components
 */
export function useABTesting(userId?: string) {
  const abTesting = ABTesting.getInstance()
  
  const getVariant = () => {
    if (userId) {
      return abTesting.getUserVariant(userId)
    }
    return abTesting.getStoredVariant() || 'old'
  }

  const trackEvent = (event: string, properties?: Record<string, any>) => {
    const variant = getVariant()
    abTesting.trackEvent(event, variant, properties)
  }

  return {
    variant: getVariant(),
    trackEvent,
    isNewVariant: getVariant() === 'new',
    isOldVariant: getVariant() === 'old'
  }
}

/**
 * Environment configuration
 */
export const ENV_CONFIG = {
  ROLLOUT_PERCENTAGE: parseInt(process.env.NEXT_PUBLIC_ROLLOUT_PERCENTAGE || '10'),
  ANALYTICS_ENABLED: process.env.NEXT_PUBLIC_ANALYTICS_ENABLED === 'true',
  SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN,
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
}

// Global type declaration for gtag
declare global {
  interface Window {
    gtag?: (...args: any[]) => void
  }
}