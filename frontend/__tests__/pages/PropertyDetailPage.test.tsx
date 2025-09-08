import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { jest } from '@jest/globals'
import PropertyDetailPage from '../../app/agent/[agentName]/properties/[propertyId]/page'

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

// Mock navigator
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn()
  }
})

Object.defineProperty(navigator, 'share', {
  value: undefined
})

const mockPropertyData = {
  id: 'prop-1',
  title: 'Beautiful 3BHK Apartment',
  description: 'A stunning 3-bedroom apartment with modern amenities and great location.',
  price: 5000000,
  property_type: 'Apartment',
  bedrooms: 3,
  bathrooms: 2,
  area: 1200,
  location: 'Mumbai, Maharashtra',
  images: [
    'https://example.com/prop1-1.jpg',
    'https://example.com/prop1-2.jpg',
    'https://example.com/prop1-3.jpg'
  ],
  features: ['Swimming Pool', 'Gym', 'Parking', 'Security'],
  created_at: '2024-01-15T10:00:00Z',
  view_count: 150,
  inquiry_count: 25
}

const mockAgentData = {
  id: 'agent-1',
  agent_name: 'John Doe',
  slug: 'john-doe',
  photo: 'https://example.com/agent.jpg',
  phone: '+1234567890',
  email: 'john@example.com',
  office_address: '123 Main St, City, State'
}

describe('PropertyDetailPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders loading state initially', () => {
    ;(fetch as jest.Mock).mockImplementation(() => new Promise(() => {}))
    
    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)
    
    expect(screen.getByText('Loading property details...')).toBeInTheDocument()
  })

  it('renders property details successfully', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful 3BHK Apartment')).toBeInTheDocument()
    })

    // Check property details
    expect(screen.getByText('A stunning 3-bedroom apartment with modern amenities and great location.')).toBeInTheDocument()
    expect(screen.getByText('₹50L')).toBeInTheDocument()
    expect(screen.getByText('Mumbai, Maharashtra')).toBeInTheDocument()
    expect(screen.getByText('Apartment')).toBeInTheDocument()
  })

  it('displays property statistics correctly', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful 3BHK Apartment')).toBeInTheDocument()
    })

    // Check property stats
    expect(screen.getByText('3')).toBeInTheDocument() // bedrooms
    expect(screen.getByText('2')).toBeInTheDocument() // bathrooms
    expect(screen.getByText('1200')).toBeInTheDocument() // area
    expect(screen.getByText('150')).toBeInTheDocument() // views
  })

  it('displays property features correctly', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Features')).toBeInTheDocument()
    })

    // Check features
    expect(screen.getByText('Swimming Pool')).toBeInTheDocument()
    expect(screen.getByText('Gym')).toBeInTheDocument()
    expect(screen.getByText('Parking')).toBeInTheDocument()
    expect(screen.getByText('Security')).toBeInTheDocument()
  })

  it('displays agent contact information', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Contact Agent')).toBeInTheDocument()
    })

    // Check agent info
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('Real Estate Agent')).toBeInTheDocument()
    expect(screen.getByText('+1234567890')).toBeInTheDocument()
    expect(screen.getByText('john@example.com')).toBeInTheDocument()
    expect(screen.getByText('123 Main St, City, State')).toBeInTheDocument()
  })

  it('handles property not found error', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404
    })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'nonexistent' }} />)

    await waitFor(() => {
      expect(screen.getByText('Property Not Found')).toBeInTheDocument()
    })

    expect(screen.getByText("The property you're looking for doesn't exist or is not public.")).toBeInTheDocument()
    expect(screen.getByText('View All Properties')).toBeInTheDocument()
    expect(screen.getByText('Agent Profile')).toBeInTheDocument()
  })

  it('handles image gallery navigation', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful 3BHK Apartment')).toBeInTheDocument()
    })

    // Check that main image is displayed
    const mainImage = screen.getByAltText('Beautiful 3BHK Apartment')
    expect(mainImage).toBeInTheDocument()
    expect(mainImage).toHaveAttribute('src', 'https://example.com/prop1-1.jpg')

    // Check thumbnail images
    expect(screen.getByAltText('Beautiful 3BHK Apartment 1')).toBeInTheDocument()
    expect(screen.getByAltText('Beautiful 3BHK Apartment 2')).toBeInTheDocument()
    expect(screen.getByAltText('Beautiful 3BHK Apartment 3')).toBeInTheDocument()
  })

  it('handles share functionality', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Share')).toBeInTheDocument()
    })

    const shareButton = screen.getByText('Share')
    fireEvent.click(shareButton)

    // Should call clipboard.writeText since navigator.share is undefined
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(window.location.href)
  })

  it('handles favorite functionality', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Favorite')).toBeInTheDocument()
    })

    const favoriteButton = screen.getByText('Favorite')
    fireEvent.click(favoriteButton)

    // Should show favorited state
    await waitFor(() => {
      expect(screen.getByText('Favorited')).toBeInTheDocument()
    })
  })

  it('shows and hides contact form', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Send Message')).toBeInTheDocument()
    })

    // Click send message button
    const sendMessageButton = screen.getByText('Send Message')
    fireEvent.click(sendMessageButton)

    // Contact form should appear
    await waitFor(() => {
      expect(screen.getByText('Send Inquiry')).toBeInTheDocument()
    })

    // Click cancel button
    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)

    // Contact form should disappear
    await waitFor(() => {
      expect(screen.queryByText('Send Inquiry')).not.toBeInTheDocument()
    })
  })

  it('submits contact form successfully', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 'inquiry-1', success: true })
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Send Message')).toBeInTheDocument()
    })

    // Open contact form
    const sendMessageButton = screen.getByText('Send Message')
    fireEvent.click(sendMessageButton)

    await waitFor(() => {
      expect(screen.getByText('Send Inquiry')).toBeInTheDocument()
    })

    // Fill form
    fireEvent.change(screen.getByLabelText('Name *'), { target: { value: 'John Smith' } })
    fireEvent.change(screen.getByLabelText('Email *'), { target: { value: 'john@example.com' } })
    fireEvent.change(screen.getByLabelText('Phone'), { target: { value: '+1234567890' } })
    fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'I am interested in this property' } })

    // Submit form
    const submitButton = screen.getByText('Send Message')
    fireEvent.click(submitButton)

    // Should call the contact API
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/agent-public/john-doe/contact',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: 'John Smith',
            email: 'john@example.com',
            phone: '+1234567890',
            message: 'I am interested in this property',
            property_id: 'prop-1',
            inquiry_type: 'property_inquiry'
          })
        })
      )
    })
  })

  it('handles contact form submission error', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Send Message')).toBeInTheDocument()
    })

    // Open contact form
    const sendMessageButton = screen.getByText('Send Message')
    fireEvent.click(sendMessageButton)

    await waitFor(() => {
      expect(screen.getByText('Send Inquiry')).toBeInTheDocument()
    })

    // Fill and submit form
    fireEvent.change(screen.getByLabelText('Name *'), { target: { value: 'John Smith' } })
    fireEvent.change(screen.getByLabelText('Email *'), { target: { value: 'john@example.com' } })
    fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'I am interested' } })

    const submitButton = screen.getByText('Send Message')
    fireEvent.click(submitButton)

    // Should show error state
    await waitFor(() => {
      expect(screen.getByText('Sending...')).toBeInTheDocument()
    })
  })

  it('handles missing property images gracefully', async () => {
    const propertyWithoutImages = { ...mockPropertyData, images: [] }
    
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => propertyWithoutImages
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful 3BHK Apartment')).toBeInTheDocument()
    })

    // Should show placeholder instead of images
    expect(screen.queryByAltText('Beautiful 3BHK Apartment')).not.toBeInTheDocument()
  })

  it('displays property information correctly', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Property Information')).toBeInTheDocument()
    })

    // Check property information
    expect(screen.getByText('Listed')).toBeInTheDocument()
    expect(screen.getByText('Views')).toBeInTheDocument()
    expect(screen.getByText('Inquiries')).toBeInTheDocument()
    expect(screen.getByText('Type')).toBeInTheDocument()
  })

  it('handles missing agent data gracefully', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPropertyData
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404
      })

    render(<PropertyDetailPage params={{ agentName: 'john-doe', propertyId: 'prop-1' }} />)

    await waitFor(() => {
      expect(screen.getByText('Beautiful 3BHK Apartment')).toBeInTheDocument()
    })

    // Should not show agent contact card
    expect(screen.queryByText('Contact Agent')).not.toBeInTheDocument()
  })
})