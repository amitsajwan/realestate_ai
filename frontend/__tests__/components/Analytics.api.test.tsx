import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import Analytics from '../../components/Analytics'

// Mock the CRM API
jest.mock('@/lib/crm-api', () => ({
  crmApi: {
    getDashboardMetrics: jest.fn(),
  },
}))

import { crmApi } from '@/lib/crm-api'

const mockCrmApi = crmApi as jest.Mocked<typeof crmApi>

describe('Analytics API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Data Loading', () => {
    it('loads analytics data on component mount', async () => {
      const mockMetrics = {
        overview_metrics: [
          {
            name: 'Total Properties',
            value: 10,
            type: 'count',
            change_percentage: 12,
            change_direction: 'up',
          },
          {
            name: 'Total Value',
            value: 5000000,
            type: 'sum',
            unit: 'USD',
            change_percentage: 8.2,
            change_direction: 'up',
          },
        ],
        property_analytics: {
          total_properties: 10,
          published_properties: 8,
          draft_properties: 2,
          archived_properties: 0,
          average_price: 500000,
          total_value: 5000000,
          conversion_rate: 0.15,
        },
        lead_analytics: {
          total_leads: 50,
          new_leads: 15,
          contacted_leads: 20,
          qualified_leads: 10,
          converted_leads: 5,
          lost_leads: 0,
          conversion_rate: 0.1,
          average_deal_value: 750000,
          total_pipeline_value: 3750000,
        },
        generated_at: '2024-01-01T00:00:00Z',
        period: 'this_month',
        date_range: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-01-31T23:59:59Z',
        },
      }

      mockCrmApi.getDashboardMetrics.mockResolvedValue(mockMetrics)

      render(<Analytics />)

      await waitFor(() => {
        expect(mockCrmApi.getDashboardMetrics).toHaveBeenCalledWith('this_month')
      })

      expect(screen.getByText('10')).toBeInTheDocument()
      expect(screen.getByText('$5,000,000')).toBeInTheDocument()
    })

    it('handles API errors gracefully', async () => {
      mockCrmApi.getDashboardMetrics.mockRejectedValue(new Error('API Error'))

      render(<Analytics />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })

    it('shows loading state while fetching data', () => {
      mockCrmApi.getDashboardMetrics.mockImplementation(() => new Promise(() => {}))

      render(<Analytics />)

      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })
  })

  describe('Period Selection', () => {
    it('loads data for selected period', async () => {
      const user = userEvent.setup()
      const mockMetrics = {
        overview_metrics: [],
        property_analytics: {},
        lead_analytics: {},
        generated_at: '2024-01-01T00:00:00Z',
        period: 'this_week',
        date_range: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-01-07T23:59:59Z',
        },
      }

      mockCrmApi.getDashboardMetrics.mockResolvedValue(mockMetrics)

      render(<Analytics />)

      const periodSelect = screen.getByLabelText(/period/i)
      await user.selectOptions(periodSelect, 'this_week')

      await waitFor(() => {
        expect(mockCrmApi.getDashboardMetrics).toHaveBeenCalledWith('this_week')
      })
    })

    it('updates data when period changes', async () => {
      const user = userEvent.setup()
      const mockMetrics = {
        overview_metrics: [],
        property_analytics: {},
        lead_analytics: {},
        generated_at: '2024-01-01T00:00:00Z',
        period: 'this_year',
        date_range: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-12-31T23:59:59Z',
        },
      }

      mockCrmApi.getDashboardMetrics.mockResolvedValue(mockMetrics)

      render(<Analytics />)

      const periodSelect = screen.getByLabelText(/period/i)
      await user.selectOptions(periodSelect, 'this_year')

      await waitFor(() => {
        expect(mockCrmApi.getDashboardMetrics).toHaveBeenCalledWith('this_year')
      })
    })
  })

  describe('Data Display', () => {
    it('displays metrics correctly from API data', async () => {
      const mockMetrics = {
        overview_metrics: [
          {
            name: 'Total Properties',
            value: 25,
            type: 'count',
            change_percentage: 15,
            change_direction: 'up',
          },
          {
            name: 'Total Value',
            value: 12500000,
            type: 'sum',
            unit: 'USD',
            change_percentage: 22.5,
            change_direction: 'up',
          },
        ],
        property_analytics: {
          total_properties: 25,
          published_properties: 20,
          draft_properties: 5,
          archived_properties: 0,
          average_price: 500000,
          total_value: 12500000,
          conversion_rate: 0.2,
        },
        lead_analytics: {
          total_leads: 100,
          new_leads: 30,
          contacted_leads: 40,
          qualified_leads: 20,
          converted_leads: 10,
          lost_leads: 0,
          conversion_rate: 0.1,
          average_deal_value: 800000,
          total_pipeline_value: 8000000,
        },
        generated_at: '2024-01-01T00:00:00Z',
        period: 'this_month',
        date_range: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-01-31T23:59:59Z',
        },
      }

      mockCrmApi.getDashboardMetrics.mockResolvedValue(mockMetrics)

      render(<Analytics />)

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument()
        expect(screen.getByText('$12,500,000')).toBeInTheDocument()
        expect(screen.getByText('+15%')).toBeInTheDocument()
        expect(screen.getByText('+22.5%')).toBeInTheDocument()
      })
    })

    it('displays property analytics correctly', async () => {
      const mockMetrics = {
        overview_metrics: [],
        property_analytics: {
          total_properties: 15,
          published_properties: 12,
          draft_properties: 3,
          archived_properties: 0,
          average_price: 750000,
          total_value: 11250000,
          conversion_rate: 0.25,
        },
        lead_analytics: {},
        generated_at: '2024-01-01T00:00:00Z',
        period: 'this_month',
        date_range: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-01-31T23:59:59Z',
        },
      }

      mockCrmApi.getDashboardMetrics.mockResolvedValue(mockMetrics)

      render(<Analytics />)

      await waitFor(() => {
        expect(screen.getByText('15')).toBeInTheDocument()
        expect(screen.getByText('$11,250,000')).toBeInTheDocument()
        expect(screen.getByText('$750,000')).toBeInTheDocument()
      })
    })

    it('displays lead analytics correctly', async () => {
      const mockMetrics = {
        overview_metrics: [],
        property_analytics: {},
        lead_analytics: {
          total_leads: 75,
          new_leads: 25,
          contacted_leads: 30,
          qualified_leads: 15,
          converted_leads: 5,
          lost_leads: 0,
          conversion_rate: 0.067,
          average_deal_value: 900000,
          total_pipeline_value: 4500000,
        },
        generated_at: '2024-01-01T00:00:00Z',
        period: 'this_month',
        date_range: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-01-31T23:59:59Z',
        },
      }

      mockCrmApi.getDashboardMetrics.mockResolvedValue(mockMetrics)

      render(<Analytics />)

      await waitFor(() => {
        expect(screen.getByText('75')).toBeInTheDocument()
        expect(screen.getByText('25')).toBeInTheDocument()
        expect(screen.getByText('6.7%')).toBeInTheDocument()
        expect(screen.getByText('$4,500,000')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('shows error message when API fails', async () => {
      mockCrmApi.getDashboardMetrics.mockRejectedValue(new Error('Network error'))

      render(<Analytics />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })

    it('retries API call when retry button is clicked', async () => {
      const user = userEvent.setup()
      const mockMetrics = {
        overview_metrics: [],
        property_analytics: {},
        lead_analytics: {},
        generated_at: '2024-01-01T00:00:00Z',
        period: 'this_month',
        date_range: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-01-31T23:59:59Z',
        },
      }

      mockCrmApi.getDashboardMetrics
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockMetrics)

      render(<Analytics />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })

      const retryButton = screen.getByRole('button', { name: /retry/i })
      await user.click(retryButton)

      await waitFor(() => {
        expect(mockCrmApi.getDashboardMetrics).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Performance', () => {
    it('loads data efficiently', async () => {
      const mockMetrics = {
        overview_metrics: [],
        property_analytics: {},
        lead_analytics: {},
        generated_at: '2024-01-01T00:00:00Z',
        period: 'this_month',
        date_range: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-01-31T23:59:59Z',
        },
      }

      mockCrmApi.getDashboardMetrics.mockResolvedValue(mockMetrics)

      const startTime = Date.now()
      render(<Analytics />)
      const endTime = Date.now()

      // Should render within reasonable time
      expect(endTime - startTime).toBeLessThan(1000)
    })
  })
})