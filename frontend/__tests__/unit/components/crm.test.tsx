import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import CRM from '@/components/CRM'
import { type Lead } from '@/lib/crm-api'

// Mock the CRM API
jest.mock('@/lib/crm-api', () => ({
  crmApi: {
    getLeads: jest.fn(),
    getLeadStats: jest.fn(),
    searchLeads: jest.fn(),
  },
}))

const mockLeads: Lead[] = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+1234567890',
    budget: 5000000,
    property_type_preference: 'villa',
    location_preference: 'Mumbai',
    timeline: '3 months',
    urgency: 'high',
    source: 'website',
    status: 'new',
    score: 85,
    notes: 'Looking for luxury villa',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Jane Smith',
    email: 'jane@example.com',
    phone: '+0987654321',
    budget: 2500000,
    property_type_preference: 'apartment',
    location_preference: 'Delhi',
    timeline: '6 months',
    urgency: 'medium',
    source: 'referral',
    status: 'contacted',
    score: 70,
    notes: 'First-time buyer',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  }
]

const mockStats = {
  total_leads: 2,
  new_leads: 1,
  contacted_leads: 1,
  qualified_leads: 0,
  converted_leads: 0,
  lost_leads: 0,
  conversion_rate: 0,
  average_lead_score: 77.5,
  lead_source_distribution: {
    website: 1,
    referral: 1,
  },
  urgency_distribution: {
    high: 1,
    medium: 1,
  },
  budget_distribution: {
    '2.5M-5M': 1,
    '5M+': 1,
  },
  average_deal_value: 3750000,
  total_pipeline_value: 7500000,
  lead_response_time: 2.5,
  follow_up_completion_rate: 85,
  top_performing_sources: ['website'],
  recent_activities: []
}

describe('CRM Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    const { crmApi } = require('@/lib/crm-api')
    crmApi.getLeads.mockResolvedValue(mockLeads)
    crmApi.getLeadStats.mockResolvedValue(mockStats)
  })

  it('should render without crashing', async () => {
    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('CRM Dashboard')).toBeInTheDocument()
    })
  })

  it('should display lead statistics', async () => {
    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Total Leads')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('New Leads')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
    })
  })

  it('should display leads list', async () => {
    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
      expect(screen.getByText('john@example.com')).toBeInTheDocument()
      expect(screen.getByText('jane@example.com')).toBeInTheDocument()
    })
  })

  it('should filter leads by search term', async () => {
    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search leads...')
    fireEvent.change(searchInput, { target: { value: 'John' } })

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument()
    })
  })

  it('should filter leads by status', async () => {
    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const statusFilter = screen.getByDisplayValue('all')
    fireEvent.change(statusFilter, { target: { value: 'new' } })

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument()
    })
  })

  it('should open lead details modal when lead is clicked', async () => {
    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const leadCard = screen.getByText('John Doe').closest('div')
    fireEvent.click(leadCard!)

    await waitFor(() => {
      expect(screen.getByText('Lead Details')).toBeInTheDocument()
      expect(screen.getByText('john@example.com')).toBeInTheDocument()
      expect(screen.getByText('+1234567890')).toBeInTheDocument()
    })
  })

  it('should display lead details correctly in modal', async () => {
    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const leadCard = screen.getByText('John Doe').closest('div')
    fireEvent.click(leadCard!)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('john@example.com')).toBeInTheDocument()
      expect(screen.getByText('+1234567890')).toBeInTheDocument()
      expect(screen.getByText('₹50L')).toBeInTheDocument() // budget
      expect(screen.getByText('Mumbai')).toBeInTheDocument() // location_preference
      expect(screen.getByText('villa')).toBeInTheDocument() // property_type_preference
      expect(screen.getByText('3 months')).toBeInTheDocument() // timeline
    })
  })

  it('should close modal when close button is clicked', async () => {
    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const leadCard = screen.getByText('John Doe').closest('div')
    fireEvent.click(leadCard!)

    await waitFor(() => {
      expect(screen.getByText('Lead Details')).toBeInTheDocument()
    })

    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)

    await waitFor(() => {
      expect(screen.queryByText('Lead Details')).not.toBeInTheDocument()
    })
  })

  it('should handle API errors gracefully', async () => {
    const { crmApi } = require('@/lib/crm-api')
    crmApi.getLeads.mockRejectedValue(new Error('API Error'))

    await act(async () => {
      render(<CRM />)
    })
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument()
    })
  })

  it('should display loading state initially', () => {
    render(<CRM />)
    expect(screen.getByText('Loading CRM data...')).toBeInTheDocument()
  })
})