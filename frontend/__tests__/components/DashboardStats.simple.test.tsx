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
  UserGroupIcon: (props: any) => <div data-testid="user-group-icon" {...props} />,
  CurrencyRupeeIcon: (props: any) => <div data-testid="currency-rupee-icon" {...props} />,
  SparklesIcon: (props: any) => <div data-testid="sparkles-icon" {...props} />,
  ArrowTrendingUpIcon: (props: any) => <div data-testid="arrow-trending-up-icon" {...props} />,
  ArrowTrendingDownIcon: (props: any) => <div data-testid="arrow-trending-down-icon" {...props} />,
  ChartBarIcon: (props: any) => <div data-testid="chart-bar-icon" {...props} />,
  CalendarDaysIcon: (props: any) => <div data-testid="calendar-days-icon" {...props} />,
  BellIcon: (props: any) => <div data-testid="bell-icon" {...props} />,
  FireIcon: (props: any) => <div data-testid="fire-icon" {...props} />,
  HomeIcon: (props: any) => <div data-testid="home-icon" {...props} />,
}))

const mockStats = {
  total_properties: 25,
  active_listings: 42,
  total_views: 1250,
  total_leads: 18,
  total_users: 150,
  monthly_leads: 8,
  revenue: "250000",
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
    
    // Use getAllByText to handle multiple elements with same text
    expect(screen.getAllByText('25')).toHaveLength(2)
    expect(screen.getAllByText('1,250')).toHaveLength(2)
    expect(screen.getAllByText('250000')).toHaveLength(2)
    expect(screen.getAllByText('18')).toHaveLength(2)
  })

  it('displays stat labels', () => {
    render(<DashboardStats stats={mockStats} />)
    
    expect(screen.getByText('Total Properties')).toBeInTheDocument()
    expect(screen.getAllByText('Active Leads')).toHaveLength(2)
    expect(screen.getByText('Property Views')).toBeInTheDocument()
    expect(screen.getAllByText('Revenue')).toHaveLength(2)
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