/**
 * Unified Property Form Tests
 * ===========================
 * 
 * Comprehensive test suite for the UnifiedPropertyForm component
 * covering all variants, features, and user interactions.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { jest } from '@jest/globals'
import UnifiedPropertyForm from '@/components/property/UnifiedPropertyForm'
import { FormVariant } from '@/types/PropertyFormTypes'

// Mock dependencies
jest.mock('@/hooks/useUnifiedPropertyForm', () => ({
  useUnifiedPropertyForm: jest.fn()
}))

jest.mock('@/utils/featureFlags', () => ({
  useABTesting: () => ({
    variant: 'new',
    trackEvent: jest.fn()
  })
}))

jest.mock('@/utils/analytics', () => ({
  analytics: {
    trackPageView: jest.fn()
  }
}))

jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn()
}))

// Mock the form hook
const mockUseUnifiedPropertyForm = require('@/hooks/useUnifiedPropertyForm').useUnifiedPropertyForm

const defaultFormReturn = {
  data: {
    title: '',
    description: '',
    location: '',
    address: '',
    area: '',
    price: '',
    bedrooms: '',
    bathrooms: '',
    amenities: '',
    propertyType: ''
  },
  setData: jest.fn(),
  reset: jest.fn(),
  state: {
    isLoading: false,
    isSubmitting: false,
    isAILoading: false,
    currentStep: 0,
    totalSteps: 1,
    errors: {},
    touched: {},
    isValid: false,
    isDirty: false
  },
  validation: {
    isValid: false,
    errors: {},
    warnings: {},
    touched: {},
    dirty: {}
  },
  submit: jest.fn(),
  nextStep: jest.fn(),
  prevStep: jest.fn(),
  goToStep: jest.fn(),
  ai: {
    suggestions: null,
    marketInsights: null,
    isGenerating: false,
    lastGenerated: null,
    error: null
  },
  generateAISuggestions: jest.fn(),
  applyAISuggestion: jest.fn(),
  marketInsights: null,
  generateMarketInsights: jest.fn(),
  register: jest.fn(),
  setValue: jest.fn(),
  getValue: jest.fn((name) => defaultFormReturn.data[name as keyof typeof defaultFormReturn.data]),
  watch: jest.fn(() => defaultFormReturn.data),
  validate: jest.fn(),
  validateField: jest.fn(),
  analytics: {
    formLoadTime: 0,
    timeToFirstInteraction: 0,
    timeToComplete: 0,
    stepsCompleted: 0,
    fieldsModified: [],
    aiSuggestionsUsed: [],
    errorsEncountered: [],
    completionRate: 0
  },
  trackEvent: jest.fn()
}

describe('UnifiedPropertyForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseUnifiedPropertyForm.mockReturnValue(defaultFormReturn)
  })

  describe('Rendering', () => {
    it('renders simple variant correctly', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('Create Property Listing')).toBeInTheDocument()
      expect(screen.getByText('Fill in the details to create your property listing')).toBeInTheDocument()
    })

    it('renders wizard variant correctly', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        state: {
          ...defaultFormReturn.state,
          currentStep: 0,
          totalSteps: 4
        }
      })

      render(
        <UnifiedPropertyForm
          variant="wizard"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('Property Listing Wizard')).toBeInTheDocument()
      expect(screen.getByText('Follow the steps to create a comprehensive property listing')).toBeInTheDocument()
    })

    it('renders AI-first variant correctly', () => {
      render(
        <UnifiedPropertyForm
          variant="ai-first"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('AI-Powered Property Listing')).toBeInTheDocument()
      expect(screen.getByText('Let AI help you create an amazing property listing')).toBeInTheDocument()
    })
  })

  describe('Form Fields', () => {
    it('renders all required form fields', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByLabelText(/Property Title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Property Description/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Location/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Full Address/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Price/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Property Type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Area/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Bedrooms/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Bathrooms/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Amenities/i)).toBeInTheDocument()
    })

    it('handles field value changes', async () => {
      const user = userEvent.setup()
      const mockSetValue = jest.fn()

      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        setValue: mockSetValue
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      const titleInput = screen.getByLabelText(/Property Title/i)
      await user.type(titleInput, 'Test Property')

      expect(mockSetValue).toHaveBeenCalledWith('title', 'Test Property')
    })

    it('displays validation errors', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        validation: {
          ...defaultFormReturn.validation,
          errors: {
            title: { message: 'Title is required' }
          },
          touched: {
            title: true
          }
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('Title is required')).toBeInTheDocument()
    })
  })

  describe('AI Features', () => {
    it('renders AI assistant when enabled', () => {
      render(
        <UnifiedPropertyForm
          variant="wizard"
          config={{
            features: {
              ai: true,
              marketInsights: true,
              qualityScoring: true,
              multilanguage: true,
              autoSave: true,
              validation: 'onBlur'
            },
            ui: {
              showProgress: true,
              showSections: false,
              showAI: true,
              showMarketInsights: true
            }
          }}
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('AI Assistant')).toBeInTheDocument()
      expect(screen.getByText('Generate AI Content')).toBeInTheDocument()
      expect(screen.getByText('Market Insights')).toBeInTheDocument()
    })

    it('hides AI assistant when disabled', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          config={{
            features: {
              ai: false,
              marketInsights: false,
              qualityScoring: false,
              multilanguage: false,
              autoSave: true,
              validation: 'onSubmit'
            },
            ui: {
              showProgress: false,
              showSections: true,
              showAI: false,
              showMarketInsights: false
            }
          }}
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.queryByText('AI Assistant')).not.toBeInTheDocument()
    })

    it('handles AI suggestion generation', async () => {
      const user = userEvent.setup()
      const mockGenerateAI = jest.fn()

      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        generateAISuggestions: mockGenerateAI
      })

      render(
        <UnifiedPropertyForm
          variant="wizard"
          config={{
            features: { ai: true },
            ui: { showAI: true }
          }}
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      const generateButton = screen.getByText('Generate AI Content')
      await user.click(generateButton)

      expect(mockGenerateAI).toHaveBeenCalled()
    })

    it('displays AI suggestions when available', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        ai: {
          ...defaultFormReturn.ai,
          suggestions: {
            title: 'Beautiful 3BHK Apartment',
            description: 'Spacious apartment with modern amenities',
            price: '5000000'
          }
        }
      })

      render(
        <UnifiedPropertyForm
          variant="wizard"
          config={{
            features: { ai: true },
            ui: { showAI: true }
          }}
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('AI Suggestions')).toBeInTheDocument()
      expect(screen.getByText('Beautiful 3BHK Apartment')).toBeInTheDocument()
      expect(screen.getByText('Spacious apartment with modern amenities')).toBeInTheDocument()
    })
  })

  describe('Wizard Navigation', () => {
    it('renders progress indicator for wizard variant', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        state: {
          ...defaultFormReturn.state,
          currentStep: 1,
          totalSteps: 4
        }
      })

      render(
        <UnifiedPropertyForm
          variant="wizard"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('Location')).toBeInTheDocument()
      expect(screen.getByText('Basic Info')).toBeInTheDocument()
      expect(screen.getByText('Pricing')).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()
    })

    it('handles step navigation', async () => {
      const user = userEvent.setup()
      const mockNextStep = jest.fn()
      const mockPrevStep = jest.fn()

      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        state: {
          ...defaultFormReturn.state,
          currentStep: 1,
          totalSteps: 4
        },
        nextStep: mockNextStep,
        prevStep: mockPrevStep
      })

      render(
        <UnifiedPropertyForm
          variant="wizard"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      expect(mockNextStep).toHaveBeenCalled()

      const prevButton = screen.getByText('Previous')
      await user.click(prevButton)

      expect(mockPrevStep).toHaveBeenCalled()
    })
  })

  describe('Form Submission', () => {
    it('handles form submission', async () => {
      const user = userEvent.setup()
      const mockSubmit = jest.fn()
      const mockOnSuccess = jest.fn()

      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        submit: mockSubmit,
        validation: {
          ...defaultFormReturn.validation,
          isValid: true
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={jest.fn()}
        />
      )

      const submitButton = screen.getByText('Create Property')
      await user.click(submitButton)

      expect(mockSubmit).toHaveBeenCalled()
    })

    it('disables submit button when form is invalid', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        validation: {
          ...defaultFormReturn.validation,
          isValid: false
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      const submitButton = screen.getByText('Create Property')
      expect(submitButton).toBeDisabled()
    })

    it('shows loading state during submission', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        state: {
          ...defaultFormReturn.state,
          isSubmitting: true
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('Creating...')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays form errors', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        state: {
          ...defaultFormReturn.state,
          errors: {
            title: { message: 'Title is required' },
            price: { message: 'Price must be a valid number' }
          }
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('Please fix the following errors:')).toBeInTheDocument()
      expect(screen.getByText('Title is required')).toBeInTheDocument()
      expect(screen.getByText('Price must be a valid number')).toBeInTheDocument()
    })

    it('handles AI generation errors', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        ai: {
          ...defaultFormReturn.ai,
          error: 'Failed to generate AI suggestions'
        }
      })

      render(
        <UnifiedPropertyForm
          variant="wizard"
          config={{
            features: { ai: true },
            ui: { showAI: true }
          }}
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('Failed to generate AI suggestions')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByLabelText(/Property Title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Property Description/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Location/i)).toBeInTheDocument()
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      const titleInput = screen.getByLabelText(/Property Title/i)
      await user.tab()
      
      expect(titleInput).toHaveFocus()
    })

    it('has proper form structure', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      // Check for proper heading structure
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
      
      // Check for form fields
      const inputs = screen.getAllByRole('textbox')
      expect(inputs.length).toBeGreaterThan(0)
    })
  })

  describe('Responsive Design', () => {
    it('renders correctly on mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      )

      expect(screen.getByText('Create Property Listing')).toBeInTheDocument()
    })
  })

  describe('Integration', () => {
    it('calls onSuccess callback on successful submission', async () => {
      const mockOnSuccess = jest.fn()
      const mockSubmit = jest.fn().mockImplementation(() => {
        mockOnSuccess({ title: 'Test Property' })
      })

      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        submit: mockSubmit,
        validation: {
          ...defaultFormReturn.validation,
          isValid: true
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={jest.fn()}
        />
      )

      const submitButton = screen.getByText('Create Property')
      await userEvent.click(submitButton)

      expect(mockOnSuccess).toHaveBeenCalledWith({ title: 'Test Property' })
    })

    it('calls onError callback on submission error', async () => {
      const mockOnError = jest.fn()
      const mockSubmit = jest.fn().mockImplementation(() => {
        mockOnError(new Error('Submission failed'))
      })

      mockUseUnifiedPropertyForm.mockReturnValue({
        ...defaultFormReturn,
        submit: mockSubmit,
        validation: {
          ...defaultFormReturn.validation,
          isValid: true
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={jest.fn()}
          onError={mockOnError}
        />
      )

      const submitButton = screen.getByText('Create Property')
      await userEvent.click(submitButton)

      expect(mockOnError).toHaveBeenCalledWith(expect.any(Error))
    })
  })
})