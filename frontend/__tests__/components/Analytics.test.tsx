import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import Analytics from '../../components/Analytics'

// Mock all dependencies
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  ChartBarIcon: (props: any) => <div data-testid="chart-bar-icon" {...props} />,
  CurrencyDollarIcon: (props: any) => <div data-testid="currency-icon" {...props} />,
  HomeIcon: (props: any) => <div data-testid="home-icon" {...props} />,
  ArrowTrendingUpIcon: (props: any) => <div data-testid="arrow-up-icon" {...props} />,
  ArrowTrendingDownIcon: (props: any) => <div data-testid="arrow-down-icon" {...props} />,
  EyeIcon: (props: any) => <div data-testid="eye-icon" {...props} />,
  CalendarIcon: (props: any) => <div data-testid="calendar-icon" {...props} />,
  MapPinIcon: (props: any) => <div data-testid="map-pin-icon" {...props} />,
}))

const mockProperties = [
  {
    id: 1,
    title: 'Modern Downtown Condo',
    price: 450000,
    status: 'for-sale',
    type: 'Condo',
    dateAdded: '2024-01-15'
  },
  {
    id: 2,
    title: 'Luxury Villa',
    price: 850000,
    status: 'sold',
    type: 'House',
    dateAdded: '2024-01-10'
  },
  {
    id: 3,
    title: 'Suburban House',
    price: 320000,
    status: 'for-rent',
    type: 'House',
    dateAdded: '2024-01-20'
  },
  {
    id: 4,
    title: 'City Apartment',
    price: 280000,
    status: 'for-sale',
    type: 'Apartment',
    dateAdded: '2024-01-25'
  }
]

describe('Analytics Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders the analytics dashboard with header', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Track your property portfolio performance and insights')).toBeInTheDocument()
    })

    it('displays last updated timestamp', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
    })

    it('renders with mock data when no properties provided', () => {
      render(<Analytics />)

      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument()
    })

    it('loads mock properties when none provided', async () => {
      render(<Analytics />)

      await waitFor(() => {
        expect(screen.getByText('4')).toBeInTheDocument() // Total properties from mock data
      })
    })
  })

  describe('Statistics Cards', () => {
    it('displays all key statistics cards', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Total Properties')).toBeInTheDocument()
      expect(screen.getByText('Total Portfolio Value')).toBeInTheDocument()
      expect(screen.getByText('Average Property Value')).toBeInTheDocument()
      expect(screen.getByText('Properties Sold')).toBeInTheDocument()
    })

    it('calculates and displays correct total properties', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('4')).toBeInTheDocument()
    })

    it('calculates and displays correct total portfolio value', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('$1,900,000')).toBeInTheDocument()
    })

    it('calculates and displays correct average property value', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('$475,000')).toBeInTheDocument()
    })

    it('displays correct number of sold properties', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('1')).toBeInTheDocument() // Properties Sold
    })

    it('shows change indicators for statistics', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('+12%')).toBeInTheDocument()
      expect(screen.getByText('+8.2%')).toBeInTheDocument()
      expect(screen.getByText('+5.1%')).toBeInTheDocument()
      expect(screen.getByText('+15%')).toBeInTheDocument()
    })

    it('displays correct change indicator colors', () => {
      render(<Analytics properties={mockProperties} />)

      const increaseIndicators = screen.getAllByText(/\+/)
      increaseIndicators.forEach(indicator => {
        expect(indicator).toHaveClass('text-green-400')
      })
    })
  })

  describe('Property Status Breakdown', () => {
    it('displays property status breakdown section', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Property Status Breakdown')).toBeInTheDocument()
    })

    it('shows correct status categories', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('For Sale')).toBeInTheDocument()
      expect(screen.getByText('For Rent')).toBeInTheDocument()
      expect(screen.getByText('Sold')).toBeInTheDocument()
    })

    it('displays correct counts for each status', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('2')).toBeInTheDocument() // For Sale
      expect(screen.getByText('1')).toBeInTheDocument() // For Rent
      expect(screen.getByText('1')).toBeInTheDocument() // Sold
    })

    it('calculates and displays correct percentages', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('(50%)')).toBeInTheDocument() // For Sale
      expect(screen.getByText('(25%)')).toBeInTheDocument() // For Rent
      expect(screen.getByText('(25%)')).toBeInTheDocument() // Sold
    })

    it('displays status color indicators', () => {
      render(<Analytics properties={mockProperties} />)

      const colorIndicators = screen.getAllByTestId(/^w-4 h-4 rounded/)
      expect(colorIndicators).toHaveLength(3)
    })
  })

  describe('Property Types Breakdown', () => {
    it('displays property types section', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Property Types')).toBeInTheDocument()
    })

    it('shows all property types from data', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Condo')).toBeInTheDocument()
      expect(screen.getByText('House')).toBeInTheDocument()
      expect(screen.getByText('Apartment')).toBeInTheDocument()
    })

    it('displays correct counts for each type', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('1')).toBeInTheDocument() // Condo
      expect(screen.getByText('2')).toBeInTheDocument() // House
      expect(screen.getByText('1')).toBeInTheDocument() // Apartment
    })

    it('calculates correct type percentages', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('(25%)')).toBeInTheDocument() // Condo
      expect(screen.getByText('(50%)')).toBeInTheDocument() // House
      expect(screen.getByText('(25%)')).toBeInTheDocument() // Apartment
    })
  })

  describe('Recent Activity', () => {
    it('displays recent activity section', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    })

    it('shows activity items', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('New property added: Modern Downtown Condo')).toBeInTheDocument()
      expect(screen.getByText('Property status updated: Luxury Villa marked as sold')).toBeInTheDocument()
      expect(screen.getByText('Price updated: Suburban House reduced by $10,000')).toBeInTheDocument()
    })

    it('displays activity timestamps', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('2 hours ago')).toBeInTheDocument()
      expect(screen.getByText('5 hours ago')).toBeInTheDocument()
      expect(screen.getByText('1 day ago')).toBeInTheDocument()
    })

    it('shows activity status indicators', () => {
      render(<Analytics properties={mockProperties} />)

      const indicators = screen.getAllByTestId(/^w-2 h-2/)
      expect(indicators).toHaveLength(3)
    })
  })

  describe('Market Insights', () => {
    it('displays market insights section', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Market Insights')).toBeInTheDocument()
    })

    it('shows market metrics', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Average Price Growth')).toBeInTheDocument()
      expect(screen.getByText('Average Time on Market')).toBeInTheDocument()
      expect(screen.getByText('Portfolio Occupancy')).toBeInTheDocument()
    })

    it('displays metric values', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('+12.5%')).toBeInTheDocument()
      expect(screen.getByText('18 days')).toBeInTheDocument()
      expect(screen.getByText('94%')).toBeInTheDocument()
    })

    it('shows metric descriptions', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('vs last quarter')).toBeInTheDocument()
      expect(screen.getByText('for sold properties')).toBeInTheDocument()
      expect(screen.getByText('rental properties')).toBeInTheDocument()
    })
  })

  describe('Data Calculations', () => {
    it('calculates statistics correctly with provided properties', () => {
      const customProperties = [
        { id: 1, title: 'Prop 1', price: 100000, status: 'for-sale', type: 'House' },
        { id: 2, title: 'Prop 2', price: 200000, status: 'sold', type: 'Condo' },
      ]

      render(<Analytics properties={customProperties} />)

      expect(screen.getByText('2')).toBeInTheDocument() // Total properties
      expect(screen.getByText('$300,000')).toBeInTheDocument() // Total value
      expect(screen.getByText('$150,000')).toBeInTheDocument() // Average value
      expect(screen.getByText('1')).toBeInTheDocument() // Sold properties
    })

    it('handles empty properties array', () => {
      render(<Analytics properties={[]} />)

      expect(screen.getByText('0')).toBeInTheDocument() // Total properties
      expect(screen.getByText('$0')).toBeInTheDocument() // Total value
    })

    it('handles single property correctly', () => {
      const singleProperty = [
        { id: 1, title: 'Single Prop', price: 500000, status: 'for-sale', type: 'House' }
      ]

      render(<Analytics properties={singleProperty} />)

      expect(screen.getByText('1')).toBeInTheDocument() // Total properties
      expect(screen.getByText('$500,000')).toBeInTheDocument() // Total value
      expect(screen.getByText('$500,000')).toBeInTheDocument() // Average value
    })
  })

  describe('Responsive Design', () => {
    it('uses responsive grid layout for statistics', () => {
      render(<Analytics properties={mockProperties} />)

      const statsGrid = screen.getByText('Total Properties').closest('div')
      expect(statsGrid).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4')
    })

    it('uses responsive layout for charts', () => {
      render(<Analytics properties={mockProperties} />)

      const chartsGrid = screen.getByText('Property Status Breakdown').closest('div')
      expect(chartsGrid).toHaveClass('grid', 'grid-cols-1', 'lg:grid-cols-2')
    })

    it('uses responsive layout for market insights', () => {
      render(<Analytics properties={mockProperties} />)

      const insightsGrid = screen.getByText('Average Price Growth').closest('div')
      expect(insightsGrid).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-3')
    })
  })

  describe('Animation and Styling', () => {
    it('applies backdrop blur styling', () => {
      render(<Analytics properties={mockProperties} />)

      const cards = screen.getAllByTestId(/^bg-white/)
      expect(cards.length).toBeGreaterThan(0)
    })

    it('displays icons correctly', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getAllByTestId('chart-bar-icon')).toHaveLength(2)
      expect(screen.getAllByTestId('home-icon')).toHaveLength(2)
      expect(screen.getAllByTestId('currency-icon')).toHaveLength(1)
      expect(screen.getAllByTestId('eye-icon')).toHaveLength(1)
    })

    it('applies correct color schemes', () => {
      render(<Analytics properties={mockProperties} />)

      expect(screen.getByText('Total Properties').closest('div')).toHaveClass('bg-blue-500')
      expect(screen.getByText('Total Portfolio Value').closest('div')).toHaveClass('bg-green-500')
      expect(screen.getByText('Average Property Value').closest('div')).toHaveClass('bg-purple-500')
      expect(screen.getByText('Properties Sold').closest('div')).toHaveClass('bg-orange-500')
    })
  })

  describe('Edge Cases', () => {
    it('handles properties with zero price', () => {
      const zeroPriceProperties = [
        { id: 1, title: 'Free Property', price: 0, status: 'for-sale', type: 'House' }
      ]

      render(<Analytics properties={zeroPriceProperties} />)

      expect(screen.getByText('$0')).toBeInTheDocument()
    })

    it('handles very large numbers', () => {
      const largePriceProperties = [
        { id: 1, title: 'Expensive Property', price: 10000000, status: 'for-sale', type: 'House' }
      ]

      render(<Analytics properties={largePriceProperties} />)

      expect(screen.getByText('$10,000,000')).toBeInTheDocument()
    })

    it('handles properties with missing fields gracefully', () => {
      const incompleteProperties = [
        { id: 1, title: 'Incomplete', price: 100000 } // missing status and type
      ]

      render(<Analytics properties={incompleteProperties} />)

      // Should not crash and display available data
      expect(screen.getByText('1')).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('renders efficiently with large dataset', () => {
      const largeDataset = Array.from({ length: 100 }, (_, i) => ({
        id: i,
        title: `Property ${i}`,
        price: 100000 + i * 1000,
        status: 'for-sale',
        type: 'House'
      }))

      const startTime = Date.now()
      render(<Analytics properties={largeDataset} />)
      const endTime = Date.now()

      // Should render within reasonable time
      expect(endTime - startTime).toBeLessThan(1000)
    })

    it('calculates statistics efficiently', () => {
      const manyProperties = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        title: `Property ${i}`,
        price: Math.random() * 1000000,
        status: Math.random() > 0.5 ? 'for-sale' : 'sold',
        type: 'House'
      }))

      const startTime = Date.now()
      render(<Analytics properties={manyProperties} />)
      const endTime = Date.now()

      // Calculations should be fast
      expect(endTime - startTime).toBeLessThan(500)
    })
  })

  describe('Accessibility', () => {
    it('has proper heading hierarchy', () => {
      render(<Analytics properties={mockProperties} />)

      const h1 = screen.getByRole('heading', { level: 1 })
      expect(h1).toHaveTextContent('Analytics Dashboard')

      const h3s = screen.getAllByRole('heading', { level: 3 })
      expect(h3s).toHaveLength(4) // Property Status, Property Types, Recent Activity, Market Insights
    })

    it('provides meaningful content for screen readers', () => {
      render(<Analytics properties={mockProperties} />)

      // Check that all data is accessible via text content
      expect(screen.getByText('$1,900,000')).toBeInTheDocument()
      expect(screen.getByText('$475,000')).toBeInTheDocument()
    })
  })
})