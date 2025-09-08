import '@testing-library/jest-dom'
import { TextEncoder, TextDecoder } from 'util'

// Polyfill for TextEncoder/TextDecoder
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Mock localStorage and sessionStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => {
      store[key] = value.toString();
    },
    removeItem: (key) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    }
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });
Object.defineProperty(window, 'sessionStorage', { value: localStorageMock });

// Note: Removed problematic setTimeout mocking that was causing recursion

// Mock clipboard API globally to avoid conflicts
const mockWriteText = jest.fn(() => Promise.resolve())
const mockReadText = jest.fn(() => Promise.resolve(''))

// Make sure the mock functions are properly configured as spies
mockWriteText.mockResolvedValue = jest.fn()
mockReadText.mockResolvedValue = jest.fn()

Object.defineProperty(global.navigator, 'clipboard', {
  value: {
    writeText: mockWriteText,
    readText: mockReadText,
  },
  writable: true,
  configurable: true,
})

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
}))

// Mock Next.js Image component
jest.mock('next/image', () => {
  const React = require('react')
  return {
    __esModule: true,
    default: (props) => React.createElement('img', { ...props, src: props.src, alt: props.alt || '' }),
  }
})

// Mock framer-motion
jest.mock('framer-motion', () => {
  const React = require('react')
  const ce = React.createElement
  return {
    motion: {
      div: ({ children, onHoverStart, onHoverEnd, ...props }) => ce('div', { ...props, onMouseEnter: onHoverStart, onMouseLeave: onHoverEnd }, children),
      button: ({ children, onHoverStart, onHoverEnd, ...props }) => ce('button', { ...props, onMouseEnter: onHoverStart, onMouseLeave: onHoverEnd }, children),
      form: ({ children, ...props }) => ce('form', { ...props }, children),
      span: ({ children, ...props }) => ce('span', { ...props }, children),
      h1: ({ children, ...props }) => ce('h1', { ...props }, children),
      h2: ({ children, ...props }) => ce('h2', { ...props }, children),
      h3: ({ children, ...props }) => ce('h3', { ...props }, children),
      p: ({ children, ...props }) => ce('p', { ...props }, children),
    },
    AnimatePresence: ({ children }) => children,
  }
})

// Mock react-hot-toast
jest.mock('react-hot-toast', () => {
  const mockToast = jest.fn()
  mockToast.success = jest.fn()
  mockToast.error = jest.fn()
  mockToast.loading = jest.fn()
  mockToast.dismiss = jest.fn()
  
  // Make the default export work as both a function and an object
  const defaultExport = Object.assign(mockToast, {
    success: mockToast.success,
    error: mockToast.error,
    loading: mockToast.loading,
    dismiss: mockToast.dismiss,
  })
  
  return {
    __esModule: true,
    default: defaultExport,
    toast: defaultExport,
    Toaster: () => null,
  }
})

// Mock Heroicons with proper React components
jest.mock('@heroicons/react/24/outline', () => {
  const React = require('react')
  const createMockIcon = (name) => {
    const MockIcon = (props) => React.createElement('div', {
      ...props,
      'data-testid': props['data-testid'] || name,
      'data-icon': name
    })
    MockIcon.displayName = name
    return MockIcon
  }
  return {
    __esModule: true,
    HomeIcon: createMockIcon('HomeIcon'),
    EyeIcon: createMockIcon('EyeIcon'),
    UserGroupIcon: createMockIcon('UserGroupIcon'),
    CurrencyRupeeIcon: createMockIcon('CurrencyRupeeIcon'),
    CurrencyDollarIcon: createMockIcon('CurrencyDollarIcon'),
    CheckCircleIcon: createMockIcon('CheckCircleIcon'),
    SparklesIcon: createMockIcon('SparklesIcon'),
    ArrowTrendingUpIcon: createMockIcon('ArrowTrendingUpIcon'),
    ArrowTrendingDownIcon: createMockIcon('ArrowTrendingDownIcon'),
    ChartBarIcon: createMockIcon('ChartBarIcon'),
    PlusIcon: createMockIcon('PlusIcon'),
    CalendarDaysIcon: createMockIcon('CalendarDaysIcon'),
    CalendarIcon: createMockIcon('CalendarIcon'),
    BellIcon: createMockIcon('BellIcon'),
    FireIcon: createMockIcon('FireIcon'),
    MapPinIcon: createMockIcon('MapPinIcon'),
    BuildingOfficeIcon: createMockIcon('BuildingOfficeIcon'),
    PencilIcon: createMockIcon('PencilIcon'),
    TrashIcon: createMockIcon('TrashIcon'),
    MagnifyingGlassIcon: createMockIcon('MagnifyingGlassIcon'),
    FunnelIcon: createMockIcon('FunnelIcon'),
    XMarkIcon: createMockIcon('XMarkIcon'),
    HeartIcon: createMockIcon('HeartIcon'),
    ShareIcon: createMockIcon('ShareIcon'),
    AdjustmentsHorizontalIcon: createMockIcon('AdjustmentsHorizontalIcon'),
    Squares2X2Icon: createMockIcon('Squares2X2Icon'),
    ListBulletIcon: createMockIcon('ListBulletIcon'),
    UsersIcon: createMockIcon('UsersIcon'),
    PhoneIcon: createMockIcon('PhoneIcon'),
    ChatBubbleLeftRightIcon: createMockIcon('ChatBubbleLeftRightIcon'),
    StarIcon: createMockIcon('StarIcon'),
    ClockIcon: createMockIcon('ClockIcon'),
    ChevronDownIcon: createMockIcon('ChevronDownIcon'),
    GlobeAltIcon: createMockIcon('GlobeAltIcon'),
    LinkIcon: createMockIcon('LinkIcon'),
    EnvelopeIcon: createMockIcon('EnvelopeIcon'),
    ExclamationTriangleIcon: createMockIcon('ExclamationTriangleIcon'),
    UserIcon: createMockIcon('UserIcon'),
    CheckIcon: createMockIcon('CheckIcon'),
    HeartSolidIcon: createMockIcon('HeartSolidIcon'),
    CogIcon: createMockIcon('CogIcon'),
    Bars3Icon: createMockIcon('Bars3Icon'),
    ArrowRightOnRectangleIcon: createMockIcon('ArrowRightOnRectangleIcon'),
  }
})

jest.mock('@heroicons/react/24/solid', () => {
  const React = require('react')
  const createMockIcon = (name) => {
    const MockIcon = (props) => React.createElement('div', {
      ...props,
      'data-testid': props['data-testid'] || name,
      'data-icon': name
    })
    MockIcon.displayName = name
    return MockIcon
  }
  return {
    __esModule: true,
    HomeIcon: createMockIcon('HomeIconSolid'),
    EyeIcon: createMockIcon('EyeIconSolid'),
    UserGroupIcon: createMockIcon('UserGroupIconSolid'),
    CurrencyRupeeIcon: createMockIcon('CurrencyRupeeIconSolid'),
    HeartIcon: createMockIcon('HeartIconSolid'),
    StarIcon: createMockIcon('StarIconSolid'),
    PhoneIcon: createMockIcon('PhoneIconSolid'),
    ChatBubbleLeftRightIcon: createMockIcon('ChatBubbleLeftRightIconSolid'),
  }
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {
    return null
  }
  disconnect() {
    return null
  }
  unobserve() {
    return null
  }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {
    return null
  }
  disconnect() {
    return null
  }
  unobserve() {
    return null
  }
}

// Suppress console errors during tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})