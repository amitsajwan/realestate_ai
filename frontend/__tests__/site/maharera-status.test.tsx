import { render, screen } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <div data-testid="enquiry-form" /> }))

const P: RegisterProject = {
  slug: 'kosmic-kourtyard-wagholi', name: 'Kosmic Kourtyard', regno: 'P52100055341', promoter: 'B', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-04-30', completion_at_registration: '2028-12-31',
  units_total: 261, units_booked: 106, details_read_at: '2026-11-27', listed_or_updated: '2026-11-13', completion_passed: false,
  maharera_url: 'https://maharerait.maharashtra.gov.in/public/project/view/43848', paragraph: 'A project in Wagholi.',
  indexable: true, finished: false, source: 'MahaRERA public records', same_area: [],
}

describe('a project MahaRERA has flagged (deregistered or in abeyance)', () => {
  it('leads with the warning and takes no enquiry', () => {
    render(<RegisterProjectPage p={{ ...P, maharera_status: 'deregistered' }} siteUrl="https://avasetu.in" facts={null} />)
    const alert = screen.getByTestId('maharera-status')
    expect(alert).toHaveTextContent('MahaRERA has deregistered this project')
    expect(alert).toHaveTextContent('27 Nov 2026')
    expect(screen.getByTestId('status-rera')).toHaveAttribute('href', P.maharera_url!)
    expect(screen.queryByTestId('enquiry-form')).not.toBeInTheDocument()
  })

  it('says "in abeyance" when that is the status', () => {
    render(<RegisterProjectPage p={{ ...P, maharera_status: 'abeyance' }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByTestId('maharera-status')).toHaveTextContent('abeyance')
  })

  it('shows no warning and keeps the form for an Active project', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.queryByTestId('maharera-status')).not.toBeInTheDocument()
    expect(screen.getByTestId('enquiry-form')).toBeInTheDocument()
  })
})
