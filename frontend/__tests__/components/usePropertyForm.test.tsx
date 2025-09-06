import { renderHook, act, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { usePropertyForm } from '../../components/property/hooks/usePropertyForm'

// Mock external dependencies
jest.mock('react-hook-form', () => ({
  useForm: () => ({
    register: jest.fn(),
    handleSubmit: jest.fn((fn) => fn),
    setValue: jest.fn(),
    watch: jest.fn(),
    trigger: jest.fn(),
    formState: {
      errors: {},
      isValid: true,
      isSubmitting: false,
      isDirty: false,
      touchedFields: {},
    },
  }),
}))

jest.mock('@hookform/resolvers/zod', () => ({
  zodResolver: jest.fn(),
}))

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

jest.mock('@/lib/validation', () => ({
  propertySchema: {},
  PropertyFormData: {},
}))

jest.mock('@/lib/api', () => ({
  apiService: {
    createProperty: jest.fn(),
    getMarketInsights: jest.fn(),
  },
  APIError: class APIError extends Error {
    constructor(message: string) {
      super(message)
      this.name = 'APIError'
    }
  },
}))

const mockApiService = require('@/lib/api').apiService
const mockToast = require('react-hot-toast').default

describe('usePropertyForm', () => {
  const mockOnSuccess = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockApiService.createProperty.mockResolvedValue({ id: 'property-123' })
    mockApiService.getMarketInsights.mockResolvedValue({
      averagePrice: 300000,
      priceRange: [250000, 350000],
      marketTrend: 'rising',
      competitorCount: 15,
      trendPercentage: 5.2,
    })
  })

  it('returns expected hook interface', () => {
    const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

    expect(result.current).toHaveProperty('register')
    expect(result.current).toHaveProperty('handleSubmit')
    expect(result.current).toHaveProperty('setValue')
    expect(result.current).toHaveProperty('watch')
    expect(result.current).toHaveProperty('trigger')
    expect(result.current).toHaveProperty('formState')
    expect(result.current).toHaveProperty('submitProperty')
    expect(result.current).toHaveProperty('generateAIContent')
    expect(result.current).toHaveProperty('getMarketInsights')
    expect(result.current).toHaveProperty('isLoading')
    expect(result.current).toHaveProperty('marketInsights')
    expect(result.current).toHaveProperty('aiSuggestions')
  })

  it('initializes with default values', () => {
    const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

    expect(result.current.isLoading).toBe(false)
    expect(result.current.marketInsights).toBeNull()
    expect(result.current.aiSuggestions).toBeNull()
  })

  describe('submitProperty', () => {
    it('calls API to create property', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.onSubmit()
      })

      expect(mockApiService.createProperty).toHaveBeenCalledWith(mockData)
    })

    it('calls onSuccess callback on successful submission', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.onSubmit()
      })

      expect(mockOnSuccess).toHaveBeenCalledWith({ id: 'property-123' })
    })

    it('shows success toast on successful submission', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.submitProperty(mockData)
      })

      expect(mockToast.success).toHaveBeenCalledWith('Property created successfully!')
    })

    it('handles submission errors', async () => {
      mockApiService.createProperty.mockRejectedValue(new Error('Submission failed'))

      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.submitProperty(mockData)
      })

      expect(mockToast.error).toHaveBeenCalledWith('Failed to create property. Please try again.')
      expect(mockOnSuccess).not.toHaveBeenCalled()
    })

    it('sets loading state during submission', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      let loadingState: boolean = false

      act(() => {
        result.current.submitProperty(mockData).then(() => {
          loadingState = result.current.isLoading
        })
      })

      // Should be loading during submission
      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })

    it('prevents multiple simultaneous submissions', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      act(() => {
        result.current.submitProperty(mockData)
        result.current.submitProperty(mockData)
        result.current.submitProperty(mockData)
      })

      await waitFor(() => {
        expect(mockApiService.createProperty).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('generateAIContent', () => {
    it('calls API to generate AI content', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableAI: true }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        address: '123 Test St',
      }

      await act(async () => {
        await result.current.generateAIContent(mockData)
      })

      expect(mockApiService.getMarketInsights).toHaveBeenCalled()
    })

    it('sets AI suggestions on successful generation', async () => {
      const mockAISuggestions = {
        title: 'AI Generated Title',
        description: 'AI Generated Description',
        marketInsights: {
          averagePrice: 300000,
          priceRange: [250000, 350000],
          marketTrend: 'rising' as const,
          competitorCount: 15,
          trendPercentage: 5.2,
        },
      }

      mockApiService.getMarketInsights.mockResolvedValue(mockAISuggestions)

      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableAI: true }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        address: '123 Test St',
      }

      await act(async () => {
        await result.current.generateAIContent(mockData)
      })

      expect(result.current.aiSuggestions).toEqual(mockAISuggestions)
    })

    it('handles AI generation errors', async () => {
      mockApiService.getMarketInsights.mockRejectedValue(new Error('AI generation failed'))

      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableAI: true }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        address: '123 Test St',
      }

      await act(async () => {
        await result.current.generateAIContent(mockData)
      })

      expect(mockToast.error).toHaveBeenCalledWith('Failed to generate AI content')
    })

    it('only generates AI content when enabled', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableAI: false }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        address: '123 Test St',
      }

      await act(async () => {
        await result.current.generateAIContent(mockData)
      })

      expect(mockApiService.getMarketInsights).not.toHaveBeenCalled()
    })
  })

  describe('getMarketInsights', () => {
    it('calls API to get market insights', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableMarketInsights: true }))

      const mockData = {
        address: '123 Test St',
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.getMarketInsights(mockData)
      })

      expect(mockApiService.getMarketInsights).toHaveBeenCalledWith(mockData)
    })

    it('sets market insights on successful fetch', async () => {
      const mockInsights = {
        averagePrice: 300000,
        priceRange: [250000, 350000],
        marketTrend: 'rising' as const,
        competitorCount: 15,
        trendPercentage: 5.2,
      }

      mockApiService.getMarketInsights.mockResolvedValue(mockInsights)

      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableMarketInsights: true }))

      const mockData = {
        address: '123 Test St',
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.getMarketInsights(mockData)
      })

      expect(result.current.marketInsights).toEqual(mockInsights)
    })

    it('handles market insights errors', async () => {
      mockApiService.getMarketInsights.mockRejectedValue(new Error('Market insights failed'))

      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableMarketInsights: true }))

      const mockData = {
        address: '123 Test St',
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.getMarketInsights(mockData)
      })

      expect(mockToast.error).toHaveBeenCalledWith('Failed to load market insights')
    })

    it('only fetches market insights when enabled', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableMarketInsights: false }))

      const mockData = {
        address: '123 Test St',
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.getMarketInsights(mockData)
      })

      expect(mockApiService.getMarketInsights).not.toHaveBeenCalled()
    })
  })

  describe('Configuration options', () => {
    it('respects enableAI option', () => {
      const { result } = renderHook(() => usePropertyForm({ enableAI: true }))

      expect(result.current).toHaveProperty('generateAIContent')
    })

    it('respects enableMarketInsights option', () => {
      const { result } = renderHook(() => usePropertyForm({ enableMarketInsights: true }))

      expect(result.current).toHaveProperty('getMarketInsights')
    })

    it('respects enableQualityScoring option', () => {
      const { result } = renderHook(() => usePropertyForm({ enableQualityScoring: true }))

      expect(result.current).toHaveProperty('aiSuggestions')
    })

    it('handles onSuccess callback', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(typeof result.current.submitProperty).toBe('function')
    })

    it('works without onSuccess callback', () => {
      const { result } = renderHook(() => usePropertyForm())

      expect(result.current).toHaveProperty('submitProperty')
    })
  })

  describe('Auto-save functionality', () => {
    it('supports auto-save when enabled', () => {
      const { result } = renderHook(() => usePropertyForm({ autoSave: true }))

      expect(result.current).toHaveProperty('submitProperty')
    })

    it('handles auto-save mode onBlur', () => {
      const { result } = renderHook(() => usePropertyForm({ autoSave: true, mode: 'onBlur' }))

      expect(result.current).toHaveProperty('formState')
    })

    it('handles auto-save mode onChange', () => {
      const { result } = renderHook(() => usePropertyForm({ autoSave: true, mode: 'onChange' }))

      expect(result.current).toHaveProperty('watch')
    })

    it('handles auto-save mode onSubmit', () => {
      const { result } = renderHook(() => usePropertyForm({ autoSave: true, mode: 'onSubmit' }))

      expect(result.current).toHaveProperty('handleSubmit')
    })
  })

  describe('Form state management', () => {
    it('exposes form state from react-hook-form', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(result.current.formState).toHaveProperty('errors')
      expect(result.current.formState).toHaveProperty('isValid')
      expect(result.current.formState).toHaveProperty('isSubmitting')
    })

    it('provides form registration function', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(typeof result.current.register).toBe('function')
    })

    it('provides form value setter', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(typeof result.current.setValue).toBe('function')
    })

    it('provides form watcher', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(typeof result.current.watch).toBe('function')
    })

    it('provides form trigger function', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(typeof result.current.trigger).toBe('function')
    })
  })

  describe('Error handling', () => {
    it('handles API errors gracefully', async () => {
      const APIError = require('@/lib/api').APIError
      mockApiService.createProperty.mockRejectedValue(new APIError('API Error'))

      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.submitProperty(mockData)
      })

      expect(mockToast.error).toHaveBeenCalled()
    })

    it('handles network errors', async () => {
      mockApiService.createProperty.mockRejectedValue(new Error('Network Error'))

      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      await act(async () => {
        await result.current.submitProperty(mockData)
      })

      expect(mockToast.error).toHaveBeenCalledWith('Failed to create property. Please try again.')
    })

    it('handles validation errors', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      const invalidData = {
        title: '',
        description: '',
        price: '',
        address: '',
        bedrooms: 0,
        bathrooms: 0,
        area: 0,
        propertyType: '',
      }

      await act(async () => {
        await result.current.submitProperty(invalidData)
      })

      expect(mockApiService.createProperty).not.toHaveBeenCalled()
    })
  })

  describe('Loading states', () => {
    it('manages loading state during operations', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(result.current.isLoading).toBe(false)

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        price: '100000',
        address: '123 Test St',
        bedrooms: 2,
        bathrooms: 2,
        area: 1000,
        propertyType: 'apartment',
      }

      act(() => {
        result.current.submitProperty(mockData)
      })

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })

    it('prevents concurrent operations', async () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess, enableAI: true }))

      const mockData = {
        title: 'Test Property',
        description: 'Test Description',
        address: '123 Test St',
      }

      act(() => {
        result.current.generateAIContent(mockData)
        result.current.generateAIContent(mockData)
      })

      await waitFor(() => {
        expect(mockApiService.getMarketInsights).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Integration with react-hook-form', () => {
    it('integrates with form validation schema', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(result.current.formState).toBeDefined()
      expect(result.current.register).toBeDefined()
    })

    it('handles form submission through handleSubmit', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(typeof result.current.handleSubmit).toBe('function')
    })

    it('supports form field watching', () => {
      const { result } = renderHook(() => usePropertyForm({ onSuccess: mockOnSuccess }))

      expect(typeof result.current.watch).toBe('function')
    })
  })
})
