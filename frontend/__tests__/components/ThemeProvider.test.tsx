import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ThemeProvider from '../../components/ThemeProvider'

// Mock the theme utility
jest.mock('@/lib/theme', () => ({
  initializeBrandTheme: jest.fn(),
}))

const mockInitializeBrandTheme = require('@/lib/theme').initializeBrandTheme

describe('ThemeProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders children correctly', () => {
    render(
      <ThemeProvider>
        <div>Test Child</div>
      </ThemeProvider>
    )

    expect(screen.getByText('Test Child')).toBeInTheDocument()
  })

  it('calls initializeBrandTheme on mount', () => {
    render(
      <ThemeProvider>
        <div>Test Child</div>
      </ThemeProvider>
    )

    expect(mockInitializeBrandTheme).toHaveBeenCalledTimes(1)
  })

  it('only calls initializeBrandTheme once', () => {
    const { rerender } = render(
      <ThemeProvider>
        <div>Test Child</div>
      </ThemeProvider>
    )

    rerender(
      <ThemeProvider>
        <div>Test Child Updated</div>
      </ThemeProvider>
    )

    expect(mockInitializeBrandTheme).toHaveBeenCalledTimes(1)
  })

  it('handles multiple children', () => {
    render(
      <ThemeProvider>
        <div>First Child</div>
        <div>Second Child</div>
        <span>Third Child</span>
      </ThemeProvider>
    )

    expect(screen.getByText('First Child')).toBeInTheDocument()
    expect(screen.getByText('Second Child')).toBeInTheDocument()
    expect(screen.getByText('Third Child')).toBeInTheDocument()
  })

  it('renders complex component trees', () => {
    render(
      <ThemeProvider>
        <header>
          <h1>App Title</h1>
          <nav>
            <ul>
              <li>Home</li>
              <li>About</li>
            </ul>
          </nav>
        </header>
        <main>
          <p>Main content</p>
        </main>
      </ThemeProvider>
    )

    expect(screen.getByText('App Title')).toBeInTheDocument()
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Main content')).toBeInTheDocument()
  })

  it('works with empty children', () => {
    render(<ThemeProvider>{null}</ThemeProvider>)

    expect(mockInitializeBrandTheme).toHaveBeenCalledTimes(1)
  })

  it('handles theme initialization errors gracefully', () => {
    mockInitializeBrandTheme.mockImplementation(() => {
      throw new Error('Theme initialization failed')
    })

    // Should not crash the component
    expect(() => {
      render(
        <ThemeProvider>
          <div>Test Child</div>
        </ThemeProvider>
      )
    }).not.toThrow()

    expect(screen.getByText('Test Child')).toBeInTheDocument()
  })

  it('maintains children rendering when theme init fails', () => {
    mockInitializeBrandTheme.mockImplementation(() => {
      throw new Error('Theme initialization failed')
    })

    render(
      <ThemeProvider>
        <div>Child 1</div>
        <div>Child 2</div>
      </ThemeProvider>
    )

    expect(screen.getByText('Child 1')).toBeInTheDocument()
    expect(screen.getByText('Child 2')).toBeInTheDocument()
  })

  it('logs theme initialization', () => {
    const consoleSpy = jest.spyOn(console, 'info').mockImplementation()

    render(
      <ThemeProvider>
        <div>Test Child</div>
      </ThemeProvider>
    )

    expect(consoleSpy).toHaveBeenCalledWith('[ThemeProvider] Initializing brand theme...')

    consoleSpy.mockRestore()
  })

  it('handles async theme initialization', async () => {
    mockInitializeBrandTheme.mockResolvedValue(undefined)

    render(
      <ThemeProvider>
        <div>Test Child</div>
      </ThemeProvider>
    )

    expect(screen.getByText('Test Child')).toBeInTheDocument()
    expect(mockInitializeBrandTheme).toHaveBeenCalledTimes(1)
  })

  it('preserves component props and state', () => {
    let renderCount = 0

    function TestComponent() {
      renderCount++
      return <div>Rendered {renderCount} times</div>
    }

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    expect(screen.getByText('Rendered 1 times')).toBeInTheDocument()
  })

  it('works with React fragments', () => {
    render(
      <ThemeProvider>
        <>
          <div>First</div>
          <div>Second</div>
        </>
      </ThemeProvider>
    )

    expect(screen.getByText('First')).toBeInTheDocument()
    expect(screen.getByText('Second')).toBeInTheDocument()
  })

  it('handles nested ThemeProviders', () => {
    render(
      <ThemeProvider>
        <ThemeProvider>
          <div>Nested Child</div>
        </ThemeProvider>
      </ThemeProvider>
    )

    expect(screen.getByText('Nested Child')).toBeInTheDocument()
    expect(mockInitializeBrandTheme).toHaveBeenCalledTimes(2)
  })

  it('maintains theme context for child components', () => {
    // This test assumes the theme context is properly set up
    render(
      <ThemeProvider>
        <div data-testid="themed-child">Themed Content</div>
      </ThemeProvider>
    )

    const themedChild = screen.getByTestId('themed-child')
    expect(themedChild).toBeInTheDocument()
  })

  it('handles component unmounting', () => {
    const { unmount } = render(
      <ThemeProvider>
        <div>Test Child</div>
      </ThemeProvider>
    )

    expect(screen.getByText('Test Child')).toBeInTheDocument()

    unmount()

    // Component should unmount without errors
    expect(screen.queryByText('Test Child')).not.toBeInTheDocument()
  })

  it('initializes theme only on first render', () => {
    const { rerender } = render(
      <ThemeProvider>
        <div>Initial</div>
      </ThemeProvider>
    )

    expect(mockInitializeBrandTheme).toHaveBeenCalledTimes(1)

    rerender(
      <ThemeProvider>
        <div>Updated</div>
      </ThemeProvider>
    )

    expect(mockInitializeBrandTheme).toHaveBeenCalledTimes(1)
    expect(screen.getByText('Updated')).toBeInTheDocument()
  })

  it('works with different child types', () => {
    render(
      <ThemeProvider>
        <div>String child</div>
        {42}
        {true && <span>Conditional child</span>}
        {null}
        {undefined}
      </ThemeProvider>
    )

    expect(screen.getByText('String child')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('Conditional child')).toBeInTheDocument()
  })
})
