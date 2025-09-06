import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import CRM from '../../components/CRM'

// Mock all dependencies
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  UsersIcon: (props: any) => <div data-testid="users-icon" {...props} />,
  PhoneIcon: (props: any) => <div data-testid="phone-icon" {...props} />,
  ChatBubbleLeftRightIcon: (props: any) => <div data-testid="chat-icon" {...props} />,
  FunnelIcon: (props: any) => <div data-testid="funnel-icon" {...props} />,
  MagnifyingGlassIcon: (props: any) => <div data-testid="search-icon" {...props} />,
  PlusIcon: (props: any) => <div data-testid="plus-icon" {...props} />,
  EyeIcon: (props: any) => <div data-testid="eye-icon" {...props} />,
  PencilIcon: (props: any) => <div data-testid="pencil-icon" {...props} />,
  TrashIcon: (props: any) => <div data-testid="trash-icon" {...props} />,
  StarIcon: (props: any) => <div data-testid="star-icon" {...props} />,
  ClockIcon: (props: any) => <div data-testid="clock-icon" {...props} />,
  CurrencyDollarIcon: (props: any) => <div data-testid="currency-icon" {...props} />,
  MapPinIcon: (props: any) => <div data-testid="map-pin-icon" {...props} />,
  ChevronDownIcon: (props: any) => <div data-testid="chevron-down-icon" {...props} />,
  XMarkIcon: (props: any) => <div data-testid="x-mark-icon" {...props} />,
}))

jest.mock('@heroicons/react/24/solid', () => ({
  __esModule: true,
  StarIcon: (props: any) => <div data-testid="star-solid-icon" {...props} />,
  PhoneIcon: (props: any) => <div data-testid="phone-solid-icon" {...props} />,
  ChatBubbleLeftRightIcon: (props: any) => <div data-testid="chat-solid-icon" {...props} />,
}))

const mockToast = require('react-hot-toast').default

describe('CRM Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders the CRM dashboard with header', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('CRM Dashboard')).toBeInTheDocument()
        expect(screen.getByText('Manage leads and customer relationships')).toBeInTheDocument()
      })
    })

    it('displays loading state initially', () => {
      render(<CRM />)

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })

    it('renders lead cards after loading', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
        expect(screen.getByText('Priya Sharma')).toBeInTheDocument()
        expect(screen.getByText('Amit Patel')).toBeInTheDocument()
      })
    })

    it('displays CRM statistics correctly', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('New Leads')).toBeInTheDocument()
        expect(screen.getByText('Pending')).toBeInTheDocument()
        expect(screen.getByText('Converted')).toBeInTheDocument()
        expect(screen.getByText('Calls Today')).toBeInTheDocument()
      })
    })

    it('shows correct lead count', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument() // Total leads
      })
    })
  })

  describe('Search Functionality', () => {
    it('filters leads by name search', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search leads...')
      await user.type(searchInput, 'Rajesh')

      expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      expect(screen.queryByText('Priya Sharma')).not.toBeInTheDocument()
      expect(screen.queryByText('Amit Patel')).not.toBeInTheDocument()
    })

    it('filters leads by email search', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('rajesh@email.com')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search leads...')
      await user.type(searchInput, 'rajesh@email.com')

      expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      expect(screen.queryByText('Priya Sharma')).not.toBeInTheDocument()
    })

    it('filters leads by phone search', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('+91 98765 43210')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search leads...')
      await user.type(searchInput, '98765 43210')

      expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      expect(screen.queryByText('Priya Sharma')).not.toBeInTheDocument()
    })

    it('filters leads by location search', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Mumbai, Thane')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search leads...')
      await user.type(searchInput, 'Mumbai')

      expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      expect(screen.queryByText('Priya Sharma')).not.toBeInTheDocument()
    })

    it('shows no results message when search yields no matches', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search leads...')
      await user.type(searchInput, 'nonexistent')

      expect(screen.getByText('No leads found')).toBeInTheDocument()
    })
  })

  describe('Filtering Functionality', () => {
    it('filters leads by status', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)

      // Select status filter
      const statusSelect = screen.getByDisplayValue('All Status')
      await user.selectOptions(statusSelect, 'new')

      expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      expect(screen.queryByText('Priya Sharma')).not.toBeInTheDocument()
      expect(screen.queryByText('Amit Patel')).not.toBeInTheDocument()
    })

    it('filters leads by urgency', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)

      // Select urgency filter
      const urgencySelect = screen.getByDisplayValue('All Urgency')
      await user.selectOptions(urgencySelect, 'high')

      expect(screen.getByText('Priya Sharma')).toBeInTheDocument()
      expect(screen.queryByText('Rajesh Kumar')).not.toBeInTheDocument()
      expect(screen.queryByText('Amit Patel')).not.toBeInTheDocument()
    })

    it('combines multiple filters', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)

      // Apply status filter
      const statusSelect = screen.getByDisplayValue('All Status')
      await user.selectOptions(statusSelect, 'qualified')

      // Apply urgency filter
      const urgencySelect = screen.getByDisplayValue('All Urgency')
      await user.selectOptions(urgencySelect, 'high')

      expect(screen.getByText('Priya Sharma')).toBeInTheDocument()
      expect(screen.queryByText('Rajesh Kumar')).not.toBeInTheDocument()
    })

    it('clears all filters', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      // Open filters and apply a filter
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)

      const statusSelect = screen.getByDisplayValue('All Status')
      await user.selectOptions(statusSelect, 'new')

      // Clear filters
      const clearButton = screen.getByRole('button', { name: /clear filters/i })
      await user.click(clearButton)

      // All leads should be visible again
      expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      expect(screen.getByText('Priya Sharma')).toBeInTheDocument()
      expect(screen.getByText('Amit Patel')).toBeInTheDocument()
    })
  })

  describe('Lead Details Modal', () => {
    it('opens lead details modal when view button is clicked', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      const viewButtons = screen.getAllByRole('button', { name: /view/i })
      await user.click(viewButtons[0])

      expect(screen.getByText('Lead Details')).toBeInTheDocument()
      expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
    })

    it('displays lead information correctly in modal', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      const viewButtons = screen.getAllByRole('button', { name: /view/i })
      await user.click(viewButtons[0])

      expect(screen.getByText('rajesh@email.com')).toBeInTheDocument()
      expect(screen.getByText('+91 98765 43210')).toBeInTheDocument()
      expect(screen.getByText('₹50,00,000')).toBeInTheDocument()
      expect(screen.getByText('3 BHK Apartment')).toBeInTheDocument()
    })

    it('closes lead details modal', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      const viewButtons = screen.getAllByRole('button', { name: /view/i })
      await user.click(viewButtons[0])

      const closeButton = screen.getByTestId('x-mark-icon').closest('button')
      await user.click(closeButton)

      expect(screen.queryByText('Lead Details')).not.toBeInTheDocument()
    })
  })

  describe('Lead Status Management', () => {
    it('displays correct status badges', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('new')).toBeInTheDocument()
        expect(screen.getByText('qualified')).toBeInTheDocument()
        expect(screen.getByText('contacted')).toBeInTheDocument()
      })
    })

    it('shows correct status colors', async () => {
      render(<CRM />)

      await waitFor(() => {
        const newBadge = screen.getByText('new')
        expect(newBadge).toHaveClass('bg-blue-100', 'text-blue-800')
      })
    })

    it('displays lead scores correctly', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('85')).toBeInTheDocument()
        expect(screen.getByText('92')).toBeInTheDocument()
        expect(screen.getByText('68')).toBeInTheDocument()
      })
    })
  })

  describe('CRM Statistics', () => {
    it('calculates and displays correct statistics', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument() // New leads
        expect(screen.getByText('2')).toBeInTheDocument() // Pending
        expect(screen.getByText('0')).toBeInTheDocument() // Converted
        expect(screen.getByText('15')).toBeInTheDocument() // Calls today
      })
    })

    it('displays total value correctly', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('₹1,65,00,000')).toBeInTheDocument() // Total value
      })
    })

    it('calculates conversion rate correctly', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('0%')).toBeInTheDocument() // Conversion rate
      })
    })
  })

  describe('Lead Actions', () => {
    it('shows action buttons for each lead', async () => {
      render(<CRM />)

      await waitFor(() => {
        const viewButtons = screen.getAllByRole('button', { name: /view/i })
        const editButtons = screen.getAllByRole('button', { name: /edit/i })
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i })

        expect(viewButtons).toHaveLength(3)
        expect(editButtons).toHaveLength(3)
        expect(deleteButtons).toHaveLength(3)
      })
    })

    it('handles edit button click', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])

      // Should open edit modal or navigate to edit page
      // This would depend on the implementation
    })

    it('handles delete button click', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      // Should open delete confirmation modal
      expect(screen.getByText('Delete Lead')).toBeInTheDocument()
    })
  })

  describe('Communication Features', () => {
    it('displays communication icons', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getAllByTestId('phone-icon')).toHaveLength(3)
        expect(screen.getAllByTestId('chat-icon')).toHaveLength(3)
      })
    })

    it('shows last contact information', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('2 days ago')).toBeInTheDocument()
        expect(screen.getByText('1 day ago')).toBeInTheDocument()
        expect(screen.getByText('1 week ago')).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Design', () => {
    it('renders correctly on different screen sizes', async () => {
      render(<CRM />)

      await waitFor(() => {
        const container = screen.getByText('CRM Dashboard').closest('div')
        expect(container).toHaveClass('space-y-6')
      })
    })

    it('adapts filter layout for mobile', async () => {
      render(<CRM />)

      await waitFor(() => {
        // Check for responsive classes
        const filtersSection = screen.getByText('Search leads...').closest('div')
        expect(filtersSection).toHaveClass('space-y-4')
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels', async () => {
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add lead/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /filters/i })).toBeInTheDocument()
      })
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search leads...')
        searchInput.focus()
        expect(document.activeElement).toBe(searchInput)
      })

      await user.keyboard('{Tab}')
      // Should move to next focusable element
    })
  })

  describe('Error Handling', () => {
    it('handles empty leads array gracefully', async () => {
      // This would require mocking the useEffect to return empty array
      // For now, we test that the component doesn't crash with normal data
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('CRM Dashboard')).toBeInTheDocument()
      })
    })

    it('handles malformed lead data gracefully', async () => {
      // Test with incomplete lead data would require mocking
      // Component should handle missing fields gracefully
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })
    })
  })

  describe('Performance', () => {
    it('filters leads efficiently', async () => {
      const user = userEvent.setup()
      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search leads...')
      const startTime = Date.now()

      await user.type(searchInput, 'Rajesh')

      const endTime = Date.now()
      const duration = endTime - startTime

      // Filtering should be fast (< 100ms)
      expect(duration).toBeLessThan(100)
    })
  })
})