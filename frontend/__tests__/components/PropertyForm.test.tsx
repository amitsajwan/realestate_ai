import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import PropertyForm from '../../components/PropertyForm'

// Mock all dependencies
jest.mock('../../lib/api', () => ({
  apiService: {
    createProperty: jest.fn(),
    getAIPropertySuggestions: jest.fn(),
    getAgentProfile: jest.fn(),
  },
  APIError: class APIError extends Error {
    constructor(message: string) {
      super(message)
      this.name = 'APIError'
    }
  },
}))

jest.mock('react-hook-form', () => ({
  useForm: jest.fn(() => ({
    register: jest.fn(),
    handleSubmit: jest.fn((fn) => (e: any) => {
      e?.preventDefault?.()
      return fn({
        title: 'Test Property',
        price: '₹25,00,000',
        address: '123 Test St',
        bedrooms: 3,
        bathrooms: 2,
        area: 1200,
        description: 'Test description',
        amenities: 'parking, garden',
      })
    }),
    setValue: jest.fn(),
    formState: { errors: {} },
  })),
}))

jest.mock('@hookform/resolvers/zod', () => ({
  zodResolver: jest.fn(() => jest.fn()),
}))

jest.mock('../../lib/validation', () => ({
  propertySchema: {},
  PropertyFormData: {},
  getFieldError: jest.fn(),
  getFieldErrorClass: jest.fn(),
}))

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  PlusIcon: (props: any) => <div data-testid="plus-icon" {...props} />,
  SparklesIcon: (props: any) => <div data-testid="sparkles-icon" {...props} />,
  ArrowLeftIcon: (props: any) => <div data-testid="arrow-left-icon" {...props} />,
  PhotoIcon: (props: any) => <div data-testid="photo-icon" {...props} />,
  CurrencyDollarIcon: (props: any) => <div data-testid="currency-icon" {...props} />,
  HomeIcon: (props: any) => <div data-testid="home-icon" {...props} />,
  MapPinIcon: (props: any) => <div data-testid="map-pin-icon" {...props} />,
  InformationCircleIcon: (props: any) => <div data-testid="info-icon" {...props} />,
}))

const mockApiService = require('../../lib/api').apiService
const mockToast = require('react-hot-toast').default

describe('PropertyForm Component', () => {
  const mockOnSuccess = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock successful API responses by default
    mockApiService.createProperty.mockResolvedValue({ success: true, data: { id: '123' } })
    mockApiService.getAIPropertySuggestions.mockResolvedValue({
      success: true,
      data: [{
        title: 'AI Generated Property',
        price: '₹30,00,000',
        description: 'AI generated description',
        amenities: 'parking, garden, pool'
      }]
    })
    mockApiService.getAgentProfile.mockResolvedValue({
      success: true,
      data: { id: '1', name: 'Test Agent' }
    })
  })

  describe('Basic Rendering', () => {
    it('renders the form with all required elements', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      expect(screen.getByText('Add New Property')).toBeInTheDocument()
      expect(screen.getByText('Create a detailed property listing')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /ai auto-fill/i })).toBeInTheDocument()
    })

    it('displays form sections correctly', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      expect(screen.getByText('Basic Information')).toBeInTheDocument()
      expect(screen.getByText('Property Details')).toBeInTheDocument()
      expect(screen.getByText('Description & Amenities')).toBeInTheDocument()
    })

    it('shows progress steps', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      expect(screen.getByText('Basic Info')).toBeInTheDocument()
      expect(screen.getByText('Details')).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    it('submits form successfully with valid data', async () => {
      const user = userEvent.setup()
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      // Find and submit the form
      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(mockApiService.createProperty).toHaveBeenCalledWith({
          user_id: '1',
          title: 'Test Property',
          type: 'Apartment',
          bedrooms: 3,
          bathrooms: 2,
          price: 2500000,
          price_unit: 'INR',
          city: 'Mumbai',
          area: 1200,
          address: '123 Test St',
          description: 'Test description',
          amenities: ['parking', 'garden']
        })
        expect(mockToast.success).toHaveBeenCalledWith('Property added successfully!')
        expect(mockOnSuccess).toHaveBeenCalled()
      })
    })

    it('handles API errors gracefully', async () => {
      const user = userEvent.setup()
      mockApiService.createProperty.mockRejectedValue(new Error('API Error'))

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to add property. Please try again.')
      })
    })

    it('handles APIError instances correctly', async () => {
      const user = userEvent.setup()
      const APIError = require('../../lib/api').APIError
      mockApiService.createProperty.mockRejectedValue(new APIError('Specific API error'))

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to add property: Specific API error')
      })
    })

    it('shows loading state during submission', async () => {
      const user = userEvent.setup()
      // Mock a delayed response
      mockApiService.createProperty.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      )

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const submitButton = screen.getByRole('button', { name: /add property/i })
      await user.click(submitButton)

      // Check if loading state is shown
      expect(submitButton).toBeDisabled()
    })
  })

  describe('AI Auto-Fill Functionality', () => {
    it('successfully auto-fills form with AI suggestions', async () => {
      const user = userEvent.setup()
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const aiButton = screen.getByRole('button', { name: /ai auto-fill/i })
      await user.click(aiButton)

      await waitFor(() => {
        expect(mockApiService.getAIPropertySuggestions).toHaveBeenCalledWith({
          property_type: 'Apartment',
          location: 'City Center',
          budget: '₹75,00,000',
          requirements: 'Modern amenities',
          agent_profile: { id: '1', name: 'Test Agent' }
        })
        expect(mockToast.success).toHaveBeenCalledWith('Property form auto-filled with AI content!')
      })
    })

    it('handles AI API errors gracefully', async () => {
      const user = userEvent.setup()
      mockApiService.getAIPropertySuggestions.mockRejectedValue(new Error('AI API Error'))

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const aiButton = screen.getByRole('button', { name: /ai auto-fill/i })
      await user.click(aiButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to generate AI content. Please try again.')
      })
    })

    it('shows loading state during AI generation', async () => {
      const user = userEvent.setup()
      mockApiService.getAIPropertySuggestions.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          success: true,
          data: [{
            title: 'AI Generated Property',
            price: '₹30,00,000',
            description: 'AI generated description',
            amenities: 'parking, garden, pool'
          }]
        }), 100))
      )

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const aiButton = screen.getByRole('button', { name: /ai auto-fill/i })
      await user.click(aiButton)

      expect(screen.getByText('Generating...')).toBeInTheDocument()
    })

    it('handles empty AI suggestions', async () => {
      const user = userEvent.setup()
      mockApiService.getAIPropertySuggestions.mockResolvedValue({
        success: true,
        data: []
      })

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const aiButton = screen.getByRole('button', { name: /ai auto-fill/i })
      await user.click(aiButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to generate AI content. Please try again.')
      })
    })
  })

  describe('Agent Profile Integration', () => {
    it('fetches agent profile on mount', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      expect(mockApiService.getAgentProfile).toHaveBeenCalled()
    })

    it('handles agent profile fetch errors gracefully', () => {
      mockApiService.getAgentProfile.mockRejectedValue(new Error('Profile fetch error'))

      // Should not throw error, just log to console
      expect(() => render(<PropertyForm onSuccess={mockOnSuccess} />)).not.toThrow()
    })
  })

  describe('Form Data Transformation', () => {
    it('correctly transforms form data for API', async () => {
      const user = userEvent.setup()
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(mockApiService.createProperty).toHaveBeenCalledWith(
          expect.objectContaining({
            user_id: '1',
            title: 'Test Property',
            price: 2500000, // Should parse currency string
            bedrooms: 3,
            bathrooms: 2,
            area: 1200,
            amenities: ['parking', 'garden'] // Should split and trim
          })
        )
      })
    })

    it('handles empty amenities field', async () => {
      const user = userEvent.setup()

      // Mock form to return empty amenities
      const mockUseForm = require('react-hook-form').useForm
      mockUseForm.mockReturnValueOnce({
        register: jest.fn(),
        handleSubmit: jest.fn((fn) => (e: any) => {
          e?.preventDefault?.()
          return fn({
            title: 'Test Property',
            price: '₹25,00,000',
            address: '123 Test St',
            bedrooms: 3,
            bathrooms: 2,
            area: 1200,
            description: 'Test description',
            amenities: '', // Empty amenities
          })
        }),
        setValue: jest.fn(),
        formState: { errors: {} },
      })

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(mockApiService.createProperty).toHaveBeenCalledWith(
          expect.objectContaining({
            amenities: [] // Should be empty array
          })
        )
      })
    })
  })

  describe('User Experience', () => {
    it('provides visual feedback during form submission', async () => {
      const user = userEvent.setup()
      mockApiService.createProperty.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      )

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const submitButton = screen.getByRole('button', { name: /add property/i })
      await user.click(submitButton)

      // Button should be disabled during submission
      expect(submitButton).toBeDisabled()
    })

    it('shows success message on successful submission', async () => {
      const user = userEvent.setup()
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Property added successfully!')
      })
    })

    it('calls onSuccess callback after successful submission', async () => {
      const user = userEvent.setup()
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled()
      })
    })
  })

  describe('Error Handling', () => {
    it('logs errors to console for debugging', async () => {
      const user = userEvent.setup()
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

      mockApiService.createProperty.mockRejectedValue(new Error('Test error'))

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('[PropertyForm] Property creation error:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })

    it('handles network errors gracefully', async () => {
      const user = userEvent.setup()
      mockApiService.createProperty.mockRejectedValue(new Error('Network error'))

      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      await user.click(screen.getByRole('button', { name: /add property/i }))

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to add property. Please try again.')
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper form structure', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      const form = screen.getByRole('form')
      expect(form).toBeInTheDocument()
    })

    it('has accessible button labels', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      expect(screen.getByRole('button', { name: /ai auto-fill/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add property/i })).toBeInTheDocument()
    })
  })

  describe('Integration with External Libraries', () => {
    it('uses react-hook-form for form management', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      // The form should be using react-hook-form hooks
      expect(require('react-hook-form').useForm).toHaveBeenCalled()
    })

    it('integrates with Zod for validation', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />)

      // Should use zodResolver
      expect(require('@hookform/resolvers/zod').zodResolver).toHaveBeenCalled()
    })
  })

  describe('Form Rendering', () => {
    it('renders all form fields correctly', () => {
      render(<PropertyForm onSuccess={mockOnSuccess} />);

      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/location/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/bedrooms/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/bathrooms/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/area/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/price/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/property type/i)).toBeInTheDocument();
    });
  });

  it('shows ZodError when bedrooms is submitted as string instead of number', async () => {
    const user = userEvent.setup();
    render(<PropertyForm onSuccess={mockOnSuccess} />);

    // Fill out required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');
    await user.type(screen.getByLabelText(/location/i), 'Test Location');
    await user.type(screen.getByLabelText(/address/i), 'Test Address');
    await user.type(screen.getByLabelText(/price/i), '$100,000');
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment');

    // Select bedrooms and bathrooms (these should be numbers but might be strings)
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '2');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '1');
    await user.type(screen.getByLabelText(/area/i), '1000');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create property/i });
    await user.click(submitButton);

    // The form should handle the conversion properly now with valueAsNumber: true
    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  it('successfully submits form with numeric bedrooms and bathrooms values', async () => {
    const user = userEvent.setup();
    render(<PropertyForm onSuccess={mockOnSuccess} />);

    // Fill out all required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');
    await user.type(screen.getByLabelText(/location/i), 'Test Location');
    await user.type(screen.getByLabelText(/address/i), 'Test Address');
    await user.type(screen.getByLabelText(/price/i), '$100,000');
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '2');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '1');
    await user.type(screen.getByLabelText(/area/i), '1000');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create property/i });
    await user.click(submitButton);

    // Verify successful submission
    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  it('validates bedrooms field is required', async () => {
    const user = userEvent.setup();
    render(<PropertyForm onSuccess={mockOnSuccess} />);

    // Fill out all fields except bedrooms
    await user.type(screen.getByLabelText(/title/i), 'Test Property');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');
    await user.type(screen.getByLabelText(/location/i), 'Test Location');
    await user.type(screen.getByLabelText(/address/i), 'Test Address');
    await user.type(screen.getByLabelText(/price/i), '$100,000');
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '1');
    await user.type(screen.getByLabelText(/area/i), '1000');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create property/i });
    await user.click(submitButton);

    // Check for validation error
    await waitFor(() => {
      expect(screen.getByText(/at least 1 bedroom is required/i)).toBeInTheDocument();
    });
  });

  it('validates bathrooms field is required', async () => {
    const user = userEvent.setup();
    render(<PropertyForm onSuccess={mockOnSuccess} />);

    // Fill out all fields except bathrooms
    await user.type(screen.getByLabelText(/title/i), 'Test Property');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');
    await user.type(screen.getByLabelText(/location/i), 'Test Location');
    await user.type(screen.getByLabelText(/address/i), 'Test Address');
    await user.type(screen.getByLabelText(/price/i), '$100,000');
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '2');
    await user.type(screen.getByLabelText(/area/i), '1000');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create property/i });
    await user.click(submitButton);

    // Check for validation error
    await waitFor(() => {
      expect(screen.getByText(/at least 1 bathroom is required/i)).toBeInTheDocument();
    });
  });

  it('validates area field is required and numeric', async () => {
    const user = userEvent.setup();
    render(<PropertyForm onSuccess={mockOnSuccess} />);

    // Fill out all fields except area
    await user.type(screen.getByLabelText(/title/i), 'Test Property');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');
    await user.type(screen.getByLabelText(/location/i), 'Test Location');
    await user.type(screen.getByLabelText(/address/i), 'Test Address');
    await user.type(screen.getByLabelText(/price/i), '$100,000');
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '2');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '1');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create property/i });
    await user.click(submitButton);

    // Check for validation error
    await waitFor(() => {
      expect(screen.getByText(/area is required/i)).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    // Mock API failure
    const mockApiService = require('../../lib/api').apiService;
    mockApiService.createProperty.mockRejectedValueOnce(new Error('API Error'));

    const user = userEvent.setup();
    render(<PropertyForm onSuccess={mockOnSuccess} />);

    // Fill out all required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');
    await user.type(screen.getByLabelText(/location/i), 'Test Location');
    await user.type(screen.getByLabelText(/address/i), 'Test Address');
    await user.type(screen.getByLabelText(/price/i), '$100,000');
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '2');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '1');
    await user.type(screen.getByLabelText(/area/i), '1000');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create property/i });
    await user.click(submitButton);

    // Verify error handling
    await waitFor(() => {
      expect(mockOnSuccess).not.toHaveBeenCalled();
    });
  });

  it('converts string values to numbers for bedrooms, bathrooms, and area', async () => {
    const user = userEvent.setup();
    const mockApiService = require('../../lib/api').apiService;

    render(<PropertyForm onSuccess={mockOnSuccess} />);

    // Fill out all required fields
    await user.type(screen.getByLabelText(/title/i), 'Test Property');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');
    await user.type(screen.getByLabelText(/location/i), 'Test Location');
    await user.type(screen.getByLabelText(/address/i), 'Test Address');
    await user.type(screen.getByLabelText(/price/i), '$100,000');
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '2');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '1');
    await user.type(screen.getByLabelText(/area/i), '1000');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create property/i });
    await user.click(submitButton);

    // Verify that the API was called with numeric values (coerced by Zod)
    await waitFor(() => {
      expect(mockApiService.createProperty).toHaveBeenCalledWith(
        expect.objectContaining({
          bedrooms: 2, // Should be number, coerced by z.coerce.number()
          bathrooms: 1, // Should be number, coerced by z.coerce.number()
          area: 1000, // Should be number, coerced by z.coerce.number()
        })
      );
    });
  });

  it('handles Zod coercion for string inputs gracefully', async () => {
    const user = userEvent.setup();
    render(<PropertyForm onSuccess={mockOnSuccess} />);

    // Fill out all required fields - these will be strings from form inputs
    await user.type(screen.getByLabelText(/title/i), 'Test Property');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');
    await user.type(screen.getByLabelText(/location/i), 'Test Location');
    await user.type(screen.getByLabelText(/address/i), 'Test Address');
    await user.type(screen.getByLabelText(/price/i), '$100,000');
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '3');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '2');
    await user.type(screen.getByLabelText(/area/i), '1500');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create property/i });
    await user.click(submitButton);

    // Verify successful submission - Zod coercion should handle string-to-number conversion
    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });
});
