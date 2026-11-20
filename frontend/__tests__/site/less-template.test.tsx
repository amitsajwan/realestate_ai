import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import ProjectPoints, { HomeSizes, labelRepeats } from '@/components/site/ProjectPoints'
import { Credit } from '@/components/site/ProfilePictures'
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

// an outside review of the Godrej Ivara page (2026-11-20): two lists of sizes that disagreed, "(not yet confirmed)" amenities and
// sizes, and the renders' warning said twice under the pictures
describe('the page states only what it can stand behind, once', () => {
  const SIZES = [
    { bhk: '2 BHK', low: 729, high: 729, kind: 'carpet area', official: true, one_site: false },
    { bhk: '3 BHK', low: 875, high: 1250, kind: 'area kind not stated', official: false, one_site: false },
    { bhk: '4 BHK', low: 1550, high: 1650, kind: 'carpet area', official: false, one_site: true },
  ]

  it('shows a size only from the builder or two sites, with its kind of area, and never "(not yet confirmed)"', () => {
    render(<HomeSizes sizes={SIZES} name="Godrej Ivara" />)
    const box = screen.getByTestId('home-sizes')
    expect(box).toHaveTextContent('2 BHK: 729 sq ft, carpet area')
    expect(box).not.toHaveTextContent(/3 BHK|4 BHK|not yet confirmed|not stated/)
  })

  it("lets the agent's price sheet be the one list of sizes when it gives carpet areas", () => {
    const offer = { price_inr: 12000000, source: "House Deal's listing", read_at: '2026-11-07',
      homes: [{ bhk: 2, label: '2 BHK', carpet_sqft: 730, price_inr: 12000000 }, { bhk: 3, label: '3 BHK', carpet_sqft: 890, price_inr: 15000000 }] }
    const { unmount } = render(<RegisterProjectPage p={{ ...P, home_sizes: SIZES }} siteUrl="https://avasetu.in" facts={{ offer } as never} />)
    expect(screen.queryByTestId('home-sizes')).toBeNull()
    expect(screen.getByTestId('price-sheet')).toHaveTextContent('730 sq ft')
    unmount()
    page({ home_sizes: SIZES })
    expect(screen.getByTestId('home-sizes')).toHaveTextContent('729 sq ft')
  })

  it('leaves out an amenity only one property site gives', () => {
    const src = (site: string) => ({ site, url: null })
    const { container } = page({ profile: { read_at: '2026-11-07', plans: [], photos: [], highlights: [
      { topic: 'parking', text: 'Basement and visitor parking', official: false, sources: [src('a.com')] },
      { topic: 'clubhouse', text: 'A clubhouse', official: false, sources: [src('a.com'), src('b.com')] },
    ] } })
    expect(container).toHaveTextContent('A clubhouse')
    expect(container).not.toHaveTextContent(/Basement and visitor parking|not yet confirmed/)
  })

  it("says where the pictures came from in one line and the renders' warning once", () => {
    const pic = (source: 'agent' | 'builder', site: string) => ({ url: `/u/${source}.webp`, width: 1, height: 1, alt: 'x', site, page_url: source === 'builder' ? 'https://builder.example/ivara' : null, source })
    render(<Credit pics={[pic('agent', 'House Deal'), pic('builder', 'builder.example')]} />)
    const credit = screen.getByTestId('pictures-credit')
    expect(credit).toHaveTextContent("From House Deal's listing and the builder's website.")
    expect(credit.textContent!.match(/Renders are/g)).toHaveLength(1)
    expect(screen.getAllByText(/Renders are/)).toHaveLength(1)
  })
})
