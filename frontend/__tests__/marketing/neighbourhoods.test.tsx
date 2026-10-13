import React from 'react'
import { render, screen } from '@testing-library/react'

// Neighbourhood articles come from the communities bot's public API: replaced here.
const mockFetch = jest.fn()
jest.mock('@/lib/site/api', () => ({ fixturesForced: () => false, serverApiBase: () => 'http://api' }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('@/components/marketing/AgentStrip', () => ({ __esModule: true, default: () => null }))
jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NOT_FOUND') } }))

import CommunityPage, { generateMetadata } from '@/app/localities/[slug]/[community]/page'
import { cleanCard, getCommunities, getCommunity } from '@/components/localities/communities'

const CARD = { area: 'wagholi', area_name: 'Wagholi', area_slug: 'wagholi', slug: 'kesnand', name: 'Kesnand', title: 'Kesnand, Wagholi: a neighbourhood guide', summary: 'Kesnand is a neighbourhood in Wagholi.', updated: '2026-10-12' }
const ARTICLE = {
  ...CARD, paragraphs: ['Kesnand is a neighbourhood in the Wagholi area.', 'There is a school nearby.'], published: '2026-10-01',
  osm_url: 'https://www.openstreetmap.org/node/1', sources: ['OpenStreetMap', 'MahaRERA public records'],
  facts: { nearby: [{ kind: 'School', name: 'Kesnand ZP School', km: 0.2 }], area_projects: 41, as_of: '2026-10-04',
    projects: [{ name: 'Kesnand Heights', regno: 'P1', promoter: 'Rohan Builders', completion: '2028-06-30', page: '/projects/kesnand-heights-wagholi' },
      { name: 'Odd', regno: 'P2', page: 'https://evil.example/x' }] },
}

function routes(map: Record<string, { status: number; body: unknown }>) {
  mockFetch.mockImplementation(async (url: string) => {
    const hit = Object.keys(map).find((k) => url.endsWith(k))
    const r = hit ? map[hit] : { status: 500, body: {} }
    return { ok: r.status === 200, status: r.status, json: async () => r.body }
  })
}

beforeEach(() => { mockFetch.mockReset(); global.fetch = mockFetch as unknown as typeof fetch })

describe('neighbourhood articles', () => {
  it('keeps only well-formed cards and hides the list on any failure', async () => {
    expect(cleanCard({ ...CARD, slug: 'Bad Slug' })).toBeNull()
    routes({ '/communities?area=wagholi': { status: 200, body: [CARD, { nope: 1 }] } })
    expect((await getCommunities('wagholi')).map((c) => c.slug)).toEqual(['kesnand'])
    routes({})
    expect(await getCommunities('wagholi')).toEqual([])
  })

  it('a 404 is not found, an outage throws, a foreign project link is dropped', async () => {
    routes({ '/communities/wagholi/kesnand': { status: 200, body: ARTICLE }, '/communities/wagholi/gone': { status: 404, body: {} } })
    expect((await getCommunity('wagholi', 'kesnand'))?.facts.projects.map((p) => p.page)).toEqual(['/projects/kesnand-heights-wagholi', null])
    expect(await getCommunity('wagholi', 'gone')).toBeNull()
    routes({})
    await expect(getCommunity('wagholi', 'kesnand')).rejects.toThrow()
  })

  it('renders the article with its facts, sources and structured data', async () => {
    routes({ '/communities/wagholi/kesnand': { status: 200, body: ARTICLE },
      '/communities?area=wagholi': { status: 200, body: [CARD, { ...CARD, slug: 'ubale-nagar', name: 'Ubale Nagar' }] } })
    const props = { params: Promise.resolve({ slug: 'wagholi', community: 'kesnand' }) }
    const { container } = render(await CommunityPage(props))
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe(CARD.title)
    expect(screen.getByText('Kesnand ZP School')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Kesnand Heights' }).getAttribute('href')).toBe('/projects/kesnand-heights-wagholi')
    expect(screen.getByRole('link', { name: 'Ubale Nagar' }).getAttribute('href')).toBe('/localities/wagholi/ubale-nagar')
    expect(screen.getByText(/Written automatically from OpenStreetMap and MahaRERA public records/)).toBeTruthy()
    const ld = [...container.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent || '{}'))
    expect(ld.find((x) => x['@type'] === 'Article')).toMatchObject({ headline: CARD.title, dateModified: '2026-10-12' })
    expect((await generateMetadata(props)).alternates?.canonical).toMatch(/\/localities\/wagholi\/kesnand$/)
  })

  it('an article from another area, or none, is a 404 and kept out of search', async () => {
    routes({ '/communities/kharadi/kesnand': { status: 404, body: {} } })
    const props = { params: Promise.resolve({ slug: 'kharadi', community: 'kesnand' }) }
    await expect(CommunityPage(props)).rejects.toThrow('NOT_FOUND')
    expect((await generateMetadata(props)).robots).toEqual({ index: false })
  })
})
