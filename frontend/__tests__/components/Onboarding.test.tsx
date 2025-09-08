import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import Onboarding from '../../components/Onboarding'

// Mock all dependencies
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
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
  UserIcon: (props: any) => <div data-testid="user-icon" {...props} />,
  BuildingOfficeIcon: (props: any) => <div data-testid="building-icon" {...props} />,
  SparklesIcon: (props: any) => <div data-testid="sparkles-icon" {...props} />,
  ShareIcon: (props: any) => <div data-testid="share-icon" {...props} />,
  DocumentTextIcon: (props: any) => <div data-testid="document-icon" {...props} />,
  PhotoIcon: (props: any) => <div data-testid="photo-icon" {...props} />,
  CheckIcon: (props: any) => <div data-testid="check-icon" {...props} />,
  ArrowRightIcon: (props: any) => <div data-testid="arrow-right-icon" {...props} />,
  ArrowLeftIcon: (props: any) => <div data-testid="arrow-left-icon" {...props} />,
}))

jest.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: any) => <div>{children}</div>,
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

jest.mock('@/lib/auth', () => ({
  authManager: {
    updateOnboarding: jest.fn(),
    logout: jest.fn(),
  },
}))

jest.mock('@/lib/api', () => ({
  apiService: {
    getBrandingSuggestions: jest.fn(),
  },
}))

jest.mock('@/lib/error-handler', () => ({
  handleError: jest.fn(),
  showSuccess: jest.fn(),
  withErrorHandling: jest.fn(),
}))

jest.mock('@/lib/theme', () => ({
  applyBrandTheme: jest.fn(),
}))

jest.mock('@/hooks/useLoading', () => ({
  useAsyncOperation: jest.fn(() => ({
    execute: jest.fn(),
    isLoading: false,
    error: null,
    data: null,
  })),
  useMultipleLoading: jest.fn(() => ({
    setLoading: jest.fn(),
    isLoading: jest.fn(() => false),
  })),
}))

jest.mock('@/components/LoadingStates', () => ({
  LoadingButton: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  LoadingOverlay: ({ children }: any) => <div>{children}</div>,
}))

const mockToast = require('react-hot-toast').default
const mockAuthManager = require('@/lib/auth').authManager
const mockApiService = require('@/lib/api').apiService
const mockWithErrorHandling = require('@/lib/error-handler').withErrorHandling
const mockApplyBrandTheme = require('@/lib/theme').applyBrandTheme

const mockUser = {
  id: '1',
  email: 'test@example.com',
  first_name: 'John',
  last_name: 'Doe',
  phone: '+1234567890',
  onboarding_completed: false,
  onboardingStep: 1,
  firstName: 'John',
  lastName: 'Doe',
  company: 'Test Company',
  position: 'Manager',
  licenseNumber: 'LIC123',
}

const mockProps = {
  user: mockUser,
  currentStep: 1,
  onStepChange: jest.fn(),
  onComplete: jest.fn(),
}

describe('Onboarding Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockWithErrorHandling.mockImplementation((fn) => fn())
  })

  describe('Initial Rendering', () => {
    it.skip('renders the onboarding component with correct step', () => {
      render(<Onboarding {...mockProps} />)

      expect(screen.getByText('Personal Info')).toBeInTheDocument()
      expect(screen.getByText('Step 1 of 6')).toBeInTheDocument()
    })

    it.skip('displays progress indicators for all steps', () => {
      render(<Onboarding {...mockProps} />)

      expect(screen.getByText('Personal Info')).toBeInTheDocument()
      expect(screen.getByText('Company')).toBeInTheDocument()
      expect(screen.getByText('AI Branding')).toBeInTheDocument()
      expect(screen.getByText('Social')).toBeInTheDocument()
      expect(screen.getByText('Terms')).toBeInTheDocument()
      expect(screen.getByText('Photo')).toBeInTheDocument()
    })

    it.skip('shows current step as active', () => {
      render(<Onboarding {...mockProps} />)

      const currentStepIndicator = screen.getByText('1')
      expect(currentStepIndicator).toHaveClass('bg-blue-500')
    })

    it('displays navigation buttons', () => {
      render(<Onboarding {...mockProps} />)

      expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /next step/i })).toBeInTheDocument()
    })
  })

  describe('Step 1: Personal Info', () => {
    it('renders personal info form fields', () => {
      render(<Onboarding {...mockProps} />)

      expect(screen.getByPlaceholderText('John')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Doe')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('+91 98765 43210')).toBeInTheDocument()
    })

    it('validates required fields', async () => {
      const user = userEvent.setup()
      render(<Onboarding {...mockProps} />)

      // Clear required fields
      const firstNameInput = screen.getByPlaceholderText('John')
      const lastNameInput = screen.getByPlaceholderText('Doe')

      await user.clear(firstNameInput)
      await user.clear(lastNameInput)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      expect(mockToast.error).toHaveBeenCalledWith('Please enter your first name')
    })

    it('accepts valid personal info', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockResolvedValue({ error: null })

      render(<Onboarding {...mockProps} />)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      expect(mockAuthManager.updateOnboarding).toHaveBeenCalledWith(2, expect.any(Object))
    })
  })

  describe.skip('Step 2: Company Info', () => {
    it('renders company form fields', () => {
      render(<Onboarding {...mockProps} currentStep={2} />)

      expect(screen.getByPlaceholderText('Real Estate Pro')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Senior Agent')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('RE123456')).toBeInTheDocument()
    })

    it('validates company name requirement', async () => {
      const user = userEvent.setup()
      render(<Onboarding {...mockProps} currentStep={2} />)

      const companyInput = screen.getByPlaceholderText('Real Estate Pro')
      await user.clear(companyInput)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      expect(mockToast.error).toHaveBeenCalledWith('Please enter your company name')
    })

    it('accepts valid company info', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockResolvedValue({ error: null })

      render(<Onboarding {...mockProps} currentStep={2} />)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      expect(mockAuthManager.updateOnboarding).toHaveBeenCalledWith(3, expect.any(Object))
    })
  })

  describe.skip('Step 3: AI Branding', () => {
    it('renders AI branding section', () => {
      render(<Onboarding {...mockProps} currentStep={3} />)

      expect(screen.getByText('AI Branding Suggestions')).toBeInTheDocument()
      expect(screen.getByText('AI Content Style')).toBeInTheDocument()
      expect(screen.getByText('AI Tone')).toBeInTheDocument()
    })

    it('shows generate branding button when no suggestions exist', () => {
      render(<Onboarding {...mockProps} currentStep={3} />)

      expect(screen.getByText('Generate Branding')).toBeInTheDocument()
    })

    it('disables generate button when company name is missing', () => {
      const userWithoutCompany = {
        ...mockUser,
        company: '',
      }

      render(<Onboarding {...mockProps} user={userWithoutCompany} currentStep={3} />)

      const generateButton = screen.getByText('Generate Branding')
      expect(generateButton).toBeDisabled()
    })

    it('generates branding suggestions', async () => {
      const user = userEvent.setup()
      const mockBrandingSuggestions = {
        tagline: 'Your Dream Home Awaits',
        about: 'Professional real estate services',
        colors: {
          primary: '#3B82F6',
          secondary: '#64748B',
          accent: '#F59E0B'
        }
      }

      mockApiService.getBrandingSuggestions.mockResolvedValue(mockBrandingSuggestions)

      render(<Onboarding {...mockProps} currentStep={3} />)

      const generateButton = screen.getByText('Generate Branding')
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Your Dream Home Awaits')).toBeInTheDocument()
      })
    })

    it('applies branding theme', async () => {
      const user = userEvent.setup()
      const mockBrandingSuggestions = {
        tagline: 'Your Dream Home Awaits',
        about: 'Professional real estate services',
        colors: {
          primary: '#3B82F6',
          secondary: '#64748B',
          accent: '#F59E0B'
        }
      }

      render(<Onboarding {...mockProps} currentStep={3} />)

      // Mock the branding suggestions in state
      const component = screen.getByText('AI Branding Suggestions').closest('div')
      // Simulate having branding suggestions
      const applyButton = screen.getByText('Apply Branding')
      await user.click(applyButton)

      expect(mockApplyBrandTheme).toHaveBeenCalled()
      expect(mockToast.success).toHaveBeenCalledWith('Branding applied and saved successfully!')
    })
  })

  describe.skip('Step 4: Social Integration', () => {
    it('renders social integration section', () => {
      render(<Onboarding {...mockProps} currentStep={4} />)

      expect(screen.getByText('Connect Facebook')).toBeInTheDocument()
      expect(screen.getByText('Connect Facebook Page')).toBeInTheDocument()
    })
  })

  describe.skip('Step 5: Terms Acceptance', () => {
    it('renders terms and privacy checkboxes', () => {
      render(<Onboarding {...mockProps} currentStep={5} />)

      expect(screen.getByText('I agree to the Terms of Service')).toBeInTheDocument()
      expect(screen.getByText('I have read and agree to the Privacy Policy')).toBeInTheDocument()
    })

    it('validates terms acceptance', async () => {
      const user = userEvent.setup()
      render(<Onboarding {...mockProps} currentStep={5} />)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      expect(mockToast.error).toHaveBeenCalledWith('Please accept the Terms of Service')
    })

    it('validates privacy acceptance', async () => {
      const user = userEvent.setup()
      render(<Onboarding {...mockProps} currentStep={5} />)

      const termsCheckbox = screen.getByLabelText('I agree to the Terms of Service')
      await user.click(termsCheckbox)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      expect(mockToast.error).toHaveBeenCalledWith('Please accept the Privacy Policy')
    })

    it('accepts terms and proceeds', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockResolvedValue({ error: null })

      render(<Onboarding {...mockProps} currentStep={5} />)

      const termsCheckbox = screen.getByLabelText('I agree to the Terms of Service')
      const privacyCheckbox = screen.getByLabelText('I have read and agree to the Privacy Policy')

      await user.click(termsCheckbox)
      await user.click(privacyCheckbox)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      expect(mockAuthManager.updateOnboarding).toHaveBeenCalledWith(6, expect.any(Object))
    })
  })

  describe.skip('Step 6: Profile Photo', () => {
    it('renders profile photo section', () => {
      render(<Onboarding {...mockProps} currentStep={6} />)

      expect(screen.getByText('Profile Photo')).toBeInTheDocument()
      expect(screen.getByText('Upload Photo')).toBeInTheDocument()
      expect(screen.getByText('Complete Onboarding')).toBeInTheDocument()
    })

    it('shows completion message', () => {
      render(<Onboarding {...mockProps} currentStep={6} />)

      expect(screen.getByText('Almost Done!')).toBeInTheDocument()
      expect(screen.getByText('Click "Complete Setup" to finish your onboarding')).toBeInTheDocument()
    })
  })

  describe.skip('Navigation', () => {
    it('disables back button on first step', () => {
      render(<Onboarding {...mockProps} />)

      const backButton = screen.getByRole('button', { name: /back/i })
      expect(backButton).toBeDisabled()
    })

    it('enables back button on subsequent steps', () => {
      render(<Onboarding {...mockProps} currentStep={2} />)

      const backButton = screen.getByRole('button', { name: /back/i })
      expect(backButton).not.toBeDisabled()
    })

    it('navigates back to previous step', async () => {
      const user = userEvent.setup()
      render(<Onboarding {...mockProps} currentStep={2} />)

      const backButton = screen.getByRole('button', { name: /back/i })
      await user.click(backButton)

      expect(mockProps.onStepChange).toHaveBeenCalledWith(1)
    })

    it('shows skip button on non-final steps', () => {
      render(<Onboarding {...mockProps} currentStep={2} />)

      expect(screen.getByText('Skip')).toBeInTheDocument()
    })

    it('hides skip button on final step', () => {
      render(<Onboarding {...mockProps} currentStep={6} />)

      expect(screen.queryByText('Skip')).not.toBeInTheDocument()
    })
  })

  describe.skip('Completion Flow', () => {
    it('completes onboarding on final step', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockResolvedValue({ error: null })

      render(<Onboarding {...mockProps} currentStep={6} />)

      const completeButton = screen.getByRole('button', { name: /complete onboarding/i })
      await user.click(completeButton)

      await waitFor(() => {
        expect(mockAuthManager.updateOnboarding).toHaveBeenCalledWith(6, expect.any(Object), true)
        expect(mockProps.onComplete).toHaveBeenCalled()
      })
    })

    it('handles completion errors', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockRejectedValue(new Error('Completion failed'))

      render(<Onboarding {...mockProps} currentStep={6} />)

      const completeButton = screen.getByRole('button', { name: /complete onboarding/i })
      await user.click(completeButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalled()
      })
    })
  })

  describe.skip('Form Data Management', () => {
    it('updates form data on input change', async () => {
      const user = userEvent.setup()
      render(<Onboarding {...mockProps} />)

      const firstNameInput = screen.getByPlaceholderText('John')
      await user.clear(firstNameInput)
      await user.type(firstNameInput, 'Jane')

      expect(firstNameInput).toHaveValue('Jane')
    })

    it('preserves form data across steps', () => {
      const { rerender } = render(<Onboarding {...mockProps} />)

      rerender(<Onboarding {...mockProps} currentStep={2} />)

      expect(screen.getByPlaceholderText('Real Estate Pro')).toBeInTheDocument()
    })

    it('loads existing user data', () => {
      render(<Onboarding {...mockProps} />)

      expect(screen.getByPlaceholderText('John')).toHaveValue('John')
      expect(screen.getByPlaceholderText('Doe')).toHaveValue('Doe')
    })
  })

  describe.skip('Progress Tracking', () => {
    it('shows completed steps with checkmarks', () => {
      render(<Onboarding {...mockProps} currentStep={3} />)

      const completedSteps = screen.getAllByTestId('check-icon')
      expect(completedSteps).toHaveLength(2) // Steps 1 and 2 completed
    })

    it('highlights current step', () => {
      render(<Onboarding {...mockProps} currentStep={3} />)

      const currentStepIndicator = screen.getByText('3')
      expect(currentStepIndicator).toHaveClass('bg-blue-500')
    })

    it('shows pending steps as gray', () => {
      render(<Onboarding {...mockProps} currentStep={2} />)

      const step3Indicator = screen.getByText('3')
      expect(step3Indicator).toHaveClass('bg-gray-200')
    })
  })

  describe.skip('Error Handling', () => {
    it('handles API errors during step updates', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockRejectedValue(new Error('API Error'))

      render(<Onboarding {...mockProps} />)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalled()
      })
    })

    it('handles branding generation errors', async () => {
      const user = userEvent.setup()
      mockApiService.getBrandingSuggestions.mockRejectedValue(new Error('Branding failed'))

      render(<Onboarding {...mockProps} currentStep={3} />)

      const generateButton = screen.getByText('Generate Branding')
      await user.click(generateButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalled()
      })
    })
  })

  describe.skip('Logout Functionality', () => {
    it('provides logout option', () => {
      render(<Onboarding {...mockProps} />)

      expect(screen.getByText('Logout')).toBeInTheDocument()
    })

    it('handles logout action', async () => {
      const user = userEvent.setup()
      const mockRouter = require('next/navigation').useRouter()

      render(<Onboarding {...mockProps} />)

      const logoutButton = screen.getByText('Logout')
      await user.click(logoutButton)

      expect(mockAuthManager.logout).toHaveBeenCalled()
      expect(mockRouter.push).toHaveBeenCalledWith('/login')
    })
  })

  describe.skip('Responsive Design', () => {
    it('adapts form layout for mobile', () => {
      render(<Onboarding {...mockProps} />)

      const formContainer = screen.getByPlaceholderText('John').closest('div')
      expect(formContainer).toHaveClass('md:grid-cols-2')
    })

    it('stacks navigation buttons appropriately', () => {
      render(<Onboarding {...mockProps} />)

      const navContainer = screen.getByRole('button', { name: /back/i }).closest('div')
      expect(navContainer).toHaveClass('flex', 'justify-between')
    })
  })

  describe.skip('Accessibility', () => {
    it('has proper form labels', () => {
      render(<Onboarding {...mockProps} />)

      expect(screen.getByLabelText('First Name *')).toBeInTheDocument()
      expect(screen.getByLabelText('Last Name *')).toBeInTheDocument()
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<Onboarding {...mockProps} />)

      const firstNameInput = screen.getByPlaceholderText('John')
      firstNameInput.focus()
      expect(document.activeElement).toBe(firstNameInput)

      await user.keyboard('{Tab}')
      // Should move to next input
    })

    it('provides proper ARIA attributes', () => {
      render(<Onboarding {...mockProps} />)

      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes).toHaveLength(2) // Terms and privacy checkboxes
    })
  })

  describe.skip('Loading States', () => {
    it('shows loading state during step transitions', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<Onboarding {...mockProps} />)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      expect(screen.getByText('Next Step')).toBeInTheDocument() // LoadingButton should show loading state
    })

    it('shows loading state during completion', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<Onboarding {...mockProps} currentStep={6} />)

      const completeButton = screen.getByRole('button', { name: /complete onboarding/i })
      await user.click(completeButton)

      expect(screen.getByText('Complete Onboarding')).toBeInTheDocument() // LoadingButton should show loading state
    })
  })

  describe.skip('Animation and Transitions', () => {
    it('animates step transitions', () => {
      render(<Onboarding {...mockProps} />)

      const stepContent = screen.getByPlaceholderText('John').closest('div')
      expect(stepContent).toBeInTheDocument() // AnimatePresence should wrap content
    })

    it('provides smooth navigation between steps', async () => {
      const user = userEvent.setup()
      mockAuthManager.updateOnboarding.mockResolvedValue({ error: null })

      render(<Onboarding {...mockProps} />)

      const nextButton = screen.getByRole('button', { name: /next step/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText('Company')).toBeInTheDocument()
      })
    })
  })
})
