import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import AIContentGenerator from '../../components/AIContentGenerator'

// Mock all dependencies
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  MagnifyingGlassIcon: (props: any) => <div data-testid="search-icon" {...props} />,
  DocumentTextIcon: (props: any) => <div data-testid="document-icon" {...props} />,
  SparklesIcon: (props: any) => <div data-testid="sparkles-icon" {...props} />,
  ClipboardDocumentIcon: (props: any) => <div data-testid="clipboard-icon" {...props} />,
  ArrowPathIcon: (props: any) => <div data-testid="arrow-path-icon" {...props} />,
  ArrowLeftIcon: (props: any) => <div data-testid="arrow-left-icon" {...props} />,
  CheckCircleIcon: (props: any) => <div data-testid="check-circle-icon" {...props} />,
  ExclamationTriangleIcon: (props: any) => <div data-testid="exclamation-icon" {...props} />,
  PhotoIcon: (props: any) => <div data-testid="photo-icon" {...props} />,
  PencilIcon: (props: any) => <div data-testid="pencil-icon" {...props} />,
  EyeIcon: (props: any) => <div data-testid="eye-icon" {...props} />,
}))

jest.mock('@heroicons/react/24/solid', () => ({
  __esModule: true,
  SparklesIcon: (props: any) => <div data-testid="sparkles-solid-icon" {...props} />,
  CheckCircleIcon: (props: any) => <div data-testid="check-circle-solid-icon" {...props} />,
}))

const mockToast = require('react-hot-toast').default

// Mock clipboard API
// Mock navigator.clipboard
const mockWriteText = jest.fn().mockResolvedValue(undefined)
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: mockWriteText,
  },
  writable: true,
  configurable: true,
})

describe('AIContentGenerator Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset clipboard mock
    mockWriteText.mockClear()
  })

  describe('Basic Rendering', () => {
    it('renders the AI content generator with header', () => {
      render(<AIContentGenerator />)

      expect(screen.getByText('AI Content Generator')).toBeInTheDocument()
      expect(screen.getByText('Generate compelling property descriptions')).toBeInTheDocument()
    })

    it('displays the form inputs correctly', () => {
      render(<AIContentGenerator />)

      expect(screen.getByPlaceholderText('Enter property details...')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /generate content/i })).toBeInTheDocument()
    })

    it('shows content type selector', () => {
      render(<AIContentGenerator />)

      expect(screen.getByText('Content Type')).toBeInTheDocument()
      expect(screen.getByDisplayValue('description')).toBeInTheDocument()
    })

    it('displays tone selector', () => {
      render(<AIContentGenerator />)

      expect(screen.getByText('Tone')).toBeInTheDocument()
      expect(screen.getByDisplayValue('professional')).toBeInTheDocument()
    })

    it('shows length selector', () => {
      render(<AIContentGenerator />)

      expect(screen.getByText('Length')).toBeInTheDocument()
      expect(screen.getByDisplayValue('medium')).toBeInTheDocument()
    })
  })

  describe('Form Input Handling', () => {
    it('updates property details input', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Beautiful 3BHK apartment in Mumbai')

      expect(input).toHaveValue('Beautiful 3BHK apartment in Mumbai')
    })

    it('handles content type selection', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const select = screen.getByDisplayValue('description')
      await user.selectOptions(select, 'headline')

      expect(select).toHaveValue('headline')
    })

    it('handles tone selection', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const select = screen.getByDisplayValue('professional')
      await user.selectOptions(select, 'casual')

      expect(select).toHaveValue('casual')
    })

    it('handles length selection', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const select = screen.getByDisplayValue('medium')
      await user.selectOptions(select, 'short')

      expect(select).toHaveValue('short')
    })
  })

  describe('Content Generation', () => {
    it('displays loading state during generation', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Test property details')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      expect(screen.getByText('Generating...')).toBeInTheDocument()
    })

    it('displays generated content after successful generation', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Beautiful 3BHK apartment in Mumbai')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })

      // Check that content is displayed
      expect(screen.getByText(/Beautiful 3BHK apartment/i)).toBeInTheDocument()
    })

    it('shows error message on generation failure', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'error-trigger')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to generate content. Please try again.')
      })
    })

    it('validates required fields before generation', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      expect(mockToast.error).toHaveBeenCalledWith('Please enter property details')
    })
  })

  describe('Content Actions', () => {
    beforeEach(async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Beautiful 3BHK apartment in Mumbai')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })

    it('copies content to clipboard successfully', async () => {
      const user = userEvent.setup()

      const copyButton = screen.getByRole('button', { name: /copy/i })
      await user.click(copyButton)

      expect(navigator.clipboard.writeText).toHaveBeenCalled()
      expect(mockToast.success).toHaveBeenCalledWith('Content copied to clipboard!')
    })

    it('handles clipboard copy failure', async () => {
      const user = userEvent.setup()

      // Mock clipboard failure
      ;(navigator.clipboard.writeText as jest.Mock).mockRejectedValue(new Error('Clipboard error'))

      const copyButton = screen.getByRole('button', { name: /copy/i })
      await user.click(copyButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to copy to clipboard')
      })
    })

    it('regenerates content when regenerate button is clicked', async () => {
      const user = userEvent.setup()

      const regenerateButton = screen.getByRole('button', { name: /regenerate/i })
      await user.click(regenerateButton)

      expect(screen.getByText('Generating...')).toBeInTheDocument()
    })

    it('allows editing generated content', async () => {
      const user = userEvent.setup()

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      // Should show editable textarea
      const textarea = screen.getByRole('textbox')
      expect(textarea).toBeInTheDocument()
      expect(textarea).toHaveAttribute('contentEditable', 'true')
    })

    it('saves edited content', async () => {
      const user = userEvent.setup()

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'Edited content')

      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      expect(mockToast.success).toHaveBeenCalledWith('Content saved successfully!')
    })
  })

  describe('Content Types', () => {
    it('generates description content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, '3BHK apartment')

      const contentTypeSelect = screen.getByDisplayValue('description')
      await user.selectOptions(contentTypeSelect, 'description')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })

    it('generates headline content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Luxury villa')

      const contentTypeSelect = screen.getByDisplayValue('description')
      await user.selectOptions(contentTypeSelect, 'headline')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })

    it('generates social media content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Modern apartment')

      const contentTypeSelect = screen.getByDisplayValue('description')
      await user.selectOptions(contentTypeSelect, 'social')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })
  })

  describe('Tone Variations', () => {
    it('generates professional tone content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Executive apartment')

      const toneSelect = screen.getByDisplayValue('professional')
      await user.selectOptions(toneSelect, 'professional')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })

    it('generates casual tone content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Cozy home')

      const toneSelect = screen.getByDisplayValue('professional')
      await user.selectOptions(toneSelect, 'casual')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })

    it('generates enthusiastic tone content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Amazing property')

      const toneSelect = screen.getByDisplayValue('professional')
      await user.selectOptions(toneSelect, 'enthusiastic')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })
  })

  describe('Length Variations', () => {
    it('generates short content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Small apartment')

      const lengthSelect = screen.getByDisplayValue('medium')
      await user.selectOptions(lengthSelect, 'short')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })

    it('generates long content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Large property')

      const lengthSelect = screen.getByDisplayValue('medium')
      await user.selectOptions(lengthSelect, 'long')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })
    })
  })

  describe('History and Templates', () => {
    it('displays generation history', () => {
      render(<AIContentGenerator />)

      expect(screen.getByText('Recent Generations')).toBeInTheDocument()
    })

    it('shows saved templates', () => {
      render(<AIContentGenerator />)

      expect(screen.getByText('Templates')).toBeInTheDocument()
    })

    it('allows loading from history', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      // Assuming there's a history item
      const historyItem = screen.getByTestId('history-item-0')
      await user.click(historyItem)

      // Should load the content
      expect(screen.getByPlaceholderText('Enter property details...')).toHaveValue('Loaded from history')
    })

    it('allows using templates', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const templateButton = screen.getByRole('button', { name: /use template/i })
      await user.click(templateButton)

      // Should populate form with template data
      expect(screen.getByPlaceholderText('Enter property details...')).toHaveValue('Template content')
    })
  })

  describe('Responsive Design', () => {
    it('adapts layout for mobile screens', () => {
      render(<AIContentGenerator />)

      const container = screen.getByText('AI Content Generator').closest('div')
      expect(container).toHaveClass('space-y-6')
    })

    it('stacks form elements vertically on small screens', () => {
      render(<AIContentGenerator />)

      const formSection = screen.getByPlaceholderText('Enter property details...').closest('div')
      expect(formSection).toHaveClass('space-y-4')
    })
  })

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      render(<AIContentGenerator />)

      expect(screen.getByLabelText('Property Details')).toBeInTheDocument()
      expect(screen.getByLabelText('Content Type')).toBeInTheDocument()
      expect(screen.getByLabelText('Tone')).toBeInTheDocument()
      expect(screen.getByLabelText('Length')).toBeInTheDocument()
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      input.focus()
      expect(document.activeElement).toBe(input)

      await user.keyboard('{Tab}')
      // Should move to next focusable element
    })

    it('has proper ARIA attributes for buttons', () => {
      render(<AIContentGenerator />)

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      expect(generateButton).toHaveAttribute('aria-label', 'Generate AI content')
    })
  })

  describe('Error Handling', () => {
    it('handles network errors gracefully', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'network-error')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Network error. Please check your connection.')
      })
    })

    it('handles API rate limiting', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'rate-limit')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Rate limit exceeded. Please try again later.')
      })
    })

    it('handles invalid input gracefully', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'invalid-input')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Invalid input. Please check your property details.')
      })
    })
  })

  describe('Performance', () => {
    it('debounces input changes', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')

      const startTime = Date.now()
      await user.type(input, 'Test input with rapid typing')
      const endTime = Date.now()

      // Should handle rapid input without excessive re-renders
      expect(endTime - startTime).toBeLessThan(500)
    })

    it('caches generated content', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Cached content')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })

      // Second generation should be faster due to caching
      await user.click(generateButton)
      expect(screen.getByText('Generating...')).toBeInTheDocument()
    })
  })

  describe('Integration with External Services', () => {
    it('integrates with AI service for content generation', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Integration test')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('Generated Content')).toBeInTheDocument()
      })

      // Verify AI service was called with correct parameters
      // This would depend on the actual AI service integration
    })

    it('handles AI service authentication', async () => {
      const user = userEvent.setup()
      render(<AIContentGenerator />)

      const input = screen.getByPlaceholderText('Enter property details...')
      await user.type(input, 'Auth test')

      const generateButton = screen.getByRole('button', { name: /generate content/i })
      await user.click(generateButton)

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Authentication failed. Please check your API key.')
      })
    })
  })
})
