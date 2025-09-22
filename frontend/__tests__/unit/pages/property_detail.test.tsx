import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { jest } from '@jest/globals'
import PropertyDetailPage from '@/app/agent/[agentName]/properties/[propertyId]/page'
import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}))

// Mock fetch
global.fetch = jest.fn()

const mockProperty = {
  id: '1',
  title: 'Beautiful House in Downtown',
  description: 'A stunning house with modern amenities and great location',
  price: 750000,
  location: 'New York',
  address: '123 Main Street, New York, NY 10001',
  bedrooms: 4,
  bathrooms: 3,
  area_sqft: 2500,
  property_type: 'House',
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  year_built: 2020,
  parking_spaces: 2,
  garden_area: 500,
  balcony_area: 100,
  furnished: true,
  pet_friendly: true,
  security_features: ['CCTV', 'Alarm System'],
  nearby_amenities: ['School', 'Hospital', 'Shopping Mall'],
  property_tax: 5000,
  maintenance_fee: 200,
  hoa_fee: 150,
  utilities_included: ['Water', 'Electricity'],
  availability_date: '2024-02-01',
  listing_type: 'Sale',
  agent_id: '1',
  agent_name: 'John Doe',
  agent_phone: '+1234567890',
  agent_email: 'john@example.com',
  agent_photo: '/agent-photo.jpg',
  images: ['/property1.jpg', '/property2.jpg', '/property3.jpg'],
}

const mockAgent = {
  id: '1',
  agent_name: 'John Doe',
  slug: 'john-doe',
  photo: '/agent-photo.jpg',
  phone: '+1234567890',
  email: 'john@example.com',
  office_address: '123 Main St',
  bio: 'Experienced real estate agent with 10 years of experience',
  specialties: ['Residential', 'Commercial'],
  experience: '10 years',
  languages: ['English', 'Spanish'],
}

describe('Property Detail Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock successful API responses
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperty,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgent,
      })
  })

  it('should render property information', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Beautiful House in Downtown')).toBeInTheDocument()
      expect(screen.getByText('A stunning house with modern amenities and great location')).toBeInTheDocument()
      expect(screen.getByText('123 Main Street, New York, NY 10001')).toBeInTheDocument()
    })
  })

  it('should display property price correctly', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('₹7.5L')).toBeInTheDocument() // 750000 formatted
    })
  })

  it('should display property key features', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('4')).toBeInTheDocument() // Bedrooms
      expect(screen.getByText('3')).toBeInTheDocument() // Bathrooms
      expect(screen.getByText('2,500')).toBeInTheDocument() // Area
      expect(screen.getByText('House')).toBeInTheDocument() // Property type
    })
  })

  it('should display property images', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      const images = screen.getAllByRole('img')
      expect(images).toHaveLength(2) // Main image + agent photo
    })
  })

  it('should display agent information', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('+1234567890')).toBeInTheDocument()
      expect(screen.getByText('john@example.com')).toBeInTheDocument()
    })
  })

  it('should handle properties with missing data gracefully', async () => {
    const propertyWithMissingData = {
      ...mockProperty,
      price: 0,
      bedrooms: null,
      bathrooms: null,
      area_sqft: null,
      property_type: '',
      description: '',
    }

    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => propertyWithMissingData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgent,
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Contact for price')).toBeInTheDocument()
      expect(screen.getByText('N/A')).toBeInTheDocument() // For missing bedrooms/bathrooms
      expect(screen.getByText('Property')).toBeInTheDocument() // Default property type
      expect(screen.getByText('No description available')).toBeInTheDocument()
    })
  })

  it('should show contact agent button', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Contact Agent')).toBeInTheDocument()
    })
  })

  it('should handle favorite toggle', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      const favoriteButton = screen.getByRole('button', { name: /favorite/i })
      fireEvent.click(favoriteButton)
      // Add assertions for favorite state change
    })
  })

  it('should handle image navigation', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      const nextButton = screen.getByRole('button', { name: /next/i })
      const prevButton = screen.getByRole('button', { name: /previous/i })
      
      expect(nextButton).toBeInTheDocument()
      expect(prevButton).toBeInTheDocument()
      
      fireEvent.click(nextButton)
      fireEvent.click(prevButton)
      // Add assertions for image navigation
    })
  })

  it('should handle loading state', () => {
    ;(fetch as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    expect(screen.getByText('Loading property...')).toBeInTheDocument()
  })

  it('should handle error state', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'))
    
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument()
    })
  })

  it('should not show navigation to other pages', async () => {
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: '1' }} />)
    
    await waitFor(() => {
      expect(screen.queryByText('Properties')).not.toBeInTheDocument()
      expect(screen.queryByText('Posts')).not.toBeInTheDocument()
    })
  })
})
