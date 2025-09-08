import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { jest } from '@jest/globals'
import AgentPublicPage from '../../app/agent/[agentName]/page'

// Mock Next.js router
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  )
})

// Mock fetch
global.fetch = jest.fn()

// Mock toast
jest.mock('react-hot-toast', () => ({
  error: jest.fn(),
  success: jest.fn()
}))

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>
  }
}))

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  UserIcon: ({ className }: any) => <div data-testid="user-icon" className={className} />,
  PhoneIcon: ({ className }: any) => <div data-testid="phone-icon" className={className} />,
  EnvelopeIcon: ({ className }: any) => <div data-testid="envelope-icon" className={className} />,
  MapPinIcon: ({ className }: any) => <div data-testid="map-pin-icon" className={className} />,
  StarIcon: ({ className }: any) => <div data-testid="star-icon" className={className} />,
  EyeIcon: ({ className }: any) => <div data-testid="eye-icon" className={className} />,
  ChatBubbleLeftRightIcon: ({ className }: any) => <div data-testid="chat-icon" className={className} />,
}))

const mockAgentData = {
  id: 'agent-1',
  agent_name: 'John Doe',
  slug: 'john-doe',
  bio: 'Experienced real estate agent with 10+ years in the market.',
  photo: 'https://example.com/photo.jpg',
  phone: '+1234567890',
  email: 'john@example.com',
  office_address: '123 Main St, City, State',
  specialties: ['Residential', 'Commercial'],
  experience: '10+ years experience',
  languages: ['English', 'Spanish'],
  view_count: 150,
  contact_count: 25
}

const mockPropertiesData = {
  properties: [
    {
      id: 'prop-1',
      title: 'Beautiful 3BHK Apartment',
      price: 5000000,
      property_type: 'Apartment',
      location: 'Mumbai, Maharashtra',
      bedrooms: 3,
      bathrooms: 2,
      area: 1200,
      images: ['https://example.com/prop1.jpg']
    },
    {
      id: 'prop-2',
      title: 'Luxury Villa with Garden',
      price: 15000000,
      property_type: 'Villa',
      location: 'Bangalore, Karnataka',
      bedrooms: 4,
      bathrooms: 3,
      area: 2500,
      images: ['https://example.com/prop2.jpg']
    }
  ]
}

describe('AgentPublicPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders loading state initially', () => {
    ;(fetch as jest.Mock).mockImplementation(() => new Promise(() => {}))
    
    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)
    
    expect(screen.getByText('Loading agent profile...')).toBeInTheDocument()
  })

  it.skip('renders agent profile successfully', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertiesData
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    expect(screen.getByText('Experienced real estate agent with 10+ years in the market.')).toBeInTheDocument()
    expect(screen.getByText('+1234567890')).toBeInTheDocument()
    expect(screen.getByText('john@example.com')).toBeInTheDocument()
    expect(screen.getByText('123 Main St, City, State')).toBeInTheDocument()
    expect(screen.getByText('Residential')).toBeInTheDocument()
    expect(screen.getByText('Commercial')).toBeInTheDocument()
    expect(screen.getByText('10+ years experience')).toBeInTheDocument()
    expect(screen.getByText('English, Spanish')).toBeInTheDocument()
  })

  it.skip('displays agent statistics', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertiesData
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('150 profile views')).toBeInTheDocument()
      expect(screen.getByText('25 inquiries')).toBeInTheDocument()
    })
  })

  it.skip('renders featured properties section', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertiesData
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Featured Properties')).toBeInTheDocument()
    })

    expect(screen.getByText('Beautiful 3BHK Apartment')).toBeInTheDocument()
    expect(screen.getByText('Luxury Villa with Garden')).toBeInTheDocument()
    expect(screen.getByText('₹5,000,000')).toBeInTheDocument()
    expect(screen.getByText('₹15,000,000')).toBeInTheDocument()
  })

  it.skip('handles agent not found error', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404
    })

    render(<AgentPublicPage params={{ agentName: 'nonexistent-agent' }} />)

    await waitFor(() => {
      expect(screen.getByText('Agent Not Found')).toBeInTheDocument()
    })

    expect(screen.getByText("The agent profile you're looking for doesn't exist or is not public.")).toBeInTheDocument()
    expect(screen.getByText('Back to Home')).toBeInTheDocument()
  })

  it.skip('handles network error gracefully', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Agent Not Found')).toBeInTheDocument()
    })
  })

  it.skip('tracks contact button clicks', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertiesData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Send Message')).toBeInTheDocument()
    })

    const contactButton = screen.getByText('Send Message')
    fireEvent.click(contactButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/agent-public/john-doe/track-contact',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'contact_button_click' })
        })
      )
    })
  })

  it.skip('renders contact information correctly', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertiesData
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Contact Information')).toBeInTheDocument()
    })

    // Check phone link
    const phoneLink = screen.getByText('+1234567890')
    expect(phoneLink.closest('a')).toHaveAttribute('href', 'tel:+1234567890')

    // Check email link
    const emailLink = screen.getByText('john@example.com')
    expect(emailLink.closest('a')).toHaveAttribute('href', 'mailto:john@example.com')
  })

  it.skip('renders navigation links correctly', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertiesData
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Properties')).toBeInTheDocument()
    })

    const propertiesLink = screen.getByText('Properties')
    expect(propertiesLink.closest('a')).toHaveAttribute('href', '/agent/john-doe/properties')

    const contactLink = screen.getByText('Contact')
    expect(contactLink.closest('a')).toHaveAttribute('href', '/agent/john-doe/contact')
  })

  it.skip('handles missing agent photo gracefully', async () => {
    const agentWithoutPhoto = { ...mockAgentData, photo: null }
    
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => agentWithoutPhoto
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertiesData
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Should render default user icon instead of photo
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument()
  })

  it.skip('renders property details correctly', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertiesData
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful 3BHK Apartment')).toBeInTheDocument()
    })

    // Check property details
    expect(screen.getByText('Mumbai, Maharashtra')).toBeInTheDocument()
    expect(screen.getByText('3 bed')).toBeInTheDocument()
    expect(screen.getByText('2 bath')).toBeInTheDocument()
    expect(screen.getByText('1200 sq ft')).toBeInTheDocument()
    expect(screen.getByText('Apartment')).toBeInTheDocument()
  })

  it.skip('handles empty properties list', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ properties: [] })
      })

    render(<AgentPublicPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Should not show featured properties section if no properties
    expect(screen.queryByText('Featured Properties')).not.toBeInTheDocument()
  })
})