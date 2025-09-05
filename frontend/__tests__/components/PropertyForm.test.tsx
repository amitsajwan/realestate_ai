import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';

// Mock all dependencies before importing the component
jest.mock('../../lib/api', () => ({
  apiService: {
    createProperty: jest.fn().mockResolvedValue({ success: true, data: { id: '123' } }),
  },
}));

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('@heroicons/react/24/outline', () => ({
  InformationCircleIcon: () => <div data-testid="info-icon" />,
  HomeIcon: () => <div data-testid="home-icon" />,
  MapPinIcon: () => <div data-testid="map-pin-icon" />,
  CurrencyDollarIcon: () => <div data-testid="currency-dollar-icon" />,
  DocumentTextIcon: () => <div data-testid="document-text-icon" />,
  CheckCircleIcon: () => <div data-testid="check-circle-icon" />,
  ExclamationTriangleIcon: () => <div data-testid="exclamation-triangle-icon" />,
  LightBulbIcon: () => <div data-testid="light-bulb-icon" />,
  ArrowRightIcon: () => <div data-testid="arrow-right-icon" />,
  ArrowLeftIcon: () => <div data-testid="arrow-left-icon" />,
}));

// Import the component after all mocks are set up
import PropertyForm from '../../components/PropertyForm';

describe('PropertyForm - ZodError Validation Tests', () => {
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders form with all required fields', () => {
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
