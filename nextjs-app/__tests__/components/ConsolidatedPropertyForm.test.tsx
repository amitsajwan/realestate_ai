import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock all dependencies before importing the component
jest.mock('../../lib/api', () => ({
  apiService: {
    createProperty: jest.fn().mockResolvedValue({ success: true, data: { id: '123' } }),
    getAgentProfile: jest.fn().mockResolvedValue({ success: true, data: { name: 'Test Agent' } }),
  },
}));

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('@heroicons/react/24/outline', () => ({
  HomeIcon: () => <div data-testid="home-icon" />,
  MapPinIcon: () => <div data-testid="map-pin-icon" />,
  CurrencyDollarIcon: () => <div data-testid="currency-dollar-icon" />,
  DocumentTextIcon: () => <div data-testid="document-text-icon" />,
  BuildingOfficeIcon: () => <div data-testid="building-office-icon" />,
  PlusIcon: () => <div data-testid="plus-icon" />,
  ExclamationCircleIcon: () => <div data-testid="exclamation-circle-icon" />,
}));

jest.mock('../../components/property/shared/PropertyFieldInput', () => {
  return function MockPropertyFieldInput({ name, label }: any) {
    return (
      <div data-testid={`field-${name}`}>
        <label>{label}</label>
        <input name={name} />
      </div>
    );
  };
});

jest.mock('../../components/property/shared/AIAssistantButton', () => ({
  AIAutoFillButton: () => <button data-testid="ai-autofill-button">AI Auto-Fill</button>,
  AISuggestionsButton: () => <button data-testid="ai-suggestions-button">AI Suggestions</button>,
  AIInsightsButton: () => <button data-testid="ai-insights-button">AI Insights</button>,
}));

jest.mock('../../components/property/hooks/usePropertyForm', () => ({
  usePropertyForm: () => ({
    register: jest.fn(() => ({ name: 'test', onChange: jest.fn() })),
    formState: { errors: {} },
    onSubmit: jest.fn(),
    isLoading: false,
    isAILoading: false,
    aiSuggestions: null,
    marketInsights: null,
    generateAISuggestions: jest.fn(),
    applyAISuggestions: jest.fn(),
    autoFillWithAI: jest.fn(),
  }),
}));

// Import the component after all mocks are set up
import ConsolidatedPropertyForm from '../../components/property/ConsolidatedPropertyForm';

describe('ConsolidatedPropertyForm', () => {
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders simple variant successfully', () => {
    render(
      <ConsolidatedPropertyForm
        variant="simple"
        onSuccess={mockOnSuccess}
        enableAI={true}
      />
    );

    // Check if basic form elements are present
    expect(screen.getByTestId('field-title')).toBeInTheDocument();
    expect(screen.getByTestId('field-propertyType')).toBeInTheDocument();
    expect(screen.getByTestId('field-location')).toBeInTheDocument();
  });

  it('renders wizard variant successfully', () => {
    render(
      <ConsolidatedPropertyForm
        variant="wizard"
        onSuccess={mockOnSuccess}
        enableAI={true}
      />
    );

    // Check if form is rendered
    expect(screen.getByTestId('field-title')).toBeInTheDocument();
  });

  it('renders AI features when enabled', () => {
    render(
      <ConsolidatedPropertyForm
        variant="simple"
        onSuccess={mockOnSuccess}
        enableAI={true}
      />
    );

    // Check if AI buttons are present
    expect(screen.getByTestId('ai-autofill-button')).toBeInTheDocument();
  });

  it('renders market insights when enabled', () => {
    render(
      <ConsolidatedPropertyForm
        variant="simple"
        onSuccess={mockOnSuccess}
        enableAI={true}
        enableMarketInsights={true}
      />
    );

    // Check if insights button is present
    expect(screen.getByTestId('ai-insights-button')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ConsolidatedPropertyForm
        variant="simple"
        onSuccess={mockOnSuccess}
        className="custom-class"
      />
    );

    // Check if custom class is applied
    expect(container.firstChild).toHaveClass('custom-class');
  });
});