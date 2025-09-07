/**
 * Analytics and Monitoring Utilities
 * ==================================
 * 
 * This module provides comprehensive analytics and monitoring for the
 * unified property form system.
 */

import { FormEvent, FormAnalytics } from '@/types/PropertyFormTypes'

/**
 * Analytics service interface
 */
interface AnalyticsService {
  track: (event: string, properties?: Record<string, any>) => void
  identify: (userId: string, traits?: Record<string, any>) => void
  page: (name: string, properties?: Record<string, any>) => void
}

/**
 * Performance monitoring interface
 */
interface PerformanceMetrics {
  formLoadTime: number
  timeToFirstInteraction: number
  timeToComplete: number
  stepsCompleted: number
  fieldsModified: string[]
  aiSuggestionsUsed: string[]
  errorsEncountered: string[]
  abandonmentPoint?: string
  completionRate: number
}

/**
 * Error tracking interface
 */
interface ErrorEvent {
  message: string
  stack?: string
  component: string
  variant: string
  userId?: string
  sessionId?: string
  timestamp: Date
  properties?: Record<string, any>
}

/**
 * Analytics Manager Class
 */
class AnalyticsManager {
  private static instance: AnalyticsManager
  private services: AnalyticsService[] = []
  private performanceMetrics: PerformanceMetrics = {
    formLoadTime: 0,
    timeToFirstInteraction: 0,
    timeToComplete: 0,
    stepsCompleted: 0,
    fieldsModified: [],
    aiSuggestionsUsed: [],
    errorsEncountered: [],
    completionRate: 0
  }
  private sessionId: string
  private userId?: string

  constructor() {
    this.sessionId = this.generateSessionId()
    this.initializeServices()
  }

  static getInstance(): AnalyticsManager {
    if (!AnalyticsManager.instance) {
      AnalyticsManager.instance = new AnalyticsManager()
    }
    return AnalyticsManager.instance
  }

  /**
   * Initialize analytics services
   */
  private initializeServices(): void {
    // Google Analytics
    if (typeof window !== 'undefined' && window.gtag) {
      this.services.push({
        track: (event: string, properties?: Record<string, any>) => {
          window.gtag!('event', event, {
            custom_parameter_session_id: this.sessionId,
            custom_parameter_user_id: this.userId,
            ...properties
          })
        },
        identify: (userId: string, traits?: Record<string, any>) => {
          window.gtag!('config', 'GA_MEASUREMENT_ID', {
            user_id: userId,
            custom_map: traits
          })
        },
        page: (name: string, properties?: Record<string, any>) => {
          window.gtag!('config', 'GA_MEASUREMENT_ID', {
            page_title: name,
            page_location: window.location.href,
            ...properties
          })
        }
      })
    }

    // Mixpanel
    if (typeof window !== 'undefined' && (window as any).mixpanel) {
      this.services.push({
        track: (event: string, properties?: Record<string, any>) => {
          (window as any).mixpanel.track(event, {
            session_id: this.sessionId,
            user_id: this.userId,
            ...properties
          })
        },
        identify: (userId: string, traits?: Record<string, any>) => {
          (window as any).mixpanel.identify(userId)
          if (traits) {
            (window as any).mixpanel.people.set(traits)
          }
        },
        page: (name: string, properties?: Record<string, any>) => {
          (window as any).mixpanel.track('Page View', {
            page_name: name,
            ...properties
          })
        }
      })
    }

    // Sentry (for error tracking)
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      this.services.push({
        track: (event: string, properties?: Record<string, any>) => {
          (window as any).Sentry.addBreadcrumb({
            message: event,
            data: properties,
            level: 'info'
          })
        },
        identify: (userId: string, traits?: Record<string, any>) => {
          (window as any).Sentry.setUser({
            id: userId,
            ...traits
          })
        },
        page: (name: string, properties?: Record<string, any>) => {
          (window as any).Sentry.setContext('page', {
            name,
            ...properties
          })
        }
      })
    }
  }

  /**
   * Track form events
   */
  trackFormEvent(event: FormEvent): void {
    const properties = {
      event_type: event.type,
      timestamp: event.timestamp.toISOString(),
      variant: event.metadata.variant,
      user_id: event.metadata.userId,
      session_id: event.metadata.sessionId,
      ...event.data
    }

    this.services.forEach(service => {
      try {
        service.track(`form_${event.type}`, properties)
      } catch (error) {
        console.error('Analytics tracking error:', error)
      }
    })

    // Update performance metrics
    this.updatePerformanceMetrics(event)
  }

  /**
   * Track form performance
   */
  trackFormPerformance(metrics: Partial<PerformanceMetrics>): void {
    this.performanceMetrics = { ...this.performanceMetrics, ...metrics }

    this.services.forEach(service => {
      try {
        service.track('form_performance', {
          ...this.performanceMetrics,
          session_id: this.sessionId,
          user_id: this.userId
        })
      } catch (error) {
        console.error('Performance tracking error:', error)
      }
    })
  }

  /**
   * Track errors
   */
  trackError(error: ErrorEvent): void {
    this.performanceMetrics.errorsEncountered.push(error.message)

    this.services.forEach(service => {
      try {
        service.track('form_error', {
          error_message: error.message,
          error_stack: error.stack,
          component: error.component,
          variant: error.variant,
          user_id: error.userId,
          session_id: error.sessionId,
          timestamp: error.timestamp.toISOString(),
          ...error.properties
        })
      } catch (trackingError) {
        console.error('Error tracking error:', trackingError)
      }
    })

    // Send to Sentry if available
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(new Error(error.message), {
        tags: {
          component: error.component,
          variant: error.variant
        },
        extra: error.properties
      })
    }
  }

  /**
   * Track user identification
   */
  identifyUser(userId: string, traits?: Record<string, any>): void {
    this.userId = userId

    this.services.forEach(service => {
      try {
        service.identify(userId, traits)
      } catch (error) {
        console.error('User identification error:', error)
      }
    })
  }

  /**
   * Track page views
   */
  trackPageView(pageName: string, properties?: Record<string, any>): void {
    this.services.forEach(service => {
      try {
        service.page(pageName, {
          session_id: this.sessionId,
          user_id: this.userId,
          ...properties
        })
      } catch (error) {
        console.error('Page tracking error:', error)
      }
    })
  }

  /**
   * Update performance metrics
   */
  private updatePerformanceMetrics(event: FormEvent): void {
    switch (event.type) {
      case 'load':
        this.performanceMetrics.formLoadTime = Date.now() - event.timestamp.getTime()
        break
      case 'field_change':
        if (!this.performanceMetrics.fieldsModified.includes(event.data.field)) {
          this.performanceMetrics.fieldsModified.push(event.data.field)
        }
        if (this.performanceMetrics.timeToFirstInteraction === 0) {
          this.performanceMetrics.timeToFirstInteraction = Date.now() - event.timestamp.getTime()
        }
        break
      case 'step_change':
        this.performanceMetrics.stepsCompleted = Math.max(
          this.performanceMetrics.stepsCompleted,
          event.data.step
        )
        break
      case 'submit':
        this.performanceMetrics.timeToComplete = Date.now() - event.timestamp.getTime()
        this.performanceMetrics.completionRate = 100
        break
      case 'ai_generate':
        if (event.data.suggestions) {
          this.performanceMetrics.aiSuggestionsUsed.push('ai_generate')
        }
        break
      case 'error':
        this.performanceMetrics.errorsEncountered.push(event.data.error)
        break
    }
  }

  /**
   * Generate session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Get current performance metrics
   */
  getPerformanceMetrics(): PerformanceMetrics {
    return { ...this.performanceMetrics }
  }

  /**
   * Get session ID
   */
  getSessionId(): string {
    return this.sessionId
  }

  /**
   * Get user ID
   */
  getUserId(): string | undefined {
    return this.userId
  }
}

/**
 * Performance monitoring utilities
 */
export class PerformanceMonitor {
  private static instance: PerformanceMonitor
  private marks: Map<string, number> = new Map()
  private measures: Map<string, number> = new Map()

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor()
    }
    return PerformanceMonitor.instance
  }

  /**
   * Mark a performance point
   */
  mark(name: string): void {
    if (typeof window !== 'undefined' && window.performance) {
      window.performance.mark(name)
      this.marks.set(name, Date.now())
    }
  }

  /**
   * Measure performance between two marks
   */
  measure(name: string, startMark: string, endMark?: string): number {
    if (typeof window !== 'undefined' && window.performance) {
      if (endMark) {
        window.performance.measure(name, startMark, endMark)
      } else {
        window.performance.measure(name, startMark)
      }

      const measure = window.performance.getEntriesByName(name, 'measure')[0]
      const duration = measure ? measure.duration : 0
      this.measures.set(name, duration)
      return duration
    }
    return 0
  }

  /**
   * Get performance measure
   */
  getMeasure(name: string): number {
    return this.measures.get(name) || 0
  }

  /**
   * Clear performance marks and measures
   */
  clear(): void {
    if (typeof window !== 'undefined' && window.performance) {
      window.performance.clearMarks()
      window.performance.clearMeasures()
    }
    this.marks.clear()
    this.measures.clear()
  }
}

/**
 * Error tracking utilities
 */
export class ErrorTracker {
  private static instance: ErrorTracker
  private analytics: AnalyticsManager

  constructor() {
    this.analytics = AnalyticsManager.getInstance()
  }

  static getInstance(): ErrorTracker {
    if (!ErrorTracker.instance) {
      ErrorTracker.instance = new ErrorTracker()
    }
    return ErrorTracker.instance
  }

  /**
   * Track form errors
   */
  trackFormError(
    error: Error,
    component: string,
    variant: string,
    properties?: Record<string, any>
  ): void {
    const errorEvent: ErrorEvent = {
      message: error.message,
      stack: error.stack,
      component,
      variant,
      userId: this.analytics.getUserId(),
      sessionId: this.analytics.getSessionId(),
      timestamp: new Date(),
      properties
    }

    this.analytics.trackError(errorEvent)
  }

  /**
   * Track API errors
   */
  trackAPIError(
    error: any,
    endpoint: string,
    method: string,
    properties?: Record<string, any>
  ): void {
    const errorEvent: ErrorEvent = {
      message: error.message || 'API Error',
      stack: error.stack,
      component: 'API',
      variant: 'api',
      userId: this.analytics.getUserId(),
      sessionId: this.analytics.getSessionId(),
      timestamp: new Date(),
      properties: {
        endpoint,
        method,
        status: error.status,
        ...properties
      }
    }

    this.analytics.trackError(errorEvent)
  }
}

/**
 * Export singleton instances
 */
export const analytics = AnalyticsManager.getInstance()
export const performanceMonitor = PerformanceMonitor.getInstance()
export const errorTracker = ErrorTracker.getInstance()

/**
 * React hook for analytics
 */
export function useAnalytics() {
  return {
    track: (event: string, properties?: Record<string, any>) => {
      analytics.services.forEach(service => {
        try {
          service.track(event, properties)
        } catch (error) {
          console.error('Analytics tracking error:', error)
        }
      })
    },
    identify: (userId: string, traits?: Record<string, any>) => {
      analytics.identifyUser(userId, traits)
    },
    trackPage: (pageName: string, properties?: Record<string, any>) => {
      analytics.trackPageView(pageName, properties)
    },
    trackError: (error: Error, component: string, variant: string, properties?: Record<string, any>) => {
      errorTracker.trackFormError(error, component, variant, properties)
    },
    trackPerformance: (metrics: Partial<PerformanceMetrics>) => {
      analytics.trackFormPerformance(metrics)
    }
  }
}

/**
 * Global type declarations
 */
declare global {
  interface Window {
    gtag?: (...args: any[]) => void
    mixpanel?: any
    Sentry?: any
  }
}