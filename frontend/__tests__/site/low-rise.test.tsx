// A villa project is filed with MahaRERA as many buildings of 2 floors and no units per building. Its page said "Towers 30 ... The
// tallest has 2 floors" over a table of "0 homes" rows (Panchshil V3 Villa Phase II, 2026-11-19).
import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { lowRise, projectFaq, type RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <section id="enquire" /> }))

const villa = (i: number) => ({ name: `V3-${150 + i}`, wing: null, floors: 2, units_residential: 0, units_other: 0, units_total: null })
const V3: RegisterProject = {
  slug: 'v3-villa-phase-ii-wagholi', name: 'V3 Villa Phase- II', regno: 'P52100052083', promoter: 'Panchshil', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2027-12-31', completion_at_registration: '2027-12-31',
  units_total: null, units_booked: null, details_read_at: '2026-10-24', listed_or_updated: '2023-07-24', completion_passed: false,
  maharera_url: null, paragraph: '', indexable: true, same_area: [], source: 'MahaRERA public records',
  details: { towers: 30, max_floors: 2, units_total: null, units_residential: null, units_other: null, booked_pct: null, registered_on: '2023-07-24', completion_moved_months: 0 },
  buildings: Array.from({ length: 30 }, (_, i) => villa(i)),
} as unknown as RegisterProject

describe('a low-rise project (villas, row houses)', () => {
  it('says buildings, not towers, and shows no column of zero homes', () => {
    render(<RegisterProjectPage p={V3} siteUrl="https://avasetu.in" facts={null} />)
    const record = screen.getByTestId('record')
    expect(within(record).getAllByText('Buildings').some((el) => el.tagName === 'DT')).toBe(true)   // the record's row label
    expect(within(record).queryByText('Towers')).not.toBeInTheDocument()
    expect(within(record).getByText(/Low-rise: none taller than 2 floors/)).toBeInTheDocument()
    expect(within(record).queryByText(/The tallest has/)).not.toBeInTheDocument()
    expect(screen.getByText('Building by building')).toBeInTheDocument()
    expect(within(screen.getByTestId('tower-by-tower')).queryByText('Homes')).not.toBeInTheDocument()
    const faq = projectFaq(V3).find((f) => /buildings|towers/.test(f.q))!
    expect(faq.q).toBe('How many buildings does V3 Villa Phase- II have?')
    expect(faq.a).toContain('none taller than 2 floors')
  })

  it('leaves a project of towers as it was', () => {
    const tower = { ...villa(0), floors: 14, units_residential: 56 }
    expect(lowRise({ buildings: [tower, { ...tower, name: 'B' }] })).toBe(false)
    expect(lowRise({ buildings: [villa(0)] })).toBe(false)            // one small building is not a villa project
  })
})
