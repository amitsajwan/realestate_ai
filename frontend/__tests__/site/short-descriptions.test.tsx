// Google shows about 160 characters of a description and 70 of a title: the site audit (seo/audit.py) found the home, place,
// area list and project pages running to 176-260, so the facts at the end were cut off in search results.
jest.mock('@/lib/site/api', () => ({ getCatalog: async () => [] }))
jest.mock('@/lib/site/hubs', () => ({
  getActive: async () => [{ name: 'Kharadi Pune Phase I - Tower 1 to 4' }, { name: 'Rosewood Park Wagholi Phase II Building B' }],
  getAreaMap: async () => null, getListed: async () => new Map(),
}))
jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NOT_FOUND') }, permanentRedirect: () => { throw new Error('REDIRECT') }, usePathname: () => '/' }))
const PRICES = { place: 'wagholi', as_of: '2026-10-21', sizes: [
  { bhk: 1, projects: 4, low: 1_047_000, high: 3_000_000, cheapest: { name: 'A', slug: 'a' }, path: '/projects/area/wagholi/1-bhk' },
  { bhk: 2, projects: 40, low: 5_580_000, high: 9_100_000, cheapest: { name: 'B', slug: 'b' }, path: '/projects/area/wagholi/2-bhk' }] }
let launches = false
const FACET = {
  key: 'upper-kharadi|top', path: '/projects/area/upper-kharadi/top', place: { key: 'upper-kharadi', slug: 'upper-kharadi', name: 'Upper Kharadi' },
  intent: 'top', possession: null, builder: null, builder_name: null, title: 'Top Projects in Upper Kharadi, Pune: 23 on MahaRERA', h1: 'x',
  answer: 'x', count: 23, changes: [], month: null, page_updated: null, indexable: true, as_of: '2026-10-24', source: 'MahaRERA',
  rows: [{ name: 'Kharadi Pune Phase I - Tower 1 to 4' }, { name: 'Kharadi Pune P2' }, { name: 'Yashwin Enchante' }],
}
jest.mock('@/lib/site/facets', () => ({
  ...jest.requireActual('@/lib/site/facets'),
  getFacets: async () => (launches ? [{ place: 'wagholi', intent: 'new-launches', possession: null, builder: null, indexable: true }] : []),
  getPlacePrices: async () => PRICES,
  getFacet: async () => FACET,
}))
jest.mock('@/lib/site/register', () => ({
  ...jest.requireActual('@/lib/site/register'),
  getRegisterPlaces: async () => [
    { key: 'wagholi', slug: 'wagholi', name: 'Wagholi', zone: 'East Pune', projects: 343, indexable: 200 },
    { key: 'kothrud', slug: 'kothrud', name: 'Kothrud', zone: 'West Pune', projects: 431, indexable: 200 },
    { key: 'upper-kharadi', slug: 'upper-kharadi', name: 'Upper Kharadi', zone: 'East Pune', projects: 23, indexable: 23 }],
  getRegisterProjects: async () => [],
}))

import { generateMetadata as placeMetadata } from '@/app/projects/area/[place]/page'
import { generateMetadata as facetMetadata } from '@/app/projects/area/[place]/[...facet]/page'
import { clipWords, fitDescription } from '@/lib/site/format'
import { registerDescription } from '@/lib/site/projectSeo'
import type { RegisterProject } from '@/lib/site/register'
import { catalogProjectMetadata } from '@/lib/site/seo'
import type { CatalogProject } from '@/lib/site/types'

describe('search descriptions fit what Google shows', () => {
  it('drops whole clauses in order until the text fits, keeping the facts outside them', () => {
    const write = (has: (n: number) => boolean) => `12 projects in Wagholi${has(2) ? ', including Castle Hills' : ''}. Possession on MahaRERA${has(1) ? ', and what to check before you buy' : ''}.`
    expect(fitDescription(write, 200)).toBe('12 projects in Wagholi, including Castle Hills. Possession on MahaRERA, and what to check before you buy.')
    expect(fitDescription(write, 80)).toBe('12 projects in Wagholi, including Castle Hills. Possession on MahaRERA.')
    expect(fitDescription(write, 50)).toBe('12 projects in Wagholi. Possession on MahaRERA.')
  })

  it('clips text it cannot shorten at a sentence or a word, never mid-word', () => {
    expect(clipWords('The first fact runs here. Another fact that runs on and on.', 40)).toBe('The first fact runs here.')
    expect(clipWords('Possession filed with MahaRERA and whether it moved', 30)).toBe('Possession filed with…')
  })

  it('a project page keeps price, possession and MahaRERA number and drops the legal name and builder first', () => {
    const p = {
      slug: 'venkatesh-vanaya-wing-i-j-phase-2-kharadi', name: 'VENKATESH VANAYA-WING- I & J-PHASE -2', marketed_name: 'Venkatesh Vanaya',
      regno: 'PR1261012601206', promoter: 'SVBPL HOMES PVT LTD', area: { key: 'kharadi', slug: 'kharadi', name: 'Kharadi' },
      completion_now: '2031-04-30', completion_at_registration: '2029-12-31', units_total: 168, units_booked: 0, indexable: true,
      prices: { read_at: '2026-10-20', rows: [{ bhk: '2 BHK', from_inr: 10_600_000, sources: [{ site: 'builder' }] }, { bhk: '3 BHK', from_inr: 14_000_000, sources: [{ site: 'builder' }] }] },
    } as unknown as RegisterProject
    const d = registerDescription(p)
    expect(d.length).toBeLessThanOrEqual(160)
    expect(d).toBe('Venkatesh Vanaya, Kharadi, Pune: 2 & 3 BHK from ₹1.06 Cr. Possession Apr 2031, 0 of 168 homes booked. MahaRERA PR1261012601206, checked by Avasetu.')
  })

  it("a page writer's long description is cut at a sentence, not mid-word", () => {
    const p = { slug: 's', name: 'Sky One', regno: 'P1', search_description: 'Sky One in Lohegaon, Pune: possession filed for June 2028 with MahaRERA, 50 of 200 homes booked, by Sky Builders. MahaRERA P1. Checked facts, map and the questions buyers ask before paying a token.' } as unknown as RegisterProject
    expect(registerDescription(p)).toBe('Sky One in Lohegaon, Pune: possession filed for June 2028 with MahaRERA, 50 of 200 homes booked, by Sky Builders. MahaRERA P1.')
  })

  it("an agent-listed project page's description fits and still ends with its MahaRERA number", () => {
    const p = {
      slug: 'lodha-camelot-kharadi', name: 'Lodha Camelot', locality: 'Kharadi', rera_no: 'P52100055555', price_min: 12_000_000, media: [],
      registrations: [{ tower: 'T1', completion: '2029-06-30' }, { tower: 'T2', completion: '2030-12-31' }, { tower: 'T3', completion: '2031-03-31' }],
      rera: { units_total: 900, units_booked: 412, completion_at_registration: '2027-12-31', completion_now: '2029-06-30', registered_on: '2022-01-10' },
    } as unknown as CatalogProject
    const web = { facts: [{ key: 'land_acres', text: '26 acres of land', sources: [] }, { key: 'open_space_pct', text: '70%', sources: [] }] }
    const d = String(catalogProjectMetadata(p, '₹1.2 Cr to ₹3.4 Cr, 2, 3, 4 BHK', web as never).description)
    expect(d.length).toBeLessThanOrEqual(160)
    expect(d).toMatch(/^₹1\.2 Cr to ₹3\.4 Cr, 2, 3, 4 BHK\. MahaRERA possession Jun 2029/)
    expect(d).toMatch(/MahaRERA P52100055555$/)
  })

  it('a place page leads with the count and prices and drops project names before cutting the facts', async () => {
    launches = true
    const meta = await placeMetadata({ params: Promise.resolve({ place: 'wagholi' }) })
    launches = false
    const d = String(meta.description)
    expect(d.length).toBeLessThanOrEqual(160)
    expect(d).toMatch(/^343 residential projects and flats in Wagholi, Pune.*1 BHK from ₹10\.47 L/)
    expect(d).toMatch(/MahaRERA possession date, whether it moved, homes booked\.$/)
    expect(String(meta.title)).toBe('Flats & Residential Projects in Wagholi, Pune: all 343 on MahaRERA')
  })

  it("a place page's title fits 70 characters", async () => {
    const meta = await placeMetadata({ params: Promise.resolve({ place: 'kothrud' }) })
    expect(String(meta.title)).toBe('New Projects & Flats in Kothrud, Pune: Price, Possession, RERA (431)')
    expect(String(meta.description).length).toBeLessThanOrEqual(160)
  })

  it('an area list page names fewer projects instead of cutting off the facts', async () => {
    const meta = await facetMetadata({ params: Promise.resolve({ place: 'upper-kharadi', facet: ['top'] }) })
    const d = String(meta.description)
    expect(d.length).toBeLessThanOrEqual(160)
    expect(d).toBe("23 top residential projects in Upper Kharadi, Pune on MahaRERA: Kharadi Pune Phase I - Tower 1 to 4. Possession filed and whether it moved, homes booked.")
  })
})
