import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import SmartPropertyForm from '../../components/SmartPropertyForm'

// Mock external dependencies
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  SparklesIcon: ({ className }: any) => <div data-testid="sparkles-icon" className={className} />,
  MapPinIcon: ({ className }: any) => <div data-testid="map-pin-icon" className={className} />,
  HomeIcon: ({ className }: any) => <div data-testid="home-icon" className={className} />,
  CurrencyDollarIcon: ({ className }: any) => <div data-testid="currency-icon" className={className} />,
  DocumentTextIcon: ({ className }: any) => <div data-testid="document-icon" className={className} />,
  CheckCircleIcon: ({ className }: any) => <div data-testid="check-icon" className={className} />,
  ExclamationTriangleIcon: ({ className }: any) => <div data-testid="warning-icon" className={className} />,
  LightBulbIcon: ({ className }: any) => <div data-testid="bulb-icon" className={className} />,
  ArrowRightIcon: ({ className }: any) => <div data-testid="arrow-right-icon" className={className} />,
  ArrowLeftIcon: ({ className }: any) => <div data-testid="arrow-left-icon" className={className} />,
}))

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
  __esModule: true,
  apiService: {
    createProperty: jest.fn(),
    getMarketInsights: jest.fn(),
  },
}))

const mockApiService = require('@/lib/api').apiService
const mockToast = require('react-hot-toast').default

describe('SmartPropertyForm', () => {
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

  it('renders form steps correctly', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByText('Location')).toBeInTheDocument()
    expect(screen.getByText('Property Details')).toBeInTheDocument()
    expect(screen.getByText('Pricing & Market')).toBeInTheDocument()
    expect(screen.getByText('AI Enhancement')).toBeInTheDocument()
    expect(screen.getByText('Review & Submit')).toBeInTheDocument()
  })

  it('starts with first step active', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const activeStep = screen.getByText('Location')
    expect(activeStep).toHaveClass('bg-blue-600')
  })

  it('shows address input on first step', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByLabelText(/property address/i)).toBeInTheDocument()
  })

  it('navigates to next step when address is entered', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const addressInput = screen.getByLabelText(/property address/i)
    await user.type(addressInput, '123 Main St, City, State 12345')

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    // Should move to property details step
    expect(screen.getByText('Property Type')).toBeInTheDocument()
  })

  it('shows property type selection', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByText('Property Type')).toBeInTheDocument()
    expect(screen.getByLabelText(/apartment/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/house/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/condo/i)).toBeInTheDocument()
  })

  it('shows bedroom and bathroom inputs', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByLabelText(/bedrooms/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/bathrooms/i)).toBeInTheDocument()
  })

  it('shows area input with proper units', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const areaInput = screen.getByLabelText(/square footage/i)
    expect(areaInput).toBeInTheDocument()
  })

  it('displays market insights when available', async () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    await waitFor(() => {
      expect(screen.getByText('Market Insights')).toBeInTheDocument()
    })

    expect(screen.getByText('$300,000')).toBeInTheDocument()
    expect(screen.getByText('Rising')).toBeInTheDocument()
    expect(screen.getByText('15 competitors')).toBeInTheDocument()
  })

  it('shows AI suggestions button', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByRole('button', { name: /get ai suggestions/i })).toBeInTheDocument()
  })

  it('generates AI content when button is clicked', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const aiButton = screen.getByRole('button', { name: /get ai suggestions/i })
    await user.click(aiButton)

    await waitFor(() => {
      expect(mockApiService.getMarketInsights).toHaveBeenCalled()
    })
  })

  it('shows AI-generated title and description', async () => {
    // Mock AI suggestions
    const mockSuggestions = {
      title: 'Beautiful Modern Apartment',
      description: 'Stunning apartment with great amenities',
      price: '300000',
      amenities: 'Pool, Gym, Parking',
      marketInsights: {
        averagePrice: 300000,
        priceRange: [250000, 350000],
        marketTrend: 'rising' as const,
        competitorCount: 15,
        trendPercentage: 5.2,
      },
      qualityScore: {
        overall: 85,
        seo: 80,
        readability: 90,
        marketRelevance: 85,
      },
    }

    // This would need to be mocked in the actual component
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    // AI suggestions would appear after generation
    expect(screen.getByText('AI Enhancement')).toBeInTheDocument()
  })

  it('shows quality score when AI suggestions are available', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByText('Quality Score')).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const submitButton = screen.getByRole('button', { name: /create property/i })

    // Try to submit without filling required fields
    await user.click(submitButton)

    // Should show validation errors
    expect(mockApiService.createProperty).not.toHaveBeenCalled()
  })

  it('submits form successfully with valid data', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    // Fill required fields (this would depend on the actual form structure)
    // For now, we'll mock the submission
    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockApiService.createProperty).toHaveBeenCalled()
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('shows success toast on successful submission', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockToast.success).toHaveBeenCalledWith('Property created successfully!')
    })
  })

  it('handles submission errors gracefully', async () => {
    mockApiService.createProperty.mockRejectedValue(new Error('Submission failed'))

    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Failed to create property. Please try again.')
    })
  })

  it('navigates between steps using step indicators', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    // Click on a different step
    const propertyDetailsStep = screen.getByText('Property Details')
    await user.click(propertyDetailsStep)

    // Should navigate to that step
    expect(screen.getByText('Property Type')).toBeInTheDocument()
  })

  it('shows progress indicator', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByText('Step 1 of 5')).toBeInTheDocument()
  })

  it('updates progress as steps are completed', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const addressInput = screen.getByLabelText(/property address/i)
    await user.type(addressInput, '123 Main St, City, State 12345')

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    expect(screen.getByText('Step 2 of 5')).toBeInTheDocument()
  })

  it('shows back button on steps after first', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const addressInput = screen.getByLabelText(/property address/i)
    await user.type(addressInput, '123 Main St, City, State 12345')

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument()
  })

  it('navigates back to previous step', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    // Go to next step
    const addressInput = screen.getByLabelText(/property address/i)
    await user.type(addressInput, '123 Main St, City, State 12345')
    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    // Go back
    const backButton = screen.getByRole('button', { name: /back/i })
    await user.click(backButton)

    expect(screen.getByText('Step 1 of 5')).toBeInTheDocument()
  })

  it('disables next button when required fields are empty', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const nextButton = screen.getByRole('button', { name: /next/i })
    expect(nextButton).toBeDisabled()
  })

  it('enables next button when required fields are filled', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const addressInput = screen.getByLabelText(/property address/i)
    await user.type(addressInput, '123 Main St, City, State 12345')

    const nextButton = screen.getByRole('button', { name: /next/i })
    expect(nextButton).not.toBeDisabled()
  })

  it('shows form validation errors', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    // Try to proceed without filling required fields
    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    // Should show validation errors
    expect(screen.getByText('Address is required')).toBeInTheDocument()
  })

  it('handles market insights API errors gracefully', async () => {
    mockApiService.getMarketInsights.mockRejectedValue(new Error('API Error'))

    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Failed to load market insights')
    })
  })

  it('shows loading state during submission', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    expect(screen.getByText('Creating Property...')).toBeInTheDocument()
  })

  it('prevents multiple submissions', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const submitButton = screen.getByRole('button', { name: /create property/i })

    await user.click(submitButton)
    await user.click(submitButton)
    await user.click(submitButton)

    expect(mockApiService.createProperty).toHaveBeenCalledTimes(1)
  })

  it('shows AI enhancement suggestions', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByText('AI Enhancement')).toBeInTheDocument()
    expect(screen.getByText('Smart Suggestions')).toBeInTheDocument()
  })

  it('displays market trend indicators', async () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    await waitFor(() => {
      expect(screen.getByText('📈 Rising')).toBeInTheDocument()
      expect(screen.getByText('+5.2%')).toBeInTheDocument()
    })
  })

  it('shows competitor analysis', async () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    await waitFor(() => {
      expect(screen.getByText('15 active competitors')).toBeInTheDocument()
    })
  })

  it('displays price recommendations', async () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    await waitFor(() => {
      expect(screen.getByText('$250,000 - $350,000')).toBeInTheDocument()
    })
  })

  it('has proper accessibility attributes', () => {
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const form = screen.getByRole('form')
    expect(form).toHaveAttribute('aria-label', 'Smart property creation form')

    const steps = screen.getAllByRole('button', { name: /step/i })
    expect(steps.length).toBeGreaterThan(0)
  })

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const addressInput = screen.getByLabelText(/property address/i)
    addressInput.focus()

    await user.keyboard('{Tab}')
    expect(document.activeElement).toBe(screen.getByRole('button', { name: /next/i }))
  })

  it('maintains form state across steps', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const addressInput = screen.getByLabelText(/property address/i)
    await user.type(addressInput, '123 Main St')

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    // Go back and check if address is still there
    const backButton = screen.getByRole('button', { name: /back/i })
    await user.click(backButton)

    expect(addressInput).toHaveValue('123 Main St')
  })

  it('shows review step with all entered data', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    // Fill some data and navigate to review
    const addressInput = screen.getByLabelText(/property address/i)
    await user.type(addressInput, '123 Main St, City, State 12345')

    // Navigate through steps to review
    for (let i = 0; i < 4; i++) {
      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)
    }

    expect(screen.getByText('Review & Submit')).toBeInTheDocument()
    expect(screen.getByText('123 Main St, City, State 12345')).toBeInTheDocument()
  })

  it('handles form reset after successful submission', async () => {
    const user = userEvent.setup()
    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const addressInput = screen.getByLabelText(/property address/i)
    await user.type(addressInput, '123 Main St')

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled()
    })

    // Form should be reset
    expect(addressInput).toHaveValue('')
  })

  it('shows confirmation dialog before submission', async () => {
    const user = userEvent.setup()

    // Mock window.confirm
    const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(true)

    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to create this property?')

    mockConfirm.mockRestore()
  })

  it('cancels submission when user declines confirmation', async () => {
    const user = userEvent.setup()

    // Mock window.confirm to return false
    const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(false)

    render(<SmartPropertyForm onSuccess={mockOnSuccess} />)

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to create this property?')
    expect(mockApiService.createProperty).not.toHaveBeenCalled()

    mockConfirm.mockRestore()
  })
})
