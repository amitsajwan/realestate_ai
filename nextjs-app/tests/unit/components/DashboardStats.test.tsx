import React from 'react'
import { render, screen } from '@testing-library/react'
import DashboardStats from '@/components/DashboardStats'

const mockStats = {
  total_properties: 12,
  active_listings: 8,
  total_leads: 24,
  total_users: 5,
  total_views: 1247,
  monthly_leads: 8,
  revenue: '₹45,00,000'
}

describe('DashboardStats Component', () => {
  beforeEach(() => {
    render(<DashboardStats stats={mockStats} />)
  })

  test('renders welcome section with correct title', () => {
    expect(screen.getByText('🚀 Welcome to PropertyAI!')).toBeInTheDocument()
    expect(screen.getByText('Your AI-powered real estate assistant is ready to help you succeed!')).toBeInTheDocument()
  })

  test('displays setup progress with all 7 steps', () => {
    for (let i = 1; i <= 7; i++) {
      expect(screen.getByText(`Step ${i}`)).toBeInTheDocument()
    }
  })

  test('shows setup complete status', () => {
    expect(screen.getByText('Setup Complete!')).toBeInTheDocument()
  })

  test('displays all stat cards with correct values', () => {
    // Total Properties
    expect(screen.getByText('Total Properties')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()

    // Property Views
    expect(screen.getByText('Property Views')).toBeInTheDocument()
    expect(screen.getByText('1,247')).toBeInTheDocument()

    // Active Leads
    expect(screen.getByText('Active Leads')).toBeInTheDocument()
    expect(screen.getByText('24')).toBeInTheDocument()

    // Revenue
    expect(screen.getByText('Revenue')).toBeInTheDocument()
    expect(screen.getByText('₹45,00,000')).toBeInTheDocument()
  })

  test('displays quick action buttons', () => {
    expect(screen.getByText('Add Property')).toBeInTheDocument()
    expect(screen.getAllByText('AI Tools')).toHaveLength(2) // Both h3 and button
    expect(screen.getByText('View Analytics')).toBeInTheDocument()
  })

  test('renders quick action cards with descriptions', () => {
    expect(screen.getByText('Start listing your properties with AI assistance')).toBeInTheDocument()
    expect(screen.getByText('Use AI to generate content and insights')).toBeInTheDocument()
    expect(screen.getByText('Track your performance and growth')).toBeInTheDocument()
  })

  test('handles zero values correctly', () => {
    const zeroStats = {
      total_properties: 0,
      active_listings: 0,
      total_leads: 0,
      total_users: 0,
      total_views: 0,
      monthly_leads: 0,
      revenue: '₹0'
    }

    render(<DashboardStats stats={zeroStats} />)
    
    expect(screen.getAllByText('0')).toHaveLength(3) // Multiple stat cards with 0
    expect(screen.getByText('₹0')).toBeInTheDocument()
  })

  test('formats large numbers correctly', () => {
    const largeStats = {
      ...mockStats,
      total_views: 1234567,
      revenue: '₹1,23,45,678'
    }

    render(<DashboardStats stats={largeStats} />)
    
    expect(screen.getByText('1,234,567')).toBeInTheDocument()
    expect(screen.getByText('₹1,23,45,678')).toBeInTheDocument()
  })
})
