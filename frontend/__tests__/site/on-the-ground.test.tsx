import { render, screen } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import type { RegisterProject } from '@/lib/site/register'

// On the ground (backend areastats/sitevisits.py): a person's dated, signed note from the site, high on the page

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <section id="enquire" /> }))

const P: RegisterProject = {
  slug: 'godrej-ivara-pune', name: 'Godrej Ivara', regno: 'PR1260002502426', promoter: 'Godrej Properties', pincode: '412207',
  area: { key: 'upper_kharadi', slug: 'upper-kharadi', name: 'Upper Kharadi' }, completion_now: '2032-12-16', completion_at_registration: '2032-08-31',
  units_total: 2792, units_booked: 489, details_read_at: '2026-11-07', listed_or_updated: '2026-11-01',
  maharera_url: null, paragraph: '', indexable: true, same_area: [], source: 'MahaRERA public records',
}
const VISIT = { visited_on: '2026-11-19', by: 'House Deal', text: 'Tower A has its slab up to the 21st floor; the approach road is two lanes.' }

describe('on the ground', () => {
  it('shows what was seen at the site, with who went and when, right under the opening', () => {
    render(<RegisterProjectPage p={{ ...P, site_visit: VISIT }} siteUrl="https://avasetu.in" facts={null} />)
    const box = screen.getByTestId('on-the-ground')
    expect(screen.getByRole('heading', { name: 'On the ground' })).toBeInTheDocument()
    expect(screen.getByTestId('visit-line')).toHaveTextContent('Visited 19 Nov 2026 by House Deal')
    expect(box.querySelector('time')).toHaveAttribute('datetime', '2026-11-19')
    expect(box).toHaveTextContent('Tower A has its slab up to the 21st floor')
    // above the price and the record: it is what only a visit gives
    expect(box.compareDocumentPosition(screen.getByTestId('record')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('shows nothing without a visit', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.queryByTestId('on-the-ground')).toBeNull()
  })
})
