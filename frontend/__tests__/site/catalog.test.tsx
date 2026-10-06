import React from 'react'
import { render, screen, within } from '@testing-library/react'
import type { CatalogProject } from '@/lib/site/types'

// Avasetu's shared project pages read the catalog from the API: replaced here by a fixed list.
const mockCatalog = jest.fn<Promise<CatalogProject[]>, [string?]>()
const mockOne = jest.fn<Promise<CatalogProject | null>, [string]>()
jest.mock('@/lib/site/api', () => ({
  getCatalog: (l?: string) => mockCatalog(l),
  getCatalogProject: (s: string) => mockOne(s),
  getLocalityListings: async () => [],
  getSitemapEntries: async () => ({ listings: [], projects: [] }),
  fixturesForced: () => true, // news falls back to its fixtures
  serverApiBase: () => 'http://api',
}))
jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))
// Avasetu's own register pages (lib/site/register): none in these tests, so unknown slugs are 404s as before
jest.mock('@/lib/site/register', () => ({ getRegisterProject: async () => null, getRegisterProjects: async () => [], longDay: () => '' }))
const mockRedirect = jest.fn((url: string) => { throw new Error('REDIRECT ' + url) })
const mockNotFound = jest.fn(() => { throw new Error('NOT_FOUND') })
jest.mock('next/navigation', () => ({
  permanentRedirect: (u: string) => mockRedirect(u),
  notFound: () => mockNotFound(),
  usePathname: () => '/',
  useRouter: () => ({ push: jest.fn() }),
}))

import ProjectsPage from '@/app/projects/page'
import SharedProjectPage, { generateMetadata } from '@/app/projects/[slug]/page'
import TwoBhk from '@/app/2-bhk/[area]/page'
import { BANDS, filterProjects, livePages, matches, MIN_PROJECTS } from '@/lib/site/filters'
import { getLocality } from '@/lib/marketing/localities'
import { byLocality, mainAgent } from '@/lib/site/projects'
import { projectMetadata } from '@/lib/site/seo'
import sitemap from '@/app/sitemap'

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
const GOYAL = project('goyal-my-home', 'Upper Kharadi', [[2, 97 * L], [3, 125 * L]], {
  agents: [
    { slug: 'house-deal', name: 'House Deal', phone: '+919876543210', project_slug: 'goyal-my-home' },
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
  it('groups the index by locality and links each card to /projects', async () => {
    expect(byLocality(ALL).map(([l, items]) => [l, items.length])).toEqual([['Upper Kharadi', 1], ['Wagholi', 4]])
    render(await ProjectsPage())
    expect(screen.getByRole('heading', { name: 'Projects in Wagholi' })).toBeInTheDocument()
    expect(screen.getAllByTestId('project-card')[0]).toHaveAttribute('href', '/projects/goyal-my-home')
    expect(screen.getByRole('link', { name: 'Wagholi buyer guide' })).toHaveAttribute('href', '/localities/wagholi')
  })

  it('shows the project with every agent, sends enquiries to the agent whose facts it shows, and links its area', async () => {
    expect(mainAgent(GOYAL).slug).toBe('house-deal')
    render(await SharedProjectPage({ params: Promise.resolve({ slug: 'goyal-my-home' }) }))
    expect(screen.getByRole('heading', { level: 1, name: 'goyal my home' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Agents for this project' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: "goyal my home on Zeta Homes's page" })).toHaveAttribute('href', '/agent/zeta/projects/my-home-upper-kharadi')
    expect(screen.getByText(/An enquiry here goes to House Deal/)).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /Buyer guide to Upper Kharadi/ })[0]).toHaveAttribute('href', '/localities/upper-kharadi')
  })

  it('redirects an agent\'s own slug to the shared address and 404s unknown or malformed slugs', async () => {
    await expect(SharedProjectPage({ params: Promise.resolve({ slug: 'my-home-upper-kharadi' }) })).rejects.toThrow('REDIRECT /projects/goyal-my-home')
    await expect(SharedProjectPage({ params: Promise.resolve({ slug: 'nope' }) })).rejects.toThrow('NOT_FOUND')
    await expect(SharedProjectPage({ params: Promise.resolve({ slug: 'Bad Slug' }) })).rejects.toThrow('NOT_FOUND')
    expect(mockOne).not.toHaveBeenCalledWith('Bad Slug')
  })

  it('has its own canonical address, and the agent copy points there', async () => {
    const md = await generateMetadata({ params: Promise.resolve({ slug: 'goyal-my-home' }) })
    expect(md.alternates?.canonical).toBe('https://avasetu.in/projects/goyal-my-home')
    expect(String(md.title)).toContain('MahaRERA')
    const agent = { agent_name: 'House Deal', slug: 'house-deal', branding_data: {} } as never
    expect(projectMetadata(agent, GOYAL, '').alternates?.canonical).toBe('https://avasetu.in/projects/goyal-my-home')
    expect(projectMetadata(agent, { ...GOYAL, catalog_slug: null }, '').alternates?.canonical).toBe('https://avasetu.in/agent/house-deal/projects/goyal-my-home')
  })

  it('puts shared pages and live filter pages in the sitemap', async () => {
    const urls = (await sitemap()).map((s) => s.url)
    expect(urls.some((u) => u.endsWith('/projects/goyal-my-home'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/2-bhk/wagholi'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/3-bhk/wagholi'))).toBe(false)
  })
})
