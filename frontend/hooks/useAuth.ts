import { useState, useEffect } from 'react'

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'agent' | 'user'
  avatar?: string
}

export interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (userData: Partial<User> & { password: string }) => Promise<void>
}

export const useAuth = (): AuthState => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate checking for existing session
    const checkAuth = async () => {
      try {
        // In a real app, this would check localStorage or make an API call
        const storedUser = localStorage.getItem('user')
        if (storedUser) {
          setUser(JSON.parse(storedUser))
        }
      } catch (error) {
        console.error('Auth check failed:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock user data
      const mockUser: User = {
        id: 'user-1',
        email,
        name: email.split('@')[0],
        role: 'admin',
      }
      
      setUser(mockUser)
      localStorage.setItem('user', JSON.stringify(mockUser))
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = (): void => {
    setUser(null)
    localStorage.removeItem('user')
  }

  const register = async (userData: Partial<User> & { password: string }): Promise<void> => {
    setIsLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock user data
      const mockUser: User = {
        id: 'user-1',
        email: userData.email || '',
        name: userData.name || userData.email?.split('@')[0] || '',
        role: userData.role || 'user',
      }
      
      setUser(mockUser)
      localStorage.setItem('user', JSON.stringify(mockUser))
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    register,
  }
}