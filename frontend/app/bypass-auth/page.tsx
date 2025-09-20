'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

export default function BypassAuthPage() {
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Simulate bypassing authentication
    const mockUser = {
      id: '68c815c945c1268def229bc1',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      onboarding_completed: true,
      onboarding_step: 6
    }

    // Store mock user in localStorage
    localStorage.setItem('auth_user', JSON.stringify(mockUser))
    localStorage.setItem('auth_token', 'mock_token_123')
    localStorage.setItem('auth_authenticated', 'true')

    // Redirect to main dashboard
    setTimeout(() => {
      router.push('/')
    }, 1000)
  }, [router])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-white">Bypassing authentication...</p>
        <p className="text-gray-300 text-sm mt-2">Redirecting to dashboard...</p>
      </div>
    </div>
  )
}