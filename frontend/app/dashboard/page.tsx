'use client'

import { authManager } from '@/lib/auth'
import { logger } from '@/lib/logger'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import Dashboard from '../page'

export default function DashboardPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      logger.info('[DashboardPage] Initializing dashboard page', {
        component: 'DashboardPage',
        action: 'init'
      })
      await authManager.init()
      const state = authManager.getState()

      logger.debug('[DashboardPage] Auth state', {
        component: 'DashboardPage',
        action: 'auth_check',
        metadata: {
          isAuthenticated: state.isAuthenticated,
          hasUser: !!state.user,
          onboardingCompleted: state.user?.onboardingCompleted
        }
      })

      if (!state.isAuthenticated) {
        logger.info('[DashboardPage] Not authenticated, redirecting to login', {
          component: 'DashboardPage',
          action: 'redirect_login'
        })
        router.replace('/login')
        return
      }

      if (!state.user?.onboardingCompleted) {
        logger.info('[DashboardPage] Onboarding not completed, redirecting to onboarding', {
          component: 'DashboardPage',
          action: 'redirect_onboarding',
          metadata: {
            onboardingCompleted: state.user?.onboardingCompleted,
            onboardingStep: state.user?.onboardingStep,
            userObject: state.user
          }
        })
        router.replace('/onboarding')
        return
      }

      // User is authenticated and onboarded, stay on dashboard
      logger.info('[DashboardPage] User authenticated and onboarded, showing dashboard', {
        component: 'DashboardPage',
        action: 'show_dashboard'
      })
      // Don't redirect - show dashboard content here
      setIsLoading(false)
    }

    initAuth()
  }, [router])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="p-8 bg-white rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-center mb-4">Loading Dashboard...</h1>
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        </div>
      </div>
    )
  }

  return <Dashboard />
}