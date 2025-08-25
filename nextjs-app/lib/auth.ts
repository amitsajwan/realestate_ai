// Authentication utilities for PropertyAI

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

// Simulate API calls
export const authAPI = {
  // Login with email/password
  async login(email: string, password: string): Promise<User> {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Mock user data - for demo purposes
    // Use different emails to test different scenarios
    const isNewUser = email.includes('new') || email.includes('test')
    
    return {
      id: '1',
      email,
      firstName: 'John',
      lastName: 'Doe',
      phone: '+91 98765 43210',
      company: 'Real Estate Pro',
      position: 'Senior Agent',
      licenseNumber: 'RE123456',
      facebookConnected: false,
      onboardingCompleted: !isNewUser, // New users need onboarding, existing users don't
      onboardingStep: isNewUser ? 1 : 7
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
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    return {
      id: '1',
      email: userData.email,
      firstName: userData.firstName,
      lastName: userData.lastName,
      phone: userData.phone,
      facebookConnected: false,
      onboardingCompleted: false,
      onboardingStep: 1
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

// Auth state management
export class AuthManager {
  private static instance: AuthManager
  private listeners: ((state: AuthState) => void)[] = []
  private state: AuthState = {
    user: null,
    isAuthenticated: false,
    isLoading: true
  }

  static getInstance(): AuthManager {
    if (!AuthManager.instance) {
      AuthManager.instance = new AuthManager()
    }
    return AuthManager.instance
  }

  async init() {
    // Check for existing session
    const user = storage.get('user')
    if (user) {
      this.state.user = user
      this.state.isAuthenticated = true
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
    this.notifyListeners()
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
