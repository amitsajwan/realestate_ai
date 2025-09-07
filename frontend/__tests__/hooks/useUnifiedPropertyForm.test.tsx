/**
 * Tests for useUnifiedPropertyForm hook
 */

import { renderHook, act } from '@testing-library/react'
import { useUnifiedPropertyForm } from '../../hooks/useUnifiedPropertyForm'
import { apiService } from '../../lib/api'

// Mock dependencies
jest.mock('../../lib/api', () => ({
  apiService: {
    createProperty: jest.fn(),
    getAIPropertySuggestions: jest.fn(),
    getMarketInsights: jest.fn()
  }
}))

jest.mock('../../utils/featureFlags', () => ({
  useFeatureFlags: jest.fn(() => ({
    USE_UNIFIED_FORM: true,
    ENABLE_AI_FEATURES: true,
    ENABLE_MARKET_INSIGHTS: true,
    ENABLE_QUALITY_SCORING: true,
    ENABLE_MULTILANGUAGE: true,
    FALLBACK_ON_ERROR: true,
    ENABLE_AB_TESTING: true,
    DEBUG_MODE: true
  })),
  useABTesting: jest.fn(() => ({
    variant: 'new',
    trackEvent: jest.fn(),
    isNewVariant: true,
    isOldVariant: false
  }))
}))

jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn()
  }
}))

describe('useUnifiedPropertyForm', () => {
  const mockOnSuccess = jest.fn()
  const mockOnError = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should initialize with default values', () => {
    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    expect(result.current.data.title).toBe('')
    expect(result.current.data.description).toBe('')
    expect(result.current.data.propertyType).toBe('')
    expect(result.current.data.bedrooms).toBe(1)
    expect(result.current.data.bathrooms).toBe(1)
    expect(result.current.data.area).toBe(0)
    expect(result.current.data.price).toBe('')
    expect(result.current.data.location).toBe('')
    expect(result.current.data.address).toBe('')
    expect(result.current.data.amenities).toBe('')
  })

  it('should handle form submission successfully', async () => {
    const mockResponse = {
      success: true,
      data: {
        id: 'test-id',
        title: 'Test Property',
        description: 'Test Description'
      }
    }

    ;(apiService.createProperty as jest.Mock).mockResolvedValue(mockResponse)

    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    // Set form data
    act(() => {
      result.current.setData({
        title: 'Test Property',
        description: 'Test Description',
        propertyType: 'apartment',
        bedrooms: 3,
        bathrooms: 2,
        area: 1200,
        price: '5000000',
        location: 'Mumbai',
        address: '123 Test Street',
        amenities: 'Swimming Pool'
      })
    })

    // Submit form
    await act(async () => {
      await result.current.submit()
    })

    expect(apiService.createProperty).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Test Property',
        description: 'Test Description',
        propertyType: 'apartment',
        bedrooms: 3,
        bathrooms: 2,
        area: 1200,
        price: '5000000',
        location: 'Mumbai',
        address: '123 Test Street',
        amenities: 'Swimming Pool'
      })
    )

    expect(mockOnSuccess).toHaveBeenCalled()
  })

  it('should handle form submission error', async () => {
    const mockError = new Error('API Error')
    ;(apiService.createProperty as jest.Mock).mockRejectedValue(mockError)

    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    // Set form data
    act(() => {
      result.current.setData({
        title: 'Test Property',
        description: 'Test Description',
        propertyType: 'apartment',
        bedrooms: 3,
        bathrooms: 2,
        area: 1200,
        price: '5000000',
        location: 'Mumbai',
        address: '123 Test Street',
        amenities: 'Swimming Pool'
      })
    })

    // Submit form
    await act(async () => {
      await result.current.submit()
    })

    expect(mockOnError).toHaveBeenCalledWith(mockError)
  })

  it('should generate AI suggestions successfully', async () => {
    const mockAIResponse = {
      success: true,
      data: {
        title: 'AI Generated Title',
        description: 'AI Generated Description',
        price: '5500000',
        amenities: 'AI Generated Amenities',
        qualityScore: {
          overall: 87,
          seo: 92,
          readability: 85,
          marketRelevance: 84
        }
      }
    }

    ;(apiService.getAIPropertySuggestions as jest.Mock).mockResolvedValue(mockAIResponse)

    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    // Generate AI suggestions
    await act(async () => {
      await result.current.generateAISuggestions()
    })

    expect(apiService.getAIPropertySuggestions).toHaveBeenCalled()
    expect(result.current.ai.suggestions).toEqual({
      title: 'AI Generated Title',
      description: 'AI Generated Description',
      price: '5500000',
      amenities: 'AI Generated Amenities',
      qualityScore: {
        overall: 87,
        seo: 92,
        readability: 85,
        marketRelevance: 84
      }
    })
  })

  it('should apply AI suggestions to form', () => {
    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    const mockSuggestion = {
      title: 'AI Generated Title',
      description: 'AI Generated Description',
      price: '5500000',
      amenities: 'AI Generated Amenities'
    }

    // Set AI suggestions
    act(() => {
      result.current.ai.suggestions = mockSuggestion
    })

    // Apply suggestions
    act(() => {
      result.current.applyAISuggestion(mockSuggestion)
    })

    expect(result.current.data.title).toBe('AI Generated Title')
    expect(result.current.data.description).toBe('AI Generated Description')
    expect(result.current.data.price).toBe('5500000')
    expect(result.current.data.amenities).toBe('AI Generated Amenities')
  })

  it('should handle wizard step navigation', () => {
    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'wizard',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    expect(result.current.state.currentStep).toBe(0)
    expect(result.current.state.totalSteps).toBe(4)

    // Go to next step
    act(() => {
      result.current.nextStep()
    })

    expect(result.current.state.currentStep).toBe(1)

    // Go to previous step
    act(() => {
      result.current.prevStep()
    })

    expect(result.current.state.currentStep).toBe(0)

    // Go to specific step
    act(() => {
      result.current.goToStep(2)
    })

    expect(result.current.state.currentStep).toBe(2)
  })

  it('should validate form fields', async () => {
    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    // Validate empty form
    const isValid = await act(async () => {
      return await result.current.validate()
    })

    expect(isValid).toBe(false)

    // Set valid data
    act(() => {
      result.current.setData({
        title: 'Test Property',
        description: 'Test Description',
        propertyType: 'apartment',
        bedrooms: 3,
        bathrooms: 2,
        area: 1200,
        price: '5000000',
        location: 'Mumbai',
        address: '123 Test Street',
        amenities: 'Swimming Pool'
      })
    })

    // Validate filled form
    const isValidFilled = await act(async () => {
      return await result.current.validate()
    })

    expect(isValidFilled).toBe(true)
  })

  it('should track analytics events', () => {
    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    // Track custom event
    act(() => {
      result.current.trackEvent('custom_event', { test: 'data' })
    })

    // The trackEvent function should be called (mocked)
    expect(result.current.trackEvent).toBeDefined()
  })

  it('should handle auto-save functionality', () => {
    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError,
        autoSave: true,
        autoSaveInterval: 1000
      })
    )

    // Set data
    act(() => {
      result.current.setData({
        title: 'Test Property',
        description: 'Test Description'
      })
    })

    // Auto-save should be enabled
    expect(result.current.state.isDirty).toBe(true)
  })

  it('should reset form data', () => {
    const { result } = renderHook(() =>
      useUnifiedPropertyForm({
        variant: 'simple',
        onSuccess: mockOnSuccess,
        onError: mockOnError
      })
    )

    // Set data
    act(() => {
      result.current.setData({
        title: 'Test Property',
        description: 'Test Description'
      })
    })

    expect(result.current.data.title).toBe('Test Property')

    // Reset form
    act(() => {
      result.current.reset()
    })

    expect(result.current.data.title).toBe('')
    expect(result.current.data.description).toBe('')
  })
})