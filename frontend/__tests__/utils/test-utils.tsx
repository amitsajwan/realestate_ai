import React from 'react'
import { render, screen, waitFor, RenderOptions } from '@testing-library/react'
import ThemeProvider from '../../components/ThemeProvider'

// Mock heroicons - common icons used across components
export const mockHeroicons = () => {
  jest.mock('@heroicons/react/24/outline', () => ({
    __esModule: true,
    BuildingOfficeIcon: (props: any) => <div data-testid="building-icon" {...props} />,
    MapPinIcon: (props: any) => <div data-testid="map-pin-icon" {...props} />,
    CurrencyRupeeIcon: (props: any) => <div data-testid="currency-icon" {...props} />,
    EyeIcon: (props: any) => <div data-testid="eye-icon" {...props} />,
    PencilIcon: (props: any) => <div data-testid="pencil-icon" {...props} />,
    TrashIcon: (props: any) => <div data-testid="trash-icon" {...props} />,
    PlusIcon: (props: any) => <div data-testid="plus-icon" {...props} />,
    MagnifyingGlassIcon: (props: any) => <div data-testid="search-icon" {...props} />,
    FunnelIcon: (props: any) => <div data-testid="funnel-icon" {...props} />,
    XMarkIcon: (props: any) => <div data-testid="x-mark-icon" {...props} />,
    HeartIcon: (props: any) => <div data-testid="heart-icon" {...props} />,
    ShareIcon: (props: any) => <div data-testid="share-icon" {...props} />,
    AdjustmentsHorizontalIcon: (props: any) => <div data-testid="adjustments-icon" {...props} />,
    Squares2X2Icon: (props: any) => <div data-testid="grid-icon" {...props} />,
    ListBulletIcon: (props: any) => <div data-testid="list-icon" {...props} />,
    SparklesIcon: (props: any) => <div data-testid="sparkles-icon" {...props} />,
    ArrowLeftIcon: (props: any) => <div data-testid="arrow-left-icon" {...props} />,
    PhotoIcon: (props: any) => <div data-testid="photo-icon" {...props} />,
    HomeIcon: (props: any) => <div data-testid="home-icon" {...props} />,
    InformationCircleIcon: (props: any) => <div data-testid="info-icon" {...props} />,
    CheckCircleIcon: (props: any) => <div data-testid="check-circle-icon" {...props} />,
    UserGroupIcon: (props: any) => <div data-testid="user-group-icon" {...props} />,
    ArrowTrendingUpIcon: (props: any) => <div data-testid="trending-up-icon" {...props} />,
    ArrowTrendingDownIcon: (props: any) => <div data-testid="trending-down-icon" {...props} />,
    ChartBarIcon: (props: any) => <div data-testid="chart-bar-icon" {...props} />,
    CalendarDaysIcon: (props: any) => <div data-testid="calendar-icon" {...props} />,
    BellIcon: (props: any) => <div data-testid="bell-icon" {...props} />,
    FireIcon: (props: any) => <div data-testid="fire-icon" {...props} />,
  }))

  jest.mock('@heroicons/react/24/solid', () => ({
    __esModule: true,
    HeartIcon: (props: any) => <div data-testid="heart-solid-icon" {...props} />,
    HomeIcon: (props: any) => <div data-testid="home-solid-icon" {...props} />,
    EyeIcon: (props: any) => <div data-testid="eye-solid-icon" {...props} />,
    UserGroupIcon: (props: any) => <div data-testid="user-group-solid-icon" {...props} />,
    CurrencyRupeeIcon: (props: any) => <div data-testid="currency-solid-icon" {...props} />,
  }))
}

// Mock external libraries
export const mockExternalLibraries = () => {
  // Mock react-hot-toast
  jest.mock('react-hot-toast', () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
      loading: jest.fn(),
      dismiss: jest.fn(),
    },
  }))

  // Mock framer-motion
  jest.mock('framer-motion', () => ({
    motion: {
      div: ({ children, onHoverStart, onHoverEnd, ...props }: any) => (
        <div
          {...props}
          onMouseEnter={onHoverStart}
          onMouseLeave={onHoverEnd}
        >
          {children}
        </div>
      ),
      button: ({ children, onHoverStart, onHoverEnd, ...props }: any) => (
        <button
          {...props}
          onMouseEnter={onHoverStart}
          onMouseLeave={onHoverEnd}
        >
          {children}
        </button>
      ),
      form: ({ children, ...props }: any) => <form {...props}>{children}</form>,
      span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
      h1: ({ children, ...props }: any) => <h1 {...props}>{children}</h1>,
      h2: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
      h3: ({ children, ...props }: any) => <h3 {...props}>{children}</h3>,
      p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
    },
    AnimatePresence: ({ children }: any) => children,
  }))

  // Mock react-hook-form
  jest.mock('react-hook-form', () => ({
    useForm: jest.fn(() => ({
      register: jest.fn(),
      handleSubmit: jest.fn((fn) => fn),
      setValue: jest.fn(),
      formState: { errors: {} },
      watch: jest.fn(),
      reset: jest.fn(),
    })),
  }))

  // Mock @hookform/resolvers/zod
  jest.mock('@hookform/resolvers/zod', () => ({
    zodResolver: jest.fn(() => jest.fn()),
  }))

  // Mock zod
  jest.mock('zod', () => ({
    object: jest.fn(() => ({
      shape: jest.fn(),
    })),
    string: jest.fn(() => ({
      min: jest.fn(),
      max: jest.fn(),
      email: jest.fn(),
      optional: jest.fn(),
    })),
    number: jest.fn(() => ({
      min: jest.fn(),
      max: jest.fn(),
      positive: jest.fn(),
      optional: jest.fn(),
    })),
    enum: jest.fn(),
  }))
}

// Mock browser APIs
export const mockBrowserAPIs = () => {
  // Mock navigator.share
  Object.defineProperty(window.navigator, 'share', {
    writable: true,
    value: jest.fn(),
  })

  // Mock navigator.clipboard
  Object.defineProperty(window.navigator, 'clipboard', {
    writable: true,
    value: {
      writeText: jest.fn(),
    },
  })

  // Mock fetch
  global.fetch = jest.fn()
}

// Test data generators
export const createMockProperty = (overrides = {}) => ({
  id: '1',
  title: 'Beautiful 3BR Apartment',
  description: 'Spacious apartment with great views',
  price: 2500000,
  address: '123 Main St, Mumbai, Maharashtra',
  bedrooms: 3,
  bathrooms: 2,
  area: 1200,
  type: 'Apartment',
  status: 'for-sale' as const,
  dateAdded: '2024-01-15T10:30:00Z',
  image: '/property1.jpg',
  ...overrides,
})

export const createMockProperties = (count = 3) => {
  return Array.from({ length: count }, (_, index) =>
    createMockProperty({
      id: `${index + 1}`,
      title: `Property ${index + 1}`,
      price: (index + 1) * 1000000,
    })
  )
}

export const createMockUser = (overrides = {}) => ({
  id: '1',
  name: 'John Doe',
  email: 'john@example.com',
  avatar: '/avatar.jpg',
  role: 'agent',
  ...overrides,
})

// Custom render function with providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <ThemeProvider>
      {children}
    </ThemeProvider>
  )
}

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }

// Test utilities
export const waitForLoadingToFinish = () =>
  waitFor(() => {
    expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
  }, { timeout: 3000 })

export const mockApiResponse = (data: any, status = 200) => {
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  })
}

export const mockApiError = (error: any, status = 500) => {
  (global.fetch as jest.Mock).mockRejectedValueOnce(error)
}

// Setup function for all tests
export const setupTestEnvironment = () => {
  mockHeroicons()
  mockExternalLibraries()
  mockBrowserAPIs()

  // Clear all mocks before each test
  beforeEach(() => {
    jest.clearAllMocks()
    ;(global.fetch as jest.Mock).mockClear()
  })
}
