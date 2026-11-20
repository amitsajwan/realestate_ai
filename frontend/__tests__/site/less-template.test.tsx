import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import ProjectPoints, { labelRepeats } from '@/components/site/ProjectPoints'
import { otherNames, projectFaq } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

// A project page read as a template (an outside model named ours "programmatic" at a glance, 2026-11-20): the same heading with the
// name stamped in, raw register text, a label its sentence repeats, and notes said on every page. Each test pins one of those.

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <section id="enquire" /> }))

const P: RegisterProject = {
  slug: 'castle-garden-wagholi', name: 'Castle Garden', regno: 'P52100080929', promoter: 'UTKARSH DREAM HOMES LLP', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-10-30', completion_at_registration: '2028-12-31',
  units_total: 416, units_booked: 244, details_read_at: '2026-10-03', listed_or_updated: '2026-09-28',
  maharera_url: 'https://maharerait.maharashtra.gov.in/public/project/view/80929', paragraph: '',
  indexable: true, same_area: [], source: 'MahaRERA public records',
}

const page = (p: Partial<RegisterProject> = {}) =>
  render(<RegisterProjectPage p={{ ...P, ...p }} siteUrl="https://avasetu.in" facts={null} />)

describe('a project page that does not read as a template', () => {
  it('names the sections plainly, without the project name stamped into each heading', () => {
    page({ profile: { read_at: '2026-11-01', highlights: [{ topic: 'amenity', text: 'Swimming pool', official: true, sources: [] }], plans: [], photos: [] } })
    const h2 = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent ?? '')
    expect(h2).toEqual(expect.arrayContaining(['Location', 'MahaRERA record']))
    expect(h2.filter((t) => t.includes('Castle Garden'))).toEqual([])
  })

  it('writes a builder MahaRERA files in capitals as people write it', () => {
    page()
    expect(screen.getByTestId('hero-line')).toHaveTextContent('by Utkarsh Dream Homes LLP')
    expect(screen.queryByText(/UTKARSH DREAM/)).toBeNull()
  })

  it('says "Booked 244 of 416" once, and shows no booked chip for a record of no homes', () => {
    const { unmount } = page()
    expect(screen.getByTestId('chip-booked')).toHaveTextContent(/^Booked244 of 416$/)
    unmount()
    page({ units_total: 0, units_booked: 0 })
    expect(screen.queryByTestId('chip-booked')).toBeNull()
    expect(screen.queryByText(/0 of 0/)).toBeNull()
  })

  it('puts no "not checked" badge on a map it could not place, and the map says it is a search by name', () => {
    page({ map: null })
    const map = screen.getByRole('heading', { name: 'Location' }).closest('section')!
    expect(map).not.toHaveTextContent('Position not checked')
    expect(map).toHaveTextContent('A map search by name.')
  })

  it('leaves out the notes that stood on every page', () => {
    const { container } = page({
      cautions: [{ key: 'slow', text: 'Bookings are slow.', source: 'rera' }],
      builder: { name: 'UTKARSH DREAM HOMES LLP', count: 3, record_ok: false, with_dates: 1, moved_later: 0, avg_months_later: null, projects: [] },
      profile: { read_at: '2026-11-01', highlights: [{ topic: 'amenity', text: 'Swimming pool', official: true, sources: [] }], plans: [], photos: [] },
    })
    expect(container).not.toHaveTextContent('not an opinion of the project')
    expect(container).not.toHaveTextContent('too few to judge')
    expect(container).not.toHaveTextContent('come only from MahaRERA')
    expect(screen.getByRole('heading', { name: 'Utkarsh Dream Homes LLP: track record' })).toBeInTheDocument()
  })
})

describe('the opening points', () => {
  it('drops a label whose sentence already says its numbers', () => {
    expect(labelRepeats('0 of 523 homes booked', 'None of the 523 units have been booked yet.')).toBe(true)
    expect(labelRepeats('Completion date moved to 31 Jul 2028', 'Registered for 31 Mar 2019, the target is now 31 Jul 2028.')).toBe(true)
    expect(labelRepeats('1-acre site', 'The project sits on a one-acre parcel.')).toBe(false)
    expect(labelRepeats('Close to EON IT Park', 'About 2 km away.')).toBe(false)
  })

  it('opens with a plain heading and a dated line, the sentence standing alone where its label only repeated it', () => {
    render(<ProjectPoints p={{ regno: 'P1', details_read_at: '2026-11-03', points: [
      { label: '0 of 523 homes booked', text: 'None of the 523 homes have been booked.' },
      { label: 'Low-rise', text: 'No building is taller than 4 floors.' },
    ] }} />)
    expect(screen.getByRole('heading', { name: 'What stands out' })).toBeInTheDocument()
    expect(screen.getByTestId('points-asof')).toHaveTextContent('As of 3 Nov 2026')
    const items = within(screen.getByTestId('project-points')).getAllByRole('listitem')
    expect(items[0]).toHaveTextContent(/^None of the 523 homes have been booked\.$/)
    expect(items[1]).toHaveTextContent('Low-rise: No building is taller than 4 floors.')
  })
})

describe('names and answers', () => {
  it('drops another name that is only the start of the one shown', () => {
    expect(otherNames({ name: 'Nivaan Meadows Phase III', aliases: ['Nivaan Meadows Phase', 'Nivaan Greens'] })).toEqual(['Nivaan Greens'])
  })

  it('asks for the possession date in writing only where the filed date moved', () => {
    const moved = projectFaq(P).find((f) => /possession date/.test(f.q))!
    expect(moved.a).toContain('Ask the builder for the possession date in your agreement, in writing.')
    const same = projectFaq({ ...P, completion_at_registration: P.completion_now }).find((f) => /possession date/.test(f.q))!
    expect(same.a).not.toContain('Ask the builder')
  })
})
