import React from 'react';
import { render, screen } from '@testing-library/react';
import CRM from '../../components/CRM';

describe('CRM', () => {
  it('renders the CRM dashboard correctly', () => {
    render(<CRM />);

    expect(screen.getByText('CRM Dashboard')).toBeInTheDocument();
    expect(screen.getByText('New Leads')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Converted')).toBeInTheDocument();
    expect(screen.getByText('Total Pipeline')).toBeInTheDocument();
  });
});