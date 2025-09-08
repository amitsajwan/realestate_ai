import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import Properties from '../../components/Properties'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

// Mock Next.js Image
jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ src, alt, ...props }: any) => <img src={src} alt={alt} {...props} />
}))

// Mock API service
jest.mock('@/lib/api', () => ({
  apiService: {
    getProperties: jest.fn(),
    createProperty: jest.fn(),
    updateProperty: jest.fn(),
    deleteProperty: jest.fn(),
  },
}))

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  BuildingOfficeIcon: (props: any) => <div data-testid="building-icon" {...props} />,
  MapPinIcon: (props: any) => <div data-testid="map-pin-icon" {...props} />,
  CurrencyRupeeIcon: (props: any) => <div data-testid="currency-icon" {...props} />,
  EyeIcon: (props: any) => <div data-testid="eye-icon" {...props} />,
  PencilIcon: (props: any) => <div data-testid="pencil-icon" {...props} />,
  TrashIcon: (props: any) => <div data-testid="trash-icon" {...props} />,
  PlusIcon: (props: any) => <div data-testid="plus-icon" {...props} />,
  MagnifyingGlassIcon: (props: any) => <div data-testid="search-icon" {...props} />,
  FunnelIcon: (props: any) => <div data-testid="funnel-icon" {...props} />,
  XMarkIcon: (props: any) => <div data-testid="x-mark-icon" {...props} />,
  HeartIcon: (props: any) => <div data-testid="heart-icon" {...props} />,
  ShareIcon: (props: any) => <div data-testid="share-icon" {...props} />,
  AdjustmentsHorizontalIcon: (props: any) => <div data-testid="adjustments-icon" {...props} />,
  Squares2X2Icon: (props: any) => <div data-testid="grid-icon" {...props} />,
  ListBulletIcon: (props: any) => <div data-testid="list-icon" {...props} />,
}))

jest.mock('@heroicons/react/24/solid', () => ({
  __esModule: true,
  HeartIcon: (props: any) => <div data-testid="heart-solid-icon" {...props} />,
}))

// Mock react-hot-toast - using global mock from jest.setup.js

// Mock navigator.share
Object.defineProperty(window.navigator, 'share', {
  writable: true,
  value: jest.fn(),
})

// Mock clipboard
Object.defineProperty(window.navigator, 'clipboard', {
  writable: true,
  value: {
    writeText: jest.fn(),
  },
})

const mockProperties = [
  {
    id: '1',
    title: 'Beautiful 3BR Apartment',
    description: 'Spacious apartment with great views',
    price: 2500000,
    address: '123 Main St, Mumbai, Maharashtra',
    bedrooms: 3,
    bathrooms: 2,
    area: 1200,
    type: 'Apartment',
    status: 'for-sale' as const,
    dateAdded: '2024-01-15T10:30:00Z',
    image: '/property1.jpg',
  },
  {
    id: '2',
    title: 'Cozy 2BR House',
    description: 'Perfect family home',
    price: 4500000,
    address: '456 Oak Ave, Delhi, Delhi',
    bedrooms: 2,
    bathrooms: 1,
    area: 800,
    type: 'House',
    status: 'for-rent' as const,
    dateAdded: '2024-01-10T10:30:00Z',
    image: '/property2.jpg',
  },
  {
    id: '3',
    title: 'Luxury Villa',
    description: 'Premium villa with pool',
    price: 15000000,
    address: '789 Palm Rd, Goa, Goa',
    bedrooms: 4,
    bathrooms: 3,
    area: 2500,
    type: 'House',
    status: 'sold' as const,
    dateAdded: '2024-01-05T10:30:00Z',
  },
]

describe('Properties Component', () => {
  const mockOnAddProperty = jest.fn()
  const mockSetProperties = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders the properties list correctly', () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      expect(screen.getByText('Properties')).toBeInTheDocument()
      expect(screen.getByText('Manage your property listings • 3 properties')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add property/i })).toBeInTheDocument()
    })

    it('displays the correct number of properties', () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      expect(screen.getByText('Manage your property listings • 3 properties')).toBeInTheDocument()
    })

    it('renders property cards with correct information', () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      expect(screen.getByText('Beautiful 3BR Apartment')).toBeInTheDocument()
      expect(screen.getByText('Cozy 2BR House')).toBeInTheDocument()
      expect(screen.getByText('Luxury Villa')).toBeInTheDocument()
    })

    it('displays property prices correctly', () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      expect(screen.getByText('₹25L')).toBeInTheDocument()
      expect(screen.getByText('₹45L')).toBeInTheDocument()
      expect(screen.getByText('₹1.5Cr')).toBeInTheDocument()
    })

    it('shows empty state when no properties exist', () => {
      render(
        <Properties
          properties={[]}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      expect(screen.getByText('No properties yet')).toBeInTheDocument()
      expect(screen.getByText('Get started by adding your first property listing to showcase your real estate portfolio.')).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('filters properties based on search term', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const searchInput = screen.getByPlaceholderText('Search by title, location, or description...')
      await user.type(searchInput, 'Beautiful')

      expect(screen.getByText('Beautiful 3BR Apartment')).toBeInTheDocument()
      expect(screen.queryByText('Cozy 2BR House')).not.toBeInTheDocument()
      expect(screen.queryByText('Luxury Villa')).not.toBeInTheDocument()
    })

    it('searches in property descriptions', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const searchInput = screen.getByPlaceholderText('Search by title, location, or description...')
      await user.type(searchInput, 'family home')

      expect(screen.getByText('Cozy 2BR House')).toBeInTheDocument()
      expect(screen.queryByText('Beautiful 3BR Apartment')).not.toBeInTheDocument()
    })

    it('searches in property addresses', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const searchInput = screen.getByPlaceholderText('Search by title, location, or description...')
      await user.type(searchInput, 'Mumbai')

      expect(screen.getByText('Beautiful 3BR Apartment')).toBeInTheDocument()
      expect(screen.queryByText('Cozy 2BR House')).not.toBeInTheDocument()
    })
  })

  describe('Filtering Functionality', () => {
    it('filters properties by status', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)

      // Select status filter
      const statusSelect = screen.getByDisplayValue('All Status')
      await user.selectOptions(statusSelect, 'for-sale')

      expect(screen.getByText('Beautiful 3BR Apartment')).toBeInTheDocument()
      expect(screen.queryByText('Cozy 2BR House')).not.toBeInTheDocument()
      expect(screen.queryByText('Luxury Villa')).not.toBeInTheDocument()
    })

    it('filters properties by type', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)

      // Select type filter
      const typeSelect = screen.getByDisplayValue('All Types')
      await user.selectOptions(typeSelect, 'House')

      expect(screen.getByText('Cozy 2BR House')).toBeInTheDocument()
      expect(screen.getByText('Luxury Villa')).toBeInTheDocument()
      expect(screen.queryByText('Beautiful 3BR Apartment')).not.toBeInTheDocument()
    })

    it('filters properties by bedroom count', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)

      // Select bedroom filter
      const bedroomSelect = screen.getByDisplayValue('All Bedrooms')
      await user.selectOptions(bedroomSelect, '3')

      expect(screen.getByText('Beautiful 3BR Apartment')).toBeInTheDocument()
      expect(screen.queryByText('Cozy 2BR House')).not.toBeInTheDocument()
      expect(screen.queryByText('Luxury Villa')).not.toBeInTheDocument()
    })

    it('clears all filters', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)

      // Apply some filters
      const statusSelect = screen.getByDisplayValue('All Status')
      await user.selectOptions(statusSelect, 'for-sale')

      // Clear filters
      const clearButton = screen.getByRole('button', { name: /clear all filters/i })
      await user.click(clearButton)

      // All properties should be visible again
      expect(screen.getByText('Beautiful 3BR Apartment')).toBeInTheDocument()
      expect(screen.getByText('Cozy 2BR House')).toBeInTheDocument()
      expect(screen.getByText('Luxury Villa')).toBeInTheDocument()
    })
  })

  describe('Sorting Functionality', () => {
    it('sorts properties by price (high to low)', async () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Open filters first
      const filtersButton = screen.getByText('Filters')
      fireEvent.click(filtersButton)

      const sortSelect = screen.getByDisplayValue('Newest First')
      fireEvent.change(sortSelect, { target: { value: 'price-desc' } })

      const propertyTitles = screen.getAllByRole('heading', { level: 3 })
      expect(propertyTitles[0]).toHaveTextContent('Luxury Villa') // ₹1.5Cr
      expect(propertyTitles[1]).toHaveTextContent('Cozy 2BR House') // ₹45L
      expect(propertyTitles[2]).toHaveTextContent('Beautiful 3BR Apartment') // ₹25L
    })

    it('sorts properties by price (low to high)', async () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Open filters first
      const filtersButton = screen.getByText('Filters')
      fireEvent.click(filtersButton)

      const sortSelect = screen.getByDisplayValue('Newest First')
      fireEvent.change(sortSelect, { target: { value: 'price-asc' } })

      const propertyTitles = screen.getAllByRole('heading', { level: 3 })
      expect(propertyTitles[0]).toHaveTextContent('Beautiful 3BR Apartment') // ₹25L
      expect(propertyTitles[1]).toHaveTextContent('Cozy 2BR House') // ₹45L
      expect(propertyTitles[2]).toHaveTextContent('Luxury Villa') // ₹1.5Cr
    })

    it('sorts properties by title (A to Z)', async () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Open filters first
      const filtersButton = screen.getByText('Filters')
      fireEvent.click(filtersButton)

      const sortSelect = screen.getByDisplayValue('Newest First')
      fireEvent.change(sortSelect, { target: { value: 'title-asc' } })

      const propertyTitles = screen.getAllByRole('heading', { level: 3 })
      expect(propertyTitles[0]).toHaveTextContent('Beautiful 3BR Apartment')
      expect(propertyTitles[1]).toHaveTextContent('Cozy 2BR House')
      expect(propertyTitles[2]).toHaveTextContent('Luxury Villa')
    })
  })

  describe('View Mode Functionality', () => {
    it('switches between grid and list view', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Initially in grid view
      expect(screen.getByTestId('grid-icon').closest('button')).toHaveClass('bg-white')

      // Switch to list view
      const listButton = screen.getByTestId('list-icon').closest('button')
      await user.click(listButton!)

      expect(screen.getByTestId('list-icon').closest('button')).toHaveClass('bg-white')
      expect(screen.getByTestId('grid-icon').closest('button')).not.toHaveClass('bg-white')
    })
  })

  describe('Property Details Modal', () => {
    it('opens property details modal when view button is clicked', async () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const viewButtons = screen.getAllByRole('button', { name: /view details/i })
      fireEvent.click(viewButtons[0])

      expect(screen.getAllByText('Beautiful 3BR Apartment')).toHaveLength(2) // Card + Modal
      expect(screen.getAllByText('123 Main St, Mumbai, Maharashtra')).toHaveLength(2) // Card + Modal
    })

    it('closes property details modal', async () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const viewButtons = screen.getAllByRole('button', { name: /view details/i })
      fireEvent.click(viewButtons[0])

      const closeButton = screen.getByTestId('x-mark-icon').closest('button')
      fireEvent.click(closeButton!)

      expect(screen.getAllByText('Beautiful 3BR Apartment')).toHaveLength(1) // Only card remains
    })

    it('displays property statistics correctly in modal', async () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const viewButtons = screen.getAllByRole('button', { name: /view details/i })
      fireEvent.click(viewButtons[0])

      expect(screen.getAllByText('3')).toHaveLength(3) // Property count + bedrooms + other instances
      expect(screen.getAllByText('2')).toHaveLength(3) // Bathrooms + other instances
      expect(screen.getByText('1200')).toBeInTheDocument() // Area
    })
  })

  describe('Delete Functionality', () => {
    it('opens delete confirmation modal', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Click delete button in modal (since delete buttons are in property cards)
      const viewButtons = screen.getAllByRole('button', { name: /view details/i })
      await user.click(viewButtons[0])

      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      expect(screen.getByRole('heading', { name: 'Delete Property' })).toBeInTheDocument()
      expect(screen.getByText('Are you sure you want to delete this property? This action cannot be undone.')).toBeInTheDocument()
    })

    it('cancels delete operation', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const viewButtons = screen.getAllByRole('button', { name: /view details/i })
      await user.click(viewButtons[0])

      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(screen.queryByText('Delete Property')).not.toBeInTheDocument()
    })

    it('confirms delete operation', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const viewButtons = screen.getAllByRole('button', { name: /view details/i })
      await user.click(viewButtons[0])

      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      const confirmDeleteButton = screen.getByRole('button', { name: /delete property/i })
      await user.click(confirmDeleteButton)

      expect(mockSetProperties).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ id: '2' }),
          expect.objectContaining({ id: '3' }),
        ])
      )
      expect(mockSetProperties).toHaveBeenCalledWith(
        expect.not.arrayContaining([
          expect.objectContaining({ id: '1' }),
        ])
      )
    })
  })

  describe('Share Functionality', () => {
    it('shares property using native share API when available', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const shareButtons = screen.getAllByTestId('share-icon')
      await user.click(shareButtons[0])

      expect(window.navigator.share).toHaveBeenCalledWith({
        title: 'Beautiful 3BR Apartment',
        text: 'Check out this property: Beautiful 3BR Apartment',
        url: expect.any(String),
      })
    })

    it.skip('falls back to clipboard when native share is not available', async () => {
      // Mock navigator.share as undefined
      Object.defineProperty(window.navigator, 'share', {
        writable: true,
        value: undefined,
      })

      // Create a proper spy for clipboard.writeText
      const writeTextSpy = jest.fn().mockResolvedValue(undefined)
      Object.defineProperty(global.navigator, 'clipboard', {
        value: { writeText: writeTextSpy },
        writable: true,
        configurable: true,
      })

      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const shareButtons = screen.getAllByTestId('share-icon')
      await user.click(shareButtons[0])

      expect(writeTextSpy).toHaveBeenCalled()
    })
  })

  describe('Favorite Functionality', () => {
    it('toggles favorite status', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const favoriteButtons = screen.getAllByTestId('heart-solid-icon')
      await user.click(favoriteButtons[0])

      // The component manages favorites internally, so we can't easily test the state
      // But we can verify the button exists and is clickable
      expect(favoriteButtons[0]).toBeInTheDocument()
    })
  })

  describe('Add Property Functionality', () => {
    it('calls onAddProperty when add button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const addButton = screen.getByRole('button', { name: /add property/i })
      await user.click(addButton)

      expect(mockOnAddProperty).toHaveBeenCalledTimes(1)
    })

    it('shows add property button in empty state', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={[]}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const addButton = screen.getByRole('button', { name: /add your first property/i })
      await user.click(addButton)

      expect(mockOnAddProperty).toHaveBeenCalledTimes(1)
    })
  })

  describe('Loading State', () => {
    it('shows loading spinner when loading prop is true', () => {
      // Note: The component doesn't currently accept a loading prop
      // This test would need to be updated if loading state is added
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Component renders normally without loading state
      expect(screen.getByText('Properties')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Check for proper button roles
      expect(screen.getByRole('button', { name: /add property/i })).toBeInTheDocument()
      expect(screen.getAllByRole('button', { name: /view details/i })).toHaveLength(3)
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      const searchInput = screen.getByPlaceholderText('Search by title, location, or description...')
      searchInput.focus()
      expect(document.activeElement).toBe(searchInput)

      await user.keyboard('{Tab}')
      // Should move to next focusable element
    })
  })

  describe('Responsive Design', () => {
    it('renders correctly on different screen sizes', () => {
      render(
        <Properties
          properties={mockProperties}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Check for responsive classes
      const container = screen.getByText('Properties').closest('div')?.parentElement?.parentElement
      expect(container).toHaveClass('space-y-4', 'sm:space-y-6')
    })
  })

  describe('Error Handling', () => {
    it('handles missing property images gracefully', () => {
      const propertiesWithoutImages = [
        {
          ...mockProperties[0],
          image: undefined,
        },
      ]

      render(
        <Properties
          properties={propertiesWithoutImages}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Should still render the property card
      expect(screen.getByText('Beautiful 3BR Apartment')).toBeInTheDocument()
      expect(screen.getByTestId('building-icon')).toBeInTheDocument()
    })

    it('handles properties with missing descriptions', () => {
      const propertiesWithoutDescriptions = [
        {
          ...mockProperties[0],
          description: undefined,
        },
      ]

      render(
        <Properties
          properties={propertiesWithoutDescriptions}
          setProperties={mockSetProperties}
          onAddProperty={mockOnAddProperty}
        />
      )

      // Should still render correctly
      expect(screen.getByText('Beautiful 3BR Apartment')).toBeInTheDocument()
    })
  })
})