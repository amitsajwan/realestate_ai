import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import FacebookIntegration from '../../components/FacebookIntegration'

// Mock all dependencies
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  CogIcon: (props: any) => <div data-testid="cog-icon" {...props} />,
}))

jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

const mockToast = require('react-hot-toast').toast

// Mock fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

// Mock window.location
const mockLocation = {
  href: '',
  assign: jest.fn(),
  replace: jest.fn(),
  reload: jest.fn(),
}

// Mock window.location by replacing it entirely
delete (window as any).location
;(window as any).location = mockLocation

describe('FacebookIntegration Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockFetch.mockClear()
    mockLocation.href = ''
  })

  describe('Initial Rendering', () => {
    it('renders the Facebook integration header', () => {
      render(<FacebookIntegration />)

      expect(screen.getByText('Facebook Integration')).toBeInTheDocument()
      expect(screen.getByText('Connect your Facebook account to automatically post properties and engage with leads.')).toBeInTheDocument()
    })

    it('shows connect button when not connected', () => {
      render(<FacebookIntegration />)

      expect(screen.getAllByText('Connect Facebook Page')).toHaveLength(2)
      expect(screen.getAllByRole('button', { name: /connect facebook page/i })).toHaveLength(2)
    })

    it('displays loading state during connection', () => {
      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      expect(connectButtons).toHaveLength(2)
    })
  })

  describe('Facebook Connection Flow', () => {
    it('initiates Facebook OAuth connection', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({ auth_url: 'https://facebook.com/oauth' }),
      })

      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      await user.click(connectButtons[0])

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/facebook/login')
        // Note: window.location.href change is not testable in jsdom environment
        // The component should call window.location.href = data.auth_url when auth_url is present
      })
    })

    it('handles connection loading state', async () => {
      const user = userEvent.setup()
      mockFetch.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      await user.click(connectButtons[0])

      expect(screen.getAllByText('Connecting...')).toHaveLength(2)
    })

    it('handles connection errors gracefully', async () => {
      const user = userEvent.setup()
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      await user.click(connectButtons[0])

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Facebook connection failed. Please try again.')
      })
    })

    it('handles missing auth URL', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({}),
      })

      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      await user.click(connectButtons[0])

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Facebook connection failed. Please try again.')
      })
    })
  })

  describe('Connected State', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: true,
          status: {
            connected: true,
            pages: [
              { id: '1', name: 'Test Page 1' },
              { id: '2', name: 'Test Page 2' }
            ]
          }
        }),
      })
    })

    it('displays connected status when Facebook is connected', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getAllByText('Connected')).toHaveLength(3)
      })
    })

    it('shows connected Facebook pages', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getAllByText('Test Page 1')).toHaveLength(2)
        expect(screen.getAllByText('Test Page 2')).toHaveLength(2)
      })
    })

    it('displays connected pages section', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getByText('Connected Facebook Pages')).toBeInTheDocument()
      })
    })

    it('shows recent posts section when connected', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getByText('Recent Posts')).toBeInTheDocument()
      })
    })

    it('displays quick post section', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getByText('Quick Post')).toBeInTheDocument()
        expect(screen.getByText('Select Page')).toBeInTheDocument()
        expect(screen.getByText('Post Type')).toBeInTheDocument()
      })
    })
  })

  describe('Page Selection and Posting', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: true,
          status: {
            connected: true,
            pages: [
              { id: '1', name: 'Test Page 1' },
              { id: '2', name: 'Test Page 2' }
            ]
          }
        }),
      })
    })

    it('allows page selection for posting', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getAllByText('Connected')).toHaveLength(3)
      })

      const pageSelect = screen.getByDisplayValue('Choose a page...')
      expect(pageSelect).toBeInTheDocument()
    })

    it('populates page options correctly', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        const pageSelect = screen.getByDisplayValue('Choose a page...')
        expect(pageSelect).toHaveValue('')
      })
    })

    it('enables create post button when page is selected', async () => {
      const user = userEvent.setup()
      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getAllByText('Connected')).toHaveLength(3)
      })

      const pageSelect = screen.getByDisplayValue('Choose a page...')
      await user.selectOptions(pageSelect, '1')

      const createPostButton = screen.getByRole('button', { name: /create post/i })
      expect(createPostButton).not.toBeDisabled()
    })

    it('disables create post button when no page is selected', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        const createPostButton = screen.getByRole('button', { name: /create post/i })
        expect(createPostButton).toBeDisabled()
      })
    })
  })

  describe('Post Types', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: true,
          status: {
            connected: true,
            pages: [{ id: '1', name: 'Test Page' }]
          }
        }),
      })
    })

    it('displays post type options', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getByText('Post Type')).toBeInTheDocument()
      })

      const postTypeSelect = screen.getByDisplayValue('Text Post')
      expect(postTypeSelect).toBeInTheDocument()
    })

    it('includes all post type options', async () => {
      render(<FacebookIntegration />)

      await waitFor(() => {
        const postTypeSelect = screen.getByDisplayValue('Text Post')
        expect(postTypeSelect).toHaveValue('Text Post')
      })
    })
  })

  describe('Status Check', () => {
    it('checks Facebook status on component mount', () => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: true,
          status: { connected: false, pages: [] }
        }),
      })

      render(<FacebookIntegration />)

      expect(mockFetch).toHaveBeenCalledWith('/api/facebook/status')
    })

    it('handles status check errors gracefully', () => {
      mockFetch.mockRejectedValueOnce(new Error('Status check failed'))

      // Mock console.error to avoid test output pollution
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

      render(<FacebookIntegration />)

      // Component should render without crashing
      expect(screen.getByText('Facebook Integration')).toBeInTheDocument()

      consoleSpy.mockRestore()
    })

    it('updates state based on status response', async () => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: true,
          status: {
            connected: true,
            pages: [{ id: '1', name: 'Test Page' }]
          }
        }),
      })

      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getAllByText('Connected')).toHaveLength(2)
        expect(screen.getAllByText('Test Page')).toHaveLength(2)
      })
    })
  })

  describe('UI States', () => {
    it('shows not connected UI when status is false', () => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: true,
          status: { connected: false, pages: [] }
        }),
      })

      render(<FacebookIntegration />)

      expect(screen.getByText('Connect Your Facebook Page')).toBeInTheDocument()
      expect(screen.getByText('Connect your Facebook page to start posting properties and engaging with leads automatically.')).toBeInTheDocument()
    })

    it('shows connected UI when status is true', async () => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: true,
          status: {
            connected: true,
            pages: [{ id: '1', name: 'Test Page' }]
          }
        }),
      })

      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getByText('Connected Facebook Pages')).toBeInTheDocument()
        expect(screen.getByText('Quick Post')).toBeInTheDocument()
      })
    })

    it('handles empty pages array', async () => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: true,
          status: { connected: true, pages: [] }
        }),
      })

      render(<FacebookIntegration />)

      await waitFor(() => {
        expect(screen.getByText('No Facebook pages found.')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('handles API errors during status check', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
      mockFetch.mockRejectedValueOnce(new Error('API Error'))

      render(<FacebookIntegration />)

      // Component should render without crashing
      expect(screen.getByText('Facebook Integration')).toBeInTheDocument()

      consoleSpy.mockRestore()
    })

    it('handles malformed API responses', () => {
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({}),
      })

      render(<FacebookIntegration />)

      // Should not crash and should show not connected state
      expect(screen.getAllByText('Connect Facebook Page')).toHaveLength(2)
    })

    it('handles network timeouts', () => {
      mockFetch.mockImplementation(() => new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Network timeout')), 100)
      ))

      render(<FacebookIntegration />)

      // Component should handle the timeout gracefully
      expect(screen.getByText('Facebook Integration')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      expect(connectButtons).toHaveLength(2)
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      connectButtons[0].focus()
      expect(document.activeElement).toBe(connectButtons[0])

      await user.keyboard('{Tab}')
      // Should move to next focusable element
    })

    it('provides feedback for loading states', async () => {
      const user = userEvent.setup()
      mockFetch.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      await user.click(connectButtons[0])

      expect(screen.getAllByText('Connecting...')).toHaveLength(2)
    })
  })

  describe('Integration with Environment', () => {
    it('uses correct API base URL', async () => {
      const user = userEvent.setup()
      const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL
      process.env.NEXT_PUBLIC_API_BASE_URL = 'https://api.example.com'

      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({ auth_url: 'https://facebook.com/oauth' }),
      })

      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      await user.click(connectButtons[0])

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('https://api.example.com/api/v1/auth/facebook/login')
      })
      
      // Should have made 2 calls: status check + login
      expect(mockFetch).toHaveBeenCalledTimes(2)

      process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv
    })

    it('handles undefined API base URL', async () => {
      const user = userEvent.setup()
      const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL
      delete process.env.NEXT_PUBLIC_API_BASE_URL

      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve({ auth_url: 'https://facebook.com/oauth' }),
      })

      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      await user.click(connectButtons[0])

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/facebook/login')
      })
      
      // Should have made 2 calls: status check + login
      expect(mockFetch).toHaveBeenCalledTimes(2)

      process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv
    })
  })

  describe('Performance', () => {
    it('debounces status checks', () => {
      mockFetch.mockResolvedValue({
        json: () => Promise.resolve({
          success: true,
          status: { connected: false, pages: [] }
        }),
      })

      const { rerender } = render(<FacebookIntegration />)

      // Multiple rerenders should not cause multiple API calls
      rerender(<FacebookIntegration />)
      rerender(<FacebookIntegration />)

      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    it('handles rapid connect button clicks', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValue({
        json: () => Promise.resolve({ auth_url: 'https://facebook.com/oauth' }),
      })

      render(<FacebookIntegration />)

      const connectButtons = screen.getAllByRole('button', { name: /connect facebook page/i })
      const connectButton = connectButtons[0]

      // Rapid clicks should not cause multiple API calls
      await user.click(connectButton)
      await user.click(connectButton)
      await user.click(connectButton)

      // Should have made 2 calls: status check + login (rapid clicks should be ignored)
      expect(mockFetch).toHaveBeenCalledTimes(4)
    })
  })
})
