import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import PropertyFieldInput from '../../components/property/shared/PropertyFieldInput'

// Mock Heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  ExclamationCircleIcon: ({ className }: any) => <div data-testid="error-icon" className={className} />,
  HomeIcon: ({ className }: any) => <div data-testid="home-icon" className={className} />,
}))

describe('PropertyFieldInput', () => {
  const mockRegister = jest.fn()
  const mockErrors = {}

  const defaultProps = {
    name: 'title' as const,
    label: 'Property Title',
    register: mockRegister,
    errors: mockErrors,
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders text input by default', () => {
    render(<PropertyFieldInput {...defaultProps} />)

    const input = screen.getByLabelText('Property Title')
    expect(input).toBeInTheDocument()
    expect(input.tagName).toBe('INPUT')
    expect(input).toHaveAttribute('type', 'text')
  })

  it('renders number input', () => {
    render(<PropertyFieldInput {...defaultProps} type="number" />)

    const input = screen.getByLabelText('Property Title')
    expect(input).toHaveAttribute('type', 'number')
  })

  it('renders textarea', () => {
    render(<PropertyFieldInput {...defaultProps} type="textarea" />)

    const textarea = screen.getByLabelText('Property Title')
    expect(textarea.tagName).toBe('TEXTAREA')
  })

  it('renders select with options', () => {
    const options = [
      { value: 'apartment', label: 'Apartment' },
      { value: 'house', label: 'House' },
    ]

    render(
      <PropertyFieldInput
        {...defaultProps}
        type="select"
        options={options}
      />
    )

    const select = screen.getByLabelText('Property Title')
    expect(select.tagName).toBe('SELECT')

    expect(screen.getByText('Apartment')).toBeInTheDocument()
    expect(screen.getByText('House')).toBeInTheDocument()
  })

  it('displays placeholder text', () => {
    render(<PropertyFieldInput {...defaultProps} placeholder="Enter title..." />)

    const input = screen.getByPlaceholderText('Enter title...')
    expect(input).toBeInTheDocument()
  })

  it('shows required indicator when required', () => {
    render(<PropertyFieldInput {...defaultProps} required />)

    expect(screen.getByText('*')).toBeInTheDocument()
  })

  it('displays help text', () => {
    render(<PropertyFieldInput {...defaultProps} helpText="This is help text" />)

    expect(screen.getByText('This is help text')).toBeInTheDocument()
  })

  it('renders icon when provided', () => {
    const HomeIcon = ({ className }: any) => <div data-testid="home-icon" className={className} />

    render(<PropertyFieldInput {...defaultProps} icon={HomeIcon} />)

    expect(screen.getByTestId('home-icon')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<PropertyFieldInput {...defaultProps} className="custom-class" />)

    const container = screen.getByText('Property Title').parentElement
    expect(container).toHaveClass('custom-class')
  })

  describe('Error handling', () => {
    it('displays error message', () => {
      const errorsWithMessage = {
        title: { message: 'Title is required' },
      }

      render(<PropertyFieldInput {...defaultProps} errors={errorsWithMessage} />)

      expect(screen.getByText('Title is required')).toBeInTheDocument()
    })

    it('shows error icon when there is an error', () => {
      const errorsWithMessage = {
        title: { type: 'required', message: 'Title is required' },
      }

      render(<PropertyFieldInput {...defaultProps} errors={errorsWithMessage} />)

      expect(screen.getByTestId('error-icon')).toBeInTheDocument()
    })

    it('applies error styling to input', () => {
      const errorsWithMessage = {
        title: { type: 'required', message: 'Title is required' },
      }

      render(<PropertyFieldInput {...defaultProps} errors={errorsWithMessage} />)

      const input = screen.getByLabelText('Property Title')
      expect(input).toHaveClass('border-red-300')
      expect(input).toHaveClass('bg-red-50')
    })

    it('does not show error when no error exists', () => {
      render(<PropertyFieldInput {...defaultProps} />)

      expect(screen.queryByTestId('error-icon')).not.toBeInTheDocument()
      expect(screen.queryByText('Title is required')).not.toBeInTheDocument()
    })
  })

  describe('Form registration', () => {
    it('calls register with correct field name', () => {
      render(<PropertyFieldInput {...defaultProps} />)

      expect(mockRegister).toHaveBeenCalledWith('title')
    })

    it('passes register props to input', () => {
      const mockRegisterReturn = { onChange: jest.fn(), onBlur: jest.fn() }
      mockRegister.mockReturnValue(mockRegisterReturn)

      render(<PropertyFieldInput {...defaultProps} />)

      const input = screen.getByLabelText('Property Title')
      expect(input).toHaveAttribute('onChange')
      expect(input).toHaveAttribute('onBlur')
    })
  })

  describe('User interactions', () => {
    it('handles text input', async () => {
      const user = userEvent.setup()
      render(<PropertyFieldInput {...defaultProps} />)

      const input = screen.getByLabelText('Property Title')
      await user.type(input, 'Test Property')

      expect(input).toHaveValue('Test Property')
    })

    it('handles number input', async () => {
      const user = userEvent.setup()
      render(<PropertyFieldInput {...defaultProps} type="number" />)

      const input = screen.getByLabelText('Property Title')
      await user.type(input, '123')

      expect(input).toHaveValue(123)
    })

    it('handles select change', async () => {
      const user = userEvent.setup()
      const options = [
        { value: 'apartment', label: 'Apartment' },
        { value: 'house', label: 'House' },
      ]

      render(
        <PropertyFieldInput
          {...defaultProps}
          type="select"
          options={options}
        />
      )

      const select = screen.getByLabelText('Property Title')
      await user.selectOptions(select, 'house')

      expect(select).toHaveValue('house')
    })

    it('handles textarea input', async () => {
      const user = userEvent.setup()
      render(<PropertyFieldInput {...defaultProps} type="textarea" />)

      const textarea = screen.getByLabelText('Property Title')
      await user.type(textarea, 'Long description text')

      expect(textarea).toHaveValue('Long description text')
    })
  })

  describe('Accessibility', () => {
    it('has proper label association', () => {
      render(<PropertyFieldInput {...defaultProps} />)

      const input = screen.getByLabelText('Property Title')
      const label = screen.getByText('Property Title')

      expect(input).toHaveAttribute('id')
      expect(label).toHaveAttribute('for')
    })

    it('has proper ARIA attributes for errors', () => {
      const errorsWithMessage = {
        title: { type: 'required', message: 'Title is required' },
      }

      render(<PropertyFieldInput {...defaultProps} errors={errorsWithMessage} />)

      const input = screen.getByLabelText('Property Title')
      expect(input).toHaveAttribute('aria-invalid', 'true')
      expect(input).toHaveAttribute('aria-describedby')
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<PropertyFieldInput {...defaultProps} />)

      const input = screen.getByLabelText('Property Title')
      input.focus()

      expect(document.activeElement).toBe(input)

      await user.keyboard('{Tab}')
      // Should move to next focusable element
    })

    it('has proper form structure', () => {
      render(<PropertyFieldInput {...defaultProps} />)

      const formGroup = screen.getByText('Property Title').parentElement
      expect(formGroup).toHaveClass('space-y-2')
    })
  })

  describe('Styling and layout', () => {
    it('applies base input styling', () => {
      render(<PropertyFieldInput {...defaultProps} />)

      const input = screen.getByLabelText('Property Title')
      expect(input).toHaveClass('w-full', 'px-4', 'py-3', 'rounded-xl')
    })

    it('applies focus styling', () => {
      render(<PropertyFieldInput {...defaultProps} />)

      const input = screen.getByLabelText('Property Title')
      expect(input).toHaveClass('focus:ring-2', 'focus:ring-blue-500')
    })

    it('adjusts padding when icon is present', () => {
      const HomeIcon = ({ className }: any) => <div data-testid="home-icon" className={className} />

      render(<PropertyFieldInput {...defaultProps} icon={HomeIcon} />)

      const input = screen.getByLabelText('Property Title')
      expect(input).toHaveClass('pl-12')
    })

    it('applies textarea specific styling', () => {
      render(<PropertyFieldInput {...defaultProps} type="textarea" />)

      const textarea = screen.getByLabelText('Property Title')
      expect(textarea).toHaveClass('resize-vertical', 'min-h-[100px]')
    })

    it('applies select specific styling', () => {
      const options = [{ value: 'test', label: 'Test' }]

      render(
        <PropertyFieldInput
          {...defaultProps}
          type="select"
          options={options}
        />
      )

      const select = screen.getByLabelText('Property Title')
      expect(select).toHaveClass('appearance-none', 'bg-no-repeat')
    })
  })

  describe('Edge cases', () => {
    it('handles empty options array', () => {
      render(
        <PropertyFieldInput
          {...defaultProps}
          type="select"
          options={[]}
        />
      )

      const select = screen.getByLabelText('Property Title')
      expect(select).toBeInTheDocument()
    })

    it('handles undefined options', () => {
      render(<PropertyFieldInput {...defaultProps} type="select" />)

      const select = screen.getByLabelText('Property Title')
      expect(select).toBeInTheDocument()
    })

    it('handles empty help text', () => {
      render(<PropertyFieldInput {...defaultProps} helpText="" />)

      expect(screen.queryByText('')).not.toBeInTheDocument()
    })

    it('handles long error messages', () => {
      const longError = 'This is a very long error message that should still be displayed properly in the UI without breaking the layout or causing overflow issues'
      const errorsWithLongMessage = {
        title: { type: 'required', message: longError },
      }

      render(<PropertyFieldInput {...defaultProps} errors={errorsWithLongMessage} />)

      expect(screen.getByText(longError)).toBeInTheDocument()
    })

    it('handles special characters in labels', () => {
      render(<PropertyFieldInput {...defaultProps} label="Property Title (Required)" />)

      expect(screen.getByText('Property Title (Required)')).toBeInTheDocument()
    })
  })

  describe('Integration with form libraries', () => {
    it('works with react-hook-form register function', () => {
      const mockRegisterReturn = {
        onChange: jest.fn(),
        onBlur: jest.fn(),
        name: 'title',
        ref: jest.fn(),
      }
      mockRegister.mockReturnValue(mockRegisterReturn)

      render(<PropertyFieldInput {...defaultProps} />)

      const input = screen.getByLabelText('Property Title')
      expect(input).toHaveAttribute('name', 'title')
    })

    it('handles form validation states', () => {
      const errorsWithValidation = {
        title: {
          message: 'Title is required',
          type: 'required',
        },
      }

      render(<PropertyFieldInput {...defaultProps} errors={errorsWithValidation} />)

      expect(screen.getByText('Title is required')).toBeInTheDocument()
    })
  })
})
