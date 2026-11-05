import { render, screen } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <div data-testid="enquiry-form" /> }))

const P = {
  slug: 'rose-court-wagholi', name: 'Rose Court', regno: 'P52100011111', promoter: 'B', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-03-31', completion_at_registration: '2029-03-31',
  units_total: 100, units_booked: 10, details_read_at: '2026-10-03', listed_or_updated: '2026-01-02', completion_passed: false,
  maharera_url: null, paragraph: 'Rose Court is a project in Wagholi.', indexable: true, finished: false, source: 'MahaRERA', same_area: [],
  checks: [{ key: 'places', label: 'Location', ok: false, at: '2026-11-04', note: 'no pincode centre to check against' }],
} as unknown as RegisterProject

describe('how we checked the page', () => {
  it('stays closed under Sources, and a buyer never reads our internal note', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    const box = screen.getByTestId('checks')
    expect(box.tagName).toBe('DETAILS')
    expect(box).not.toHaveAttribute('open')
    expect(screen.getByText('Sources')).toBeInTheDocument()
    expect(box.textContent).not.toContain('no pincode centre')
    expect(box.textContent).toContain('We are still checking this')
  })
})
