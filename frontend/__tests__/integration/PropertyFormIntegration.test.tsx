/**
 * Integration tests for Property Form system
 */

import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRouter } from 'next/navigation'
import PropertyFormWrapper from '../../components/property/PropertyFormWrapper'
import { apiService } from '../../lib/api'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn()
}))

// Mock API service
jest.mock('../../lib/api', () => ({
  apiService: {
    createProperty: jest.fn(),
    getAIPropertySuggestions: jest.fn(),
    getMarketInsights: jest.fn()
  }
}))

// Mock feature flags
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

// Mock analytics
jest.mock('../../utils/analytics', () => ({
  useAnalytics: jest.fn(() => ({
    track: jest.fn(),
    identify: jest.fn(),
    trackPage: jest.fn(),
    trackError: jest.fn(),
    trackPerformance: jest.fn()
  }))
}))

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>
  },
  AnimatePresence: ({ children }: any) => <>{children}</>
}))

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn()
  }
}))

describe('Property Form Integration Tests', () => {
  const mockPush = jest.fn()
  const mockOnSuccess = jest.fn()
  const mockOnError = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn()
    })
  })

  describe('Simple Form Variant', () => {
    it('should render and submit simple form successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 'test-id',
          title: 'Test Property',
          description: 'Test Description'
        }
      }

      ;(apiService.createProperty as jest.Mock).mockResolvedValue(mockResponse)

      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Check if form renders
      expect(screen.getByText('Add New Property')).toBeInTheDocument()
      expect(screen.getByText('Create a detailed property listing')).toBeInTheDocument()

      // Fill form fields
      await userEvent.type(screen.getByLabelText(/property title/i), 'Test Property')
      await userEvent.type(screen.getByLabelText(/property description/i), 'A beautiful test property')
      await userEvent.selectOptions(screen.getByLabelText(/property type/i), 'apartment')
      await userEvent.selectOptions(screen.getByLabelText(/bedrooms/i), '3')
      await userEvent.selectOptions(screen.getByLabelText(/bathrooms/i), '2')
      await userEvent.type(screen.getByLabelText(/area/i), '1200')
      await userEvent.type(screen.getByLabelText(/price/i), '5000000')
      await userEvent.type(screen.getByLabelText(/location/i), 'Mumbai')
      await userEvent.type(screen.getByLabelText(/full address/i), '123 Test Street, Mumbai')
      await userEvent.type(screen.getByLabelText(/amenities/i), 'Swimming Pool, Gym')

      // Submit form
      await userEvent.click(screen.getByText('Create Property'))

      // Wait for API call
      await waitFor(() => {
        expect(apiService.createProperty).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Test Property',
            description: 'A beautiful test property',
            propertyType: 'apartment',
            bedrooms: 3,
            bathrooms: 2,
            area: 1200,
            price: '5000000',
            location: 'Mumbai',
            address: '123 Test Street, Mumbai',
            amenities: 'Swimming Pool, Gym'
          })
        )
      })

      expect(mockOnSuccess).toHaveBeenCalled()
    })

    it('should handle form validation errors', async () => {
      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Try to submit empty form
      await userEvent.click(screen.getByText('Create Property'))

      // Check for validation errors
      await waitFor(() => {
        expect(screen.getByText('Title is required')).toBeInTheDocument()
        expect(screen.getByText('Description is required')).toBeInTheDocument()
        expect(screen.getByText('Property type is required')).toBeInTheDocument()
      })
    })
  })

  describe('Wizard Form Variant', () => {
    it('should render and navigate through wizard steps', async () => {
      render(
        <PropertyFormWrapper
          variant="wizard"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Check if wizard renders
      expect(screen.getByText('Smart Property Form')).toBeInTheDocument()
      expect(screen.getByText('Step-by-step property listing with AI insights')).toBeInTheDocument()

      // Check for step indicators
      expect(screen.getByText('Location')).toBeInTheDocument()
      expect(screen.getByText('Property Details')).toBeInTheDocument()
      expect(screen.getByText('Pricing')).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()

      // Check for navigation buttons
      expect(screen.getByText('Previous')).toBeInTheDocument()
      expect(screen.getByText('Next')).toBeInTheDocument()
    })

    it('should navigate between wizard steps', async () => {
      render(
        <PropertyFormWrapper
          variant="wizard"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Fill first step (Location)
      await userEvent.type(screen.getByLabelText(/location/i), 'Mumbai')
      await userEvent.type(screen.getByLabelText(/full address/i), '123 Test Street, Mumbai')

      // Go to next step
      await userEvent.click(screen.getByText('Next'))

      // Should be on Property Details step
      expect(screen.getByText('Property Details')).toBeInTheDocument()

      // Go back to previous step
      await userEvent.click(screen.getByText('Previous'))

      // Should be back on Location step
      expect(screen.getByText('Location Details')).toBeInTheDocument()
    })
  })

  describe('AI-First Form Variant', () => {
    it('should render AI-first form with AI features', () => {
      render(
        <PropertyFormWrapper
          variant="ai-first"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Check if AI-first form renders
      expect(screen.getByText('AI Property Generator')).toBeInTheDocument()
      expect(screen.getByText('Create compelling property listings with AI')).toBeInTheDocument()

      // Check for AI features
      expect(screen.getByText('AI Auto-Fill')).toBeInTheDocument()
    })

    it('should generate AI suggestions', async () => {
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

      render(
        <PropertyFormWrapper
          variant="ai-first"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Click AI Auto-Fill button
      await userEvent.click(screen.getByText('AI Auto-Fill'))

      // Wait for AI suggestions
      await waitFor(() => {
        expect(apiService.getAIPropertySuggestions).toHaveBeenCalled()
      })

      // Check if AI suggestions are displayed
      await waitFor(() => {
        expect(screen.getByText('AI Suggestions')).toBeInTheDocument()
        expect(screen.getByText('AI Generated Title')).toBeInTheDocument()
        expect(screen.getByText('AI Generated Description')).toBeInTheDocument()
      })
    })
  })

  describe('Feature Flag Integration', () => {
    it('should fallback to old form when unified form is disabled', () => {
      // Mock feature flags with unified form disabled
      const { useFeatureFlags } = require('../../utils/featureFlags')
      useFeatureFlags.mockReturnValue({
        USE_UNIFIED_FORM: false,
        ENABLE_AI_FEATURES: true,
        ENABLE_MARKET_INSIGHTS: true,
        ENABLE_QUALITY_SCORING: true,
        ENABLE_MULTILANGUAGE: true,
        FALLBACK_ON_ERROR: true,
        ENABLE_AB_TESTING: true,
        DEBUG_MODE: true
      })

      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Should render old form (PropertyForm component)
      // This would need to be adjusted based on the actual old form component
      expect(screen.getByText('Add New Property')).toBeInTheDocument()
    })

    it('should hide AI features when disabled', () => {
      // Mock feature flags with AI features disabled
      const { useFeatureFlags } = require('../../utils/featureFlags')
      useFeatureFlags.mockReturnValue({
        USE_UNIFIED_FORM: true,
        ENABLE_AI_FEATURES: false,
        ENABLE_MARKET_INSIGHTS: false,
        ENABLE_QUALITY_SCORING: false,
        ENABLE_MULTILANGUAGE: true,
        FALLBACK_ON_ERROR: true,
        ENABLE_AB_TESTING: true,
        DEBUG_MODE: true
      })

      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // AI features should be hidden
      expect(screen.queryByText('AI Auto-Fill')).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const mockError = new Error('API Error')
      ;(apiService.createProperty as jest.Mock).mockRejectedValue(mockError)

      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Fill form
      await userEvent.type(screen.getByLabelText(/property title/i), 'Test Property')
      await userEvent.type(screen.getByLabelText(/property description/i), 'Test Description')
      await userEvent.selectOptions(screen.getByLabelText(/property type/i), 'apartment')
      await userEvent.selectOptions(screen.getByLabelText(/bedrooms/i), '3')
      await userEvent.selectOptions(screen.getByLabelText(/bathrooms/i), '2')
      await userEvent.type(screen.getByLabelText(/area/i), '1200')
      await userEvent.type(screen.getByLabelText(/price/i), '5000000')
      await userEvent.type(screen.getByLabelText(/location/i), 'Mumbai')
      await userEvent.type(screen.getByLabelText(/full address/i), '123 Test Street, Mumbai')
      await userEvent.type(screen.getByLabelText(/amenities/i), 'Swimming Pool')

      // Submit form
      await userEvent.click(screen.getByText('Create Property'))

      // Wait for error handling
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith(mockError)
      })
    })

    it('should handle AI generation errors', async () => {
      const mockError = new Error('AI Generation Error')
      ;(apiService.getAIPropertySuggestions as jest.Mock).mockRejectedValue(mockError)

      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Click AI Auto-Fill button
      await userEvent.click(screen.getByText('AI Auto-Fill'))

      // Wait for error handling
      await waitFor(() => {
        expect(apiService.getAIPropertySuggestions).toHaveBeenCalled()
      })

      // Error should be handled gracefully (not crash the form)
      expect(screen.getByText('Add New Property')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper form structure', () => {
      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Check for proper form structure
      const form = screen.getByRole('form')
      expect(form).toBeInTheDocument()

      // Check for proper labels
      expect(screen.getByLabelText(/property title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/property description/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/property type/i)).toBeInTheDocument()

      // Check for required field indicators
      const requiredFields = screen.getAllByText('*')
      expect(requiredFields.length).toBeGreaterThan(0)
    })

    it('should support keyboard navigation', async () => {
      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Tab through form fields
      const titleField = screen.getByLabelText(/property title/i)
      const descriptionField = screen.getByLabelText(/property description/i)

      titleField.focus()
      expect(titleField).toHaveFocus()

      await userEvent.tab()
      expect(descriptionField).toHaveFocus()
    })
  })
})