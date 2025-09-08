import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { jest } from '@jest/globals'
import AgentContactPage from '../../app/agent/[agentName]/contact/page'

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
  languages: ['English', 'Spanish']
}

describe('AgentContactPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders loading state initially', () => {
    ;(fetch as jest.Mock).mockImplementation(() => new Promise(() => {}))
    
    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)
    
    expect(screen.getByText('Loading agent profile...')).toBeInTheDocument()
  })

  it('renders contact form successfully', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgentData
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Get in Touch')).toBeInTheDocument()
    })

    expect(screen.getByText('Send a message to John Doe and they\'ll get back to you as soon as possible.')).toBeInTheDocument()
    expect(screen.getByLabelText('Full Name *')).toBeInTheDocument()
    expect(screen.getByLabelText('Email Address *')).toBeInTheDocument()
    expect(screen.getByLabelText('Phone Number')).toBeInTheDocument()
    expect(screen.getByLabelText('Inquiry Type')).toBeInTheDocument()
    expect(screen.getByLabelText('Message *')).toBeInTheDocument()
  })

  it('displays agent information correctly', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgentData
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Contact Information')).toBeInTheDocument()
    })

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('Real Estate Agent')).toBeInTheDocument()
    expect(screen.getByText('+1234567890')).toBeInTheDocument()
    expect(screen.getByText('john@example.com')).toBeInTheDocument()
    expect(screen.getByText('123 Main St, City, State')).toBeInTheDocument()
    expect(screen.getByText('Experienced real estate agent with 10+ years in the market.')).toBeInTheDocument()
  })

  it('displays agent specialties', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgentData
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Specialties')).toBeInTheDocument()
    })

    expect(screen.getByText('Residential')).toBeInTheDocument()
    expect(screen.getByText('Commercial')).toBeInTheDocument()
  })

  it('handles form input changes', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgentData
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Full Name *')).toBeInTheDocument()
    })

    const nameInput = screen.getByLabelText('Full Name *')
    const emailInput = screen.getByLabelText('Email Address *')
    const messageInput = screen.getByLabelText('Message *')

    fireEvent.change(nameInput, { target: { value: 'Jane Smith' } })
    fireEvent.change(emailInput, { target: { value: 'jane@example.com' } })
    fireEvent.change(messageInput, { target: { value: 'I am interested in properties' } })

    expect(nameInput).toHaveValue('Jane Smith')
    expect(emailInput).toHaveValue('jane@example.com')
    expect(messageInput).toHaveValue('I am interested in properties')
  })

  it('submits form successfully', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 'inquiry-1', success: true })
      })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Get in Touch')).toBeInTheDocument()
    })

    // Fill form
    fireEvent.change(screen.getByLabelText('Full Name *'), { target: { value: 'Jane Smith' } })
    fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'jane@example.com' } })
    fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'I am interested in properties' } })

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
            name: 'Jane Smith',
            email: 'jane@example.com',
            phone: '',
            message: 'I am interested in properties',
            inquiry_type: 'general'
          })
        })
      )
    })
  })

  it('shows success message after form submission', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 'inquiry-1', success: true })
      })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Get in Touch')).toBeInTheDocument()
    })

    // Fill and submit form
    fireEvent.change(screen.getByLabelText('Full Name *'), { target: { value: 'Jane Smith' } })
    fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'jane@example.com' } })
    fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'I am interested' } })

    const submitButton = screen.getByText('Send Message')
    fireEvent.click(submitButton)

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText('Message Sent Successfully!')).toBeInTheDocument()
    })

    expect(screen.getByText('Thank you for your message. John Doe will get back to you as soon as possible.')).toBeInTheDocument()
    expect(screen.getByText('Back to Agent Profile')).toBeInTheDocument()
    expect(screen.getByText('View Properties')).toBeInTheDocument()
  })

  it('handles form submission error', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgentData
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500
      })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Get in Touch')).toBeInTheDocument()
    })

    // Fill and submit form
    fireEvent.change(screen.getByLabelText('Full Name *'), { target: { value: 'Jane Smith' } })
    fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'jane@example.com' } })
    fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'I am interested' } })

    const submitButton = screen.getByText('Send Message')
    fireEvent.click(submitButton)

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText('Sending...')).toBeInTheDocument()
    })
  })

  it('handles agent not found error', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404
    })

    render(<AgentContactPage params={{ agentName: 'nonexistent-agent' }} />)

    await waitFor(() => {
      expect(screen.getByText('Agent Not Found')).toBeInTheDocument()
    })

    expect(screen.getByText('Agent not found')).toBeInTheDocument()
    expect(screen.getByText('Back to Home')).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgentData
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Get in Touch')).toBeInTheDocument()
    })

    const submitButton = screen.getByText('Send Message')
    fireEvent.click(submitButton)

    // Form should not submit without required fields
    expect(fetch).toHaveBeenCalledTimes(1) // Only the initial agent fetch
  })

  it('handles inquiry type selection', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgentData
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Inquiry Type')).toBeInTheDocument()
    })

    const inquirySelect = screen.getByLabelText('Inquiry Type')
    fireEvent.change(inquirySelect, { target: { value: 'property_inquiry' } })

    expect(inquirySelect).toHaveValue('property_inquiry')
  })

  it('displays contact links correctly', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgentData
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

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

  it('handles missing agent photo gracefully', async () => {
    const agentWithoutPhoto = { ...mockAgentData, photo: null }
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => agentWithoutPhoto
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Should render default placeholder instead of photo
    expect(screen.getByText('AG')).toBeInTheDocument()
  })

  it('displays navigation links correctly', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgentData
    })

    render(<AgentContactPage params={{ agentName: 'john-doe' }} />)

    await waitFor(() => {
      expect(screen.getByText('Agent Profile')).toBeInTheDocument()
    })

    const agentProfileLink = screen.getByText('Agent Profile')
    expect(agentProfileLink.closest('a')).toHaveAttribute('href', '/agent/john-doe')

    const propertiesLink = screen.getByText('Properties')
    expect(propertiesLink.closest('a')).toHaveAttribute('href', '/agent/john-doe/properties')
  })
})