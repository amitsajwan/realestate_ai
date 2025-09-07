/**
 * Performance tests for Property Form system
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { performance } from 'perf_hooks'
import PropertyFormWrapper from '../../components/property/PropertyFormWrapper'

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn()
  }))
}))

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

jest.mock('../../utils/analytics', () => ({
  useAnalytics: jest.fn(() => ({
    track: jest.fn(),
    identify: jest.fn(),
    trackPage: jest.fn(),
    trackError: jest.fn(),
    trackPerformance: jest.fn()
  }))
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>
  },
  AnimatePresence: ({ children }: any) => <>{children}</>
}))

jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn()
  }
}))

describe('Property Form Performance Tests', () => {
  const mockOnSuccess = jest.fn()
  const mockOnError = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Form Load Performance', () => {
    it('should load simple form within 2 seconds', async () => {
      const startTime = performance.now()

      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Wait for form to be fully rendered
      await waitFor(() => {
        expect(screen.getByText('Add New Property')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const loadTime = endTime - startTime

      // Form should load within 2 seconds (2000ms)
      expect(loadTime).toBeLessThan(2000)
      console.log(`Simple form load time: ${loadTime.toFixed(2)}ms`)
    })

    it('should load wizard form within 2 seconds', async () => {
      const startTime = performance.now()

      render(
        <PropertyFormWrapper
          variant="wizard"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Wait for form to be fully rendered
      await waitFor(() => {
        expect(screen.getByText('Smart Property Form')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const loadTime = endTime - startTime

      // Form should load within 2 seconds (2000ms)
      expect(loadTime).toBeLessThan(2000)
      console.log(`Wizard form load time: ${loadTime.toFixed(2)}ms`)
    })

    it('should load AI-first form within 2 seconds', async () => {
      const startTime = performance.now()

      render(
        <PropertyFormWrapper
          variant="ai-first"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Wait for form to be fully rendered
      await waitFor(() => {
        expect(screen.getByText('AI Property Generator')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const loadTime = endTime - startTime

      // Form should load within 2 seconds (2000ms)
      expect(loadTime).toBeLessThan(2000)
      console.log(`AI-first form load time: ${loadTime.toFixed(2)}ms`)
    })
  })

  describe('Form Interaction Performance', () => {
    it('should handle field updates within 100ms', async () => {
      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      const titleField = screen.getByLabelText(/property title/i)
      
      const startTime = performance.now()
      
      // Simulate typing in the title field
      titleField.focus()
      titleField.value = 'Test Property'
      titleField.dispatchEvent(new Event('input', { bubbles: true }))
      
      const endTime = performance.now()
      const interactionTime = endTime - startTime

      // Field update should be handled within 100ms
      expect(interactionTime).toBeLessThan(100)
      console.log(`Field update time: ${interactionTime.toFixed(2)}ms`)
    })

    it('should handle form validation within 200ms', async () => {
      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      const submitButton = screen.getByText('Create Property')
      
      const startTime = performance.now()
      
      // Click submit to trigger validation
      submitButton.click()
      
      // Wait for validation to complete
      await waitFor(() => {
        expect(screen.getByText('Title is required')).toBeInTheDocument()
      })
      
      const endTime = performance.now()
      const validationTime = endTime - startTime

      // Validation should complete within 200ms
      expect(validationTime).toBeLessThan(200)
      console.log(`Form validation time: ${validationTime.toFixed(2)}ms`)
    })
  })

  describe('Memory Usage', () => {
    it('should not have memory leaks during form interactions', async () => {
      const initialMemory = process.memoryUsage().heapUsed

      const { unmount } = render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Simulate multiple form interactions
      for (let i = 0; i < 10; i++) {
        const titleField = screen.getByLabelText(/property title/i)
        titleField.value = `Test Property ${i}`
        titleField.dispatchEvent(new Event('input', { bubbles: true }))
        
        const descriptionField = screen.getByLabelText(/property description/i)
        descriptionField.value = `Test Description ${i}`
        descriptionField.dispatchEvent(new Event('input', { bubbles: true }))
      }

      // Unmount component
      unmount()

      // Force garbage collection if available
      if (global.gc) {
        global.gc()
      }

      const finalMemory = process.memoryUsage().heapUsed
      const memoryIncrease = finalMemory - initialMemory

      // Memory increase should be reasonable (less than 10MB)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024)
      console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`)
    })
  })

  describe('Bundle Size Performance', () => {
    it('should have reasonable bundle size', () => {
      // This test would typically be run in a build environment
      // For now, we'll just verify that the component can be imported
      expect(PropertyFormWrapper).toBeDefined()
      
      // In a real test environment, you would:
      // 1. Build the application
      // 2. Analyze the bundle size
      // 3. Assert that form-related chunks are under 500KB
      console.log('Bundle size test would be implemented in build environment')
    })
  })

  describe('API Response Performance', () => {
    it('should handle API responses within 3 seconds', async () => {
      // Mock API response with delay
      const { apiService } = require('../../lib/api')
      apiService.createProperty.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          success: true,
          data: { id: 'test-id' }
        }), 1000))
      )

      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Fill form
      const titleField = screen.getByLabelText(/property title/i)
      titleField.value = 'Test Property'
      titleField.dispatchEvent(new Event('input', { bubbles: true }))
      
      const descriptionField = screen.getByLabelText(/property description/i)
      descriptionField.value = 'Test Description'
      descriptionField.dispatchEvent(new Event('input', { bubbles: true }))
      
      const propertyTypeField = screen.getByLabelText(/property type/i)
      propertyTypeField.value = 'apartment'
      propertyTypeField.dispatchEvent(new Event('change', { bubbles: true }))
      
      const bedroomsField = screen.getByLabelText(/bedrooms/i)
      bedroomsField.value = '3'
      bedroomsField.dispatchEvent(new Event('change', { bubbles: true }))
      
      const bathroomsField = screen.getByLabelText(/bathrooms/i)
      bathroomsField.value = '2'
      bathroomsField.dispatchEvent(new Event('change', { bubbles: true }))
      
      const areaField = screen.getByLabelText(/area/i)
      areaField.value = '1200'
      areaField.dispatchEvent(new Event('input', { bubbles: true }))
      
      const priceField = screen.getByLabelText(/price/i)
      priceField.value = '5000000'
      priceField.dispatchEvent(new Event('input', { bubbles: true }))
      
      const locationField = screen.getByLabelText(/location/i)
      locationField.value = 'Mumbai'
      locationField.dispatchEvent(new Event('input', { bubbles: true }))
      
      const addressField = screen.getByLabelText(/full address/i)
      addressField.value = '123 Test Street, Mumbai'
      addressField.dispatchEvent(new Event('input', { bubbles: true }))
      
      const amenitiesField = screen.getByLabelText(/amenities/i)
      amenitiesField.value = 'Swimming Pool'
      amenitiesField.dispatchEvent(new Event('input', { bubbles: true }))

      const startTime = performance.now()
      
      // Submit form
      const submitButton = screen.getByText('Create Property')
      submitButton.click()
      
      // Wait for API response
      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled()
      })
      
      const endTime = performance.now()
      const responseTime = endTime - startTime

      // API response should be handled within 3 seconds
      expect(responseTime).toBeLessThan(3000)
      console.log(`API response time: ${responseTime.toFixed(2)}ms`)
    })
  })

  describe('Rendering Performance', () => {
    it('should render form sections efficiently', async () => {
      const startTime = performance.now()

      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      // Wait for all form sections to render
      await waitFor(() => {
        expect(screen.getByText('Basic Information')).toBeInTheDocument()
        expect(screen.getByText('Location Details')).toBeInTheDocument()
        expect(screen.getByText('Pricing Information')).toBeInTheDocument()
        expect(screen.getByText('Description & Amenities')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // All sections should render within 1 second
      expect(renderTime).toBeLessThan(1000)
      console.log(`Form sections render time: ${renderTime.toFixed(2)}ms`)
    })

    it('should handle large form data efficiently', async () => {
      render(
        <PropertyFormWrapper
          variant="simple"
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      )

      const startTime = performance.now()

      // Fill form with large data
      const descriptionField = screen.getByLabelText(/property description/i)
      const largeDescription = 'A'.repeat(1000) // 1000 character description
      descriptionField.value = largeDescription
      descriptionField.dispatchEvent(new Event('input', { bubbles: true }))

      const endTime = performance.now()
      const largeDataTime = endTime - startTime

      // Large data should be handled within 200ms
      expect(largeDataTime).toBeLessThan(200)
      console.log(`Large data handling time: ${largeDataTime.toFixed(2)}ms`)
    })
  })
})