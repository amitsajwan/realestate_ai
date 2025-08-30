'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { authManager } from '@/lib/auth'
import Dashboard from '../page'

export default function DashboardPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      console.log('[DashboardPage] Initializing dashboard page')
      await authManager.init()
      const state = authManager.getState()
      
      console.log('[DashboardPage] Auth state:', {
        isAuthenticated: state.isAuthenticated,
        hasUser: !!state.user,
        onboardingCompleted: state.user?.onboardingCompleted
      })
      
      if (!state.isAuthenticated) {
        console.log('[DashboardPage] Not authenticated, redirecting to login')
        router.replace('/login')
        return
      }

      if (!state.user?.onboardingCompleted) {
        console.log('[DashboardPage] Onboarding not completed, redirecting to onboarding')
        router.replace('/onboarding')
        return
      }

      // User is authenticated and onboarded, stay on dashboard
      console.log('[DashboardPage] User authenticated and onboarded, showing dashboard')
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