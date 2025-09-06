import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import AIAssistantButton from '../../components/property/shared/AIAssistantButton'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    button: ({ children, onClick, ...props }: any) => (
      <button onClick={onClick} {...props}>
        {children}
      </button>
    ),
  },
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  SparklesIcon: ({ className }: any) => <div data-testid="sparkles-icon" className={className} />,
  LightBulbIcon: ({ className }: any) => <div data-testid="bulb-icon" className={className} />,
  CommandLineIcon: ({ className }: any) => <div data-testid="command-icon" className={className} />,
}))

describe('AIAssistantButton', () => {
  const mockOnGenerate = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockOnGenerate.mockResolvedValue(undefined)
  })

  describe('Auto-fill variant', () => {
    it('renders with correct text and icon', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      expect(screen.getByText('AI Auto-Fill')).toBeInTheDocument()
      expect(screen.getByTestId('sparkles-icon')).toBeInTheDocument()
    })

    it('shows loading text when loading', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="auto-fill"
        />
      )

      expect(screen.getByText('Filling...')).toBeInTheDocument()
    })

    it('applies correct gradient classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('from-purple-600', 'to-blue-600')
    })
  })

  describe('Suggestions variant', () => {
    it('renders with correct text and icon', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="suggestions"
        />
      )

      expect(screen.getByText('Get AI Suggestions')).toBeInTheDocument()
      expect(screen.getByTestId('bulb-icon')).toBeInTheDocument()
    })

    it('shows loading text when loading', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="suggestions"
        />
      )

      expect(screen.getByText('Generating...')).toBeInTheDocument()
    })

    it('applies correct gradient classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="suggestions"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('from-emerald-600', 'to-teal-600')
    })
  })

  describe('Generate variant', () => {
    it('renders with correct text and icon', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="generate"
        />
      )

      expect(screen.getByText('Generate Content')).toBeInTheDocument()
      expect(screen.getByTestId('sparkles-icon')).toBeInTheDocument()
    })

    it('shows loading text when loading', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="generate"
        />
      )

      expect(screen.getByText('Creating...')).toBeInTheDocument()
    })

    it('applies correct gradient classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="generate"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('from-violet-600', 'to-purple-600')
    })
  })

  describe('Insights variant', () => {
    it('renders with correct text and icon', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="insights"
        />
      )

      expect(screen.getByText('Market Insights')).toBeInTheDocument()
      expect(screen.getByTestId('bulb-icon')).toBeInTheDocument()
    })

    it('shows loading text when loading', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="insights"
        />
      )

      expect(screen.getByText('Analyzing...')).toBeInTheDocument()
    })

    it('applies correct gradient classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="insights"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('from-orange-600', 'to-red-600')
    })
  })

  describe('Size variants', () => {
    it('applies small size classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
          size="sm"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('px-3', 'py-2', 'text-sm')
    })

    it('applies medium size classes by default', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('px-4', 'py-3', 'text-base')
    })

    it('applies large size classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
          size="lg"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('px-6', 'py-4', 'text-lg')
    })
  })

  describe('Interaction handling', () => {
    it('calls onGenerate when clicked', async () => {
      const user = userEvent.setup()
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockOnGenerate).toHaveBeenCalledTimes(1)
    })

    it('does not call onGenerate when loading', async () => {
      const user = userEvent.setup()
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockOnGenerate).not.toHaveBeenCalled()
    })

    it('does not call onGenerate when disabled', async () => {
      const user = userEvent.setup()
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
          disabled={true}
        />
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockOnGenerate).not.toHaveBeenCalled()
    })

    it('handles async onGenerate function', async () => {
      const user = userEvent.setup()
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockOnGenerate).toHaveBeenCalledTimes(1)
      await waitFor(() => {
        expect(mockOnGenerate).toHaveBeenCalled()
      })
    })

    it('handles onGenerate errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      mockOnGenerate.mockRejectedValue(new Error('Generation failed'))

      const user = userEvent.setup()
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalled()
      })

      consoleSpy.mockRestore()
    })
  })

  describe('Loading states', () => {
    it('disables button when loading', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('shows loading cursor when loading', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('cursor-not-allowed')
    })

    it('applies loading opacity', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('opacity-75')
    })

    it('prevents multiple clicks during loading', async () => {
      const user = userEvent.setup()
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      await user.click(button)
      await user.click(button)
      await user.click(button)

      expect(mockOnGenerate).not.toHaveBeenCalled()
    })
  })

  describe('Disabled state', () => {
    it('applies disabled styling', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
          disabled={true}
        />
      )

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(button).toHaveClass('opacity-50', 'cursor-not-allowed')
    })

    it('does not apply hover effects when disabled', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
          disabled={true}
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:from-purple-700')
    })
  })

  describe('Custom children', () => {
    it('renders custom children when provided', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        >
          Custom Text
        </AIAssistantButton>
      )

      expect(screen.getByText('Custom Text')).toBeInTheDocument()
    })

    it('overrides default text with custom children', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        >
          <span>Custom Element</span>
        </AIAssistantButton>
      )

      expect(screen.getByText('Custom Element')).toBeInTheDocument()
      expect(screen.queryByText('AI Auto-Fill')).not.toBeInTheDocument()
    })
  })

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
          className="custom-class"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })

    it('combines custom className with default classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
          className="custom-class"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
      expect(button).toHaveClass('inline-flex', 'items-center')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes when loading', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={true}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-disabled', 'true')
    })

    it('has proper button role', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      button.focus()

      expect(document.activeElement).toBe(button)

      await user.keyboard('{Enter}')
      expect(mockOnGenerate).toHaveBeenCalledTimes(1)
    })

    it('supports space key activation', async () => {
      const user = userEvent.setup()
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      button.focus()

      await user.keyboard(' ')
      expect(mockOnGenerate).toHaveBeenCalledTimes(1)
    })
  })

  describe('Animation and styling', () => {
    it('applies hover gradient classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:from-purple-700', 'hover:to-blue-700')
    })

    it('applies focus styles', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('focus:ring-2', 'focus:ring-offset-2')
    })

    it('applies transition classes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('transition-all', 'duration-200')
    })

    it('applies rounded corners', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('rounded-lg')
    })

    it('applies shadow', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('shadow-md', 'hover:shadow-lg')
    })
  })

  describe('Icon positioning', () => {
    it('positions icon correctly with text', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
        />
      )

      const button = screen.getByRole('button')
      const icon = screen.getByTestId('sparkles-icon')

      expect(button).toHaveClass('gap-2')
      expect(icon).toHaveClass('w-5', 'h-5')
    })

    it('adjusts icon size for different button sizes', () => {
      render(
        <AIAssistantButton
          onGenerate={mockOnGenerate}
          isLoading={false}
          variant="auto-fill"
          size="lg"
        />
      )

      const icon = screen.getByTestId('sparkles-icon')
      expect(icon).toHaveClass('w-6', 'h-6')
    })
  })

  describe('Error handling', () => {
    it('handles undefined onGenerate prop', () => {
      expect(() => {
        render(
          <AIAssistantButton
            onGenerate={undefined as any}
            isLoading={false}
            variant="auto-fill"
          />
        )
      }).toThrow()
    })

    it('handles invalid variant prop', () => {
      expect(() => {
        render(
          <AIAssistantButton
            onGenerate={mockOnGenerate}
            isLoading={false}
            variant={'invalid' as any}
          />
        )
      }).toThrow()
    })
  })
})
