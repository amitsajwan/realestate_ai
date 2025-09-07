'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { apiService } from '@/lib/api'
import { toast } from 'react-hot-toast'

interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  phone?: string
  is_active: boolean
  onboarding_completed: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  signup: (userData: any) => Promise<void>
  refreshUser: () => Promise<void>
  getSessionId: () => string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [sessionId] = useState(() => {
    // Generate or retrieve session ID
    if (typeof window !== 'undefined') {
      let sessionId = localStorage.getItem('sessionId')
      if (!sessionId) {
        sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        localStorage.setItem('sessionId', sessionId)
      }
      return sessionId
    }
    return `session_${Date.now()}`
  })
  const router = useRouter()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setIsLoading(false)
        return
      }

      const response = await apiService.getCurrentUser()
      if (response.success && response.data) {
        setUser(response.data)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      localStorage.removeItem('token')
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await apiService.login({ email, password })
      if (response.success && response.data) {
        localStorage.setItem('token', response.data.access_token)
        await checkAuth()
        toast.success('Logged in successfully!')
        router.push('/dashboard')
      }
    } catch (error: any) {
      console.error('Login failed:', error)
      toast.error(error.message || 'Login failed')
      throw error
    }
  }

  const logout = async () => {
    try {
      localStorage.removeItem('token')
      setUser(null)
      toast.success('Logged out successfully!')
      router.push('/login')
    } catch (error) {
      console.error('Logout failed:', error)
      toast.error('Logout failed')
    }
  }

  const signup = async (userData: any) => {
    try {
      const response = await apiService.signup(userData)
      if (response.success && response.data) {
        localStorage.setItem('token', response.data.access_token)
        await checkAuth()
        toast.success('Account created successfully!')
        router.push('/onboarding')
      }
    } catch (error: any) {
      console.error('Signup failed:', error)
      toast.error(error.message || 'Signup failed')
      throw error
    }
  }

  const refreshUser = async () => {
    await checkAuth()
  }

  const getSessionId = () => sessionId

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    signup,
    refreshUser,
    getSessionId
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}