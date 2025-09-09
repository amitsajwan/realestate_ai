/**
 * User Testing Framework
 * ======================
 * 
 * This module provides comprehensive user testing capabilities
 * for the unified property form system, including A/B testing,
 * user feedback collection, and performance monitoring.
 */

import { FormVariant, FormAnalytics } from '@/types/PropertyFormTypes'

/**
 * User testing session interface
 */
export interface UserTestingSession {
  sessionId: string
  userId?: string
  variant: FormVariant
  startTime: Date
  endTime?: Date
  completed: boolean
  abandoned: boolean
  abandonmentPoint?: string
  feedback?: UserFeedback
  analytics: FormAnalytics
  deviceInfo: DeviceInfo
  browserInfo: BrowserInfo
}

/**
 * User feedback interface
 */
export interface UserFeedback {
  rating: number // 1-5 scale
  comments: string
  difficulty: 'very-easy' | 'easy' | 'moderate' | 'difficult' | 'very-difficult'
  features: {
    ai: boolean
    marketInsights: boolean
    wizard: boolean
    autoSave: boolean
  }
  suggestions: string
  wouldRecommend: boolean
  submittedAt: Date
}

/**
 * Device information interface
 */
export interface DeviceInfo {
  type: 'desktop' | 'tablet' | 'mobile'
  screenWidth: number
  screenHeight: number
  userAgent: string
  platform: string
}

/**
 * Browser information interface
 */
export interface BrowserInfo {
  name: string
  version: string
  engine: string
  language: string
  timezone: string
}

/**
 * User testing event interface
 */
export interface UserTestingEvent {
  type: 'form_start' | 'form_complete' | 'form_abandon' | 'step_change' | 'field_interaction' | 'ai_usage' | 'error' | 'feedback'
  timestamp: Date
  data: any
  sessionId: string
  variant: FormVariant
}

/**
 * User Testing Manager Class
 */
class UserTestingManager {
  private static instance: UserTestingManager
  private sessions: Map<string, UserTestingSession> = new Map()
  private events: UserTestingEvent[] = []
  private currentSession: UserTestingSession | null = null

  static getInstance(): UserTestingManager {
    if (!UserTestingManager.instance) {
      UserTestingManager.instance = new UserTestingManager()
    }
    return UserTestingManager.instance
  }

  /**
   * Start a new user testing session
   */
  startSession(variant: FormVariant, userId?: string): UserTestingSession {
    const sessionId = this.generateSessionId()
    const deviceInfo = this.getDeviceInfo()
    const browserInfo = this.getBrowserInfo()

    const session: UserTestingSession = {
      sessionId,
      userId,
      variant,
      startTime: new Date(),
      completed: false,
      abandoned: false,
      analytics: {
        formId: variant,
        events: [],
        formLoadTime: 0,
        timeToFirstInteraction: 0,
        timeToComplete: 0,
        stepsCompleted: 0,
        fieldsModified: [],
        aiSuggestionsUsed: [],
        errorsEncountered: [],
        completionRate: 0,
        averageTime: 0,
        errorRate: 0
      },
      deviceInfo,
      browserInfo
    }

    this.sessions.set(sessionId, session)
    this.currentSession = session

    // Track session start
    this.trackEvent({
      type: 'form_start',
      timestamp: new Date(),
      data: { variant, userId },
      sessionId,
      variant
    })

    // Store in localStorage for persistence
    if (typeof window !== 'undefined') {
      localStorage.setItem('user-testing-session', JSON.stringify(session))
    }

    return session
  }

  /**
   * Complete the current session
   */
  completeSession(analytics: FormAnalytics): void {
    if (!this.currentSession) return

    if (this.currentSession) {
      this.currentSession.endTime = new Date()
      this.currentSession.completed = true
      this.currentSession.analytics = analytics
    }

    this.trackEvent({
      type: 'form_complete',
      timestamp: new Date(),
      data: { analytics },
      sessionId: this.currentSession?.sessionId || '',
      variant: this.currentSession?.variant || 'smart'
    })

    // Send to analytics service
    this.sendSessionData(this.currentSession)

    // Clear current session
    this.currentSession = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user-testing-session')
    }
  }

  /**
   * Abandon the current session
   */
  abandonSession(abandonmentPoint: string): void {
    if (!this.currentSession) return

    this.currentSession.endTime = new Date()
    this.currentSession.abandoned = true
    this.currentSession.abandonmentPoint = abandonmentPoint

    this.trackEvent({
      type: 'form_abandon',
      timestamp: new Date(),
      data: { abandonmentPoint },
      sessionId: this.currentSession.sessionId,
      variant: this.currentSession.variant
    })

    // Send to analytics service
    this.sendSessionData(this.currentSession)

    // Clear current session
    this.currentSession = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user-testing-session')
    }
  }

  /**
   * Track user testing event
   */
  trackEvent(event: UserTestingEvent): void {
    this.events.push(event)

    // Update current session analytics
    if (this.currentSession && event.sessionId === this.currentSession.sessionId) {
      this.updateSessionAnalytics(event)
    }

    // Send to analytics service
    this.sendEventData(event)
  }

  /**
   * Collect user feedback
   */
  collectFeedback(feedback: Omit<UserFeedback, 'submittedAt'>): void {
    if (!this.currentSession) return

    const completeFeedback: UserFeedback = {
      ...feedback,
      submittedAt: new Date()
    }

    this.currentSession.feedback = completeFeedback

    this.trackEvent({
      type: 'feedback',
      timestamp: new Date(),
      data: { feedback: completeFeedback },
      sessionId: this.currentSession.sessionId,
      variant: this.currentSession.variant
    })
  }

  /**
   * Get current session
   */
  getCurrentSession(): UserTestingSession | null {
    return this.currentSession
  }

  /**
   * Get all sessions
   */
  getAllSessions(): UserTestingSession[] {
    return Array.from(this.sessions.values())
  }

  /**
   * Get session by ID
   */
  getSession(sessionId: string): UserTestingSession | undefined {
    return this.sessions.get(sessionId)
  }

  /**
   * Get testing statistics
   */
  getTestingStats(): {
    totalSessions: number
    completionRate: number
    averageCompletionTime: number
    abandonmentRate: number
    variantPerformance: Record<FormVariant, {
      sessions: number
      completionRate: number
      averageTime: number
      satisfaction: number
    }>
  } {
    const sessions = this.getAllSessions()
    const completedSessions = sessions.filter(s => s.completed)
    const abandonedSessions = sessions.filter(s => s.abandoned)

    const stats = {
      totalSessions: sessions.length,
      completionRate: sessions.length > 0 ? (completedSessions.length / sessions.length) * 100 : 0,
      averageCompletionTime: 0,
      abandonmentRate: sessions.length > 0 ? (abandonedSessions.length / sessions.length) * 100 : 0,
      variantPerformance: {} as Record<FormVariant, any>
    }

    // Calculate average completion time
    if (completedSessions.length > 0) {
      const totalTime = completedSessions.reduce((sum, session) => {
        if (session.endTime) {
          return sum + (session.endTime.getTime() - session.startTime.getTime())
        }
        return sum
      }, 0)
      stats.averageCompletionTime = totalTime / completedSessions.length
    }

    // Calculate variant performance
    const variants: FormVariant[] = ['simple', 'wizard', 'ai-first']
    variants.forEach(variant => {
      const variantSessions = sessions.filter(s => s.variant === variant)
      const variantCompleted = variantSessions.filter(s => s.completed)
      const variantAbandoned = variantSessions.filter(s => s.abandoned)

      let averageTime = 0
      if (variantCompleted.length > 0) {
        const totalTime = variantCompleted.reduce((sum, session) => {
          if (session.endTime) {
            return sum + (session.endTime.getTime() - session.startTime.getTime())
          }
          return sum
        }, 0)
        averageTime = totalTime / variantCompleted.length
      }

      let satisfaction = 0
      const feedbackSessions = variantSessions.filter(s => s.feedback)
      if (feedbackSessions.length > 0) {
        satisfaction = feedbackSessions.reduce((sum, session) => {
          return sum + (session.feedback?.rating || 0)
        }, 0) / feedbackSessions.length
      }

      stats.variantPerformance[variant] = {
        sessions: variantSessions.length,
        completionRate: variantSessions.length > 0 ? (variantCompleted.length / variantSessions.length) * 100 : 0,
        averageTime,
        satisfaction
      }
    })

    return stats
  }

  /**
   * Generate session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Get device information
   */
  private getDeviceInfo(): DeviceInfo {
    if (typeof window === 'undefined') {
      return {
        type: 'desktop',
        screenWidth: 1920,
        screenHeight: 1080,
        userAgent: 'unknown',
        platform: 'unknown'
      }
    }

    const width = window.innerWidth
    const height = window.innerHeight
    let type: 'desktop' | 'tablet' | 'mobile' = 'desktop'

    if (width < 768) {
      type = 'mobile'
    } else if (width < 1024) {
      type = 'tablet'
    }

    return {
      type,
      screenWidth: width,
      screenHeight: height,
      userAgent: navigator.userAgent,
      platform: navigator.platform
    }
  }

  /**
   * Get browser information
   */
  private getBrowserInfo(): BrowserInfo {
    if (typeof window === 'undefined') {
      return {
        name: 'unknown',
        version: 'unknown',
        engine: 'unknown',
        language: 'en',
        timezone: 'UTC'
      }
    }

    const userAgent = navigator.userAgent
    let name = 'unknown'
    let version = 'unknown'
    let engine = 'unknown'

    // Simple browser detection
    if (userAgent.includes('Chrome')) {
      name = 'Chrome'
      const match = userAgent.match(/Chrome\/(\d+)/)
      if (match) version = match[1]
    } else if (userAgent.includes('Firefox')) {
      name = 'Firefox'
      const match = userAgent.match(/Firefox\/(\d+)/)
      if (match) version = match[1]
    } else if (userAgent.includes('Safari')) {
      name = 'Safari'
      const match = userAgent.match(/Version\/(\d+)/)
      if (match) version = match[1]
    } else if (userAgent.includes('Edge')) {
      name = 'Edge'
      const match = userAgent.match(/Edge\/(\d+)/)
      if (match) version = match[1]
    }

    return {
      name,
      version,
      engine,
      language: navigator.language,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    }
  }

  /**
   * Update session analytics based on event
   */
  private updateSessionAnalytics(event: UserTestingEvent): void {
    if (!this.currentSession) return

    switch (event.type) {
      case 'field_interaction':
        if (this.currentSession?.analytics?.fieldsModified && !this.currentSession.analytics.fieldsModified.includes(event.data.field)) {
          this.currentSession.analytics.fieldsModified.push(event.data.field)
        }
        if (this.currentSession?.analytics && this.currentSession.analytics.timeToFirstInteraction === 0) {
          this.currentSession.analytics.timeToFirstInteraction = Date.now() - this.currentSession.startTime.getTime()
        }
        break

      case 'step_change':
        if (this.currentSession?.analytics) {
          this.currentSession.analytics.stepsCompleted = Math.max(
            this.currentSession.analytics.stepsCompleted || 0,
            event.data.step
          )
        }
        break

      case 'ai_usage':
        if (this.currentSession?.analytics?.aiSuggestionsUsed && !this.currentSession.analytics.aiSuggestionsUsed.includes(event.data.type)) {
          this.currentSession.analytics.aiSuggestionsUsed.push(event.data.type)
        }
        break

      case 'error':
        if (this.currentSession?.analytics?.errorsEncountered) {
          this.currentSession.analytics.errorsEncountered.push(event.data.error)
        }
        break
    }
  }

  /**
   * Send session data to analytics service
   */
  private async sendSessionData(session: UserTestingSession): Promise<void> {
    try {
      // Send to your analytics service
      if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('event', 'user_testing_session', {
          session_id: session.sessionId,
          variant: session.variant,
          completed: session.completed,
          abandoned: session.abandoned,
          completion_time: session.endTime ? session.endTime.getTime() - session.startTime.getTime() : 0,
          device_type: session.deviceInfo.type,
          browser: session.browserInfo.name
        })
      }

      // Send to your backend API
      await fetch('/api/analytics/user-testing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(session)
      })
    } catch (error) {
      console.error('Failed to send session data:', error)
    }
  }

  /**
   * Send event data to analytics service
   */
  private async sendEventData(event: UserTestingEvent): Promise<void> {
    try {
      // Send to your analytics service
      if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('event', 'user_testing_event', {
          event_type: event.type,
          session_id: event.sessionId,
          variant: event.variant,
          timestamp: event.timestamp.toISOString(),
          ...event.data
        })
      }
    } catch (error) {
      console.error('Failed to send event data:', error)
    }
  }
}

/**
 * User Testing Hook for React Components
 */
export function useUserTesting(variant: FormVariant, userId?: string) {
  const manager = UserTestingManager.getInstance()

  const startSession = () => {
    return manager.startSession(variant, userId)
  }

  const completeSession = (analytics: FormAnalytics) => {
    manager.completeSession(analytics)
  }

  const abandonSession = (abandonmentPoint: string) => {
    manager.abandonSession(abandonmentPoint)
  }

  const trackEvent = (type: UserTestingEvent['type'], data: any) => {
    const currentSession = manager.getCurrentSession()
    if (currentSession) {
      manager.trackEvent({
        type,
        timestamp: new Date(),
        data,
        sessionId: currentSession.sessionId,
        variant: currentSession.variant
      })
    }
  }

  const collectFeedback = (feedback: Omit<UserFeedback, 'submittedAt'>) => {
    manager.collectFeedback(feedback)
  }

  const getCurrentSession = () => {
    return manager.getCurrentSession()
  }

  const getTestingStats = () => {
    return manager.getTestingStats()
  }

  return {
    startSession,
    completeSession,
    abandonSession,
    trackEvent,
    collectFeedback,
    getCurrentSession,
    getTestingStats
  }
}

/**
 * Export singleton instance
 */
export const userTestingManager = UserTestingManager.getInstance()

// Global type declaration for gtag
declare global {
  interface Window {
    gtag?: (...args: any[]) => void
  }
}