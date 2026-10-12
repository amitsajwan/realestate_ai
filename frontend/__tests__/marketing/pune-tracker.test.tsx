import React from 'react'
import { render, screen, within } from '@testing-library/react'

// The tracker reads every area's MahaRERA stats from the API: replaced here.
const mockFetch = jest.fn()
jest.mock('@/lib/site/api', () => ({ fixturesForced: () => false, serverApiBase: () => 'http://api' }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
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

  it('an outage gives the refreshing note, kept out of search', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) })
    expect(await getCityStats()).toBeNull()
    mockFetch.mockRejectedValue(new Error('down'))
    expect(await getCityStats()).toBeNull()
    render(await TrackerPage())
    expect(screen.getByText(/being refreshed/)).toBeTruthy()
    expect((await generateMetadata()).robots).toEqual({ index: false, follow: true })
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => BODY })
    expect((await generateMetadata()).robots).toBeUndefined()
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
