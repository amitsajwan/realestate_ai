import React from 'react';
import { render, screen } from '@testing-library/react';
import ProfileSettings from '../../components/ProfileSettings';

// Mock dependencies
jest.mock('../../lib/auth', () => ({
  authManager: {
    getCurrentUser: jest.fn(() => Promise.resolve({
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      phone: '123-456-7890'
    })),
    updateProfile: jest.fn(() => Promise.resolve({ success: true })),
    getState: jest.fn(() => ({
      isAuthenticated: true,
      user: { id: '1', name: 'Test User', email: 'test@example.com' },
      token: 'mock-token',
      refreshToken: 'mock-refresh-token',
      isLoading: false,
      error: null
    })),
    subscribe: jest.fn(() => jest.fn())
  }
}));

jest.mock('../../lib/api', () => ({
  apiService: {
    updateProfile: jest.fn(() => Promise.resolve({ success: true })),
    getBrandingSuggestions: jest.fn(() => Promise.resolve({ success: true, data: {} }))
  }
}));

jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn()
  }
}));

jest.mock('../../lib/theme', () => ({
  applyBrandTheme: jest.fn()
}));

jest.mock('../../lib/error-handler', () => ({
  handleError: jest.fn(),
  showSuccess: jest.fn(),
  withErrorHandling: jest.fn((fn) => fn)
}));

jest.mock('../../hooks/useLoading', () => ({
  useAsyncOperation: jest.fn(() => ({ isLoading: false, execute: jest.fn() })),
  useMultipleLoading: jest.fn(() => ({ isLoading: jest.fn(() => false), setLoading: jest.fn() }))
}));

jest.mock('../../components/LoadingStates', () => ({
  LoadingButton: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  LoadingOverlay: ({ children }: any) => <div>{children}</div>
}));

jest.mock('../../lib/form-validation', () => ({
  profileSettingsSchema: {
    parse: jest.fn((data) => data)
  },
  FormValidator: jest.fn()
}));



describe('ProfileSettings', () => {
  it('renders the profile settings form correctly', () => {
    render(<ProfileSettings />);
    
    expect(screen.getByText('Profile Settings')).toBeInTheDocument();
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
  });
});