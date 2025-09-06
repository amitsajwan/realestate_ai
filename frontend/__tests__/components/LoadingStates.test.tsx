import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import {
  LoadingSpinner,
  LoadingButton,
  LoadingOverlay,
  LoadingCard,
  SkeletonLoader,
  LoadingStateWrapper,
  ProgressBar
} from '../../components/LoadingStates'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

describe('LoadingStates Components', () => {
  describe('LoadingSpinner', () => {
    it('renders with default size and color', () => {
      render(<LoadingSpinner />)

      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toBeInTheDocument()
      expect(spinner).toHaveClass('w-6', 'h-6', 'text-blue-600')
    })

    it('renders with small size', () => {
      render(<LoadingSpinner size="sm" />)

      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveClass('w-4', 'h-4')
    })

    it('renders with large size', () => {
      render(<LoadingSpinner size="lg" />)

      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveClass('w-8', 'h-8')
    })

    it('renders with secondary color', () => {
      render(<LoadingSpinner color="secondary" />)

      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveClass('text-gray-600')
    })

    it('renders with white color', () => {
      render(<LoadingSpinner color="white" />)

      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveClass('text-white')
    })

    it('applies custom className', () => {
      render(<LoadingSpinner className="custom-class" />)

      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveClass('custom-class')
    })

    it('contains SVG with proper structure', () => {
      render(<LoadingSpinner />)

      const svg = screen.getByTestId('loading-spinner').querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('viewBox', '0 0 24 24')
    })
  })

  describe('LoadingButton', () => {
    const mockOnClick = jest.fn()

    beforeEach(() => {
      mockOnClick.mockClear()
    })

    it('renders button with children', () => {
      render(<LoadingButton isLoading={false} onClick={mockOnClick}>Click me</LoadingButton>)

      expect(screen.getByText('Click me')).toBeInTheDocument()
    })

    it('shows loading spinner when isLoading is true', () => {
      render(<LoadingButton isLoading={true} onClick={mockOnClick}>Click me</LoadingButton>)

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })

    it('hides children when loading', () => {
      render(<LoadingButton isLoading={true} onClick={mockOnClick}>Click me</LoadingButton>)

      expect(screen.queryByText('Click me')).not.toBeInTheDocument()
    })

    it('disables button when loading', () => {
      render(<LoadingButton isLoading={true} onClick={mockOnClick}>Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('calls onClick when not loading', async () => {
      const user = userEvent.setup()
      render(<LoadingButton isLoading={false} onClick={mockOnClick}>Click me</LoadingButton>)

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockOnClick).toHaveBeenCalledTimes(1)
    })

    it('does not call onClick when loading', async () => {
      const user = userEvent.setup()
      render(<LoadingButton isLoading={true} onClick={mockOnClick}>Click me</LoadingButton>)

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockOnClick).not.toHaveBeenCalled()
    })

    it('applies primary variant styles', () => {
      render(<LoadingButton isLoading={false} variant="primary">Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-blue-600', 'hover:bg-blue-700')
    })

    it('applies secondary variant styles', () => {
      render(<LoadingButton isLoading={false} variant="secondary">Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-gray-600', 'hover:bg-gray-700')
    })

    it('applies outline variant styles', () => {
      render(<LoadingButton isLoading={false} variant="outline">Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('border-2', 'border-blue-600', 'text-blue-600')
    })

    it('applies small size styles', () => {
      render(<LoadingButton isLoading={false} size="sm">Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('px-3', 'py-1.5', 'text-sm')
    })

    it('applies large size styles', () => {
      render(<LoadingButton isLoading={false} size="lg">Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('px-6', 'py-3', 'text-lg')
    })

    it('applies custom className', () => {
      render(<LoadingButton isLoading={false} className="custom-class">Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })

    it('has proper ARIA attributes when loading', () => {
      render(<LoadingButton isLoading={true}>Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-label', 'Loading, please wait')
    })

    it('applies disabled styles when disabled', () => {
      render(<LoadingButton isLoading={false} disabled>Click me</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('cursor-not-allowed')
    })
  })

  describe('LoadingOverlay', () => {
    it('renders children when not loading', () => {
      render(
        <LoadingOverlay isLoading={false}>
          <div>Content</div>
        </LoadingOverlay>
      )

      expect(screen.getByText('Content')).toBeInTheDocument()
    })

    it('shows loading overlay when loading', () => {
      render(
        <LoadingOverlay isLoading={true}>
          <div>Content</div>
        </LoadingOverlay>
      )

      expect(screen.getByText('Content')).toBeInTheDocument()
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('uses custom message', () => {
      render(
        <LoadingOverlay isLoading={true} message="Custom loading...">
          <div>Content</div>
        </LoadingOverlay>
      )

      expect(screen.getByText('Custom loading...')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <LoadingOverlay isLoading={false} className="custom-class">
          <div>Content</div>
        </LoadingOverlay>
      )

      const container = screen.getByText('Content').parentElement
      expect(container).toHaveClass('custom-class')
    })

    it('has proper ARIA attributes', () => {
      render(
        <LoadingOverlay isLoading={true}>
          <div>Content</div>
        </LoadingOverlay>
      )

      const overlay = screen.getByRole('status')
      expect(overlay).toHaveAttribute('aria-live', 'polite')
      expect(overlay).toHaveAttribute('aria-label', 'Loading content')
    })
  })

  describe('LoadingCard', () => {
    it('renders with default message', () => {
      render(<LoadingCard />)

      expect(screen.getByText('Loading...')).toBeInTheDocument()
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })

    it('renders with custom message', () => {
      render(<LoadingCard message="Custom loading..." />)

      expect(screen.getByText('Custom loading...')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(<LoadingCard className="custom-class" />)

      const card = screen.getByText('Loading...').parentElement
      expect(card).toHaveClass('custom-class')
    })

    it('has proper ARIA attributes', () => {
      render(<LoadingCard />)

      const card = screen.getByRole('status')
      expect(card).toHaveAttribute('aria-live', 'polite')
      expect(card).toHaveAttribute('aria-label', 'Loading content')
    })

    it('has proper styling', () => {
      render(<LoadingCard />)

      const card = screen.getByText('Loading...').parentElement
      expect(card).toHaveClass('bg-white', 'rounded-lg', 'shadow-md', 'p-6')
    })
  })

  describe('SkeletonLoader', () => {
    it('renders with default 3 lines', () => {
      render(<SkeletonLoader />)

      const skeletonLines = screen.getAllByTestId('skeleton-line')
      expect(skeletonLines).toHaveLength(3)
    })

    it('renders with custom number of lines', () => {
      render(<SkeletonLoader lines={5} />)

      const skeletonLines = screen.getAllByTestId('skeleton-line')
      expect(skeletonLines).toHaveLength(5)
    })

    it('applies custom className', () => {
      render(<SkeletonLoader className="custom-class" />)

      const container = screen.getByTestId('skeleton-container')
      expect(container).toHaveClass('custom-class')
    })

    it('has proper skeleton styling', () => {
      render(<SkeletonLoader />)

      const skeletonLines = screen.getAllByTestId('skeleton-line')
      skeletonLines.forEach(line => {
        expect(line).toHaveClass('animate-pulse', 'bg-gray-300', 'rounded')
      })
    })

    it('has proper layout structure', () => {
      render(<SkeletonLoader />)

      const container = screen.getByTestId('skeleton-container')
      expect(container).toHaveClass('animate-pulse', 'space-y-3')
    })
  })

  describe('LoadingStateWrapper', () => {
    const mockLoadingState = {
      isLoading: false,
      error: null,
      success: null,
    }

    it('renders children when not loading and no error', () => {
      render(
        <LoadingStateWrapper loadingState={mockLoadingState}>
          <div>Content</div>
        </LoadingStateWrapper>
      )

      expect(screen.getByText('Content')).toBeInTheDocument()
    })

    it('renders loading component when loading', () => {
      const loadingState = { ...mockLoadingState, isLoading: true }

      render(
        <LoadingStateWrapper loadingState={loadingState}>
          <div>Content</div>
        </LoadingStateWrapper>
      )

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })

    it('renders custom loading component', () => {
      const loadingState = { ...mockLoadingState, isLoading: true }
      const customLoading = <div>Custom Loading</div>

      render(
        <LoadingStateWrapper loadingState={loadingState} loadingComponent={customLoading}>
          <div>Content</div>
        </LoadingStateWrapper>
      )

      expect(screen.getByText('Custom Loading')).toBeInTheDocument()
    })

    it('renders error component when error exists', () => {
      const loadingState = { ...mockLoadingState, error: 'Test error' }

      render(
        <LoadingStateWrapper loadingState={loadingState}>
          <div>Content</div>
        </LoadingStateWrapper>
      )

      expect(screen.getByText('Test error')).toBeInTheDocument()
    })

    it('renders custom error component', () => {
      const loadingState = { ...mockLoadingState, error: 'Test error' }
      const customError = <div>Custom Error</div>

      render(
        <LoadingStateWrapper loadingState={loadingState} errorComponent={customError}>
          <div>Content</div>
        </LoadingStateWrapper>
      )

      expect(screen.getByText('Custom Error')).toBeInTheDocument()
    })

    it('renders success component when success exists', () => {
      const loadingState = { ...mockLoadingState, success: 'Success!' }

      render(
        <LoadingStateWrapper loadingState={loadingState}>
          <div>Content</div>
        </LoadingStateWrapper>
      )

      expect(screen.getByText('Success!')).toBeInTheDocument()
      expect(screen.getByText('Content')).toBeInTheDocument()
    })

    it('renders custom success component', () => {
      const loadingState = { ...mockLoadingState, success: 'Success!' }
      const customSuccess = <div>Custom Success</div>

      render(
        <LoadingStateWrapper loadingState={loadingState} successComponent={customSuccess}>
          <div>Content</div>
        </LoadingStateWrapper>
      )

      expect(screen.getByText('Custom Success')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <LoadingStateWrapper loadingState={mockLoadingState} className="custom-class">
          <div>Content</div>
        </LoadingStateWrapper>
      )

      const container = screen.getByText('Content').parentElement
      expect(container).toHaveClass('custom-class')
    })
  })

  describe('ProgressBar', () => {
    it('renders with default props', () => {
      render(<ProgressBar progress={50} />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveStyle({ width: '50%' })
    })

    it('renders with 0 progress', () => {
      render(<ProgressBar progress={0} />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveStyle({ width: '0%' })
    })

    it('renders with 100 progress', () => {
      render(<ProgressBar progress={100} />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveStyle({ width: '100%' })
    })

    it('clamps progress to 0-100 range', () => {
      render(<ProgressBar progress={150} />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveStyle({ width: '100%' })
    })

    it('shows percentage by default', () => {
      render(<ProgressBar progress={75} />)

      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('hides percentage when showPercentage is false', () => {
      render(<ProgressBar progress={75} showPercentage={false} />)

      expect(screen.queryByText('75%')).not.toBeInTheDocument()
    })

    it('applies primary color by default', () => {
      render(<ProgressBar progress={50} />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveClass('bg-blue-600')
    })

    it('applies secondary color', () => {
      render(<ProgressBar progress={50} color="secondary" />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveClass('bg-gray-600')
    })

    it('applies success color', () => {
      render(<ProgressBar progress={50} color="success" />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveClass('bg-green-600')
    })

    it('applies warning color', () => {
      render(<ProgressBar progress={50} color="warning" />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveClass('bg-yellow-600')
    })

    it('applies danger color', () => {
      render(<ProgressBar progress={50} color="danger" />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveClass('bg-red-600')
    })

    it('applies small size', () => {
      render(<ProgressBar progress={50} size="sm" />)

      const container = screen.getByTestId('progress-bar-container')
      expect(container).toHaveClass('h-1')
    })

    it('applies medium size by default', () => {
      render(<ProgressBar progress={50} />)

      const container = screen.getByTestId('progress-bar-container')
      expect(container).toHaveClass('h-2')
    })

    it('applies large size', () => {
      render(<ProgressBar progress={50} size="lg" />)

      const container = screen.getByTestId('progress-bar-container')
      expect(container).toHaveClass('h-3')
    })

    it('applies custom className', () => {
      render(<ProgressBar progress={50} className="custom-class" />)

      const container = screen.getByTestId('progress-bar-container').parentElement
      expect(container).toHaveClass('custom-class')
    })

    it('has proper accessibility structure', () => {
      render(<ProgressBar progress={50} />)

      const container = screen.getByTestId('progress-bar-container')
      expect(container).toHaveAttribute('role', 'progressbar')
      expect(container).toHaveAttribute('aria-valuenow', '50')
      expect(container).toHaveAttribute('aria-valuemin', '0')
      expect(container).toHaveAttribute('aria-valuemax', '100')
    })

    it('shows percentage labels', () => {
      render(<ProgressBar progress={25} />)

      expect(screen.getByText('0%')).toBeInTheDocument()
      expect(screen.getByText('25%')).toBeInTheDocument()
      expect(screen.getByText('100%')).toBeInTheDocument()
    })
  })

  describe('Integration Tests', () => {
    it('LoadingButton integrates with LoadingOverlay', () => {
      const mockOnClick = jest.fn()

      render(
        <LoadingOverlay isLoading={true}>
          <LoadingButton isLoading={true} onClick={mockOnClick}>
            Test Button
          </LoadingButton>
        </LoadingOverlay>
      )

      expect(screen.getAllByTestId('loading-spinner')).toHaveLength(2)
    })

    it('ProgressBar handles decimal values', () => {
      render(<ProgressBar progress={33.7} />)

      const progressBar = screen.getByTestId('progress-bar-fill')
      expect(progressBar).toHaveStyle({ width: '33.7%' })
      expect(screen.getByText('34%')).toBeInTheDocument()
    })

    it('SkeletonLoader works with different line counts', () => {
      render(<SkeletonLoader lines={1} />)

      const skeletonLines = screen.getAllByTestId('skeleton-line')
      expect(skeletonLines).toHaveLength(1)
    })
  })

  describe('Performance', () => {
    it('ProgressBar handles rapid updates', () => {
      const { rerender } = render(<ProgressBar progress={0} />)

      for (let i = 0; i <= 100; i += 10) {
        rerender(<ProgressBar progress={i} />)
        const progressBar = screen.getByTestId('progress-bar-fill')
        expect(progressBar).toHaveStyle({ width: `${i}%` })
      }
    })

    it('LoadingSpinner renders efficiently', () => {
      const startTime = Date.now()

      render(<LoadingSpinner />)

      const endTime = Date.now()
      expect(endTime - startTime).toBeLessThan(50)
    })
  })

  describe('Accessibility', () => {
    it('all loading components have proper ARIA attributes', () => {
      render(
        <>
          <LoadingOverlay isLoading={true}><div>Content</div></LoadingOverlay>
          <LoadingCard />
          <ProgressBar progress={50} />
        </>
      )

      expect(screen.getAllByRole('status')).toHaveLength(2)
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })

    it('LoadingButton provides loading feedback', () => {
      render(<LoadingButton isLoading={true}>Test</LoadingButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-label', 'Loading, please wait')
    })

    it('ProgressBar has complete ARIA implementation', () => {
      render(<ProgressBar progress={75} />)

      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '75')
      expect(progressBar).toHaveAttribute('aria-valuemin', '0')
      expect(progressBar).toHaveAttribute('aria-valuemax', '100')
    })
  })
})
