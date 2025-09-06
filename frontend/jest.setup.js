import '@testing-library/jest-dom'
import React from 'react'
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

// Mock setTimeout and clearTimeout for Jest environment
global.setTimeout = jest.fn((fn, delay) => {
  return setTimeout(fn, delay || 0);
});
global.clearTimeout = jest.fn((id) => {
  clearTimeout(id);
});

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
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props) => {
    // eslint-disable-next-line @next/next/no-img-element
    return React.createElement('img', {
      ...props,
      src: props.src,
      alt: props.alt || '',
    })
  },
}))

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, onHoverStart, onHoverEnd, ...props }) => (
      <div 
        {...props} 
        onMouseEnter={onHoverStart} 
        onMouseLeave={onHoverEnd}
      >
        {children}
      </div>
    ),
    button: ({ children, onHoverStart, onHoverEnd, ...props }) => (
      <button 
        {...props} 
        onMouseEnter={onHoverStart} 
        onMouseLeave={onHoverEnd}
      >
        {children}
      </button>
    ),
    form: ({ children, ...props }) => <form {...props}>{children}</form>,
    span: ({ children, ...props }) => <span {...props}>{children}</span>,
    h1: ({ children, ...props }) => <h1 {...props}>{children}</h1>,
    h2: ({ children, ...props }) => <h2 {...props}>{children}</h2>,
    h3: ({ children, ...props }) => <h3 {...props}>{children}</h3>,
    p: ({ children, ...props }) => <p {...props}>{children}</p>,
  },
  AnimatePresence: ({ children }) => children,
}))

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  },
  Toaster: () => null,
}))

// Mock Heroicons with proper React components
const createMockIcon = (name) => {
  const MockIcon = (props) => React.createElement('div', {
    ...props,
    'data-testid': props['data-testid'] || name,
    'data-icon': name
  })
  MockIcon.displayName = name
  return MockIcon
}

jest.mock('@heroicons/react/24/outline', () => ({
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
}))

jest.mock('@heroicons/react/24/solid', () => ({
  __esModule: true,
  HomeIcon: createMockIcon('HomeIconSolid'),
  EyeIcon: createMockIcon('EyeIconSolid'),
  UserGroupIcon: createMockIcon('UserGroupIconSolid'),
  CurrencyRupeeIcon: createMockIcon('CurrencyRupeeIconSolid'),
  HeartIcon: createMockIcon('HeartIconSolid'),
  StarIcon: createMockIcon('StarIconSolid'),
  PhoneIcon: createMockIcon('PhoneIconSolid'),
  ChatBubbleLeftRightIcon: createMockIcon('ChatBubbleLeftRightIconSolid'),
}))

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