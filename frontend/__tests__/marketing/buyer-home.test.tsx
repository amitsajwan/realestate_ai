import React from 'react'
import { render, screen, within } from '@testing-library/react'
import BuyerHome, { metadata } from '@/app/page'

jest.mock('@/components/news/NewsSection', () => ({ __esModule: true, default: () => null }))
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), usePathname: () => '/' }))

const API: Record<string, unknown> = {
  '/public/areas/stats': { as_of: '2026-10-21', source: 'MahaRERA', areas: [
    { area: { key: 'kharadi', name: 'Kharadi', slug: 'kharadi', tier: 'it' }, as_of: '2026-10-21', projects: 66, completing: [], units_total: null, units_booked: null, recent: [], source: 'MahaRERA' },
  ] },
  '/public/register/places': [{ key: 'kharadi', slug: 'kharadi', name: 'Kharadi', zone: 'East', projects: 66, indexable: 40 },
    { key: 'wagholi', slug: 'wagholi', name: 'Wagholi', zone: 'East', projects: 80, indexable: 0 }],
  '/public/facets': [
    { key: 'k1', path: '/projects/area/kharadi/new-launches', place: 'kharadi', place_slug: 'kharadi', intent: 'new-launches', possession: null, builder: null, label: 'New launches in Kharadi', count: 7, indexable: true, page_updated: null },
    { key: 'k2', path: '/projects/area/kharadi/new-launches/by-lodha', place: 'kharadi', place_slug: 'kharadi', intent: 'new-launches', possession: null, builder: 'lodha', label: 'x', count: 3, indexable: true, page_updated: null },
  ],
  '/public/register/spotlight': [{ slug: 'lodha-camelot-kharadi', name: 'Lodha Camelot', area: 'Kharadi', area_slug: 'kharadi', note: 'New tower registered', fact: 'f', source: 'MahaRERA', picked: true }],
  '/public/builders': [{ slug: 'lodha', name: 'Lodha', projects: 9, indexable: true, page_updated: null, brand: true },
    { slug: 'thin', name: 'Thin Builder', projects: 1, indexable: false, page_updated: null }],
}

beforeEach(() => {
  global.fetch = jest.fn(async (url: string) => {
    const key = Object.keys(API).find((k) => new URL(String(url)).pathname.endsWith(k))
    return key ? ({ ok: true, status: 200, json: async () => API[key] } as Response) : ({ ok: false, status: 404, json: async () => ({}) } as Response)
  }) as unknown as typeof fetch
})

describe("buyers' home", () => {
  it('is about new projects in Pune, for Google and for people', async () => {
    expect(String(metadata.title)).toMatch(/^New Projects in Pune/)
    expect(metadata.alternates?.canonical).toMatch(/\/?$/)
    render(await BuyerHome())
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/new projects in pune/i)
    expect(screen.getByText(/66 projects in our areas, read from MahaRERA/i)).toBeInTheDocument()
    const ask = screen.getAllByRole('link', { name: /tell us what you need/i })   // the header button and the hero's
    expect(ask.length).toBe(2)
    for (const a of ask) expect(a).toHaveAttribute('href', '/agent/avasetu#enquire')
  })

  it('links the hottest projects, every area, the live lists and builders with pages', async () => {
    render(await BuyerHome())
    expect(within(screen.getByTestId('home-hot')).getByRole('link', { name: /lodha camelot/i })).toHaveAttribute('href', '/projects/lodha-camelot-kharadi')
    expect(screen.queryByTestId('hot-strip')).toBeNull()   // the section replaces the banner here: the same links once
    const it = screen.getByTestId('home-areas-it')
    expect(within(it).getByRole('link', { name: 'New projects in Kharadi' })).toHaveAttribute('href', '/projects/area/kharadi')
    expect(within(it).getByRole('link', { name: 'Living in Kharadi' })).toHaveAttribute('href', '/localities/kharadi')
    // an area whose list is not in search yet links its guide, never a noindex page
    expect(within(screen.getByTestId('home-areas-affordable')).getByRole('link', { name: 'Wagholi' })).toHaveAttribute('href', '/localities/wagholi')
    const launches = within(screen.getByTestId('home-launches')).getAllByRole('link')
    expect(launches.map((a) => a.getAttribute('href'))).toEqual(['/projects/area/kharadi/new-launches'])   // builder lists stay on their place
    const builders = within(screen.getByTestId('home-builders')).getAllByRole('link')
    expect(builders.map((a) => a.getAttribute('href'))).toEqual(['/builders/lodha'])
  })

  it('names the search box target for Google and sends agents to /agents', async () => {
    const { container } = render(await BuyerHome())
    const ld = Array.from(container.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.textContent || '{}'))
    expect(ld.map((x) => x['@type'])).toEqual(['Organization', 'WebSite'])
    expect(ld[1].potentialAction.target.urlTemplate).toMatch(/\/projects\?q=\{search_term_string\}$/)
    expect(ld[0].contactPoint).toBeUndefined()
    expect(screen.getAllByRole('link', { name: /^for agents$/i }).every((a) => a.getAttribute('href') === '/agents')).toBe(true)
  })

  it('still renders, with the areas, when the API is down', async () => {
    global.fetch = jest.fn(async () => { throw new Error('down') }) as unknown as typeof fetch
    render(await BuyerHome())
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(within(screen.getByTestId('home-areas-it')).getByRole('link', { name: 'Kharadi' })).toHaveAttribute('href', '/localities/kharadi')
    expect(screen.queryByTestId('home-hot')).toBeNull()
  }, 30000)   // the register reads wait out their retries (lib/site/retry) before giving up
})
