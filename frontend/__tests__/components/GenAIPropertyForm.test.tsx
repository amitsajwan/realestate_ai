import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import GenAIPropertyForm from '../../components/GenAIPropertyForm'

// Mock external dependencies
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  SparklesIcon: ({ className }: any) => <div data-testid="sparkles-icon" className={className} />,
  HomeIcon: ({ className }: any) => <div data-testid="home-icon" className={className} />,
  MapPinIcon: ({ className }: any) => <div data-testid="map-pin-icon" className={className} />,
}))

jest.mock('@/components/LoadingStates', () => ({
  __esModule: true,
  LoadingButton: ({ children, isLoading, onClick, ...props }: any) => (
    <button
      onClick={onClick}
      disabled={isLoading}
      data-testid="loading-button"
      {...props}
    >
      {isLoading ? 'Loading...' : children}
    </button>
  ),
}))

jest.mock('@/hooks/useLoading', () => ({
  __esModule: true,
  useAsyncOperation: () => ({
    execute: jest.fn(),
    isLoading: false,
    error: null,
    data: null,
  }),
}))

jest.mock('@/lib/api', () => ({
  __esModule: true,
  apiService: {
    generatePropertyContent: jest.fn(),
    createProperty: jest.fn(),
  },
}))

jest.mock('@/lib/logger', () => ({
  __esModule: true,
  logger: {
    info: jest.fn(),
    error: jest.fn(),
  },
}))

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

const mockApiService = require('@/lib/api').apiService
const mockToast = require('react-hot-toast').toast

describe('GenAIPropertyForm', () => {
  const mockOnSuccess = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockApiService.generatePropertyContent.mockResolvedValue({
      title: 'AI Generated Title',
      description: 'AI Generated Description',
    })
    mockApiService.createProperty.mockResolvedValue({ id: 'property-123' })
  })

  it('renders form with all required fields', () => {
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/price/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/bedrooms/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/bathrooms/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/area/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/property type/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/language/i)).toBeInTheDocument()
  })

  it('renders with default form values', () => {
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByLabelText(/bedrooms/i)).toHaveValue(2)
    expect(screen.getByLabelText(/bathrooms/i)).toHaveValue(2)
    expect(screen.getByLabelText(/property type/i)).toHaveValue('apartment')
    expect(screen.getByLabelText(/language/i)).toHaveValue('English')
  })

  it('updates form data when inputs change', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const titleInput = screen.getByLabelText(/title/i)
    await user.clear(titleInput)
    await user.type(titleInput, 'Test Property')

    expect(titleInput).toHaveValue('Test Property')
  })

  it('converts numeric inputs to numbers', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const bedroomsInput = screen.getByLabelText(/bedrooms/i)
    await user.clear(bedroomsInput)
    await user.type(bedroomsInput, '3')

    expect(bedroomsInput).toHaveValue(3)
  })

  it('handles empty numeric inputs', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const bedroomsInput = screen.getByLabelText(/bedrooms/i)
    await user.clear(bedroomsInput)

    expect(bedroomsInput).toHaveValue(0)
  })

  it('shows AI generation button', () => {
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    expect(screen.getByRole('button', { name: /generate with ai/i })).toBeInTheDocument()
  })

  it('shows loading state during AI generation', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const generateButton = screen.getByRole('button', { name: /generate with ai/i })
    await user.click(generateButton)

    // The button should show loading state
    expect(screen.getByTestId('loading-button')).toBeInTheDocument()
  })

  it('calls API to generate content when AI button is clicked', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const generateButton = screen.getByRole('button', { name: /generate with ai/i })
    await user.click(generateButton)

    await waitFor(() => {
      expect(mockApiService.generatePropertyContent).toHaveBeenCalled()
    })
  })

  it('populates form with AI generated content', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const generateButton = screen.getByRole('button', { name: /generate with ai/i })
    await user.click(generateButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/title/i)).toHaveValue('AI Generated Title')
      expect(screen.getByLabelText(/description/i)).toHaveValue('AI Generated Description')
    })
  })

  it('shows success toast when AI generation succeeds', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const generateButton = screen.getByRole('button', { name: /generate with ai/i })
    await user.click(generateButton)

    await waitFor(() => {
      expect(mockToast.success).toHaveBeenCalledWith('Content generated successfully!')
    })
  })

  it('shows error toast when AI generation fails', async () => {
    mockApiService.generatePropertyContent.mockRejectedValue(new Error('API Error'))

    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const generateButton = screen.getByRole('button', { name: /generate with ai/i })
    await user.click(generateButton)

    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Failed to generate content. Please try again.')
    })
  })

  it('submits form successfully', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    // Fill required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property')
    await user.type(screen.getByLabelText(/description/i), 'Test Description')
    await user.type(screen.getByLabelText(/price/i), '100000')
    await user.type(screen.getByLabelText(/location/i), 'Test Location')

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockApiService.createProperty).toHaveBeenCalled()
      expect(mockOnSuccess).toHaveBeenCalledWith('property-123')
    })
  })

  it('shows success toast on form submission', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    // Fill required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property')
    await user.type(screen.getByLabelText(/description/i), 'Test Description')
    await user.type(screen.getByLabelText(/price/i), '100000')
    await user.type(screen.getByLabelText(/location/i), 'Test Location')

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockToast.success).toHaveBeenCalledWith('Property created successfully!')
    })
  })

  it('handles form submission errors', async () => {
    mockApiService.createProperty.mockRejectedValue(new Error('Submission failed'))

    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    // Fill required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property')
    await user.type(screen.getByLabelText(/description/i), 'Test Description')
    await user.type(screen.getByLabelText(/price/i), '100000')
    await user.type(screen.getByLabelText(/location/i), 'Test Location')

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Failed to create property. Please try again.')
    })
  })

  it('validates required fields', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    // Form should not submit with empty required fields
    expect(mockApiService.createProperty).not.toHaveBeenCalled()
  })

  it('displays property type options', () => {
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const propertyTypeSelect = screen.getByLabelText(/property type/i)
    expect(propertyTypeSelect).toHaveValue('apartment')

    // Check if select has options (this depends on the actual implementation)
    expect(propertyTypeSelect.tagName).toBe('SELECT')
  })

  it('displays language options', () => {
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const languageSelect = screen.getByLabelText(/language/i)
    expect(languageSelect).toHaveValue('English')
    expect(languageSelect.tagName).toBe('SELECT')
  })

  it('handles numeric input validation', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const areaInput = screen.getByLabelText(/area/i)
    await user.type(areaInput, 'invalid')

    // Should handle invalid input gracefully
    expect(areaInput).toHaveValue(0)
  })

  it('shows proper loading states during submission', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    // Fill required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property')
    await user.type(screen.getByLabelText(/description/i), 'Test Description')
    await user.type(screen.getByLabelText(/price/i), '100000')
    await user.type(screen.getByLabelText(/location/i), 'Test Location')

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    // Button should show loading state
    expect(screen.getByTestId('loading-button')).toBeInTheDocument()
  })

  it('logs successful operations', async () => {
    const mockLogger = require('@/lib/logger').logger
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const generateButton = screen.getByRole('button', { name: /generate with ai/i })
    await user.click(generateButton)

    await waitFor(() => {
      expect(mockLogger.info).toHaveBeenCalledWith('AI content generation started')
    })
  })

  it('logs errors appropriately', async () => {
    const mockLogger = require('@/lib/logger').logger
    mockApiService.generatePropertyContent.mockRejectedValue(new Error('API Error'))

    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const generateButton = screen.getByRole('button', { name: /generate with ai/i })
    await user.click(generateButton)

    await waitFor(() => {
      expect(mockLogger.error).toHaveBeenCalled()
    })
  })

  it('handles onSuccess callback correctly', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    // Fill required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property')
    await user.type(screen.getByLabelText(/description/i), 'Test Description')
    await user.type(screen.getByLabelText(/price/i), '100000')
    await user.type(screen.getByLabelText(/location/i), 'Test Location')

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalledWith('property-123')
    })
  })

  it('works without onSuccess callback', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm />)

    // Fill required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property')
    await user.type(screen.getByLabelText(/description/i), 'Test Description')
    await user.type(screen.getByLabelText(/price/i), '100000')
    await user.type(screen.getByLabelText(/location/i), 'Test Location')

    const submitButton = screen.getByRole('button', { name: /create property/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockApiService.createProperty).toHaveBeenCalled()
    })
  })

  it('renders with proper accessibility attributes', () => {
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const form = screen.getByRole('form')
    expect(form).toHaveAttribute('aria-label', 'Property creation form with AI assistance')
  })

  it('has proper form structure', () => {
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const form = screen.getByRole('form')
    expect(form).toBeInTheDocument()

    // Check for required field indicators
    const requiredFields = screen.getAllByText('*')
    expect(requiredFields.length).toBeGreaterThan(0)
  })

  it('handles rapid AI generation requests', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    const generateButton = screen.getByRole('button', { name: /generate with ai/i })

    // Click multiple times rapidly
    await user.click(generateButton)
    await user.click(generateButton)
    await user.click(generateButton)

    // Should only call API once due to loading state
    await waitFor(() => {
      expect(mockApiService.generatePropertyContent).toHaveBeenCalledTimes(1)
    })
  })

  it('maintains form state during AI generation', async () => {
    const user = userEvent.setup()
    render(<GenAIPropertyForm onSuccess={mockOnSuccess} />)

    // Fill some fields
    await user.type(screen.getByLabelText(/title/i), 'Original Title')
    await user.type(screen.getByLabelText(/location/i), 'Original Location')

    // Generate AI content
    const generateButton = screen.getByRole('button', { name: /generate with ai/i })
    await user.click(generateButton)

    // Original values should be preserved until AI content is applied
    expect(screen.getByLabelText(/title/i)).toHaveValue('Original Title')
    expect(screen.getByLabelText(/location/i)).toHaveValue('Original Location')
  })
})
