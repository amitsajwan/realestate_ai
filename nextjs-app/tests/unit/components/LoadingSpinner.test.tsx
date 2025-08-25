import React from 'react'
import { render, screen } from '@testing-library/react'
import LoadingSpinner from '@/components/LoadingSpinner'

describe('LoadingSpinner Component', () => {
  test('renders with default props', () => {
    render(<LoadingSpinner />)
    
    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveClass('flex', 'flex-col', 'items-center', 'justify-center')
  })

  test('renders with custom text', () => {
    const testText = 'Loading data...'
    render(<LoadingSpinner text={testText} />)
    
    expect(screen.getByText(testText)).toBeInTheDocument()
  })

  test('renders with different sizes', () => {
    const { rerender } = render(<LoadingSpinner size="sm" />)
    let spinner = screen.getByTestId('loading-spinner').querySelector('div')
    expect(spinner).toHaveClass('w-4', 'h-4')

    rerender(<LoadingSpinner size="md" />)
    spinner = screen.getByTestId('loading-spinner').querySelector('div')
    expect(spinner).toHaveClass('w-8', 'h-8')

    rerender(<LoadingSpinner size="lg" />)
    spinner = screen.getByTestId('loading-spinner').querySelector('div')
    expect(spinner).toHaveClass('w-12', 'h-12')
  })

  test('renders with different colors', () => {
    const { rerender } = render(<LoadingSpinner color="white" />)
    let spinner = screen.getByTestId('loading-spinner').querySelector('div')
    expect(spinner).toHaveClass('border-white', 'border-t-transparent')

    rerender(<LoadingSpinner color="primary" />)
    spinner = screen.getByTestId('loading-spinner').querySelector('div')
    expect(spinner).toHaveClass('border-primary-500', 'border-t-transparent')

    rerender(<LoadingSpinner color="secondary" />)
    spinner = screen.getByTestId('loading-spinner').querySelector('div')
    expect(spinner).toHaveClass('border-secondary-500', 'border-t-transparent')
  })

  test('applies custom className', () => {
    const customClass = 'custom-spinner-class'
    render(<LoadingSpinner className={customClass} />)
    
    const container = screen.getByTestId('loading-spinner')
    expect(container).toHaveClass(customClass)
  })

  test('renders without text when text prop is not provided', () => {
    render(<LoadingSpinner />)
    
    const textElement = screen.queryByText('Loading data...')
    expect(textElement).not.toBeInTheDocument()
  })

  test('has correct animation classes', () => {
    render(<LoadingSpinner />)
    
    const spinner = screen.getByTestId('loading-spinner').querySelector('div')
    expect(spinner).toHaveClass('animate-spin')
  })

  test('has correct border classes', () => {
    render(<LoadingSpinner />)
    
    const spinner = screen.getByTestId('loading-spinner').querySelector('div')
    expect(spinner).toHaveClass('border-4', 'rounded-full')
  })
})
