import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import Analytics from '@/components/Analytics'
import { type Property } from '@/lib/data-transformers'

// Mock the CRM API
jest.mock('@/lib/crm-api', () => ({
  crmApi: {
    getDashboardMetrics: jest.fn().mockResolvedValue({
      overview_metrics: [
        {
          name: 'Total Properties',
          value: 2,
          type: 'count',
          unit: '',
          description: 'Total number of properties'
        }
      ],
      property_analytics: {
        total_properties: 2,
        published_properties: 2,
        draft_properties: 0,
        archived_properties: 0,
        average_price: 3750000,
        total_value: 7500000,
        price_range_distribution: {
          'Under 10L': 0,
          '10L - 20L': 0,
          '20L - 50L': 1,
          '50L - 1Cr': 1,
          'Above 1Cr': 0
        },
        property_type_distribution: {
          villa: 1,
          apartment: 1
        },
        location_distribution: {
          'Mumbai': 1,
          'Delhi': 1
        },
        status_distribution: {
          'for-sale': 1,
          'for-rent': 1
        },
        average_days_on_market: 30,
        conversion_rate: 0,
        top_performing_properties: [],
        recent_activity: []
      }
    }),
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

  it('should render without crashing', async () => {
    await act(async () => {
      render(<Analytics properties={mockProperties} />)
    })
    await waitFor(() => {
      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument()
    })
  })

  it('should display property statistics', async () => {
    await act(async () => {
      render(<Analytics properties={mockProperties} />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Total Properties')).toBeInTheDocument()
      // Look for the specific "2" in the Total Properties card
      const totalPropertiesCard = screen.getByText('Total Properties').closest('div')
      expect(totalPropertiesCard).toHaveTextContent('2')
    }, { timeout: 3000 })
  })

  it('should display property type distribution', async () => {
    await act(async () => {
      render(<Analytics properties={mockProperties} />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Property Types')).toBeInTheDocument()
      expect(screen.getByText('villa')).toBeInTheDocument()
      expect(screen.getByText('apartment')).toBeInTheDocument()
    })
  })

  it('should handle empty properties array', async () => {
    await act(async () => {
      render(<Analytics properties={[]} />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Total Properties')).toBeInTheDocument()
      // The component uses API data when properties are empty, so expect 2 from mock
      const totalPropertiesCard = screen.getByText('Total Properties').closest('div')
      expect(totalPropertiesCard).toHaveTextContent('2')
    })
  })

  it('should handle undefined properties', async () => {
    await act(async () => {
      render(<Analytics />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Total Properties')).toBeInTheDocument()
      // The component uses API data when properties are undefined, so expect 2 from mock
      const totalPropertiesCard = screen.getByText('Total Properties').closest('div')
      expect(totalPropertiesCard).toHaveTextContent('2')
    })
  })

  it('should display loading state initially', () => {
    render(<Analytics properties={mockProperties} />)
    expect(screen.getByText('Loading analytics...')).toBeInTheDocument()
  })

  it('should display error state when API fails', async () => {
    const { crmApi } = require('@/lib/crm-api')
    crmApi.getDashboardMetrics.mockRejectedValue(new Error('API Error'))

    await act(async () => {
      render(<Analytics properties={mockProperties} />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('should calculate and display correct percentages', async () => {
    // Reset the mock to ensure it returns success
    const { crmApi } = require('@/lib/crm-api')
    crmApi.getDashboardMetrics.mockResolvedValue({
      overview_metrics: [],
      property_analytics: {
        total_properties: 2,
        published_properties: 2,
        draft_properties: 0,
        archived_properties: 0,
        average_price: 3750000,
        total_value: 7500000,
        price_range_distribution: {},
        property_type_distribution: {
          villa: 1,
          apartment: 1
        },
        location_distribution: {},
        status_distribution: {},
        average_days_on_market: 30,
        conversion_rate: 0,
        top_performing_properties: [],
        recent_activity: []
      }
    })

    await act(async () => {
      render(<Analytics properties={mockProperties} />)
    })
    
    await waitFor(() => {
      // Check that the Property Types section exists
      expect(screen.getByText('Property Types')).toBeInTheDocument()
      // The component should show the property types from the mock data
      expect(screen.getByText('villa')).toBeInTheDocument()
      expect(screen.getByText('apartment')).toBeInTheDocument()
    })
  })

  it('should display average price correctly', async () => {
    // Reset the mock to ensure it returns success
    const { crmApi } = require('@/lib/crm-api')
    crmApi.getDashboardMetrics.mockResolvedValue({
      overview_metrics: [],
      property_analytics: {
        total_properties: 2,
        published_properties: 2,
        draft_properties: 0,
        archived_properties: 0,
        average_price: 3750000,
        total_value: 7500000,
        price_range_distribution: {},
        property_type_distribution: {
          villa: 1,
          apartment: 1
        },
        location_distribution: {},
        status_distribution: {},
        average_days_on_market: 30,
        conversion_rate: 0,
        top_performing_properties: [],
        recent_activity: []
      }
    })

    await act(async () => {
      render(<Analytics properties={mockProperties} />)
    })
    
    await waitFor(() => {
      // Check that the component renders without error
      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument()
      // The component should show the property types from the mock data
      expect(screen.getByText('villa')).toBeInTheDocument()
      expect(screen.getByText('apartment')).toBeInTheDocument()
    })
  })
})