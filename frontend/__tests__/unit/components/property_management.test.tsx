import { render, screen, waitFor } from '@testing-library/react'
import PropertyManagement from '@/components/PropertyManagement'
import '@testing-library/jest-dom'

// Mock fetch
global.fetch = jest.fn()

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}))

const mockProperties = [
  {
    id: '1',
    title: 'Test Property',
    description: 'A test property',
    price: 500000,
    location: 'Test City',
    bedrooms: 3,
    bathrooms: 2,
    area_sqft: 2000,
    property_type: 'House',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    images: ['/test-image.jpg'],
  },
]

describe('PropertyManagement Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock successful API response
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProperties,
    })
  })

  it('should render without crashing', async () => {
    render(<PropertyManagement />)
    
    await waitFor(() => {
      expect(screen.getByText('Property Management')).toBeInTheDocument()
    })
  })
  
  it('should display properties list', async () => {
    render(<PropertyManagement />)
    
    await waitFor(() => {
      expect(screen.getByText('Test Property')).toBeInTheDocument()
      expect(screen.getByText('Test City')).toBeInTheDocument()
    })
  })

  it('should display property price correctly', async () => {
    render(<PropertyManagement />)
    
    await waitFor(() => {
      expect(screen.getByText('₹5.0L')).toBeInTheDocument() // 500000 formatted
    })
  })

  it('should display property details correctly', async () => {
    render(<PropertyManagement />)
    
    await waitFor(() => {
      expect(screen.getByText('3 bed')).toBeInTheDocument()
      expect(screen.getByText('2 bath')).toBeInTheDocument()
      expect(screen.getByText('2,000 sq ft')).toBeInTheDocument()
    })
  })

  it('should handle properties with missing data gracefully', async () => {
    const propertiesWithMissingData = [
      {
        id: '2',
        title: 'Incomplete Property',
        description: '',
        price: 0,
        location: '',
        bedrooms: null,
        bathrooms: null,
        area_sqft: null,
        property_type: '',
        status: 'active',
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        images: [],
      },
    ]

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => propertiesWithMissingData,
    })

    render(<PropertyManagement />)
    
    await waitFor(() => {
      expect(screen.getByText('Incomplete Property')).toBeInTheDocument()
      expect(screen.getByText('Contact for price')).toBeInTheDocument()
      expect(screen.getByText('N/A bed')).toBeInTheDocument()
      expect(screen.getByText('N/A bath')).toBeInTheDocument()
      expect(screen.getByText('N/A sq ft')).toBeInTheDocument()
    })
  })
  
  it('should handle user interactions', async () => {
    render(<PropertyManagement />)
    
    await waitFor(() => {
      expect(screen.getByText('Property Management')).toBeInTheDocument()
    })
    
    // Add more specific interaction tests as needed
  })
})