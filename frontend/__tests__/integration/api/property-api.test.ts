import { APIService } from '@/lib/api'

// Mock fetch globally
global.fetch = jest.fn()

describe('Property API Integration', () => {
  let apiService: APIService

  beforeEach(() => {
    apiService = new APIService()
    jest.clearAllMocks()
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('Property CRUD Operations', () => {
    const mockProperty = {
      title: 'Test Property',
      description: 'Test Description',
      price: 5000000,
      address: '123 Test St',
      location: 'Mumbai',
      bedrooms: 4,
      bathrooms: 3,
      area: 2500,
      area_sqft: 2500,
      type: 'villa',
      property_type: 'villa',
      status: 'for-sale' as const,
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

      const result = await apiService.createProperty(mockProperty)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/properties/properties/',
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

      const result = await apiService.getProperties()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/properties/properties/',
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

      const result = await apiService.updateProperty('1', updatedProperty)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/properties/properties/1',
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

      const result = await apiService.deleteProperty('1')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/properties/properties/1',
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

      await expect(apiService.getProperties()).rejects.toThrow('Network error')
    })

    it('should handle API errors with proper status codes', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Bad Request' }),
      })

      await expect(apiService.createProperty({} as any)).rejects.toThrow()
    })

    it('should handle authentication errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      })

      await expect(apiService.getProperties()).rejects.toThrow()
    })
  })

  describe('Authentication Flow', () => {
    it('should include authorization header when token is present', async () => {
      apiService.setToken('test-token')

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
        status: 200,
      })

      await apiService.getProperties()

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
      // Mock initial request with expired token
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Token expired' }),
        })
        // Mock token refresh
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ access_token: 'new-token' }),
        })
        // Mock retry with new token
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })

      apiService.setToken('expired-token')
      await apiService.getProperties()

      expect(fetch).toHaveBeenCalledTimes(3) // Initial + refresh + retry
    })
  })
})