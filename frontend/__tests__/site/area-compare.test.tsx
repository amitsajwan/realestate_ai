import React from 'react'
import { render, screen, within } from '@testing-library/react'
import AreaCompareView, { PairLinks, compareLead, compareQuestions } from '@/components/localities/AreaCompare'
import { getLocality } from '@/lib/marketing/localities'
import { cleanAreaCompare, cleanPairs, pairsWith, type AreaCompare } from '@/lib/site/compare'

const maps = (lat: number, lon: number) => `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`
const area = (key: string, name: string, slug: string) => ({ key, name, slug, tier: 'it' })
const side = (a: ReturnType<typeof area>, extra: Record<string, unknown> = {}) => ({
  area: a, as_of: '2026-11-20', projects: 120, units_total: 9000, units_booked: 6300, registered_this_year: 14,
  registered_last_year: 11, completing_this_year: 9, completing_next_year: 17,
  metro: { name: 'Ramwadi', line_short: 'Aqua Line (Line 2)', km: 6 }, dates: { with_dates: 40, moved: 10, median_months: 9 }, ...extra,
})
const KHARADI = area('kharadi', 'Kharadi', 'kharadi')
const WAGHOLI = area('wagholi', 'Wagholi', 'wagholi')

// the backend's answer for Kharadi and Wagholi (areastats/compare.py), shortened, with made-up counts
const RAW = {
  slug: 'kharadi-vs-wagholi', as_of: '2026-11-20', apart_km: 5,
  sides: [side(KHARADI), side(WAGHOLI, { projects: 210, units_total: null, units_booked: null, metro: null, dates: null,
    registered_this_year: 30 })],
  distances: [
    { key: 'eon', name: 'EON IT Park (EON Free Zone)', kind: 'work', kind_label: 'Work', a_km: 1, b_km: 6, maps: maps(18.551815, 73.951153), source: 'OSM' },
    { key: 'airport', name: 'Pune Airport', kind: 'travel', kind_label: 'Travel', a_km: 6, b_km: 7.5, maps: maps(18.580375, 73.918227), source: 'OSM' },
    { key: 'bad', name: 'Somewhere', kind: 'work', kind_label: 'Work', a_km: 2, b_km: 3, maps: 'https://evil.example/x', source: '' },
  ],
  related: [{ slug: 'kharadi-vs-upper-kharadi', a: KHARADI, b: area('upper_kharadi', 'Upper Kharadi', 'upper-kharadi'), apart_km: 2.5 }],
  note: 'Straight-line distances from the middle of each area, rounded; not travel times.',
  attribution: 'Positions © OpenStreetMap contributors', source: 'MahaRERA public records',
}

const clean = () => cleanAreaCompare(RAW, 'kharadi-vs-wagholi') as AreaCompare

describe('two areas side by side', () => {
  it('keeps only the pair asked for, in its one order', () => {
    expect(clean().sides.map((s) => s.area.slug)).toEqual(['kharadi', 'wagholi'])
    expect(cleanAreaCompare(RAW, 'wagholi-vs-kharadi')).toBeNull()
    expect(cleanAreaCompare({ ...RAW, sides: [RAW.sides[0]] }, 'kharadi-vs-wagholi')).toBeNull()
    expect(cleanAreaCompare(null, 'kharadi-vs-wagholi')).toBeNull()
  })

  it('drops a distance whose map link is not Google Maps', () => {
    expect(clean().distances.map((d) => d.key)).toEqual(['eon', 'airport'])
  })

  it('opens with a dated answer from both columns and names no winner', () => {
    const lead = compareLead(clean())
    expect(lead).toBe('As of 20 November 2026, MahaRERA lists 120 projects in Kharadi with 9,000 homes and 210 in Wagholi. '
      + 'The middles of the two areas are about 5 km apart.')
    expect(lead).not.toMatch(/better|best|cheaper/i)
  })

  it('shows each figure under its own area, and says plainly what is not known', () => {
    render(<AreaCompareView c={clean()} guides={[getLocality('kharadi'), getLocality('wagholi')]} />)
    const register = within(screen.getByTestId('area-compare')).getAllByRole('table')[0]
    const row = (label: string | RegExp) => within(register).getByRole('row', { name: label })
    expect(within(row(/^Homes booked/)).getAllByRole('cell').map((c) => c.textContent))
      .toEqual(['6,300 of 9,000 (70%)', 'Not reported for every project'])
    expect(within(row(/moved the possession date/)).getAllByRole('cell').map((c) => c.textContent))
      .toEqual(['10 of 40 (25%), by 9 months in the middle case', 'No project being built with both dates'])
    expect(within(row(/Nearest metro/)).getAllByRole('cell').map((c) => c.textContent))
      .toEqual(['Ramwadi, Aqua Line (Line 2): about 6 km', 'None within reach yet'])
    expect(within(row('Registered in 2026 so far 14 30')).getAllByRole('cell')).toHaveLength(2)
  })

  it('measures the same places from both areas and bolds the nearer', () => {
    render(<AreaCompareView c={clean()} guides={[undefined, undefined]} />)
    const eon = screen.getByRole('row', { name: /EON IT Park/ })
    const [k, w] = within(eon).getAllByRole('cell')
    expect([k.textContent, w.textContent]).toEqual(['1 km', '6 km'])
    expect(k.className).toContain('font-bold')
    expect(w.className).not.toContain('font-bold')
    expect(within(eon).getByRole('link').getAttribute('href')).toBe(maps(18.551815, 73.951153))
    expect(screen.queryByText('Who each area suits')).toBeNull()   // without both guides, no half-filled section
  })

  it('answers the searched questions from the page figures only', () => {
    const qs = compareQuestions(clean())
    expect(qs.map((q) => q.q)).toEqual([
      'How far is Kharadi from Wagholi?',
      'Which has more new projects, Kharadi or Wagholi?',
      'Is Kharadi or Wagholi closer to EON IT Park (EON Free Zone)?',
    ])
    expect(qs[1].a).toContain('MahaRERA lists 210 projects in Wagholi and 120 in Kharadi')
    expect(qs[2].a).toMatch(/^Kharadi: about 1 km from its middle, against about 6 km from Wagholi's/)
  })

  it('links an area guide to its pairs, nearest first', () => {
    const pairs = cleanPairs([
      { slug: 'kharadi-vs-lohegaon', a: KHARADI, b: area('lohegaon', 'Lohegaon', 'lohegaon'), apart_km: 6.5 },
      { slug: 'kharadi-vs-wagholi', a: KHARADI, b: WAGHOLI, apart_km: 5 },
      { slug: 'hinjawadi-vs-wakad', a: area('hinjawadi', 'Hinjawadi', 'hinjawadi'), b: area('wakad', 'Wakad', 'wakad'), apart_km: 3 },
      { slug: 'wrong-slug', a: KHARADI, b: WAGHOLI, apart_km: 5 },
    ])
    expect(pairs).toHaveLength(3)
    const mine = pairsWith(pairs, 'kharadi')
    render(<PairLinks pairs={mine} title="Compare Kharadi with nearby areas" />)
    expect(screen.getAllByRole('link').map((a) => [a.textContent, a.getAttribute('href')])).toEqual([
      ['Kharadi vs Wagholi', '/localities/compare/kharadi-vs-wagholi'],
      ['Kharadi vs Lohegaon', '/localities/compare/kharadi-vs-lohegaon'],
    ])
  })

  it('shows no links when there are no pairs', () => {
    const { container } = render(<PairLinks pairs={[]} title="x" />)
    expect(container.innerHTML).toBe('')
  })
})
