import React from 'react'
import { render, screen } from '@testing-library/react'
import VerifiedFacts from '@/components/site/VerifiedFacts'
import type { PropertyFactsView } from '@/lib/site/types'

const FACTS: PropertyFactsView = {
  project: 'Gulmohar City',
  locality: 'Ranjangaon',
  maharera: {
    rera_no: 'P52100076768', url: 'https://maharerait.maharashtra.gov.in/public/project/view/46398', project_type: 'Plotted',
    registered_on: '2024-06-28', completion_at_registration: '2028-12-31', completion_now: '2029-04-30', moved_months: 4,
    units_total: 123, read_at: '2026-10-01T00:00:00+00:00',
  },
  nearby: [{ label: 'Hospital', name: 'Narwade Hospital', km: 0.4 }, { label: 'Industrial area', name: 'IndoSpace Industrial Park', km: 3 }],
  nearby_source: { name: 'OpenStreetMap contributors', url: 'https://www.openstreetmap.org/copyright' },
  numbers: { price_per_sqft: 1676, plot_guntha: 1.77, plot_sqm: 179, emi: { emi: 22425, loan: 2584000, rate: 8.5, years: 20 } },
}

describe('VerifiedFacts', () => {
  it('shows MahaRERA, nearby and worked-out numbers, each with its source', () => {
    render(<VerifiedFacts f={FACTS} />)
    expect(screen.getByRole('heading', { name: /checked for you/i })).toBeInTheDocument()
    expect(screen.getByText('P52100076768')).toBeInTheDocument()
    expect(screen.getByText('30 Apr 2029 (was 31 Dec 2028)')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /check it yourself/i })).toHaveAttribute('href', FACTS.maharera!.url)
    expect(screen.getByText(/read 1 Oct 2026/)).toBeInTheDocument()
    expect(screen.getByText('Narwade Hospital')).toBeInTheDocument()
    expect(screen.getByText('3 km')).toBeInTheDocument()
    expect(screen.getByText('₹1,676 per sq.ft')).toBeInTheDocument()
    expect(screen.getByText('1.77 guntha (about 179 sq.m)')).toBeInTheDocument()
    expect(screen.getByText('₹22,425 a month')).toBeInTheDocument()
    expect(screen.getByText(/₹25.84 L loan/)).toBeInTheDocument()
  })

  it('renders nothing without facts, and only the blocks it has', () => {
    const { container } = render(<VerifiedFacts f={null} />)
    expect(container).toBeEmptyDOMElement()
    render(<VerifiedFacts f={{ nearby: FACTS.nearby, nearby_source: FACTS.nearby_source }} />)
    expect(screen.queryByText(/on maharera/i)).not.toBeInTheDocument()
    expect(screen.getByText('Narwade Hospital')).toBeInTheDocument()
  })
})
