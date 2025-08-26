// Authentication utilities for PropertyAI

import { apiService } from './api'

export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  phone?: string
  company?: string
  position?: string
  licenseNumber?: string
  facebookConnected: boolean
  onboardingCompleted: boolean
  onboardingStep: number
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

// Enhanced token management with expiration handling
class TokenManager {
  private static readonly TOKEN_KEY = 'auth_token'
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token'
  private static readonly TOKEN_EXPIRY_KEY = 'token_expiry'

  static setTokens(accessToken: string, refreshToken?: string, expiresIn?: number) {
    if (typeof window === 'undefined') return

    const expiryTime = expiresIn ? Date.now() + (expiresIn * 1000) : null
    
    localStorage.setItem(this.TOKEN_KEY, accessToken)
    if (refreshToken) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken)
    }
    if (expiryTime) {
      localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime.toString())
    }
  }

  static getAccessToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(this.TOKEN_KEY)
  }

  static getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(this.REFRESH_TOKEN_KEY)
  }

  static isTokenExpired(): boolean {
    if (typeof window === 'undefined') return true
    
    const expiryTime = localStorage.getItem(this.TOKEN_EXPIRY_KEY)
    if (!expiryTime) return true
    
    // Consider token expired if it expires within 5 minutes
    const bufferTime = 5 * 60 * 1000 // 5 minutes
    return Date.now() + bufferTime >= parseInt(expiryTime)
  }

  static clearTokens() {
    if (typeof window === 'undefined') return
    
    localStorage.removeItem(this.TOKEN_KEY)
    localStorage.removeItem(this.REFRESH_TOKEN_KEY)
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY)
  }

  static shouldRefreshToken(): boolean {
    return this.isTokenExpired() && !!this.getRefreshToken()
  }
}

// Enhanced API calls with automatic token refresh
export const authAPI = {
  // Login with email/password
  async login(email: string, password: string): Promise<User> {
    try {
      const response = await apiService.login(email, password)
      
      if (response.success && response.access_token) {
        // Store tokens with expiration
        TokenManager.setTokens(
          response.access_token,
          response.refresh_token,
          response.expires_in || 3600 // Default 1 hour
        )
        
        // Set token in API service
        apiService.setToken(response.access_token)
        
        // Mock user data - for demo purposes
        // Use different emails to test different scenarios
        const isNewUser = email.includes('new') || email.includes('test') || email.includes('onboarding')
        
        const userObj = {
          id: response.user_id || '1',
          email,
          firstName: isNewUser ? '' : 'John',
          lastName: isNewUser ? '' : 'Doe',
          phone: isNewUser ? '' : '+91 98765 43210',
          company: isNewUser ? '' : 'Real Estate Pro',
          position: isNewUser ? '' : 'Senior Agent',
          licenseNumber: isNewUser ? '' : 'RE123456',
          facebookConnected: false,
          onboardingCompleted: response.onboarding_completed !== undefined ? response.onboarding_completed : !isNewUser,
          onboardingStep: response.onboarding_completed === true ? 7 : (isNewUser ? 1 : 7)
        }
        return userObj
      } else {
        throw new Error(response.message || 'Login failed')
      }
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  },

  // Register new user
  async register(userData: {
    email: string
    password: string
    firstName: string
    lastName: string
    phone?: string
  }): Promise<User> {
    try {
      const response = await apiService.register({
        name: `${userData.firstName} ${userData.lastName}`,
        email: userData.email,
        password: userData.password
      })
      
      if (response.success && response.access_token) {
        // Store tokens
        TokenManager.setTokens(
          response.access_token,
          response.refresh_token,
          response.expires_in || 3600
        )
        
        // Set token in API service
        apiService.setToken(response.access_token)
        
        return {
          id: response.user_id || '1',
          email: userData.email,
          firstName: userData.firstName,
          lastName: userData.lastName,
          phone: userData.phone,
          facebookConnected: false,
          onboardingCompleted: false,
          onboardingStep: 1
        }
      } else {
        throw new Error(response.message || 'Registration failed')
      }
    } catch (error) {
      console.error('Registration error:', error)
      throw error
    }
  },

  // Refresh token
  async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = TokenManager.getRefreshToken()
      if (!refreshToken) {
        return false
      }

      // TODO: Implement actual refresh token endpoint
      // const response = await apiService.refreshToken(refreshToken)
      
      // For now, simulate successful refresh
      const currentToken = TokenManager.getAccessToken()
      if (currentToken) {
        // Extend token expiry by 1 hour
        TokenManager.setTokens(currentToken, refreshToken, 3600)
        return true
      }
      
      return false
    } catch (error) {
      console.error('Token refresh error:', error)
      return false
    }
  },

  // Update onboarding progress
  async updateOnboarding(userId: string, step: number, data: Partial<User>): Promise<User> {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    return {
      id: userId,
      email: 'john@example.com',
      firstName: 'John',
      lastName: 'Doe',
      facebookConnected: false,
      ...data,
      onboardingStep: step,
      onboardingCompleted: step >= 7
    }
  },

  // Connect Facebook
  async connectFacebook(userId: string, facebookData: any): Promise<User> {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    return {
      id: userId,
      email: 'john@example.com',
      firstName: 'John',
      lastName: 'Doe',
      facebookConnected: true,
      onboardingCompleted: true,
      onboardingStep: 7
    }
  }
}

// Local storage utilities
export const storage = {
  get(key: string) {
    if (typeof window === 'undefined') return null
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch {
      return null
    }
  },

  set(key: string, value: any) {
    if (typeof window === 'undefined') return
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // Handle error
    }
  },

  remove(key: string) {
    if (typeof window === 'undefined') return
    try {
      localStorage.removeItem(key)
    } catch {
      // Handle error
    }
  }
}

// Enhanced Auth state management with token refresh
export class AuthManager {
  private static instance: AuthManager
  private listeners: ((state: AuthState) => void)[] = []
  private state: AuthState = {
    user: null,
    isAuthenticated: false,
    isLoading: true
  }
  private tokenRefreshInterval: NodeJS.Timeout | null = null

  static getInstance(): AuthManager {
    if (!AuthManager.instance) {
      AuthManager.instance = new AuthManager()
    }
    return AuthManager.instance
  }

  async init() {
    console.log('[AuthManager] Initializing auth manager...')
    
    // Check for Facebook OAuth token from URL parameters
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search)
      const facebookToken = urlParams.get('token')
      const authSuccess = urlParams.get('auth') === 'success'
      
      console.log('[AuthManager] URL params found:', {
        hasToken: !!facebookToken,
        hasAuthSuccess: authSuccess,
        fullUrl: window.location.href,
        params: Object.fromEntries(urlParams.entries())
      })
      
      if (facebookToken && authSuccess) {
        console.log('[AuthManager] Processing Facebook OAuth token...')
        
        try {
          // Decode the JWT to get user info
          const tokenParts = facebookToken.split('.')
          if (tokenParts.length === 3) {
            const payload = JSON.parse(atob(tokenParts[1]))
            console.log('[AuthManager] Decoded token payload:', payload)
            
            const user = {
              id: payload.user_id || payload.sub || '1',
              email: payload.email || 'user@example.com',
              firstName: payload.first_name || 'User',
              lastName: payload.last_name || 'Name',
              facebookConnected: true,
              onboardingCompleted: payload.onboarding_completed || false,
              onboardingStep: payload.onboarding_step || 1
            }
            
            console.log('[AuthManager] Created user object:', user)
            
            // Store the token and user
            TokenManager.setTokens(facebookToken, facebookToken, 3600)
            storage.set('user', user)
            
            console.log('[AuthManager] Stored tokens and user in localStorage')
            console.log('[AuthManager] localStorage after storage:', {
              access_token: localStorage.getItem('access_token'),
              user: localStorage.getItem('user')
            })
            
            this.state.user = user
            this.state.isAuthenticated = true
            
            // Set token in API service
            apiService.setToken(facebookToken)
            
            // Start token refresh monitoring
            this.startTokenRefreshMonitoring()
            
            // Clean URL parameters
            console.log('[AuthManager] Cleaning URL parameters...')
            window.history.replaceState({}, document.title, '/')
            
            console.log('[AuthManager] Facebook OAuth processing completed successfully')
          } else {
            console.error('[AuthManager] Invalid token format:', facebookToken)
          }
        } catch (error) {
          console.error('[AuthManager] Error handling Facebook OAuth token:', error)
        }
      } else {
        console.log('[AuthManager] No Facebook OAuth parameters found, checking existing session...')
      }
    }
    
    // Check for existing session and token validity
    const user = storage.get('user')
    const accessToken = TokenManager.getAccessToken()
    
    if (user && accessToken && !this.state.isAuthenticated) {
      // Check if token needs refresh
      if (TokenManager.shouldRefreshToken()) {
        const refreshSuccess = await authAPI.refreshToken()
        if (!refreshSuccess) {
          // Token refresh failed, clear everything
          this.logout()
          this.state.isLoading = false
          this.notifyListeners()
          return
        }
      }
      
      this.state.user = user
      this.state.isAuthenticated = true
      
      // Set token in API service
      apiService.setToken(accessToken)
      
      // Start token refresh monitoring
      this.startTokenRefreshMonitoring()
    }
    
    this.state.isLoading = false
    this.notifyListeners()
  }

  async login(email: string, password: string) {
    this.state.isLoading = true
    this.notifyListeners()

    try {
      const user = await authAPI.login(email, password)
      this.state.user = user
      this.state.isAuthenticated = true
      storage.set('user', user)
      
      // Start token refresh monitoring
      this.startTokenRefreshMonitoring()
      
      return user
    } catch (error) {
      throw error
    } finally {
      this.state.isLoading = false
      this.notifyListeners()
    }
  }

  async register(userData: any) {
    this.state.isLoading = true
    this.notifyListeners()

    try {
      const user = await authAPI.register(userData)
      this.state.user = user
      this.state.isAuthenticated = true
      storage.set('user', user)
      
      // Start token refresh monitoring
      this.startTokenRefreshMonitoring()
      
      return user
    } catch (error) {
      throw error
    } finally {
      this.state.isLoading = false
      this.notifyListeners()
    }
  }

  async updateOnboarding(step: number, data: Partial<User>) {
    if (!this.state.user) return

    try {
      const user = await authAPI.updateOnboarding(this.state.user.id, step, data)
      this.state.user = user
      storage.set('user', user)
      this.notifyListeners()
      return user
    } catch (error) {
      throw error
    }
  }

  logout() {
    this.state.user = null
    this.state.isAuthenticated = false
    storage.remove('user')
    TokenManager.clearTokens()
    apiService.clearToken()
    
    // Stop token refresh monitoring
    this.stopTokenRefreshMonitoring()
    
    this.notifyListeners()
  }

  // Start monitoring token expiration and auto-refresh
  private startTokenRefreshMonitoring() {
    if (this.tokenRefreshInterval) {
      clearInterval(this.tokenRefreshInterval)
    }
    
    // Check token every 5 minutes
    this.tokenRefreshInterval = setInterval(async () => {
      if (TokenManager.shouldRefreshToken()) {
        const refreshSuccess = await authAPI.refreshToken()
        if (!refreshSuccess) {
          // Auto logout on refresh failure
          this.logout()
        }
      }
    }, 5 * 60 * 1000) // 5 minutes
  }

  // Stop token refresh monitoring
  private stopTokenRefreshMonitoring() {
    if (this.tokenRefreshInterval) {
      clearInterval(this.tokenRefreshInterval)
      this.tokenRefreshInterval = null
    }
  }

  getState(): AuthState {
    return { ...this.state }
  }

  subscribe(listener: (state: AuthState) => void) {
    this.listeners.push(listener)
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener)
    }
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.getState()))
  }
}

export const authManager = AuthManager.getInstance()

// Export TokenManager for testing
export { TokenManager }
