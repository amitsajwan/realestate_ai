import { act, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import PickButtons from '@/components/site/PickButtons'
import PicksBar from '@/components/site/PicksBar'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { briefLine, compareRows, soonerNearby } from '@/lib/site/projectCompare'
import {
  COMPARE_KEY, COMPARE_MAX, SAVED_KEY, comparePath, parseSlugs, readPicks, shortlistMessage, shortlistPath, toggle, whatsappShare,
} from '@/lib/site/picks'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <div data-testid="enquiry-form" /> }))

const TODAY = '2026-11-21'

const IVARA: RegisterProject = {
  slug: 'godrej-ivara-pune', name: 'GODREJ IVARA', marketed_name: 'Godrej Ivara', regno: 'P52100055555', promoter: 'Godrej Properties',
  pincode: '412207', area: { key: 'upper_kharadi', slug: 'upper-kharadi', name: 'Upper Kharadi' }, completion_now: '2030-12-31',
  completion_at_registration: '2030-06-30', units_total: 400, units_booked: 100, details_read_at: '2026-11-01', listed_or_updated: '2026-10-01',
  maharera_url: null, paragraph: '', indexable: true, source: 'MahaRERA public records', completion_passed: false,
  details: { towers: 4, max_floors: 30, units_total: 400, units_residential: 400, units_other: 0, booked_pct: 25, registered_on: '2025-01-10', completion_moved_months: 6 },
  prices: { read_at: '2026-11-10', rows: [{ bhk: '2', from_inr: 9_000_000, to_inr: null, official: true, sqft: 730, per_sqft: 12_329, sources: [{ site: 'godrejproperties.com', url: 'https://godrejproperties.com' }] }] },
  area_rate: { place: 'Upper Kharadi', per_sqft: 9_800, projects: 6 },
  builder: { name: 'Godrej Properties', slug: 'godrej-properties', count: 12, record_ok: true, with_dates: 9, moved_later: 3, avg_months_later: 5, projects: [] },
  same_area: [
    { name: 'Soon Towers', slug: 'soon-towers', completion_now: '2027-12-31' },
    { name: 'Close Call', slug: 'close-call', completion_now: '2030-06-30' },
    { name: 'Already Due', slug: 'already-due', completion_now: '2026-01-31' },
  ],
}

// a page of two registrations: the record (120 homes) is one wing; the project is 300 homes, 90 booked
const TWO_WINGS: RegisterProject = {
  ...IVARA, slug: 'two-wings', name: 'TWO WINGS A', marketed_name: 'Two Wings', regno: 'P52100066666', units_total: 120, units_booked: 10,
  prices: null, area_rate: null, builder: null, same_area: [],
  project: { registrations: 2, regnos: ['P52100066666', 'P52100066667'], units_total: 300, units_counted: 2, units_booked: 90, booked_of: 300,
    booked_counted: 2, completion_first: '2029-03-31', completion_last: '2031-03-31', completion_passed: false },
}

beforeEach(() => window.localStorage.clear())

describe('the compare and shortlist lists', () => {
  it('reads only real project slugs from the link, each once, up to the most', () => {
    expect(parseSlugs('godrej-ivara-pune,,BAD SLUG,godrej-ivara-pune,lodha-camelot', 3)).toEqual(['godrej-ivara-pune', 'lodha-camelot'])
    expect(parseSlugs(['a', 'b,c', 'd'], COMPARE_MAX)).toEqual(['a', 'b', 'c'])
    expect(parseSlugs(undefined, 3)).toEqual([])
  })

  it('a full list drops its oldest pick, and a second press takes a pick out', () => {
    expect(toggle(['a', 'b', 'c'], 'd', 3)).toEqual(['b', 'c', 'd'])
    expect(toggle(['a', 'b'], 'a', 3)).toEqual(['b'])
  })

  it('the links carry the list, so a shared link opens the same projects', () => {
    expect(comparePath(['a', 'b'])).toBe('/compare?projects=a,b')
    expect(shortlistPath(['a'])).toBe('/shortlist?ids=a')
    const msg = shortlistMessage(['Godrej Ivara', 'Lodha Camelot'], 'https://avasetu.in/shortlist?ids=a,b')
    expect(msg).toContain('1. Godrej Ivara\n2. Lodha Camelot')
    expect(whatsappShare(msg)).toBe('https://wa.me/?text=' + encodeURIComponent(msg))
  })
})

describe('the side-by-side table', () => {
  it('says each fact the project page says, and the all-in cost on the lowest published price', () => {
    const rows = Object.fromEntries(compareRows([IVARA]).map((r) => [r.key, r.cells[0]]))
    expect(rows.price?.text).toBe('From ₹90 L')
    expect(rows['all-in']?.text).toMatch(/^About ₹/)
    expect(rows['per-sqft']?.sub).toBe('Upper Kharadi middle ₹9,800 (6 projects)')
    expect(rows.booked).toEqual({ text: '25% booked', sub: '100 of 400 homes' })
    expect(rows.open?.text).toBe('300 homes')
    expect(rows.moved?.text).toBe('Moved 6 months later')
    expect(rows.towers?.text).toBe('4 towers, up to 30 floors')
    expect(rows.builder).toMatchObject({ text: '3 of 9 moved their date', href: '/builders/godrej-properties' })
  })

  it('compares a page of several registrations as the whole project, never one wing (CLAUDE.md rule 11)', () => {
    const rows = Object.fromEntries(compareRows([TWO_WINGS]).map((r) => [r.key, r.cells[0]]))
    expect(rows.booked?.text).toBe('30% booked')
    expect(rows.booked?.sub).toContain('90 of 300 homes')
    expect(rows.possession?.sub).toBe('to Mar 2031, by registration')
    expect(rows.towers).toBeUndefined()
    expect(rows.moved?.text).toBe('See each registration')
    expect(briefLine(TWO_WINGS)).toContain('30% booked')
  })

  it('leaves out a row no project has a fact for, and dashes a missing one', () => {
    const rows = compareRows([IVARA, TWO_WINGS])
    expect(rows.find((r) => r.key === 'from-space')).toBeUndefined()
    expect(rows.find((r) => r.key === 'price')?.cells[1]).toBeNull()
  })
})

describe('possession sooner nearby', () => {
  it('names projects still to come whose filed date is a year or more earlier, soonest first', () => {
    expect(soonerNearby(IVARA, TODAY)).toEqual([{ name: 'Soon Towers', slug: 'soon-towers', on: '2027-12-31', months: 36 }])
  })

  it('shows on the project page as a link to compare the two', () => {
    render(<RegisterProjectPage p={IVARA} siteUrl="https://avasetu.in" facts={null} />)
    const line = screen.getByTestId('sooner-nearby')
    expect(line).toHaveTextContent('Want possession sooner? Soon Towers is filed for Dec 2027, 3 years earlier: compare the two.')
    expect(line.querySelector('a')).toHaveAttribute('href', '/compare?projects=godrej-ivara-pune,soon-towers')
    expect(screen.getByTestId('pick-buttons')).toBeInTheDocument()
  })
})

describe('compare and save without signing in', () => {
  it('keeps the picks in this browser and shows the bar with them', () => {
    render(<><PicksBar /><PickButtons slug="godrej-ivara-pune" name="Godrej Ivara" /><PickButtons slug="lodha-camelot" name="Lodha Camelot" /></>)
    expect(screen.queryByTestId('picks-bar')).not.toBeInTheDocument()
    const [compareA, compareB] = screen.getAllByTestId('pick-compare')
    act(() => { fireEvent.click(compareA) })
    expect(screen.getByTestId('picks-bar')).toHaveTextContent('Pick one more to compare')
    act(() => { fireEvent.click(compareB) })
    expect(window.localStorage.getItem(COMPARE_KEY)).toBe('godrej-ivara-pune,lodha-camelot')
    expect(screen.getByTestId('picks-compare')).toHaveAttribute('href', '/compare?projects=godrej-ivara-pune,lodha-camelot')
    act(() => { fireEvent.click(screen.getAllByTestId('pick-save')[0]) })
    expect(readPicks('saved')).toEqual(['godrej-ivara-pune'])
    expect(window.localStorage.getItem(SAVED_KEY)).toBe('godrej-ivara-pune')
    expect(screen.getByTestId('picks-shortlist')).toHaveAttribute('href', '/shortlist?ids=godrej-ivara-pune')
    expect(screen.getAllByTestId('pick-save')[0]).toHaveAttribute('aria-pressed', 'true')
  })
})
