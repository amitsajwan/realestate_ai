import { render, screen, waitFor } from '@testing-library/react'
import { jest } from '@jest/globals'
import AgentPostsPage from '@/app/agent/[agentName]/posts/page'
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

const mockPosts = [
  {
    id: '1',
    title: 'Market Update: Q1 2024',
    content: 'The real estate market is showing strong growth in Q1 2024...',
    property_id: '1',
    property_title: 'Beautiful House',
    language: 'en',
    channels: ['facebook', 'instagram'],
    status: 'published',
    created_at: '2024-01-01T00:00:00Z',
    view_count: 150,
    like_count: 25,
    share_count: 10,
    comment_count: 5,
  },
  {
    id: '2',
    title: 'New Property Listing',
    content: 'Check out this amazing new property in downtown...',
    property_id: '2',
    property_title: 'Modern Apartment',
    language: 'en',
    channels: ['facebook', 'twitter'],
    status: 'published',
    created_at: '2024-01-02T00:00:00Z',
    view_count: 200,
    like_count: 30,
    share_count: 15,
    comment_count: 8,
  },
]

describe('Agent Posts Page', () => {
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
          posts: mockPosts,
          total: 2,
          page: 1,
          limit: 10,
        }),
      })
  })

  it('should render agent information', async () => {
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Real Estate Agent')).toBeInTheDocument()
    })
  })

  it('should render page title and description', async () => {
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Marketing Updates')).toBeInTheDocument()
      expect(screen.getByText('Stay updated with the latest property news and market insights from John Doe.')).toBeInTheDocument()
    })
  })

  it('should render posts list', async () => {
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Market Update: Q1 2024')).toBeInTheDocument()
      expect(screen.getByText('New Property Listing')).toBeInTheDocument()
    })
  })

  it('should display post content', async () => {
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('The real estate market is showing strong growth in Q1 2024...')).toBeInTheDocument()
      expect(screen.getByText('Check out this amazing new property in downtown...')).toBeInTheDocument()
    })
  })

  it('should display post engagement metrics', async () => {
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument() // View count
      expect(screen.getByText('25')).toBeInTheDocument() // Like count
      expect(screen.getByText('10')).toBeInTheDocument() // Share count
      expect(screen.getByText('5')).toBeInTheDocument() // Comment count
    })
  })

  it('should show contact agent button', async () => {
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Contact')).toBeInTheDocument()
    })
  })

  it('should not show navigation to other pages', async () => {
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.queryByText('Properties')).not.toBeInTheDocument()
      expect(screen.queryByText('Posts')).not.toBeInTheDocument()
    })
  })

  it('should handle empty posts state', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgent,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          posts: [],
          total: 0,
          page: 1,
          limit: 10,
        }),
      })

    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('No updates yet')).toBeInTheDocument()
      expect(screen.getByText('This agent hasn\'t shared any marketing updates yet.')).toBeInTheDocument()
    })
  })

  it('should handle loading state', () => {
    ;(fetch as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    expect(screen.getByText('Loading posts...')).toBeInTheDocument()
  })

  it('should handle error state', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'))
    
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      expect(screen.getByText('Error loading posts')).toBeInTheDocument()
    })
  })

  it('should display post dates correctly', async () => {
    render(<AgentPostsPage params={{ agentName: 'john-doe' }} />)
    
    await waitFor(() => {
      // Check if dates are displayed (format may vary)
      expect(screen.getByText(/January 1, 2024/)).toBeInTheDocument()
      expect(screen.getByText(/January 2, 2024/)).toBeInTheDocument()
    })
  })
})
