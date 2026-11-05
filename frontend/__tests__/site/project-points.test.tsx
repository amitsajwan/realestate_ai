import { render, screen } from '@testing-library/react'
import ProjectPoints, { HomeSizes } from '@/components/site/ProjectPoints'

describe('the points and the sizes', () => {
  it('opens with a dated line and each point', () => {
    render(<ProjectPoints p={{ regno: 'P1', details_read_at: '2026-11-03', points: [{ label: '99% of 832 homes booked', text: 'Almost all are sold.' }] }} />)
    expect(screen.getByRole('heading', { name: /As of 3 Nov 2026, from MahaRERA P1/ })).toBeTruthy()
    expect(screen.getByText('99% of 832 homes booked:')).toBeTruthy()
  })

  it('shows nothing without points', () => {
    const { container } = render(<ProjectPoints p={{ regno: 'P1', details_read_at: null, points: [] }} />)
    expect(container.firstChild).toBeNull()
  })

  it('says the kind of area with every size', () => {
    render(<HomeSizes name="Rose Court" sizes={[{ bhk: '2 BHK', low: 725, high: 780, kind: 'carpet area' }, { bhk: '3 BHK', low: 1050, high: 1050, kind: 'area kind not stated' }]} />)
    expect(screen.getByText(/725 to 780 sq ft, carpet area/)).toBeTruthy()
    expect(screen.getByText(/1,050 sq ft, area kind not stated/)).toBeTruthy()
  })
})
