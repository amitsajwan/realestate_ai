import React from 'react'
import { render, screen, within } from '@testing-library/react'

// The tracker reads every area's MahaRERA stats from the API: replaced here.
const mockFetch = jest.fn()
jest.mock('@/lib/site/api', () => ({ fixturesForced: () => false, serverApiBase: () => 'http://api' }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
// the pages a count can open: the area's project list and its live "possession <year>" lists
const mockPlaces = jest.fn(async () => [] as unknown[])
const mockFacets = jest.fn(async () => [] as unknown[])
jest.mock('@/lib/site/register', () => ({ ...jest.requireActual('@/lib/site/register'), getRegisterPlaces: () => mockPlaces() }))
jest.mock('@/lib/site/facets', () => ({ ...jest.requireActual('@/lib/site/facets'), getFacets: () => mockFacets() }))
jest.mock('@/components/marketing/AgentStrip', () => ({ __esModule: true, default: () => null }))

import TrackerPage, { generateMetadata } from '@/app/pune-maharera-tracker/page'
import { cleanCityStats, getCityStats } from '@/components/localities/areaStats'

const area = (slug: string, name: string, extra: Record<string, unknown>) => ({
  area: { key: slug.replace('-', '_'), name, slug, tier: 'affordable' }, as_of: '2026-10-04', projects: 0, completing: [],
  units_total: null, units_booked: null, recent: [], source: 'MahaRERA public records', ...extra,
})
const BODY = {
  as_of: '2026-10-04', source: 'MahaRERA public records',
  areas: [
    area('wagholi', 'Wagholi', { projects: 41, completing: [{ year: 2026, projects: 6 }, { year: 2027, projects: 12 }], units_total: 5210, units_booked: 3100 }),
    area('kharadi', 'Kharadi', { projects: 20, completing: [{ year: 2027, projects: 4 }] }),
    area('baner', 'Baner', { projects: 0 }),
  ],
}

beforeEach(() => {
  mockFetch.mockReset()
  mockPlaces.mockResolvedValue([])
  mockFacets.mockResolvedValue([])
  global.fetch = mockFetch as unknown as typeof fetch
})

describe('Pune MahaRERA tracker', () => {
  it('reads all areas, leaving out areas with no projects', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => BODY })
    const c = await getCityStats()
    expect(mockFetch.mock.calls[0][0]).toBe('http://api/api/v1/public/areas/stats')
    expect(c?.areas.map((a) => a.area.slug)).toEqual(['wagholi', 'kharadi'])
    expect(c?.asOf).toBe('2026-10-04')
    expect(cleanCityStats({ areas: [] })).toBeNull()
  })

  it('a failed read before any figures is an error page, never an empty page that asks to leave search', async () => {
    mockFetch.mockRejectedValue(new Error('down'))
    let fresh: typeof import('@/app/pune-maharera-tracker/page') | undefined
    jest.isolateModules(() => { fresh = require('@/app/pune-maharera-tracker/page') })   // nothing read yet in this process
    await expect(fresh!.generateMetadata()).rejects.toThrow(/temporarily unavailable/)
    await expect(fresh!.default()).rejects.toThrow(/temporarily unavailable/)
  })

  it('a slow or failed read keeps the last figures, and the page stays in search', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => BODY })
    expect((await getCityStats())?.asOf).toBe('2026-10-04')
    mockFetch.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) })
    expect((await getCityStats())?.asOf).toBe('2026-10-04')
    mockFetch.mockRejectedValue(new Error('timeout'))
    expect((await getCityStats())?.areas.map((a) => a.area.slug)).toEqual(['wagholi', 'kharadi'])
    expect((await generateMetadata()).robots).toBeUndefined()
    render(await TrackerPage())
    expect(screen.queryByText(/being refreshed/)).toBeNull()
    expect(screen.getAllByRole('row').some((r) => r.textContent?.startsWith('Wagholi'))).toBe(true)
  })

  it('shows each area linked to its guide, totals without partial sums, and a citation', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => BODY })
    const { container } = render(await TrackerPage())
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Pune MahaRERA tracker')
    const rows = screen.getAllByRole('row')
    const wagholi = rows.find((r) => r.textContent?.startsWith('Wagholi'))!
    expect(within(wagholi).getByRole('link').getAttribute('href')).toBe('/localities/wagholi')
    expect(wagholi.textContent).toContain('3,100 of 5,210')
    const kharadi = rows.find((r) => r.textContent?.startsWith('Kharadi'))!
    expect(kharadi.textContent).toContain('n/a')
    const all = rows.find((r) => r.textContent?.startsWith('All areas'))!
    expect(all.textContent).toBe('All areas61n/a616')   // projects, booked (unknown for Kharadi), due 2026, due 2027
    expect(screen.getByText(/as of 4 October 2026\.$/).textContent).toContain('/pune-maharera-tracker')
    const ld = [...container.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent || '{}'))
    expect(ld.find((x) => x['@type'] === 'Dataset')).toMatchObject({ dateModified: '2026-10-04', isAccessibleForFree: true })
  })
})

describe('the tracker\'s counts', () => {
  it('open the area\'s project list and its possession-year list, only where those pages exist', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => BODY })
    mockPlaces.mockResolvedValue([{ key: 'wagholi', slug: 'wagholi', name: 'Wagholi', zone: 'East', projects: 41, indexable: 40 }])
    mockFacets.mockResolvedValue([
      { key: 'w27', path: '/projects/area/wagholi/possession-2027', place: 'wagholi', place_slug: 'wagholi', intent: 'all', possession: 2027, builder: null, label: '', count: 11, indexable: true, page_updated: null },
      { key: 'w27b', path: '/projects/area/wagholi/2-bhk/possession-2026', place: 'wagholi', place_slug: 'wagholi', intent: 'all', possession: 2026, builder: null, bhk: 2, label: '', count: 3, indexable: true, page_updated: null },
    ])
    render(await TrackerPage())
    const rows = screen.getAllByRole('row')
    const wagholi = rows.find((r) => r.textContent?.startsWith('Wagholi'))!
    expect(within(wagholi).getByRole('link', { name: '41 projects in Wagholi' })).toHaveAttribute('href', '/projects/area/wagholi')
    expect(within(wagholi).getByRole('link', { name: '12 projects in Wagholi due 2027' })).toHaveAttribute('href', '/projects/area/wagholi/possession-2027')
    expect(within(wagholi).queryByRole('link', { name: /due 2026/ })).toBeNull()   // a 2 BHK list is not the year's list
    const kharadi = rows.find((r) => r.textContent?.startsWith('Kharadi'))!
    expect(within(kharadi).getAllByRole('link')).toHaveLength(1)   // only its guide: no project list or year list here
  })
})

describe('Possession dates that moved', () => {
  const moves = (with_dates: number, moved: number, extension_only: number, median_months: number | null, biggest: unknown[] = []) =>
    ({ with_dates, moved, extension_only, median_months, biggest })
  const MOVES = {
    ...BODY,
    areas: [
      area('wagholi', 'Wagholi', { projects: 41, date_moves: moves(30, 6, 9, 8, [
        { name: 'Gagan Micasaa', page: '/projects/gagan-micasaa', regno: 'P52100000001', months: 14, from: '2027-06-30', to: '2028-12-31' }]) }),
      area('kharadi', 'Kharadi', { projects: 20, date_moves: moves(10, 2, 3, 5, [
        { name: 'Bad page', page: 'https://elsewhere.com', regno: 'P52100000002', months: 20, from: '2027-01-31', to: '2028-09-30' }]) }),
    ],
  }

  it('says how many builders moved their date, area by area, net of MahaRERA\'s extension, biggest moves first', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => MOVES })
    render(await TrackerPage())
    const report = screen.getByTestId('date-moves')
    expect(screen.getByTestId('date-moves-answer')).toHaveTextContent('the builders of 8 of 40 home projects still being built in these areas (20%)')
    expect(within(report).getAllByRole('row').find((r) => r.textContent?.startsWith('Wagholi'))).toHaveTextContent('Wagholi306 (20%)8 months9')
    const items = within(report).getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('Bad page (Kharadi): filed for 31 January 2027 at registration, now 30 September 2028, 20 months later')
    expect(within(items[0]).queryByRole('link')).toBeNull()   // only our own project pages are linked
    expect(within(items[1]).getByRole('link', { name: 'Gagan Micasaa' }).getAttribute('href')).toBe('/projects/gagan-micasaa')
  })

  it('leaves out figures that do not add up', () => {
    expect(cleanCityStats({ ...MOVES, areas: [area('wagholi', 'Wagholi', { projects: 3, date_moves: moves(2, 2, 1, 3) })] })?.areas[0].date_moves).toBeNull()
  })
})
