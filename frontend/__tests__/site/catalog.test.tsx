import React from 'react'
import { render, screen, within } from '@testing-library/react'
import type { CatalogProject } from '@/lib/site/types'

// Avasetu's shared project pages read the catalog from the API: replaced here by a fixed list.
const mockCatalog = jest.fn<Promise<CatalogProject[]>, [string?]>()
const mockOne = jest.fn<Promise<CatalogProject | null>, [string]>()
const mockEntries = jest.fn(async (): Promise<{ listings: unknown[]; projects: unknown[] }> => ({ listings: [], projects: [] }))
jest.mock('@/lib/site/api', () => ({
  getCatalog: (l?: string) => mockCatalog(l),
  getCatalogProject: (s: string) => mockOne(s),
  getLocalityListings: async () => [],
  getSitemapEntries: () => mockEntries(),
  fixturesForced: () => true, // news falls back to its fixtures
  serverApiBase: () => 'http://api',
}))
jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))
// Avasetu's own register pages (lib/site/register): none in these tests, so unknown slugs are 404s as before
const mockRegister = jest.fn(async (): Promise<unknown[]> => [])
const mockPlaces = jest.fn(async (): Promise<unknown[]> => [])
// the project page a listing's MahaRERA number shows (a tower merged into its project is looked up, not in the register list)
const mockProjectOfListing = jest.fn(async (_regno?: string | null): Promise<string | null> => null)
jest.mock('@/lib/site/register', () => ({ getRegisterProject: async () => null, getRegisterProjects: () => mockRegister(), longDay: () => '',
  getRegisterPlaces: () => mockPlaces(), placePath: (s: string) => `/projects/area/${s}`,
  projectPageOfListing: (r?: string | null) => mockProjectOfListing(r),
  regnoKey: (r?: string | null) => (r || '').trim().toUpperCase() }))
// topic guides (lib/site/topics): none unless a test sets them
const mockTopics = jest.fn(async (): Promise<unknown[]> => [])
jest.mock('@/lib/site/topics', () => ({ ...jest.requireActual('@/lib/site/topics'), fetchTopics: () => mockTopics() }))
const mockRedirect = jest.fn((url: string) => { throw new Error('REDIRECT ' + url) })
const mockNotFound = jest.fn(() => { throw new Error('NOT_FOUND') })
jest.mock('next/navigation', () => ({
  permanentRedirect: (u: string) => mockRedirect(u),
  notFound: () => mockNotFound(),
  usePathname: () => '/',
  useRouter: () => ({ push: jest.fn() }),
}))

import SharedProjectPage, { generateMetadata } from '@/app/projects/[slug]/page'
import TwoBhk from '@/app/2-bhk/[area]/page'
import { BANDS, filterProjects, livePages, matches, MIN_PROJECTS } from '@/lib/site/filters'
import { getLocality } from '@/lib/marketing/localities'
import { byLocality, mainAgent } from '@/lib/site/projects'
import { projectMetadata } from '@/lib/site/seo'
import sitemap, { sitemapGroups } from '@/lib/site/sitemap'

function project(slug: string, locality: string, homes: Array<[number, number]>, extra: Partial<CatalogProject> = {}): CatalogProject {
  const configurations = homes.map(([bhk, price]) => ({ label: `${bhk} BHK`, bhk, carpet_sqft: 800, price_inr: price, price_per_sqft: Math.round(price / 800), source: 'agent' as const }))
  return {
    id: slug, slug, name: slug.replace(/-/g, ' '), builder: 'B', locality, address: '', pincode: '', rera_no: 'P52100000' + slug.length.toString().padStart(3, '0'),
    scope_note: '', configurations, price_min: Math.min(...homes.map((h) => h[1])), price_max: Math.max(...homes.map((h) => h[1])),
    bhk_options: [...new Set(homes.map((h) => h[0]))], possession_target: null, positioning: '', who_it_suits: [], highlights: [], amenities: [],
    specs: {}, provenance: {}, nearby: [], place: null, maps_query: slug, media: [],
    rera: { regno: 'P1', name: '', promoter: '', project_type: '', registered_on: null, completion_at_registration: null, completion_now: '2029-04-30', units_total: 100, units_booked: 50, url: 'https://maharerait.maharashtra.gov.in/x', checked_at: '2026-10-03' },
    booked_pct: 50, completion_moved_months: 0, catalog_slug: slug,
    agents: [{ slug: 'house-deal', name: 'House Deal', phone: '+919876543210', project_slug: slug }],
    ...extra,
  }
}

const L = 100_000
const WAGHOLI = [
  project('amco-equa', 'Wagholi', [[2, 66 * L], [3, 90 * L]]),
  project('anshul-medora', 'Wagholi', [[2, 72 * L]]),
  project('rohan-abhilasha-4', 'Wagholi', [[2, 70 * L], [2.5, 82 * L]]),
  project('triaa-kosmic', 'Wagholi', [[3, 98 * L]]),
]
const GOYAL = project('goyal-my-home-kharadi', 'Upper Kharadi', [[2, 97 * L], [3, 125 * L]], {
  agents: [
    { slug: 'house-deal', name: 'House Deal', phone: '+919876543210', project_slug: 'goyal-my-home-kharadi' },
    { slug: 'zeta', name: 'Zeta Homes', phone: null, project_slug: 'my-home-upper-kharadi' },
  ],
})
const ALL = [GOYAL, ...WAGHOLI]

beforeEach(() => {
  mockCatalog.mockImplementation(async (l?: string) => (l ? ALL.filter((p) => p.locality.toLowerCase() === l.toLowerCase()) : ALL))
  mockOne.mockImplementation(async (s: string) => ALL.find((p) => p.slug === s || p.agents.some((a) => a.project_slug === s)) ?? null)
  process.env.NEXT_PUBLIC_SITE_URL = 'https://avasetu.in'
})

describe('filter pages only exist with enough real projects', () => {
  const wagholi = getLocality('wagholi')!
  it('matches 2 BHK pages to 2 and 2.5 BHK homes, and bands by quoted price', () => {
    expect(matches({ kind: 'bhk', bhk: 2 }, WAGHOLI[2].configurations[1])).toBe(true) // 2.5 BHK
    expect(matches({ kind: 'bhk', bhk: 2 }, WAGHOLI[0].configurations[1])).toBe(false)
    const band = BANDS.find((b) => b.slug === '50-75-lakh')!
    expect(filterProjects(ALL, wagholi, { kind: 'band', band }).map((m) => m.project.slug)).toEqual(['amco-equa', 'rohan-abhilasha-4', 'anshul-medora'])
  })

  it('lists a page only when at least MIN_PROJECTS projects match', () => {
    expect(MIN_PROJECTS).toBe(3)
    const paths = livePages(ALL).map((p) => p.path)
    expect(paths).toContain('/2-bhk/wagholi') // three projects with 2 or 2.5 BHK
    expect(paths).not.toContain('/3-bhk/wagholi') // two
    expect(paths).not.toContain('/2-bhk/upper-kharadi') // one
  })

  it('renders the comparison table, and 404s a thin page', async () => {
    // the route returns <FilterPage/>, an async server component: render what it renders
    const page = async (area: string) => { const el = await TwoBhk({ params: Promise.resolve({ area }) }); return el.type(el.props) }
    render(await page('wagholi'))
    expect(screen.getByRole('heading', { level: 1, name: '2 BHK in Wagholi, Pune' })).toBeInTheDocument()
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(1 + 4) // header + 4 matching homes
    await expect(page('upper-kharadi')).rejects.toThrow('NOT_FOUND')
    await expect(page('nowhere')).rejects.toThrow('NOT_FOUND')
  })
})

describe('shared project pages', () => {
  // /projects itself is the home finder since 2026-10-30 (projects-register-list.test.tsx)
  it('groups the catalog by locality', () => {
    expect(byLocality(ALL).map(([l, items]) => [l, items.length])).toEqual([['Upper Kharadi', 1], ['Wagholi', 4]])
  })

  it('shows the project with every agent, sends enquiries to the agent whose facts it shows, and links its area', async () => {
    expect(mainAgent(GOYAL).slug).toBe('house-deal')
    render(await SharedProjectPage({ params: Promise.resolve({ slug: 'goyal-my-home-kharadi' }) }))
    expect(screen.getByRole('heading', { level: 1, name: 'goyal my home kharadi' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Agents for this project' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: "goyal my home kharadi on Zeta Homes's page" })).toHaveAttribute('href', '/agent/zeta/projects/my-home-upper-kharadi')
    // the ask box after the facts says it too (9052d168); the agents section is where it names who gets the enquiry
    expect(within(screen.getByRole('region', { name: 'Agents for this project' })).getByText(/An enquiry here goes to House Deal/)).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /Buyer guide to Upper Kharadi/ })[0]).toHaveAttribute('href', '/localities/upper-kharadi')
  })

  it('asks right after the project details, and gives phones a bottom bar to the form', async () => {
    process.env.NEXT_PUBLIC_SHOW_AGENT_PHONE = 'true'
    try {
      render(await SharedProjectPage({ params: Promise.resolve({ slug: 'rohan-abhilasha-4' }) }))
    } finally {
      delete process.env.NEXT_PUBLIC_SHOW_AGENT_PHONE
    }
    const ask = screen.getByTestId('ask-prompt')
    expect(ask.compareDocumentPosition(screen.getByRole('heading', { name: /Questions buyers ask/ })) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(within(ask).getByRole('link', { name: 'Get price sheet & floor plans' })).toHaveAttribute('href', '#enquire')
    expect(within(ask).getByText(/An enquiry here goes to House Deal/)).toBeInTheDocument()
    expect(within(ask).getByText('WhatsApp').closest('a')?.getAttribute('href')).toMatch(/^https:\/\/wa\.me\/919876543210\?text=/)
    expect(within(screen.getByTestId('sticky-join')).getByText('Get price & plans')).toHaveAttribute('href', '#enquire')
  })

  it('redirects an agent\'s own slug to the shared address and 404s unknown or malformed slugs', async () => {
    await expect(SharedProjectPage({ params: Promise.resolve({ slug: 'my-home-upper-kharadi' }) })).rejects.toThrow('REDIRECT /projects/goyal-my-home-kharadi')
    // House Deal's catalog pages were taken down on 2026-10-20: the old address goes to the project's own page
    await expect(SharedProjectPage({ params: Promise.resolve({ slug: 'goyal-my-home' }) })).rejects.toThrow('REDIRECT /projects/my-home-upper-kharadi')
    await expect(SharedProjectPage({ params: Promise.resolve({ slug: 'nope' }) })).rejects.toThrow('NOT_FOUND')
    await expect(SharedProjectPage({ params: Promise.resolve({ slug: 'Bad Slug' }) })).rejects.toThrow('NOT_FOUND')
    expect(mockOne).not.toHaveBeenCalledWith('Bad Slug')
  })

  it('has its own canonical address, and the agent copy points there', async () => {
    const md = await generateMetadata({ params: Promise.resolve({ slug: 'goyal-my-home-kharadi' }) })
    expect(md.alternates?.canonical).toBe('https://avasetu.in/projects/goyal-my-home-kharadi')
    expect(String(md.title)).toContain('Possession')
    const agent = { agent_name: 'House Deal', slug: 'house-deal', branding_data: {} } as never
    expect(projectMetadata(agent, GOYAL, '').alternates?.canonical).toBe('https://avasetu.in/projects/goyal-my-home-kharadi')
    expect(projectMetadata(agent, { ...GOYAL, catalog_slug: null }, '').alternates?.canonical).toBe('https://avasetu.in/agent/house-deal/projects/goyal-my-home-kharadi')
  })

  it('dates a register page by its last change, so Google re-reads it after we improve it', async () => {
    mockRegister.mockResolvedValueOnce([
      { slug: 'lodha-camelot-kharadi', regno: 'PR1', name: 'LODHA CAMELOT', area: 'kharadi', completion_now: null,
        listed_or_updated: '2026-09-01', page_updated: '2026-10-12', indexable: true },
      { slug: 'older-api', regno: 'PR2', name: 'OLD', area: 'kharadi', completion_now: null, listed_or_updated: '2026-09-02', indexable: true },
    ])
    const entries = await sitemap()
    const at = (path: string) => entries.find((e) => e.url.endsWith(path))?.lastModified
    expect(at('/projects/lodha-camelot-kharadi')).toEqual(new Date('2026-10-12'))
    expect(at('/projects/older-api')).toBeUndefined()     // MahaRERA's own date never dates our page
  })

  it('lists an area with its own guide once, as the guide', async () => {
    mockTopics.mockResolvedValue([{ slug: 'upper-kharadi', checked_on: '2026-10-20' }])
    const urls = (await sitemap()).map((s) => s.url)
    mockTopics.mockResolvedValue([])
    expect(urls.some((u) => u.endsWith('/guides/upper-kharadi'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/localities/upper-kharadi'))).toBe(false)
    expect(urls.some((u) => u.endsWith('/localities/kharadi'))).toBe(true)   // no guide of its own: stays
  })

  it('keeps the last guides when the guides read comes back empty, as when the backend restarts during a deploy', async () => {
    mockTopics.mockResolvedValue([{ slug: 'upper-kharadi', checked_on: '2026-10-20' }])
    await sitemap()
    mockTopics.mockResolvedValue([])
    const urls = (await sitemap()).map((s) => s.url)
    delete (globalThis as { __avasetuSitemapLists?: unknown }).__avasetuSitemapLists
    expect(urls.some((u) => u.endsWith('/guides/upper-kharadi'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/localities/upper-kharadi'))).toBe(false)
  })

  it('builds the sitemap again a minute later when a list is still empty, as right after a deploy restarts both', async () => {
    const g = globalThis as { __avasetuSitemap?: unknown; __avasetuSitemapLists?: unknown }
    delete g.__avasetuSitemap
    delete g.__avasetuSitemapLists
    mockPlaces.mockResolvedValue([{ key: 'wagholi', slug: 'wagholi', name: 'Wagholi', indexable: 1 }])   // an area sitemap: a good build
    mockTopics.mockClear()
    await sitemapGroups(0)
    await sitemapGroups(2 * 60_000)        // inside the usual 10 minutes, but no guides were read
    mockPlaces.mockResolvedValue([])
    delete g.__avasetuSitemap
    expect(mockTopics).toHaveBeenCalledTimes(2)
  })

  it('leaves pages made in bulk out of the sitemap: localities without a guide and our social posts', async () => {
    mockCatalog.mockResolvedValueOnce([...ALL, project('gulmohar-heights', 'Gulmohar City', [[2, 60 * L]])])
    const urls = (await sitemap()).map((s) => s.url)
    expect(urls.some((u) => u.endsWith('/projects/gulmohar-heights'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/localities/gulmohar-city'))).toBe(false)
    expect(urls.some((u) => u.includes('/posts'))).toBe(false)
  })

  it('lists an agent listing only when its page names itself, as the listing page decides, merged towers included', async () => {
    mockRegister.mockResolvedValueOnce([
      { slug: 'kohinoor-kaleido-wagholi', regno: 'P52100046027', name: 'K', area: 'wagholi', completion_now: null, listed_or_updated: null, indexable: true },
      { slug: 'thin-one-wagholi', regno: 'P52100000001', name: 'T', area: 'wagholi', completion_now: null, listed_or_updated: null, indexable: false },
    ])
    const listing = (id: string, rera_no: string | null) => ({ agent_slug: 'house-deal', id, updated_at: '2026-10-30', locality: 'Wagholi', rera_no })
    mockEntries.mockResolvedValueOnce({ projects: [], listings: [
      listing('on-project-page', ' p52100046027'),   // the project's own number, written loosely: names the project page
      listing('on-tower', 'P52100078107'),           // a tower merged into Kohinoor Kaleido: not in the list, names the project page
      listing('lone-tower', 'P52100080485'),         // a tower whose project is not in search: names itself
      listing('on-thin-project', 'P52100000001'),    // a project page out of search: the listing names itself
      listing('resale', null),
    ] })
    mockProjectOfListing.mockImplementation(async (r) => (r === 'P52100078107' ? 'kohinoor-kaleido-wagholi' : null))
    const urls = (await sitemap()).map((s) => s.url)
    mockProjectOfListing.mockReset()
    const listed = (id: string) => urls.some((u) => u.endsWith('/listings/' + id))
    expect(['on-project-page', 'on-tower'].filter(listed)).toEqual([])
    expect(['lone-tower', 'on-thin-project', 'resale'].every(listed)).toBe(true)
    expect(urls.some((u) => u.endsWith('/projects/kohinoor-kaleido-wagholi'))).toBe(true)
  })

  it('puts shared pages and live filter pages in the sitemap', async () => {
    const urls = (await sitemap()).map((s) => s.url)
    expect(urls.some((u) => u.endsWith('/projects/goyal-my-home-kharadi'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/2-bhk/wagholi'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/3-bhk/wagholi'))).toBe(false)
  })
})
