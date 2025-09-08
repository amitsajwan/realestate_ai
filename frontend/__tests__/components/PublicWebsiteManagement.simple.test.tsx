import React from 'react'
import { render, screen } from '@testing-library/react'
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

describe('PublicWebsiteManagement', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear()
  })

  test('should render without crashing', () => {
    (fetch as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<PublicWebsiteManagement />)
    
    // Should render the loading spinner
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  test('should render main interface when data loads', async () => {
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
    }

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

    // Wait for the component to load
    await screen.findByText('Public Website Management')
    
    expect(screen.getByText('Manage your public agent website and profile')).toBeInTheDocument()
    expect(screen.getByText('Total Views')).toBeInTheDocument()
    expect(screen.getByText('Total Contacts')).toBeInTheDocument()
    expect(screen.getByText('Public Properties')).toBeInTheDocument()
    expect(screen.getByText('Recent Inquiries')).toBeInTheDocument()
  })
})