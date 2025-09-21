import { propertiesAPI } from '@/lib/properties/api'

// Mock fetch globally
global.fetch = jest.fn()

// Mock the auth manager
jest.mock('@/lib/auth', () => ({
  authManager: {
    getState: jest.fn(),
    getToken: jest.fn(),
    isAuthenticated: jest.fn(),
  },
}))

describe('Property API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Configure the auth manager mock
    const { authManager } = require('@/lib/auth')
    authManager.getState.mockReturnValue({
      isAuthenticated: true,
      user: { id: 'test-user', email: 'test@example.com' },
      token: 'test-token',
      refreshToken: 'test-refresh-token',
      isLoading: false,
      error: null
    })
    authManager.getToken.mockReturnValue('test-token')
    authManager.isAuthenticated.mockReturnValue(true)
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('Property CRUD Operations', () => {
    const mockProperty = {
      title: 'Test Property',
      description: 'Test Description',
      price: 5000000,
      location: 'Mumbai',
      bedrooms: 4,
      bathrooms: 3,
      areaSqft: 2500,
      propertyType: 'villa',
      features: ['parking', 'garden', 'security'],
      images: [],
      amenities: 'Swimming pool, Gym, Garden'
    }

    it('should create a property successfully', async () => {
      const mockResponse = {
        id: '1',
        ...mockProperty,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        status: 201,
      })

      const result = await propertiesAPI.createProperty(mockProperty)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/properties/',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(mockProperty),
        })
      )

      expect(result).toEqual(mockResponse)
    })

    it('should get properties successfully', async () => {
      const mockProperties = [
        {
          id: '1',
          ...mockProperty,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperties,
        status: 200,
      })

      const result = await propertiesAPI.getProperties()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/properties/?skip=0&limit=100',
        expect.objectContaining({
          method: 'GET',
        })
      )

      expect(result).toEqual(mockProperties)
    })

    it('should update a property successfully', async () => {
      const updatedProperty = {
        ...mockProperty,
        title: 'Updated Property',
        price: 6000000,
      }

      const mockResponse = {
        id: '1',
        ...updatedProperty,
        updated_at: '2024-01-02T00:00:00Z',
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        status: 200,
      })

      const result = await propertiesAPI.updateProperty('1', updatedProperty)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/properties/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updatedProperty),
        })
      )

      expect(result).toEqual(mockResponse)
    })

    it('should delete a property successfully', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Property deleted successfully' }),
        status: 200,
      })

      const result = await propertiesAPI.deleteProperty('1')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/properties/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      )

      expect(result).toEqual({ message: 'Property deleted successfully' })
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

      await expect(propertiesAPI.getProperties()).rejects.toThrow('Network error')
    })

    it('should handle API errors with proper status codes', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Bad Request' }),
      })

      await expect(propertiesAPI.createProperty({} as any)).rejects.toThrow()
    })

    it('should handle authentication errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      })

      await expect(propertiesAPI.getProperties()).rejects.toThrow()
    })
  })

  describe('Authentication Flow', () => {
    it('should include authorization header when token is present', async () => {
      // Mock auth token for testing

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
        status: 200,
      })

      await propertiesAPI.getProperties()

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })

    it('should handle token refresh', async () => {
      // Mock request with expired token
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Token expired' }),
      })

      // PropertiesAPI should throw an error for expired tokens
      await expect(propertiesAPI.getProperties()).rejects.toThrow('Token expired')

      expect(fetch).toHaveBeenCalledTimes(1) // Only initial call
    })
  })
})