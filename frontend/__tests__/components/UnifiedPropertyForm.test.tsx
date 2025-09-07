/**
 * Unified Property Form Tests
 * ===========================
 * 
 * Comprehensive test suite for the unified property form component.
 */

import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { motion } from 'framer-motion'
import UnifiedPropertyForm from '../../components/property/UnifiedPropertyForm'
import { useFeatureFlags, useABTesting } from '../../utils/featureFlags'

// Mock dependencies
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>
  },
  AnimatePresence: ({ children }: any) => <>{children}</>
}))

jest.mock('../../utils/featureFlags', () => ({
  useFeatureFlags: jest.fn(),
  useABTesting: jest.fn()
}))

jest.mock('../../hooks/useUnifiedPropertyForm', () => ({
  useUnifiedPropertyForm: jest.fn()
}))

jest.mock('../../lib/api', () => ({
  apiService: {
    createProperty: jest.fn(),
    getAIPropertySuggestions: jest.fn(),
    getMarketInsights: jest.fn()
  }
}))

jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn()
  }
}))

// Mock data
const mockFormData = {
  title: 'Test Property',
  description: 'Test Description',
  propertyType: 'apartment',
  bedrooms: 2,
  bathrooms: 2,
  area: 1200,
  price: '5000000',
  location: 'Mumbai',
  address: '123 Test Street',
  amenities: 'Swimming Pool, Gym'
}

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

const mockMarketInsights = {
  averagePrice: 4800000,
  priceRange: [4500000, 5200000],
  marketTrend: 'rising',
  competitorCount: 12,
  trendPercentage: 8.5
}

// Test setup
describe('UnifiedPropertyForm', () => {
  const mockOnSuccess = jest.fn()
  const mockOnError = jest.fn()
  
  const mockUseFeatureFlags = useFeatureFlags as jest.MockedFunction<typeof useFeatureFlags>
  const mockUseABTesting = useABTesting as jest.MockedFunction<typeof useABTesting>
  const mockUseUnifiedPropertyForm = require('../../hooks/useUnifiedPropertyForm').useUnifiedPropertyForm as jest.MockedFunction<any>

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Default feature flags
    mockUseFeatureFlags.mockReturnValue({
      USE_UNIFIED_FORM: true,
      ENABLE_AI_FEATURES: true,
      ENABLE_MARKET_INSIGHTS: true,
      ENABLE_QUALITY_SCORING: true,
      ENABLE_MULTILANGUAGE: true,
      FALLBACK_ON_ERROR: true,
      ENABLE_AB_TESTING: true,
      DEBUG_MODE: true
    })
    
    // Default A/B testing
    mockUseABTesting.mockReturnValue({
      variant: 'new',
      trackEvent: jest.fn(),
      isNewVariant: true,
      isOldVariant: false
    })
    
    // Default form hook
    mockUseUnifiedPropertyForm.mockReturnValue({
      data: mockFormData,
      setData: jest.fn(),
      state: {
        isLoading: false,
        isSubmitting: false,
        isAILoading: false,
        currentStep: 0,
        totalSteps: 4,
        errors: {},
        touched: {},
        isValid: true,
        isDirty: false
      },
      validation: {
        isValid: true,
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
      getValue: jest.fn(),
      watch: jest.fn(),
      validate: jest.fn(),
      validateField: jest.fn(),
      analytics: {
        formLoadTime: 1000,
        timeToFirstInteraction: 500,
        timeToComplete: 0,
        stepsCompleted: 0,
        fieldsModified: [],
        aiSuggestionsUsed: [],
        errorsEncountered: [],
        completionRate: 0
      },
      trackEvent: jest.fn()
    })
  })

  describe('Rendering', () => {
    it('renders simple variant correctly', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      expect(screen.getByText('Add New Property')).toBeInTheDocument()
      expect(screen.getByText('Create a detailed property listing')).toBeInTheDocument()
      expect(screen.getByText('Basic Information')).toBeInTheDocument()
      expect(screen.getByText('Location Details')).toBeInTheDocument()
      expect(screen.getByText('Pricing Information')).toBeInTheDocument()
      expect(screen.getByText('Description & Amenities')).toBeInTheDocument()
    })

    it('renders wizard variant correctly', () => {
      render(
        <UnifiedPropertyForm
          variant="wizard"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      expect(screen.getByText('Smart Property Form')).toBeInTheDocument()
      expect(screen.getByText('Step-by-step property listing with AI insights')).toBeInTheDocument()
      expect(screen.getByText('Previous')).toBeInTheDocument()
      expect(screen.getByText('Next')).toBeInTheDocument()
    })

    it('renders ai-first variant correctly', () => {
      render(
        <UnifiedPropertyForm
          variant="ai-first"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      expect(screen.getByText('AI Property Generator')).toBeInTheDocument()
      expect(screen.getByText('Create compelling property listings with AI')).toBeInTheDocument()
    })

    it('renders with custom className', () => {
      const { container } = render(
        <UnifiedPropertyForm
          variant="simple"
          className="custom-class"
          onSuccess={mockOnSuccess}
        />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('Form Fields', () => {
    it('renders all required form fields', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      // Check for form fields
      expect(screen.getByText('Property Title')).toBeInTheDocument()
      expect(screen.getByText('Property Type')).toBeInTheDocument()
      expect(screen.getByText('Bedrooms')).toBeInTheDocument()
      expect(screen.getByText('Bathrooms')).toBeInTheDocument()
      expect(screen.getByText('Location')).toBeInTheDocument()
      expect(screen.getByText('Full Address')).toBeInTheDocument()
      expect(screen.getByText('Area (sq ft)')).toBeInTheDocument()
      expect(screen.getByText('Price')).toBeInTheDocument()
      expect(screen.getByText('Property Description')).toBeInTheDocument()
      expect(screen.getByText('Amenities')).toBeInTheDocument()
    })

    it('shows required field indicators', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      // Check for required field indicators
      const requiredFields = screen.getAllByText('*')
      expect(requiredFields.length).toBeGreaterThan(0)
    })
  })

  describe('AI Integration', () => {
    it('shows AI auto-fill button when AI features are enabled', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.getByText('AI Auto-Fill')).toBeInTheDocument()
    })

    it('hides AI features when disabled', () => {
      mockUseFeatureFlags.mockReturnValue({
        USE_UNIFIED_FORM: true,
        ENABLE_AI_FEATURES: false,
        ENABLE_MARKET_INSIGHTS: false,
        ENABLE_QUALITY_SCORING: false,
        ENABLE_MULTILANGUAGE: false,
        FALLBACK_ON_ERROR: true,
        ENABLE_AB_TESTING: true,
        DEBUG_MODE: true
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.queryByText('AI Auto-Fill')).not.toBeInTheDocument()
    })

    it('handles AI suggestion generation', async () => {
      const mockGenerateAI = jest.fn()
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        generateAISuggestions: mockGenerateAI
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      const aiButton = screen.getByText('AI Auto-Fill')
      await userEvent.click(aiButton)

      expect(mockGenerateAI).toHaveBeenCalled()
    })

    it('displays AI suggestions when available', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        ai: {
          suggestions: {
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
          },
          marketInsights: null,
          isGenerating: false,
          lastGenerated: new Date(),
          error: null
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.getByText('AI Suggestions')).toBeInTheDocument()
      expect(screen.getByText('AI Generated Title')).toBeInTheDocument()
      expect(screen.getByText('AI Generated Description')).toBeInTheDocument()
      expect(screen.getByText('Apply All')).toBeInTheDocument()
    })
  })

  describe('Market Insights', () => {
    it('displays market insights when available', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        marketInsights: mockMarketInsights
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.getByText('Market Insights')).toBeInTheDocument()
      expect(screen.getByText('Average Price:')).toBeInTheDocument()
      expect(screen.getByText('Market Trend:')).toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    it('handles form submission', async () => {
      const mockSubmit = jest.fn()
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        submit: mockSubmit
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      const submitButton = screen.getByText('Create Property')
      await userEvent.click(submitButton)

      expect(mockSubmit).toHaveBeenCalled()
    })

    it('shows loading state during submission', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        state: {
          ...mockUseUnifiedPropertyForm().state,
          isSubmitting: true
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.getByText('Creating Property...')).toBeInTheDocument()
    })
  })

  describe('Wizard Navigation', () => {
    it('handles step navigation in wizard variant', async () => {
      const mockNextStep = jest.fn()
      const mockPrevStep = jest.fn()
      
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        nextStep: mockNextStep,
        prevStep: mockPrevStep
      })

      render(
        <UnifiedPropertyForm
          variant="wizard"
          onSuccess={mockOnSuccess}
        />
      )

      const nextButton = screen.getByText('Next')
      await userEvent.click(nextButton)

      expect(mockNextStep).toHaveBeenCalled()
    })

    it('shows final submit button on last step', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        state: {
          ...mockUseUnifiedPropertyForm().state,
          currentStep: 3,
          totalSteps: 4
        }
      })

      render(
        <UnifiedPropertyForm
          variant="wizard"
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.getByText('Create Property')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays validation errors', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        validation: {
          isValid: false,
          errors: {
            title: 'Title is required',
            price: 'Price must be a valid number'
          },
          warnings: {},
          touched: {},
          dirty: {}
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.getByText('Title is required')).toBeInTheDocument()
      expect(screen.getByText('Price must be a valid number')).toBeInTheDocument()
    })

    it('handles AI generation errors', () => {
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        ai: {
          suggestions: null,
          marketInsights: null,
          isGenerating: false,
          lastGenerated: null,
          error: 'Failed to generate AI suggestions'
        }
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      // Error should be handled by the hook, not displayed in UI
      expect(screen.queryByText('Failed to generate AI suggestions')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper form structure', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      const form = screen.getByRole('form')
      expect(form).toBeInTheDocument()
    })

    it('has proper button roles', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      const submitButton = screen.getByRole('button', { name: /create property/i })
      expect(submitButton).toBeInTheDocument()
    })

    it('has proper heading structure', () => {
      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      const mainHeading = screen.getByRole('heading', { level: 1 })
      expect(mainHeading).toBeInTheDocument()
      expect(mainHeading).toHaveTextContent('Add New Property')
    })
  })

  describe('Initial Data', () => {
    it('initializes form with provided data', () => {
      const initialData = {
        title: 'Initial Title',
        description: 'Initial Description',
        price: '6000000'
      }

      render(
        <UnifiedPropertyForm
          variant="simple"
          initialData={initialData}
          onSuccess={mockOnSuccess}
        />
      )

      // Form should be initialized with the provided data
      expect(mockUseUnifiedPropertyForm).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: 'simple'
        })
      )
    })
  })

  describe('Analytics Tracking', () => {
    it('tracks form events', () => {
      const mockTrackEvent = jest.fn()
      mockUseUnifiedPropertyForm.mockReturnValue({
        ...mockUseUnifiedPropertyForm(),
        trackEvent: mockTrackEvent
      })

      render(
        <UnifiedPropertyForm
          variant="simple"
          onSuccess={mockOnSuccess}
        />
      )

      expect(mockTrackEvent).toHaveBeenCalledWith('form_rendered', expect.any(Object))
    })
  })
})