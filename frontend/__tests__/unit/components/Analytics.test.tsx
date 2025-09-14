import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import Analytics from '@/components/Analytics'
import { type Property } from '@/lib/data-transformers'

// Mock the CRM API
jest.mock('@/lib/crm-api', () => ({
  crmApi: {
    getDashboardMetrics: jest.fn(),
  },
}))

const mockProperties: Property[] = [
  {
    id: '1',
    title: 'Test Villa',
    price: 5000000,
    address: '123 Test St',
    location: 'Mumbai',
    bedrooms: 4,
    bathrooms: 3,
    area: 2500,
    area_sqft: 2500,
    type: 'villa',
    property_type: 'villa',
    status: 'for-sale',
    dateAdded: '2024-01-01',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    title: 'Test Apartment',
    price: 2500000,
    address: '456 Test Ave',
    location: 'Delhi',
    bedrooms: 2,
    bathrooms: 2,
    area: 1200,
    area_sqft: 1200,
    type: 'apartment',
    property_type: 'apartment',
    status: 'for-rent',
    dateAdded: '2024-01-02',
    created_at: '2024-01-02T00:00:00Z',
  }
]

describe('Analytics Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render without crashing', () => {
    render(<Analytics properties={mockProperties} />)
    expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument()
  })

  it('should display property statistics', async () => {
    render(<Analytics properties={mockProperties} />)
    
    await waitFor(() => {
      expect(screen.getByText('Total Properties')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument() // total_properties
    })
  })

  it('should display property type distribution', async () => {
    render(<Analytics properties={mockProperties} />)
    
    await waitFor(() => {
      expect(screen.getByText('Property Types')).toBeInTheDocument()
      expect(screen.getByText('villa')).toBeInTheDocument()
      expect(screen.getByText('apartment')).toBeInTheDocument()
    })
  })

  it('should handle empty properties array', async () => {
    render(<Analytics properties={[]} />)
    
    await waitFor(() => {
      expect(screen.getByText('Total Properties')).toBeInTheDocument()
      expect(screen.getByText('0')).toBeInTheDocument()
    })
  })

  it('should handle undefined properties', async () => {
    render(<Analytics />)
    
    await waitFor(() => {
      expect(screen.getByText('Total Properties')).toBeInTheDocument()
      expect(screen.getByText('0')).toBeInTheDocument()
    })
  })

  it('should display loading state initially', () => {
    render(<Analytics properties={mockProperties} />)
    expect(screen.getByText('Loading analytics...')).toBeInTheDocument()
  })

  it('should display error state when API fails', async () => {
    const { crmApi } = require('@/lib/crm-api')
    crmApi.getDashboardMetrics.mockRejectedValue(new Error('API Error'))

    render(<Analytics properties={mockProperties} />)
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load analytics')).toBeInTheDocument()
    })
  })

  it('should calculate and display correct percentages', async () => {
    render(<Analytics properties={mockProperties} />)
    
    await waitFor(() => {
      // Both villa and apartment should show 50% each
      const percentageElements = screen.getAllByText('50%')
      expect(percentageElements).toHaveLength(2)
    })
  })

  it('should display average price correctly', async () => {
    render(<Analytics properties={mockProperties} />)
    
    await waitFor(() => {
      expect(screen.getByText('₹37.5L')).toBeInTheDocument() // (5000000 + 2500000) / 2
    })
  })
})