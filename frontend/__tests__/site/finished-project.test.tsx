import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <div data-testid="enquiry-form" /> }))

const P: RegisterProject = {
  slug: 'old-greens-wagholi', name: 'Old Greens', regno: 'P52100011111', promoter: 'B', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2016-03-31', completion_at_registration: '2016-03-31',
  units_total: 100, units_booked: 100, details_read_at: '2026-10-03', listed_or_updated: '2016-01-02', completion_passed: true,
  maharera_url: null, paragraph: 'Old Greens is a project in Wagholi.', indexable: false, finished: true, source: 'MahaRERA public records',
  same_area: [{ name: 'New Heights', slug: 'new-heights-wagholi', completion_now: '2027-06-30', price_from: 6_500_000, bhk: '2 BHK' }],
}

describe('a finished project page (owner 2026-11-01: no enquiry, show what is still being built)', () => {
  it('has no enquiry form and leads to the projects still being built nearby', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.queryByTestId('enquiry-form')).not.toBeInTheDocument()
    expect(screen.getByTestId('see-building')).toHaveAttribute('href', '#same-title')
    const list = screen.getByTestId('compare')
    expect(within(list).getByText('Still being built in Wagholi')).toBeInTheDocument()
    expect(within(list).getByText('New Heights').closest('a')).toHaveAttribute('href', '/projects/new-heights-wagholi')
    expect(screen.getByTestId('finished-note')).toHaveTextContent('Old Greens is finished')
  })

  it('keeps the form on a project still being built', () => {
    render(<RegisterProjectPage p={{ ...P, finished: false, completion_now: '2029-10-30' }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByTestId('enquiry-form')).toBeInTheDocument()
    expect(screen.queryByTestId('see-building')).not.toBeInTheDocument()
    expect(screen.getByText('Other projects in Wagholi')).toBeInTheDocument()
  })
})
