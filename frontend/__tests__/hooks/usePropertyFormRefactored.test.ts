/**
 * Test cases for Refactored Property Form Hook
 * ============================================
 * 
 * Comprehensive tests for the simplified property form hook
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { usePropertyFormRefactored } from '@/hooks/usePropertyFormRefactored'
import { apiService } from '@/lib/api'
import toast from 'react-hot-toast'

// Mock dependencies
jest.mock('@/lib/api')
jest.mock('react-hot-toast')
jest.mock('@/lib/validation', () => ({
  propertySchema: {
    parse: jest.fn((data) => data),
    safeParse: jest.fn((data) => ({ success: true, data }))
  }
}))

const mockApiService = apiService as jest.Mocked<typeof apiService>
const mockToast = toast as jest.Mocked<typeof toast>

describe('usePropertyFormRefactored', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    })
  })

  describe('Form Initialization', () => {
    test('should initialize with default values', () => {
      const { result } = renderHook(() => usePropertyFormRefactored())

      expect(result.current.state.isLoading).toBe(false)
      expect(result.current.state.isSubmitting).toBe(false)
      expect(result.current.state.isValid).toBe(false)
      expect(result.current.state.isDirty).toBe(false)
      expect(result.current.aiSuggestions).toBeNull()
      expect(result.current.isAILoading).toBe(false)
      expect(result.current.marketInsights).toBeNull()
    })

    test('should initialize with custom options', () => {
      const options = {
        enableAI: true,
        enableMarketInsights: true,
        autoSave: true
      }

      const { result } = renderHook(() => usePropertyFormRefactored(options))

      expect(result.current.state.isLoading).toBe(false)
      expect(result.current.aiSuggestions).toBeNull()
      expect(result.current.marketInsights).toBeNull()
    })
  })

  describe('Form State Management', () => {
    test('should update form state when submitting', async () => {
      mockApiService.createProperty.mockResolvedValue({
        success: true,
        data: { id: '123' }
      })

      const { result } = renderHook(() => usePropertyFormRefactored())

      await act(async () => {
        await result.current.onSubmit({
          title: 'Test Property',
          description: 'Test Description',
          propertyType: 'Apartment',
          bedrooms: 2,
          bathrooms: 2,
          area: 1200,
          price: '5000000',
          location: 'Mumbai',
          address: '123 Test Street',
          amenities: 'Parking, Gym'
        })
      })

      expect(result.current.state.isSubmitting).toBe(false)
    })

    test('should handle form submission errors', async () => {
      const errorMessage = 'Failed to create property'
      mockApiService.createProperty.mockRejectedValue(new Error(errorMessage))

      const onError = jest.fn()
      const { result } = renderHook(() => usePropertyFormRefactored({ onError }))

      await act(async () => {
        await result.current.onSubmit({
          title: 'Test Property',
          description: 'Test Description',
          propertyType: 'Apartment',
          bedrooms: 2,
          bathrooms: 2,
          area: 1200,
          price: '5000000',
          location: 'Mumbai',
          address: '123 Test Street',
          amenities: 'Parking, Gym'
        })
      })

      expect(mockToast.error).toHaveBeenCalledWith(errorMessage)
      expect(onError).toHaveBeenCalled()
    })
  })

  describe('AI Integration', () => {
    test('should generate AI suggestions successfully', async () => {
      const mockSuggestions = {
        title: 'AI Generated Title',
        description: 'AI Generated Description',
        price: '5500000',
        amenities: 'AI Generated Amenities'
      }

      mockApiService.getAIPropertySuggestions.mockResolvedValue({
        success: true,
        data: [mockSuggestions]
      })

      const { result } = renderHook(() => usePropertyFormRefactored({ enableAI: true }))

      await act(async () => {
        await result.current.generateAISuggestions()
      })

      expect(result.current.aiSuggestions).toEqual({
        title: mockSuggestions.title,
        description: mockSuggestions.description,
        price: mockSuggestions.price,
        amenities: mockSuggestions.amenities,
        qualityScore: 85
      })
      expect(mockToast.success).toHaveBeenCalledWith('AI suggestions generated successfully!')
    })

    test('should handle AI suggestion generation errors', async () => {
      const errorMessage = 'AI service unavailable'
      mockApiService.getAIPropertySuggestions.mockRejectedValue(new Error(errorMessage))

      const { result } = renderHook(() => usePropertyFormRefactored({ enableAI: true }))

      await act(async () => {
        await result.current.generateAISuggestions()
      })

      expect(result.current.aiSuggestions).toBeNull()
      expect(mockToast.error).toHaveBeenCalledWith('Failed to generate AI suggestions. Please try again.')
    })

    test('should apply AI suggestions with confirmation', async () => {
      const mockSuggestions = {
        title: 'AI Generated Title',
        description: 'AI Generated Description',
        price: '5500000',
        amenities: 'AI Generated Amenities'
      }

      mockApiService.getAIPropertySuggestions.mockResolvedValue({
        success: true,
        data: [mockSuggestions]
      })

      // Mock window.confirm
      window.confirm = jest.fn(() => true)

      const { result } = renderHook(() => usePropertyFormRefactored({ enableAI: true }))

      // Generate suggestions first
      await act(async () => {
        await result.current.generateAISuggestions()
      })

      // Apply suggestions
      await act(async () => {
        result.current.applyAISuggestions()
      })

      expect(window.confirm).toHaveBeenCalled()
      expect(mockToast.success).toHaveBeenCalledWith('AI suggestions applied!')
    })

    test('should not apply AI suggestions if user cancels', async () => {
      const mockSuggestions = {
        title: 'AI Generated Title',
        description: 'AI Generated Description',
        price: '5500000',
        amenities: 'AI Generated Amenities'
      }

      mockApiService.getAIPropertySuggestions.mockResolvedValue({
        success: true,
        data: [mockSuggestions]
      })

      // Mock window.confirm to return false
      window.confirm = jest.fn(() => false)

      const { result } = renderHook(() => usePropertyFormRefactored({ enableAI: true }))

      // Generate suggestions first
      await act(async () => {
        await result.current.generateAISuggestions()
      })

      // Try to apply suggestions
      await act(async () => {
        result.current.applyAISuggestions()
      })

      expect(window.confirm).toHaveBeenCalled()
      expect(mockToast.success).not.toHaveBeenCalledWith('AI suggestions applied!')
    })
  })

  describe('Market Insights', () => {
    test('should generate market insights', async () => {
      const { result } = renderHook(() => usePropertyFormRefactored({ enableMarketInsights: true }))

      await act(async () => {
        await result.current.generateMarketInsights()
      })

      expect(result.current.marketInsights).toEqual({
        averagePrice: 3200000,
        priceRange: [2800000, 4200000],
        marketTrend: 'rising',
        competitorCount: 12
      })
    })

    test('should not generate market insights when disabled', async () => {
      const { result } = renderHook(() => usePropertyFormRefactored({ enableMarketInsights: false }))

      await act(async () => {
        await result.current.generateMarketInsights()
      })

      expect(result.current.marketInsights).toBeNull()
    })
  })

  describe('Auto-save Functionality', () => {
    test('should save form data to localStorage when auto-save is enabled', async () => {
      const { result } = renderHook(() => usePropertyFormRefactored({ autoSave: true }))

      // Mock form data
      const formData = {
        title: 'Test Property',
        description: 'Test Description'
      }

      // Simulate form data change
      await act(async () => {
        result.current.setValue('title', formData.title)
        result.current.setValue('description', formData.description)
      })

      // Wait for auto-save timeout
      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'property-form-draft',
          expect.stringContaining('Test Property')
        )
      }, { timeout: 2000 })
    })

    test('should load draft data from localStorage on mount', () => {
      const draftData = {
        title: 'Draft Property',
        description: 'Draft Description'
      }

      ;(localStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(draftData))

      renderHook(() => usePropertyFormRefactored({ autoSave: true }))

      expect(localStorage.getItem).toHaveBeenCalledWith('property-form-draft')
    })

    test('should clear draft data after successful submission', async () => {
      mockApiService.createProperty.mockResolvedValue({
        success: true,
        data: { id: '123' }
      })

      const { result } = renderHook(() => usePropertyFormRefactored({ autoSave: true }))

      await act(async () => {
        await result.current.onSubmit({
          title: 'Test Property',
          description: 'Test Description',
          propertyType: 'Apartment',
          bedrooms: 2,
          bathrooms: 2,
          area: 1200,
          price: '5000000',
          location: 'Mumbai',
          address: '123 Test Street',
          amenities: 'Parking, Gym'
        })
      })

      expect(localStorage.removeItem).toHaveBeenCalledWith('property-form-draft')
    })
  })

  describe('Form Validation', () => {
    test('should validate form data before submission', async () => {
      mockApiService.createProperty.mockResolvedValue({
        success: true,
        data: { id: '123' }
      })

      const { result } = renderHook(() => usePropertyFormRefactored())

      await act(async () => {
        await result.current.onSubmit({
          title: 'Test Property',
          description: 'Test Description',
          propertyType: 'Apartment',
          bedrooms: 2,
          bathrooms: 2,
          area: 1200,
          price: '5000000',
          location: 'Mumbai',
          address: '123 Test Street',
          amenities: 'Parking, Gym'
        })
      })

      expect(mockApiService.createProperty).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test Property',
          type: 'Apartment',
          bedrooms: 2,
          bathrooms: 2,
          price: 5000000,
          price_unit: 'INR',
          city: 'Mumbai',
          area: 1200,
          address: '123 Test Street',
          description: 'Test Description',
          amenities: ['Parking', 'Gym']
        })
      )
    })
  })

  describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      const apiError = new Error('API Error')
      mockApiService.createProperty.mockRejectedValue(apiError)

      const onError = jest.fn()
      const { result } = renderHook(() => usePropertyFormRefactored({ onError }))

      await act(async () => {
        await result.current.onSubmit({
          title: 'Test Property',
          description: 'Test Description',
          propertyType: 'Apartment',
          bedrooms: 2,
          bathrooms: 2,
          area: 1200,
          price: '5000000',
          location: 'Mumbai',
          address: '123 Test Street',
          amenities: 'Parking, Gym'
        })
      })

      expect(mockToast.error).toHaveBeenCalledWith('API Error')
      expect(onError).toHaveBeenCalledWith(apiError)
    })

    test('should handle localStorage errors gracefully', () => {
      // Mock localStorage to throw error
      ;(localStorage.getItem as jest.Mock).mockImplementation(() => {
        throw new Error('localStorage error')
      })

      // Should not throw error
      expect(() => {
        renderHook(() => usePropertyFormRefactored({ autoSave: true }))
      }).not.toThrow()
    })
  })

  describe('Success Callbacks', () => {
    test('should call onSuccess callback after successful submission', async () => {
      const responseData = { id: '123', title: 'Test Property' }
      mockApiService.createProperty.mockResolvedValue({
        success: true,
        data: responseData
      })

      const onSuccess = jest.fn()
      const { result } = renderHook(() => usePropertyFormRefactored({ onSuccess }))

      await act(async () => {
        await result.current.onSubmit({
          title: 'Test Property',
          description: 'Test Description',
          propertyType: 'Apartment',
          bedrooms: 2,
          bathrooms: 2,
          area: 1200,
          price: '5000000',
          location: 'Mumbai',
          address: '123 Test Street',
          amenities: 'Parking, Gym'
        })
      })

      expect(onSuccess).toHaveBeenCalledWith({ success: true, data: responseData })
      expect(mockToast.success).toHaveBeenCalledWith('Property added successfully!')
    })
  })
})
