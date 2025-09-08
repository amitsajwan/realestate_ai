import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ErrorBoundary } from '../../components/ErrorBoundary'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  ExclamationTriangleIcon: (props: any) => <div data-testid="exclamation-triangle-icon" {...props} />,
  ArrowPathIcon: (props: any) => <div data-testid="arrow-path-icon" {...props} />,
}))

// Mock logger
jest.mock('../../lib/logger', () => ({
  logger: {
    error: jest.fn(),
  },
}))

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error
beforeAll(() => {
  console.error = jest.fn()
})

afterAll(() => {
  console.error = originalConsoleError
})

// Component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>No error</div>
}

describe('ErrorBoundary Component - Simple Tests', () => {
  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('No error')).toBeInTheDocument()
  })

  it('renders error UI when child component throws', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
    expect(screen.getByText(/We encountered an unexpected error/)).toBeInTheDocument()
  })

  it('displays Try Again and Refresh Page buttons when error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /refresh page/i })).toBeInTheDocument()
  })

  it('renders without crashing', () => {
    expect(() => render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    )).not.toThrow()
  })
})