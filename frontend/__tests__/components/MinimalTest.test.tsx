import React from 'react';
import { render } from '@testing-library/react';

// Test if basic React rendering works
describe('Minimal Test', () => {
  test('renders basic div', () => {
    const { container } = render(<div>Hello World</div>);
    expect(container.firstChild).toHaveTextContent('Hello World');
  });

  test('renders with Heroicons', () => {
    const { MapPinIcon } = require('@heroicons/react/24/outline');
    const TestComponent = () => (
      <div>
        <MapPinIcon className="w-5 h-5" />
        <span>Test</span>
      </div>
    );
    
    const { container } = render(<TestComponent />);
    expect(container.firstChild).toBeInTheDocument();
  });
});