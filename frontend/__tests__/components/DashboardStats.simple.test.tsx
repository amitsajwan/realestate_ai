import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import DashboardStats from '../../components/DashboardStats'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  FireIcon: (props: any) => <div data-testid="fire-icon" {...props} />,
  CalendarDaysIcon: (props: any) => <div data-testid="calendar-days-icon" {...props} />,
  BuildingOfficeIcon: (props: any) => <div data-testid="building-office-icon" {...props} />,
  SparklesIcon: (props: any) => <div data-testid="sparkles-icon" {...props} />,
  ChartBarIcon: (props: any) => <div data-testid="chart-bar-icon" {...props} />,
  DocumentTextIcon: (props: any) => <div data-testid="document-text-icon" {...props} />,
  PlusIcon: (props: any) => <div data-testid="plus-icon" {...props} />,
  EyeIcon: (props: any) => <div data-testid="eye-icon" {...props} />,
  UsersIcon: (props: any) => <div data-testid="users-icon" {...props} />,
  CurrencyDollarIcon: (props: any) => <div data-testid="currency-dollar-icon" {...props} />,
  ArrowUpIcon: (props: any) => <div data-testid="arrow-up-icon" {...props} />,
  ArrowDownIcon: (props: any) => <div data-testid="arrow-down-icon" {...props} />,
  CheckCircleIcon: (props: any) => <div data-testid="check-circle-icon" {...props} />,
  ClockIcon: (props: any) => <div data-testid="clock-icon" {...props} />,
}))

const mockStats = {
  total_properties: 25,
  active_listings: 42,
  total_views: 1250,
  revenue: 250000,
  properties_trend: 12,
  listings_trend: -5,
  views_trend: 8,
  revenue_trend: 15,
}

describe('DashboardStats Component - Simple Tests', () => {
  it('renders without crashing', () => {
    expect(() => render(<DashboardStats stats={mockStats} />)).not.toThrow()
  })

  it('displays greeting with emoji', () => {
    render(<DashboardStats stats={mockStats} />)
    
    expect(screen.getByText(/Good Morning! 🌅/)).toBeInTheDocument()
  })

  it('displays all stat values correctly', () => {
    render(<DashboardStats stats={mockStats} />)
    
    expect(screen.getByText('25')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('1,250')).toBeInTheDocument()
    expect(screen.getByText('₹2,50,000')).toBeInTheDocument()
  })

  it('displays stat labels', () => {
    render(<DashboardStats stats={mockStats} />)
    
    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(screen.getByText('Active Leads')).toBeInTheDocument()
    expect(screen.getByText('Total Views')).toBeInTheDocument()
    expect(screen.getByText('Revenue')).toBeInTheDocument()
  })

  it('displays action buttons with correct text', () => {
    render(<DashboardStats stats={mockStats} />)
    
    expect(screen.getByRole('button', { name: /Add new property listing/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Explore AI/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /View Analytics/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Try Demo/i })).toBeInTheDocument()
  })

  it('displays quick action titles', () => {
    render(<DashboardStats stats={mockStats} />)
    
    expect(screen.getByText('Add Properties')).toBeInTheDocument()
    expect(screen.getByText('AI Tools')).toBeInTheDocument()
    expect(screen.getByText('Analytics')).toBeInTheDocument()
    expect(screen.getByText('Smart Form Demo')).toBeInTheDocument()
  })
})