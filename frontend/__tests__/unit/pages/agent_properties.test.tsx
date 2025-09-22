import { render, screen, waitFor } from '@testing-library/react'
import { jest } from '@jest/globals'
import AgentPropertiesPage from '@/app/agent/[agentName]/properties/page'
import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => ({
    get: jest.fn(),
  }),
}))

// Mock fetch
global.fetch = jest.fn()

const mockAgent = {
  id: '1',
  agent_name: 'John Doe',
  slug: 'john-doe',
  bio: 'Experienced real estate agent',
  photo: '/agent-photo.jpg',
  phone: '+1234567890',
  email: 'john@example.com',
  office_address: '123 Main St',
  specialties: ['Residential', 'Commercial'],
  experience: '5 years',
  languages: ['English', 'Spanish'],
  view_count: 100,
  contact_count: 25,
}

const mockProperties = [
  {
    id: '1',
    title: 'Beautiful House',
    description: 'A beautiful house in the city',
    price: 500000,
    location: 'New York',
    bedrooms: 3,
    bathrooms: 2,
    area_sqft: 2000,
    property_type: 'House',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    agent_id: '1',
    images: ['/property1.jpg'],
  },
  {
    id: '2',
    title: 'Modern Apartment',
    description: 'A modern apartment with great views',
    price: 300000,
    location: 'Los Angeles',
    bedrooms: 2,
    bathrooms: 1,
    area_sqft: 1200,
    property_type: 'Apartment',
    status: 'active',
    created_at: '2024-01-02T00:00:00Z',
    agent_id: '1',
    images: ['/property2.jpg'],
  },
]

describe('Agent Properties Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock successful API responses
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgent,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          properties: mockProperties,
          total: 2,
          page: 1,
          limit: 12,
        }),
      })
  })

  it('should render agent information', async () => {
    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Real Estate Agent')).toBeInTheDocument()
    })
  })

  it('should render properties list', async () => {
    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Beautiful House')).toBeInTheDocument()
      expect(screen.getByText('Modern Apartment')).toBeInTheDocument()
    })
  })

  it('should display property prices correctly', async () => {
    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('₹5.0L')).toBeInTheDocument() // 500000 formatted
      expect(screen.getByText('₹3.0L')).toBeInTheDocument() // 300000 formatted
    })
  })

  it('should display property details correctly', async () => {
    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('3 bed')).toBeInTheDocument()
      expect(screen.getByText('2 bed')).toBeInTheDocument()
      expect(screen.getByText('2 bath')).toBeInTheDocument()
      expect(screen.getByText('1 bath')).toBeInTheDocument()
      expect(screen.getByText('2,000 sq ft')).toBeInTheDocument()
      expect(screen.getByText('1,200 sq ft')).toBeInTheDocument()
    })
  })

  it('should handle properties with missing data gracefully', async () => {
    const propertiesWithMissingData = [
      {
        id: '3',
        title: 'Incomplete Property',
        description: '',
        price: 0,
        location: '',
        bedrooms: null,
        bathrooms: null,
        area_sqft: null,
        property_type: '',
        status: 'active',
        created_at: '2024-01-03T00:00:00Z',
        agent_id: '1',
        images: [],
      },
    ]

    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgent,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          properties: propertiesWithMissingData,
          total: 1,
          page: 1,
          limit: 12,
        }),
      })

    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Incomplete Property')).toBeInTheDocument()
      expect(screen.getByText('Contact for price')).toBeInTheDocument()
      expect(screen.getByText('N/A bed')).toBeInTheDocument()
      expect(screen.getByText('N/A bath')).toBeInTheDocument()
      expect(screen.getByText('N/A sq ft')).toBeInTheDocument()
      expect(screen.getByText('Property')).toBeInTheDocument()
    })
  })

  it('should show contact agent button', async () => {
    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Contact Agent')).toBeInTheDocument()
    })
  })

  it('should not show navigation to other pages', async () => {
    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.queryByText('Properties')).not.toBeInTheDocument()
      expect(screen.queryByText('Posts')).not.toBeInTheDocument()
    })
  })

  it('should handle loading state', () => {
    ;(fetch as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    expect(screen.getByText('Loading properties...')).toBeInTheDocument()
  })

  it('should handle error state', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'))
    
    render(<AgentPropertiesPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Error loading properties')).toBeInTheDocument()
    })
  })
})
