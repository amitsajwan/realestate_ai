import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SmartPropertyForm from '@/components/SmartPropertyForm';

// Mock the API service
jest.mock('@/lib/api', () => ({
  apiService: {
    getAgentProfile: jest.fn().mockResolvedValue({ success: true, data: {} }),
    getCurrentUser: jest.fn().mockResolvedValue({ id: 'user-123' }),
    createProperty: jest.fn().mockResolvedValue({ success: true }),
    uploadImages: jest.fn().mockResolvedValue({ success: true, files: [] }),
  },
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: { div: ({ children, ...props }: any) => <div {...props}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('PropertyForm Price Handling', () => {
  test('renders price input as number type', async () => {
    const user = userEvent.setup();
    render(<SmartPropertyForm />);
    
    // Navigate to pricing step
    await user.type(screen.getByLabelText(/property address/i), '123 Test Street');
    await user.type(screen.getByLabelText(/area\/locality/i), 'Test City');
    await user.click(screen.getByText('Next'));
    
    await user.selectOptions(screen.getByLabelText(/property type/i), 'Apartment');
    await user.type(screen.getByLabelText(/area \(sq ft\)/i), '1200');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '3');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '2');
    await user.click(screen.getByText('Next'));
    
    // Test price input
    const priceInput = screen.getByLabelText(/property price/i);
    expect(priceInput).toHaveAttribute('type', 'number');
  });

  test('validates price input correctly', async () => {
    const user = userEvent.setup();
    render(<SmartPropertyForm />);
    
    // Navigate to pricing step
    await user.type(screen.getByLabelText(/property address/i), '123 Test Street');
    await user.type(screen.getByLabelText(/area\/locality/i), 'Test City');
    await user.click(screen.getByText('Next'));
    
    await user.selectOptions(screen.getByLabelText(/property type/i), 'Apartment');
    await user.type(screen.getByLabelText(/area \(sq ft\)/i), '1200');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '3');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '2');
    await user.click(screen.getByText('Next'));
    
    // Try to proceed without entering price
    await user.click(screen.getByText('Next'));
    
    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText('Price is required')).toBeInTheDocument();
    });
  });

  test('handles price input as number', async () => {
    const user = userEvent.setup();
    render(<SmartPropertyForm />);
    
    // Navigate to pricing step
    await user.type(screen.getByLabelText(/property address/i), '123 Test Street');
    await user.type(screen.getByLabelText(/area\/locality/i), 'Test City');
    await user.click(screen.getByText('Next'));
    
    await user.selectOptions(screen.getByLabelText(/property type/i), 'Apartment');
    await user.type(screen.getByLabelText(/area \(sq ft\)/i), '1200');
    await user.selectOptions(screen.getByLabelText(/bedrooms/i), '3');
    await user.selectOptions(screen.getByLabelText(/bathrooms/i), '2');
    await user.click(screen.getByText('Next'));
    
    // Test price input
    const priceInput = screen.getByLabelText(/property price/i);
    await user.type(priceInput, '5000000');
    expect(priceInput).toHaveValue(5000000);
  });
});