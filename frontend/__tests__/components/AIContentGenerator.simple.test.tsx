import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
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
  SparklesIcon: (props: any) => <div data-testid="sparkles-icon" {...props} />,
  ArrowLeftIcon: (props: any) => <div data-testid="arrow-left-icon" {...props} />,
}))

// Mock clipboard API
const mockWriteText = jest.fn().mockResolvedValue(undefined)
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: mockWriteText,
  },
  writable: true,
  configurable: true,
})

describe('AIContentGenerator Component - Simple Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockWriteText.mockClear()
  })

  it('renders the AI content generator with correct header', () => {
    render(<AIContentGenerator />)

    expect(screen.getByText('AI Content Generation')).toBeInTheDocument()
    expect(screen.getByText('Generate engaging content for your properties using AI assistance.')).toBeInTheDocument()
  })

  it('displays the form inputs correctly', () => {
    render(<AIContentGenerator />)

    expect(screen.getByText('Property Type')).toBeInTheDocument()
    expect(screen.getByText('Content Style')).toBeInTheDocument()
    expect(screen.getByText('Describe your property')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /generate content/i })).toBeInTheDocument()
  })

  it('shows the back to dashboard button', () => {
    render(<AIContentGenerator />)

    expect(screen.getByRole('button', { name: /back to dashboard/i })).toBeInTheDocument()
  })

  it('displays the generated content section', () => {
    render(<AIContentGenerator />)

    expect(screen.getByText('Generated Content')).toBeInTheDocument()
    expect(screen.getByText('Generated content will appear here after you click "Generate Content"')).toBeInTheDocument()
  })

  it('renders without crashing', () => {
    expect(() => render(<AIContentGenerator />)).not.toThrow()
  })
})