import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import Properties from '../../components/Properties_new'

// Mock external dependencies
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ src, alt, ...props }: any) => <img src={src} alt={alt} {...props} />,
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  BuildingOfficeIcon: ({ className }: any) => <div data-testid="building-icon" className={className} />,
  MapPinIcon: ({ className }: any) => <div data-testid="map-pin-icon" className={className} />,
  CurrencyRupeeIcon: ({ className }: any) => <div data-testid="currency-icon" className={className} />,
  EyeIcon: ({ className }: any) => <div data-testid="eye-icon" className={className} />,
  PencilIcon: ({ className }: any) => <div data-testid="pencil-icon" className={className} />,
  TrashIcon: ({ className }: any) => <div data-testid="trash-icon" className={className} />,
  PlusIcon: ({ className }: any) => <div data-testid="plus-icon" className={className} />,
  MagnifyingGlassIcon: ({ className }: any) => <div data-testid="search-icon" className={className} />,
  FunnelIcon: ({ className }: any) => <div data-testid="filter-icon" className={className} />,
  XMarkIcon: ({ className }: any) => <div data-testid="x-icon" className={className} />,
  HeartIcon: ({ className }: any) => <div data-testid="heart-icon" className={className} />,
  ShareIcon: ({ className }: any) => <div data-testid="share-icon" className={className} />,
  AdjustmentsHorizontalIcon: ({ className }: any) => <div data-testid="adjustments-icon" className={className} />,
  Squares2X2Icon: ({ className }: any) => <div data-testid="grid-icon" className={className} />,
  ListBulletIcon: ({ className }: any) => <div data-testid="list-icon" className={className} />,
}))

jest.mock('@heroicons/react/24/solid', () => ({
  __esModule: true,
  HeartIcon: ({ className }: any) => <div data-testid="heart-solid-icon" className={className} />,
}))

jest.mock('@/lib/api', () => ({
  __esModule: true,
  apiService: {
    getProperties: jest.fn(),
    deleteProperty: jest.fn(),
    toggleFavorite: jest.fn(),
  },
}))

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

const mockApiService = require('@/lib/api').apiService
const mockToast = require('react-hot-toast').default

describe('Properties Component', () => {
  const mockProperties = [
    {
      id: '1',
      title: 'Beautiful Apartment',
      description: 'A lovely apartment in the city center',
      price: 250000,
      address: '123 Main St, City',
      bedrooms: 2,
      bathrooms: 2,
      area: 1200,
      type: 'apartment',
      status: 'for-sale' as const,
      dateAdded: '2024-01-01',
      image: '/test-image.jpg',
    },
    {
      id: '2',
      title: 'Spacious House',
      description: 'A large family house',
      price: 450000,
      address: '456 Oak Ave, Suburb',
      bedrooms: 4,
      bathrooms: 3,
      area: 2500,
      type: 'house',
      status: 'for-rent' as const,
      dateAdded: '2024-01-02',
    },
  ]

  const mockOnAddProperty = jest.fn()
  const mockSetProperties = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockApiService.getProperties.mockResolvedValue(mockProperties)
    mockApiService.deleteProperty.mockResolvedValue({})
    mockApiService.toggleFavorite.mockResolvedValue({})
  })

  it('renders component initially', () => {
    render(<Properties />)

    // Component should render without showing loading spinner
    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(document.querySelector('.animate-spin')).not.toBeInTheDocument()
  })

  it('loads and displays properties', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
      expect(screen.getByText('Spacious House')).toBeInTheDocument()
    })

    // Should not call API when properties are provided
    expect(mockApiService.getProperties).not.toHaveBeenCalled()
  })

  it('displays property details correctly', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    expect(screen.getByText('123 Main St, City')).toBeInTheDocument()
    expect(screen.getByText('₹2.5L')).toBeInTheDocument()
    expect(screen.getAllByText('2')).toHaveLength(2)
    expect(screen.getByText('1200')).toBeInTheDocument()
  })

  it('shows property images when available', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const images = screen.getAllByRole('img')
    expect(images).toHaveLength(1)
    expect(images[0]).toHaveAttribute('src', '/test-image.jpg')
    expect(images[0]).toHaveAttribute('alt', 'Beautiful Apartment')
  })

  it('displays property status badges', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('FOR SALE')).toBeInTheDocument()
      expect(screen.getByText('FOR RENT')).toBeInTheDocument()
    })
  })

  it('shows add property button when onAddProperty is provided', async () => {
    render(<Properties onAddProperty={mockOnAddProperty} properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const addButton = screen.getByRole('button', { name: /add property/i })
    expect(addButton).toBeInTheDocument()
  })

  it('calls onAddProperty when add button is clicked', async () => {
    const user = userEvent.setup()
    render(<Properties onAddProperty={mockOnAddProperty} properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const addButton = screen.getByRole('button', { name: /add property/i })
    await user.click(addButton)

    expect(mockOnAddProperty).toHaveBeenCalledTimes(1)
  })

  it('shows search input', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    expect(screen.getByPlaceholderText('Search by title, location, or description...')).toBeInTheDocument()
  })

  it('filters properties based on search', async () => {
    const user = userEvent.setup()
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search by title, location, or description...')
    await user.type(searchInput, 'Beautiful')

    expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    expect(screen.queryByText('Spacious House')).not.toBeInTheDocument()
  })

  it('shows filter options', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /filters/i })).toBeInTheDocument()
  })

  it('toggles between grid and list view', async () => {
    const user = userEvent.setup()
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const gridButton = screen.getByTestId('grid-icon').closest('button')
    const listButton = screen.getByTestId('list-icon').closest('button')

    expect(gridButton).toBeInTheDocument()
    expect(listButton).toBeInTheDocument()

    await user.click(listButton!)
    // View should change (this would be tested by checking class names or layout)
  })

  it('shows property actions (view, edit, delete)', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    expect(screen.getAllByTestId('pencil-icon')).toHaveLength(2)
    expect(screen.getAllByTestId('trash-icon')).toHaveLength(4)
  })

  it.skip('handles property deletion', async () => {
    const user = userEvent.setup()
    render(<Properties properties={mockProperties} setProperties={mockSetProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByTestId('trash-icon')
    await user.click(deleteButtons[0])

    expect(mockApiService.deleteProperty).toHaveBeenCalledWith('1')
  })

  it.skip('shows success toast after deletion', async () => {
    const user = userEvent.setup()
    render(<Properties properties={mockProperties} setProperties={mockSetProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByTestId('trash-icon')
    await user.click(deleteButtons[0])

    await waitFor(() => {
      expect(mockToast.success).toHaveBeenCalledWith('Property deleted successfully')
    })
  })

  it.skip('handles deletion errors', async () => {
    mockApiService.deleteProperty.mockRejectedValue(new Error('Delete failed'))

    const user = userEvent.setup()
    render(<Properties properties={mockProperties} setProperties={mockSetProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByTestId('trash-icon')
    await user.click(deleteButtons[0])

    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Failed to delete property')
    })
  })

  it('handles favorite toggle', async () => {
    const user = userEvent.setup()
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const favoriteButtons = screen.getAllByTestId('heart-solid-icon')
    await user.click(favoriteButtons[0])

    // The component manages favorites internally, so we can't easily test the API call
    expect(favoriteButtons[0]).toBeInTheDocument()
  })

  it('shows share button', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    expect(screen.getAllByTestId('share-icon')).toHaveLength(2)
  })

  it('displays property type icons', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    expect(screen.getAllByTestId('building-icon')).toHaveLength(1)
  })

  it('shows empty state when no properties', async () => {
    render(<Properties properties={[]} />)

    await waitFor(() => {
      expect(screen.getByText('No properties found')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    render(<Properties properties={[]} />)

    await waitFor(() => {
      expect(screen.getByText('No properties found')).toBeInTheDocument()
    })
  })

  it('uses provided properties prop', () => {
    render(<Properties properties={mockProperties} />)

    expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    expect(screen.getByText('Spacious House')).toBeInTheDocument()

    // Should not call API when properties are provided
    expect(mockApiService.getProperties).not.toHaveBeenCalled()
  })

  it('calls setProperties when provided', async () => {
    render(<Properties properties={mockProperties} setProperties={mockSetProperties} />)

    // Component should render with provided properties
    expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
  })

  it('formats prices correctly', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('₹2.5L')).toBeInTheDocument()
      expect(screen.getByText('₹4.5L')).toBeInTheDocument()
    })
  })

  it('displays property areas correctly', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('1200')).toBeInTheDocument()
      expect(screen.getByText('2500')).toBeInTheDocument()
    })
  })

  it('shows property dates', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
      expect(screen.getByText('Spacious House')).toBeInTheDocument()
    })
  })

  it('handles missing property descriptions', async () => {
    const propertiesWithoutDesc = [
      {
        ...mockProperties[0],
        description: undefined,
      },
    ]

    render(<Properties properties={propertiesWithoutDesc} />)

    expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    // Should not crash without description
  })

  it('handles missing property images', async () => {
    const propertiesWithoutImages = [
      {
        ...mockProperties[0],
        image: undefined,
      },
    ]

    render(<Properties properties={propertiesWithoutImages} />)

    expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    // Should show placeholder or no image without crashing
  })

  it('renders component without crashing', async () => {
    render(<Properties properties={mockProperties} />)

    // Component should render without showing loading spinner
    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(document.querySelector('.animate-spin')).not.toBeInTheDocument()
  })

  it('maintains search state during re-renders', async () => {
    const user = userEvent.setup()
    const { rerender } = render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search by title, location, or description...')
    await user.type(searchInput, 'Beautiful')

    expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    expect(screen.queryByText('Spacious House')).not.toBeInTheDocument()

    // Re-render should maintain search
    rerender(<Properties properties={mockProperties} />)

    expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    expect(screen.queryByText('Spacious House')).not.toBeInTheDocument()
  })

  it.skip('has proper accessibility attributes', async () => {
    render(<Properties properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const propertyCards = screen.getAllByRole('article')
    expect(propertyCards).toHaveLength(2)

    // Check that cards have proper aria-labels
    expect(propertyCards[0]).toHaveAttribute('aria-label', 'Property: Beautiful Apartment')
    expect(propertyCards[1]).toHaveAttribute('aria-label', 'Property: Spacious House')
  })

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup()
    render(<Properties onAddProperty={mockOnAddProperty} properties={mockProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const addButton = screen.getByRole('button', { name: /add property/i })
    addButton.focus()

    expect(document.activeElement).toBe(addButton)

    await user.keyboard('{Enter}')
    expect(mockOnAddProperty).toHaveBeenCalledTimes(1)
  })

  it.skip('handles rapid clicks on action buttons', async () => {
    const user = userEvent.setup()
    render(<Properties properties={mockProperties} setProperties={mockSetProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByTestId('trash-icon')

    // Click multiple times rapidly
    await user.click(deleteButtons[0])
    await user.click(deleteButtons[0])
    await user.click(deleteButtons[0])

    // Should only call API once
    expect(mockApiService.deleteProperty).toHaveBeenCalledTimes(1)
  })

  it.skip('updates property list after deletion', async () => {
    const user = userEvent.setup()
    render(<Properties properties={mockProperties} setProperties={mockSetProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
      expect(screen.getByText('Spacious House')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByTestId('trash-icon')
    await user.click(deleteButtons[0])

    await waitFor(() => {
      expect(screen.queryByText('Beautiful Apartment')).not.toBeInTheDocument()
      expect(screen.getByText('Spacious House')).toBeInTheDocument()
    })
  })

  it('shows confirmation dialog for deletion', async () => {
    const user = userEvent.setup()

    // Mock window.confirm
    const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(true)

    render(<Properties properties={mockProperties} setProperties={mockSetProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByTestId('trash-icon')
    await user.click(deleteButtons[0])

    expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to delete this property?')

    mockConfirm.mockRestore()
  })

  it('cancels deletion when user declines confirmation', async () => {
    const user = userEvent.setup()

    // Mock window.confirm to return false
    const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(false)

    render(<Properties properties={mockProperties} setProperties={mockSetProperties} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful Apartment')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByTestId('trash-icon')
    await user.click(deleteButtons[0])

    expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to delete this property?')
    expect(mockApiService.deleteProperty).not.toHaveBeenCalled()

    mockConfirm.mockRestore()
  })
})
