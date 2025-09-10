import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import CRM from '../../components/CRM'

// Mock the CRM API
jest.mock('@/lib/crm-api', () => ({
  crmApi: {
    getLeads: jest.fn(),
    getLeadStats: jest.fn(),
    createLead: jest.fn(),
    updateLead: jest.fn(),
    deleteLead: jest.fn(),
    addLeadActivity: jest.fn(),
  },
}))

import { crmApi } from '@/lib/crm-api'

const mockCrmApi = crmApi as jest.Mocked<typeof crmApi>

describe('CRM API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Data Loading', () => {
    it('loads leads data on component mount', async () => {
      const mockLeads = {
        leads: [
          {
            id: '1',
            name: 'John Doe',
            email: 'john@example.com',
            phone: '+1234567890',
            status: 'new',
            urgency: 'high',
            score: 85,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
        total_pages: 1,
        filters_applied: {},
      }

      const mockStats = {
        total_leads: 1,
        new_leads: 1,
        contacted_leads: 0,
        qualified_leads: 0,
        converted_leads: 0,
        lost_leads: 0,
        conversion_rate: 0,
        average_deal_value: 0,
        total_pipeline_value: 0,
        leads_this_month: 1,
        leads_this_week: 1,
        leads_today: 0,
      }

      mockCrmApi.getLeads.mockResolvedValue(mockLeads)
      mockCrmApi.getLeadStats.mockResolvedValue(mockStats)

      render(<CRM />)

      await waitFor(() => {
        expect(mockCrmApi.getLeads).toHaveBeenCalledWith({}, 1, 20)
        expect(mockCrmApi.getLeadStats).toHaveBeenCalled()
      })

      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    it('handles API errors gracefully', async () => {
      mockCrmApi.getLeads.mockRejectedValue(new Error('API Error'))
      mockCrmApi.getLeadStats.mockRejectedValue(new Error('API Error'))

      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })

    it('shows loading state while fetching data', () => {
      mockCrmApi.getLeads.mockImplementation(() => new Promise(() => {}))
      mockCrmApi.getLeadStats.mockImplementation(() => new Promise(() => {}))

      render(<CRM />)

      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })
  })

  describe('Lead Management', () => {
    it('creates a new lead successfully', async () => {
      const user = userEvent.setup()
      const mockNewLead = {
        id: '2',
        name: 'Jane Smith',
        email: 'jane@example.com',
        phone: '+1234567891',
        status: 'new',
        urgency: 'medium',
        score: 75,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      mockCrmApi.createLead.mockResolvedValue(mockNewLead)

      render(<CRM />)

      const addButton = screen.getByRole('button', { name: /add lead/i })
      await user.click(addButton)

      // Fill form and submit
      const nameInput = screen.getByLabelText(/name/i)
      await user.type(nameInput, 'Jane Smith')

      const emailInput = screen.getByLabelText(/email/i)
      await user.type(emailInput, 'jane@example.com')

      const submitButton = screen.getByRole('button', { name: /create/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockCrmApi.createLead).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Jane Smith',
            email: 'jane@example.com',
          })
        )
      })
    })

    it('updates lead status successfully', async () => {
      const user = userEvent.setup()
      const mockUpdatedLead = {
        id: '1',
        name: 'John Doe',
        status: 'contacted',
        // ... other properties
      }

      mockCrmApi.updateLead.mockResolvedValue(mockUpdatedLead)

      render(<CRM />)

      // Wait for leads to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      // Update status
      const statusSelect = screen.getByLabelText(/status/i)
      await user.selectOptions(statusSelect, 'contacted')

      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockCrmApi.updateLead).toHaveBeenCalledWith('1', {
          status: 'contacted',
        })
      })
    })

    it('deletes a lead successfully', async () => {
      const user = userEvent.setup()

      mockCrmApi.deleteLead.mockResolvedValue(undefined)

      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      // Confirm deletion
      const confirmButton = screen.getByRole('button', { name: /confirm/i })
      await user.click(confirmButton)

      await waitFor(() => {
        expect(mockCrmApi.deleteLead).toHaveBeenCalledWith('1')
      })
    })
  })

  describe('Search and Filtering', () => {
    it('searches leads with API call', async () => {
      const user = userEvent.setup()
      const mockSearchResults = {
        leads: [],
        total: 0,
        page: 1,
        per_page: 20,
        total_pages: 0,
        filters_applied: { search_term: 'test' },
      }

      mockCrmApi.getLeads.mockResolvedValue(mockSearchResults)

      render(<CRM />)

      const searchInput = screen.getByPlaceholderText(/search/i)
      await user.type(searchInput, 'test')

      await waitFor(() => {
        expect(mockCrmApi.getLeads).toHaveBeenCalledWith(
          { search_term: 'test' },
          1,
          20
        )
      })
    })

    it('filters leads by status with API call', async () => {
      const user = userEvent.setup()
      const mockFilteredResults = {
        leads: [],
        total: 0,
        page: 1,
        per_page: 20,
        total_pages: 0,
        filters_applied: { status: 'new' },
      }

      mockCrmApi.getLeads.mockResolvedValue(mockFilteredResults)

      render(<CRM />)

      const filterButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filterButton)

      const statusSelect = screen.getByLabelText(/status/i)
      await user.selectOptions(statusSelect, 'new')

      await waitFor(() => {
        expect(mockCrmApi.getLeads).toHaveBeenCalledWith(
          { status: 'new' },
          1,
          20
        )
      })
    })
  })

  describe('Pagination', () => {
    it('loads next page of leads', async () => {
      const user = userEvent.setup()
      const mockPage2Results = {
        leads: [],
        total: 50,
        page: 2,
        per_page: 20,
        total_pages: 3,
        filters_applied: {},
      }

      mockCrmApi.getLeads.mockResolvedValue(mockPage2Results)

      render(<CRM />)

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(mockCrmApi.getLeads).toHaveBeenCalledWith({}, 2, 20)
      })
    })
  })

  describe('Error Handling', () => {
    it('shows error message when API fails', async () => {
      mockCrmApi.getLeads.mockRejectedValue(new Error('Network error'))
      mockCrmApi.getLeadStats.mockRejectedValue(new Error('Network error'))

      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })

    it('retries API call when retry button is clicked', async () => {
      const user = userEvent.setup()
      const mockLeads = {
        leads: [],
        total: 0,
        page: 1,
        per_page: 20,
        total_pages: 0,
        filters_applied: {},
      }

      mockCrmApi.getLeads
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockLeads)

      render(<CRM />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })

      const retryButton = screen.getByRole('button', { name: /retry/i })
      await user.click(retryButton)

      await waitFor(() => {
        expect(mockCrmApi.getLeads).toHaveBeenCalledTimes(2)
      })
    })
  })
})