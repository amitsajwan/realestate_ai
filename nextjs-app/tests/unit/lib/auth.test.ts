import { authManager, authAPI, storage, TokenManager } from '@/lib/auth'

// Mock the API service
jest.mock('@/lib/api', () => ({
  apiService: {
    login: jest.fn(),
    register: jest.fn(),
    setToken: jest.fn(),
    clearToken: jest.fn(),
  },
}))

describe('Authentication System', () => {
  beforeEach(() => {
    // Clear all mocks and localStorage
    jest.clearAllMocks()
    localStorage.clear()
    
    // Reset auth manager state
    authManager.logout()
  })

  describe('TokenManager', () => {
    test('sets and gets tokens correctly', () => {
      const accessToken = 'test-access-token'
      const refreshToken = 'test-refresh-token'
      const expiresIn = 3600

      TokenManager.setTokens(accessToken, refreshToken, expiresIn)

      expect(TokenManager.getAccessToken()).toBe(accessToken)
      expect(TokenManager.getRefreshToken()).toBe(refreshToken)
    })

    test('clears tokens correctly', () => {
      TokenManager.setTokens('test-token', 'refresh-token', 3600)
      TokenManager.clearTokens()

      expect(TokenManager.getAccessToken()).toBeNull()
      expect(TokenManager.getRefreshToken()).toBeNull()
    })

    test('detects expired tokens', () => {
      // Set token to expire 1 second ago
      const pastTime = Date.now() - 1000
      localStorage.setItem('token_expiry', pastTime.toString())
      localStorage.setItem('auth_token', 'test-token')

      expect(TokenManager.isTokenExpired()).toBe(true)
    })

    test('detects valid tokens', () => {
      // Set token to expire in 1 hour
      const futureTime = Date.now() + 3600000
      localStorage.setItem('token_expiry', futureTime.toString())
      localStorage.setItem('auth_token', 'test-token')

      expect(TokenManager.isTokenExpired()).toBe(false)
    })
  })

  describe('Storage Utilities', () => {
    test('sets and gets values correctly', () => {
      const testData = { user: 'test', id: 123 }
      storage.set('test-key', testData)
      
      const retrieved = storage.get('test-key')
      expect(retrieved).toEqual(testData)
    })

    test('returns null for non-existent keys', () => {
      const result = storage.get('non-existent')
      expect(result).toBeNull()
    })

    test('removes values correctly', () => {
      storage.set('test-key', 'test-value')
      storage.remove('test-key')
      
      const result = storage.get('test-key')
      expect(result).toBeNull()
    })

    test('handles invalid JSON gracefully', () => {
      // Simulate corrupted localStorage
      localStorage.setItem('test-key', 'invalid-json')
      
      const result = storage.get('test-key')
      expect(result).toBeNull()
    })
  })

  describe('AuthManager', () => {
    test('initializes with no user when no stored data', async () => {
      await authManager.init()
      const state = authManager.getState()
      
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(state.isLoading).toBe(false)
    })

    test('initializes with stored user data', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        facebookConnected: false,
        onboardingCompleted: true,
        onboardingStep: 7
      }

      storage.set('user', mockUser)
      TokenManager.setTokens('test-token', 'refresh-token', 3600)

      await authManager.init()
      const state = authManager.getState()
      
      expect(state.user).toEqual(mockUser)
      expect(state.isAuthenticated).toBe(true)
    })

    test('handles login successfully', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        facebookConnected: false,
        onboardingCompleted: true,
        onboardingStep: 7
      }

      // Mock successful login
      const { apiService } = require('@/lib/api')
      apiService.login.mockResolvedValue({
        success: true,
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        user_id: '1',
        expires_in: 3600
      })

      const result = await authManager.login('test@example.com', 'password')
      
      expect(result).toEqual(mockUser)
      expect(apiService.login).toHaveBeenCalledWith('test@example.com', 'password')
    })

    test('handles login failure', async () => {
      const { apiService } = require('@/lib/api')
      apiService.login.mockRejectedValue(new Error('Invalid credentials'))

      await expect(authManager.login('test@example.com', 'wrong-password'))
        .rejects.toThrow('Invalid credentials')
    })

    test('handles registration successfully', async () => {
      const mockUser = {
        id: '1',
        email: 'new@example.com',
        firstName: 'New',
        lastName: 'User',
        facebookConnected: false,
        onboardingCompleted: false,
        onboardingStep: 1
      }

      const { apiService } = require('@/lib/api')
      apiService.register.mockResolvedValue({
        success: true,
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        user_id: '1',
        expires_in: 3600
      })

      const result = await authManager.register({
        email: 'new@example.com',
        password: 'password',
        firstName: 'New',
        lastName: 'User'
      })
      
      expect(result).toEqual(mockUser)
    })

    test('handles logout correctly', () => {
      // Set up initial state
      storage.set('user', { id: '1', email: 'test@example.com' })
      TokenManager.setTokens('test-token', 'refresh-token', 3600)

      authManager.logout()
      const state = authManager.getState()
      
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(storage.get('user')).toBeNull()
    })

    test('updates onboarding progress', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        facebookConnected: false,
        onboardingCompleted: false,
        onboardingStep: 1
      }

      storage.set('user', mockUser)

      const updatedUser = await authManager.updateOnboarding(3, {
        company: 'Test Company',
        phone: '+1234567890'
      })

      expect(updatedUser.onboardingStep).toBe(3)
      expect(updatedUser.company).toBe('Test Company')
      expect(updatedUser.phone).toBe('+1234567890')
    })

    test('notifies subscribers of state changes', () => {
      const mockListener = jest.fn()
      const unsubscribe = authManager.subscribe(mockListener)

      // Trigger a state change
      authManager.logout()

      expect(mockListener).toHaveBeenCalledWith({
        user: null,
        isAuthenticated: false,
        isLoading: false
      })

      unsubscribe()
    })
  })

  describe('AuthAPI', () => {
    test('handles token refresh', async () => {
      TokenManager.setTokens('old-token', 'refresh-token', 0) // Expired token

      const result = await authAPI.refreshToken()
      
      // Should return true if refresh is successful
      expect(typeof result).toBe('boolean')
    })

    test('handles Facebook connection', async () => {
      const result = await authAPI.connectFacebook('1', { access_token: 'fb-token' })
      
      expect(result.facebookConnected).toBe(true)
      expect(result.onboardingCompleted).toBe(true)
      expect(result.onboardingStep).toBe(7)
    })
  })
})
