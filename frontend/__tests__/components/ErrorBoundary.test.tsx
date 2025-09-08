import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ErrorBoundary, useErrorHandler, withErrorBoundary } from '../../components/ErrorBoundary'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  ExclamationTriangleIcon: () => <div data-testid="exclamation-triangle-icon" />,
  ArrowPathIcon: () => <div data-testid="arrow-path-icon" />,
}))

// Mock window.location.reload
const mockReload = jest.fn()
// Simple mock for window.location.reload
(window.location as any).reload = mockReload;

// Component that throws an error for testing
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>No error</div>
}

// Component for testing useErrorHandler hook
const TestHookComponent = () => {
  const { error, handleError, clearError } = useErrorHandler()

  if (error) {
    return (
      <div>
        <div data-testid="error-message">Error: {error.message}</div>
        <button onClick={clearError} data-testid="clear-error">Clear Error</button>
      </div>
    )
  }

  return (
    <div>
      <div data-testid="no-error">No error</div>
      <button 
        onClick={() => handleError(new Error('Hook test error'))} 
        data-testid="trigger-error"
      >
        Trigger Error
      </button>
    </div>
  )
}

// Component for testing withErrorBoundary HOC
const TestComponent = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('HOC test error')
  }
  return <div data-testid="hoc-component">HOC Component</div>
}

const WrappedComponent = withErrorBoundary(TestComponent)

describe('ErrorBoundary', () => {
  // Suppress console.error for these tests
  const originalError = console.error
  beforeAll(() => {
    console.error = jest.fn()
  })

  afterAll(() => {
    console.error = originalError
  })

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('ErrorBoundary Component', () => {
    it('renders children when there is no error', () => {
      render(
        <ErrorBoundary>
          <div data-testid="child">Child component</div>
        </ErrorBoundary>
      )

      expect(screen.getByTestId('child')).toBeInTheDocument()
      expect(screen.getByText('Child component')).toBeInTheDocument()
    })

    it('renders error UI when child component throws', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
      expect(screen.getByText(/We encountered an unexpected error/)).toBeInTheDocument()
      expect(screen.getByTestId('exclamation-triangle-icon')).toBeInTheDocument()
    })

    it('renders custom fallback when provided', () => {
      const customFallback = <div data-testid="custom-fallback">Custom Error UI</div>

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument()
      expect(screen.getByText('Custom Error UI')).toBeInTheDocument()
      expect(screen.queryByText('Oops! Something went wrong')).not.toBeInTheDocument()
    })

    it('displays Try Again and Refresh Page buttons', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Refresh Page/i })).toBeInTheDocument()
      expect(screen.getByTestId('arrow-path-icon')).toBeInTheDocument()
    })

    it('handles Try Again button click', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Error should be displayed
      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()

      // Click Try Again
      fireEvent.click(screen.getByRole('button', { name: /Try Again/i }))

      // Re-render with no error
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Test Component')).toBeInTheDocument()
      expect(screen.queryByText('Oops! Something went wrong')).not.toBeInTheDocument()
    })

    it('handles Refresh Page button click', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      fireEvent.click(screen.getByRole('button', { name: /Refresh Page/i }))
      expect(mockReload).toHaveBeenCalledTimes(1)
    })

    it('logs error to console when error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('[ErrorBoundary] ErrorBoundary caught an error:'),
        expect.any(Error),
        expect.any(Object)
      )
    })

    it('updates state correctly when error occurs', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      // Initially no error
      expect(screen.getByText('Test Component')).toBeInTheDocument()

      // Trigger error
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Error UI should be displayed
      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
    })
  })

  describe('useErrorHandler Hook', () => {
    it('initially has no error', () => {
      render(<TestHookComponent />)
      
      expect(screen.getByTestId('no-error')).toBeInTheDocument()
      expect(screen.getByText('Test Component')).toBeInTheDocument()
    })

    it('handles error when triggered', () => {
      render(<TestHookComponent />)
      
      fireEvent.click(screen.getByTestId('trigger-error'))
      
      expect(screen.getByTestId('error-message')).toBeInTheDocument()
      expect(screen.getByText('Error: Hook test error')).toBeInTheDocument()
    })

    it('clears error when clearError is called', () => {
      render(<TestHookComponent />)
      
      // Trigger error
      fireEvent.click(screen.getByTestId('trigger-error'))
      expect(screen.getByText('Error: Hook test error')).toBeInTheDocument()
      
      // Clear error
      fireEvent.click(screen.getByTestId('clear-error'))
      expect(screen.getByTestId('no-error')).toBeInTheDocument()
      expect(screen.queryByTestId('error-message')).not.toBeInTheDocument()
    })

    it('logs error to console when handleError is called', () => {
      render(<TestHookComponent />)
      
      fireEvent.click(screen.getByTestId('trigger-error'))
      
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('[ErrorBoundary] Error caught by useErrorHandler:'),
        expect.any(Error)
      )
    })
  })

  describe('withErrorBoundary HOC', () => {
    it('renders wrapped component when no error', () => {
      render(<WrappedComponent shouldThrow={false} />)
      
      expect(screen.getByTestId('hoc-component')).toBeInTheDocument()
      expect(screen.getByText('HOC Component')).toBeInTheDocument()
    })

    it('renders error boundary when wrapped component throws', () => {
      render(<WrappedComponent shouldThrow={true} />)
      
      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
      expect(screen.queryByTestId('hoc-component')).not.toBeInTheDocument()
    })

    it('uses custom fallback when provided', () => {
      const CustomFallback = <div data-testid="hoc-fallback">HOC Custom Fallback</div>
      const WrappedWithFallback = withErrorBoundary(TestComponent, CustomFallback)
      
      render(<WrappedWithFallback shouldThrow={true} />)
      
      expect(screen.getByTestId('hoc-fallback')).toBeInTheDocument()
      expect(screen.getByText('HOC Custom Fallback')).toBeInTheDocument()
      expect(screen.queryByText('Oops! Something went wrong')).not.toBeInTheDocument()
    })

    it('passes props correctly to wrapped component', () => {
      const TestPropsComponent = ({ testProp }: { testProp: string; shouldThrow: boolean }) => (
        <div data-testid="props-test">{testProp}</div>
      )
      
      const WrappedPropsComponent = withErrorBoundary(TestPropsComponent)
      
      render(<WrappedPropsComponent testProp="test value" shouldThrow={false} />)
      
      expect(screen.getByTestId('props-test')).toBeInTheDocument()
      expect(screen.getByText('test value')).toBeInTheDocument()
    })
  })

  describe('Error Recovery', () => {
    it('can recover from error state', () => {
      let shouldThrow = true
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={shouldThrow} />
        </ErrorBoundary>
      )

      // Error state
      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()

      // Click Try Again
      fireEvent.click(screen.getByRole('button', { name: /Try Again/i }))

      // Re-render without error
      shouldThrow = false
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={shouldThrow} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Test Component')).toBeInTheDocument()
      expect(screen.queryByText('Oops! Something went wrong')).not.toBeInTheDocument()
    })
  })
})