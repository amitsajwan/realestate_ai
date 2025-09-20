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
          onboarding_completed: state.user?.onboarding_completed
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

      // Check if user needs onboarding with better validation
      const needsOnboarding = state.user && 
        (state.user.onboarding_completed === false || 
         state.user.onboarding_completed === undefined ||
         (state.user.onboarding_step && state.user.onboarding_step < 6))
      
      if (needsOnboarding) {
        logger.info('[DashboardPage] Onboarding not completed, checking redirect conditions', {
          component: 'DashboardPage',
          action: 'onboarding_check',
          metadata: {
            onboarding_completed: state.user?.onboarding_completed,
            onboarding_step: state.user?.onboarding_step,
            needsOnboarding
          }
        })
        
        // Add a flag to prevent redirect loops
        const redirectedFromOnboarding = sessionStorage.getItem('redirected_from_onboarding')
        if (redirectedFromOnboarding === 'true') {
          logger.warn('[DashboardPage] Detected potential redirect loop, staying on dashboard', {
            component: 'DashboardPage',
            action: 'loop_prevention'
          })
          sessionStorage.removeItem('redirected_from_onboarding')
          setIsLoading(false)
          return
        }
        
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