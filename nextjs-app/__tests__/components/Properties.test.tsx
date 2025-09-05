import React from 'react';
import { render, screen } from '@testing-library/react';
import Properties from '../../components/Properties';

describe('Properties', () => {
  it('renders the properties list correctly', () => {
    render(<Properties />);

    expect(screen.getByText('Properties')).toBeInTheDocument();
    expect(screen.getByText(/Manage your property listings/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add property/i })).toBeInTheDocument();
  });
});