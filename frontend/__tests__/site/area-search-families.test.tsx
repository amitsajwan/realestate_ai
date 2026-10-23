import { render, screen } from '@testing-library/react'
import React from 'react'

// A place page answers every way buyers search for it (docs/plan/seo-system.md, "Every way buyers search"): projects, flats,
// property, prices by size, and the other spellings of its name; old /2-bhk/<area> URLs give way to the size page.
jest.mock('@/lib/site/api', () => ({ getCatalog: async () => [] }))
jest.mock('@/lib/site/hubs', () => ({ getActive: async () => [], getAreaMap: async () => null, getListedSlugs: async () => new Map() }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NOT_FOUND') }, usePathname: () => '/' }))
const FACETS = [
  { key: 'lohegaon|all|bhk=2', path: '/projects/area/lohegaon/2-bhk', place: 'lohegaon', place_slug: 'lohegaon', intent: 'all', possession: null,
    builder: null, bhk: 2, label: '2 BHK flats', count: 4, indexable: true, page_updated: null },
]
const PRICES = { place: 'lohegaon', as_of: '2026-10-21', sizes: [
  { bhk: 2, projects: 4, low: 6_900_000, high: 9_100_000, cheapest: { name: 'Sky One', slug: 'sky-one' }, path: '/projects/area/lohegaon/2-bhk' }] }
jest.mock('@/lib/site/facets', () => ({
  ...jest.requireActual('@/lib/site/facets'),
  getFacets: async () => FACETS,
  getPlacePrices: async () => PRICES,
}))
jest.mock('@/lib/site/register', () => ({
  ...jest.requireActual('@/lib/site/register'),
  getRegisterPlaces: async () => [{ key: 'lohegaon', slug: 'lohegaon', name: 'Lohegaon', zone: 'East Pune', spellings: ['Lohgaon', 'Lohogaon'], projects: 2, indexable: 2 }],
  getRegisterProjects: async () => [
    { slug: 'sky-one', regno: 'P1', name: 'SKY ONE', marketed_name: 'Sky One', area: 'lohegaon', completion_now: '2028-06-30', indexable: true, stage: null,
      promoter: 'Sky Builders', units_total: 200, units_booked: 50, page_updated: '2026-10-19T08:00:00+00:00' },
    { slug: 'river-two', regno: 'P2', name: 'RIVER TWO', area: 'lohegaon', completion_now: '2029-01-31', indexable: true, stage: null,
      promoter: 'Sky Builders', units_total: 100, units_booked: 10, page_updated: '2026-10-20T08:00:00+00:00' },
  ],
}))

import PlaceProjectsPage, { generateMetadata } from '@/app/projects/area/[place]/page'
import { facetFaq, sizePage, withoutMovedSizePages } from '@/lib/site/facets'
import type { FacetLink, FacetPage } from '@/lib/site/facets'

const params = Promise.resolve({ place: 'lohegaon' })

describe('place page answers flats, property and price searches', () => {
  it('says flats and property in its title and description, with the starting price by size', async () => {
    const meta = await generateMetadata({ params })
    expect(String(meta.title)).toMatch(/Flats in Lohegaon, Pune/)
    expect(meta.description).toMatch(/projects and flats in Lohegaon, Pune; 2 BHK from ₹69/)
    expect(meta.description).toMatch(/buy property/)
  })

  it('shows flat prices by size linking the size page, the other spellings, and the list as structured data', async () => {
    const { container } = render(await PlaceProjectsPage({ params }))
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('New projects and flats in Lohegaon, Pune')
    expect(screen.getByText('Also spelt Lohgaon, Lohogaon')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Flat prices in Lohegaon' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '4 with 2 BHK flats' })).toHaveAttribute('href', '/projects/area/lohegaon/2-bhk')
    const ld = [...container.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent || '{}'))
    expect(screen.getByTestId('place-answer')).toHaveTextContent(
      /MahaRERA lists 2 housing projects in Lohegaon, Pune being built or recently finished\. 60 of their 300 homes are booked\. The earliest filed completion date is Sky One \(Jun 2028\)\. 2 BHK flats start from ₹69/)
    expect(screen.getByText('Updated 20 Oct 2026')).toBeInTheDocument()
    expect(screen.getByText('Which builders have the most projects in Lohegaon?')).toBeInTheDocument()
    const faq = ld.find((x) => x['@type'] === 'FAQPage')
    expect(faq.mainEntity.map((q: { name: string }) => q.name)).toEqual([
      'How many new projects are there in Lohegaon, Pune?', 'What is the price of a 2 BHK flat in Lohegaon?',
      'Which projects in Lohegaon have the earliest possession?', 'Which builders have the most projects in Lohegaon?',
      'Where do these Lohegaon numbers come from?'])
    expect(ld.find((x) => x['@type'] === 'WebPage').dateModified).toBe('2026-10-20T08:00:00+00:00')
    const list = ld.find((x) => x['@type'] === 'ItemList')
    expect(list.itemListElement).toHaveLength(2)
    expect(list.about.alternateName).toEqual(['Lohgaon, Pune', 'Lohogaon, Pune'])
  })
})

describe('size pages take over from the old /2-bhk/<area> pages', () => {
  const all = FACETS as FacetLink[]
  it('finds the live size page and drops the old URL from links and the sitemap', () => {
    expect(sizePage(all, 'lohegaon', 2)?.path).toBe('/projects/area/lohegaon/2-bhk')
    expect(sizePage(all, 'lohegaon', 3)).toBeNull()
    expect(withoutMovedSizePages([{ path: '/2-bhk/lohegaon' }, { path: '/3-bhk/lohegaon' }, { path: '/price/under-50-lakh/lohegaon' }], all))
      .toEqual([{ path: '/3-bhk/lohegaon' }, { path: '/price/under-50-lakh/lohegaon' }])
  })

  it('answers the size and price questions on a size page', () => {
    const p = { bhk: 2, intent: 'all', place: { key: 'lohegaon', slug: 'lohegaon', name: 'Lohegaon' }, rows: [{ name: 'Sky One' }],
      answer: 'As of 21 Oct 2026, 4 projects ...', as_of: '2026-10-21' } as unknown as FacetPage
    const qs = facetFaq(p).map((f) => f.q)
    expect(qs).toContain('Which new projects in Lohegaon, Pune have 2 BHK flats?')
    expect(qs).toContain('What is the price of a 2 BHK flat in Lohegaon?')
  })
})
