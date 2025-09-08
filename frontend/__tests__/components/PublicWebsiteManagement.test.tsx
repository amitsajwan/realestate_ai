import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import PublicWebsiteManagement from '../../components/PublicWebsiteManagement'

// Mock fetch
global.fetch = jest.fn()

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

// Use JSDOM default window.location.origin

describe('PublicWebsiteManagement', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear()
  })

  test('should render loading spinner initially', () => {
    (fetch as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<PublicWebsiteManagement />)
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  test('should render public website management interface', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential', 'Commercial'],
      experience: '10+ years',
      languages: ['English', 'Spanish'],
      is_active: true,
      is_public: true,
      view_count: 100,
      contact_count: 25,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    const mockStats = {
      total_views: 100,
      total_contacts: 25,
      properties_count: 10,
      recent_inquiries: 5
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('Public Website Management')).toBeInTheDocument()
    })

    expect(screen.getByText('Manage your public agent website and profile')).toBeInTheDocument()
    expect(screen.getByText('Total Views')).toBeInTheDocument()
    expect(screen.getByText('Total Contacts')).toBeInTheDocument()
    expect(screen.getByText('Public Properties')).toBeInTheDocument()
    expect(screen.getByText('Recent Inquiries')).toBeInTheDocument()
  })

  test('should show public website status', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential'],
      experience: '10+ years',
      languages: ['English'],
      is_active: true,
      is_public: true,
      view_count: 100,
      contact_count: 25,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_views: 0, total_contacts: 0, properties_count: 0, recent_inquiries: 0 })
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('Public Website Active')).toBeInTheDocument()
    })

    expect(screen.getByText('Your public website is live and visible to visitors')).toBeInTheDocument()
  })

  test('should allow editing profile', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential'],
      experience: '10+ years',
      languages: ['English'],
      is_active: true,
      is_public: false,
      view_count: 0,
      contact_count: 0,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_views: 0, total_contacts: 0, properties_count: 0, recent_inquiries: 0 })
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('Edit Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Edit Profile'))

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument()
    })

    expect(screen.getByDisplayValue('Test bio')).toBeInTheDocument()
    expect(screen.getByDisplayValue('+1234567890')).toBeInTheDocument()
    expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument()
    expect(screen.getByDisplayValue('123 Main St')).toBeInTheDocument()
  })

  test('should show specialties checkboxes', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential'],
      experience: '10+ years',
      languages: ['English'],
      is_active: true,
      is_public: false,
      view_count: 0,
      contact_count: 0,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_views: 0, total_contacts: 0, properties_count: 0, recent_inquiries: 0 })
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('Edit Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Edit Profile'))

    await waitFor(() => {
      expect(screen.getByText('Residential')).toBeInTheDocument()
    })

    expect(screen.getByText('Commercial')).toBeInTheDocument()
    expect(screen.getByText('Luxury')).toBeInTheDocument()
    expect(screen.getByText('Investment')).toBeInTheDocument()
    expect(screen.getByText('First-time Buyers')).toBeInTheDocument()
    expect(screen.getByText('Relocation')).toBeInTheDocument()
  })

  test('should show languages checkboxes', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential'],
      experience: '10+ years',
      languages: ['English'],
      is_active: true,
      is_public: false,
      view_count: 0,
      contact_count: 0,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_views: 0, total_contacts: 0, properties_count: 0, recent_inquiries: 0 })
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('Edit Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Edit Profile'))

    await waitFor(() => {
      expect(screen.getByText('English')).toBeInTheDocument()
    })

    expect(screen.getByText('Spanish')).toBeInTheDocument()
    expect(screen.getByText('French')).toBeInTheDocument()
    expect(screen.getByText('Mandarin')).toBeInTheDocument()
    expect(screen.getByText('Hindi')).toBeInTheDocument()
    expect(screen.getByText('Arabic')).toBeInTheDocument()
  })

  test('should show quick actions', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential'],
      experience: '10+ years',
      languages: ['English'],
      is_active: true,
      is_public: false,
      view_count: 0,
      contact_count: 0,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_views: 0, total_contacts: 0, properties_count: 0, recent_inquiries: 0 })
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    })

    expect(screen.getByText('Manage Properties')).toBeInTheDocument()
    expect(screen.getByText('View Inquiries')).toBeInTheDocument()
  })

  test('should show public status toggle', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential'],
      experience: '10+ years',
      languages: ['English'],
      is_active: true,
      is_public: false,
      view_count: 0,
      contact_count: 0,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_views: 0, total_contacts: 0, properties_count: 0, recent_inquiries: 0 })
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('Edit Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Edit Profile'))

    await waitFor(() => {
      expect(screen.getByText('Public Website Status')).toBeInTheDocument()
    })

    expect(screen.getByText('Make your website visible to the public')).toBeInTheDocument()
  })

  test('should handle profile save', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential'],
      experience: '10+ years',
      languages: ['English'],
      is_active: true,
      is_public: false,
      view_count: 0,
      contact_count: 0,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_views: 0, total_contacts: 0, properties_count: 0, recent_inquiries: 0 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockProfile, agent_name: 'Updated Name' })
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('Edit Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Edit Profile'))

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument()
    })

    const nameInput = screen.getByDisplayValue('John Doe')
    fireEvent.change(nameInput, { target: { value: 'Updated Name' } })

    fireEvent.click(screen.getByText('Save Changes'))

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/v1/agent-public/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: expect.stringContaining('Updated Name')
      })
    })
  })

  test('should show view public site button when profile is public', async () => {
    const mockProfile = {
      id: '1',
      agent_name: 'John Doe',
      slug: 'john-doe',
      bio: 'Test bio',
      phone: '+1234567890',
      email: 'john@example.com',
      office_address: '123 Main St',
      specialties: ['Residential'],
      experience: '10+ years',
      languages: ['English'],
      is_active: true,
      is_public: true,
      view_count: 100,
      contact_count: 25,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    };

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_views: 100, total_contacts: 25, properties_count: 10, recent_inquiries: 5 })
      })

    render(<PublicWebsiteManagement />)

    await waitFor(() => {
      expect(screen.getByText('View Public Site')).toBeInTheDocument()
    })

    const viewButton = screen.getByText('View Public Site')
    const origin = window.location.origin
    expect(viewButton.closest('a')).toHaveAttribute('href', `${origin}/agent/john-doe`)
    expect(viewButton.closest('a')).toHaveAttribute('target', '_blank')
  })
})