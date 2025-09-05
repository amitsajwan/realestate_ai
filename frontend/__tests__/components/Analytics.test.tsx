import React from 'react';
import { render, screen } from '@testing-library/react';
import Analytics from '../../components/Analytics';

describe('Analytics', () => {
  it('renders the analytics dashboard correctly', () => {
    const mockProperties = [
      {
        id: 1,
        title: 'Test Property',
        price: 300000,
        status: 'for-sale',
        type: 'House'
      }
    ];
    
    render(<Analytics properties={mockProperties} />);
    
    expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Total Properties')).toBeInTheDocument();
    expect(screen.getByText('Total Portfolio Value')).toBeInTheDocument();
    expect(screen.getByText('Average Property Value')).toBeInTheDocument();
    expect(screen.getByText('Properties Sold')).toBeInTheDocument();
  });
});