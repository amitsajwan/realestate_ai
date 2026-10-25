// /llms.txt: a map of the site for AI assistants from the same lists as the sitemap (app/llms.txt/route.ts)
jest.mock('@/lib/site/facets', () => ({
  getFacets: async () => [
    { key: 'lohegaon|all|bhk=2', path: '/projects/area/lohegaon/2-bhk', place: 'lohegaon', place_slug: 'lohegaon', intent: 'all', possession: null,
      builder: null, bhk: 2, label: '2 BHK flats', count: 4, indexable: true, page_updated: null },
    { key: 'lohegaon|top|builder=x', path: '/projects/area/lohegaon/top/by-x', place: 'lohegaon', place_slug: 'lohegaon', intent: 'top', possession: null,
      builder: 'x', label: 'Top projects', count: 3, indexable: true, page_updated: null },
  ],
}))
jest.mock('@/lib/site/api', () => ({
  getCatalog: async () => [
    { slug: 'gera-world-of-joy', name: 'Gera World of Joy', builder: 'Gera Developments', locality: 'Kharadi', rera_no: 'P52100011111',
      registrations: [{ regno: 'P52100022222', tower: 'Tower 2' }], price_min: 9500000, price_max: 12000000, agents: [{ slug: 'a' }] },
    { slug: 'nobody-sells', name: 'Nobody Sells', builder: 'X', locality: 'Kharadi', rera_no: 'P52100099999', agents: [] },
  ],
}))
const row = (o: Record<string, unknown>) => ({ regno: 'P0', name: 'X', area: 'wagholi', indexable: true, active: true, sold_out: false,
  completion_now: '2029-10-30', listed_or_updated: null, ...o })
jest.mock('@/lib/site/register', () => ({
  ...jest.requireActual('@/lib/site/register'),
  getRegisterProjects: async () => [
    row({ slug: 'unpriced-new', regno: 'P1', name: 'Unpriced New', page_updated: '2026-10-24' }),
    row({ slug: 'priced-old', regno: 'P2', name: 'PRICED OLD', marketed_name: 'Priced Old', promoter: 'Rohan Builders', units_total: 416,
      units_booked: 244, price_from: 6900000, page_updated: '2026-10-01' }),
    row({ slug: 'gera-tower-2', regno: 'P52100022222', name: 'Gera Tower 2', area: 'kharadi' }),   // the agent-listed project's tower
    row({ slug: 'thin-page', regno: 'P3', indexable: false }), row({ slug: 'finished', regno: 'P4', active: false }),
    row({ slug: 'all-booked', regno: 'P5', sold_out: true }), row({ slug: 'akurdi-one', regno: 'P6', area: null }),
  ],
  getRegisterPlaces: async () => [
    { key: 'akurdi', slug: 'akurdi', name: 'Akurdi', zone: 'PCMC', projects: 90, indexable: 50 },
    { key: 'lohegaon', slug: 'lohegaon', name: 'Lohegaon', zone: 'East Pune', projects: 20, indexable: 12 },
    { key: 'thin', slug: 'thin', name: 'Thin', zone: 'East Pune', projects: 3, indexable: 0 },
  ],
}))

import { GET } from '@/app/llms.txt/route'
import { getMarketingConfig } from '@/lib/marketing/config'

// jsdom has no fetch Response: the little the route uses
class FakeResponse {
  constructor(private body: string, private init: { headers?: Record<string, string> } = {}) {}
  headers = { get: (k: string) => this.init.headers?.[k] ?? null }
  async text() { return this.body }
}
;(global as unknown as { Response: unknown }).Response = FakeResponse

describe('/llms.txt', () => {
  it('lists our areas first, their lists and the data pages, never a page out of search', async () => {
    const res = await GET()
    const text = await res.text()
    expect(res.headers.get('Content-Type')).toMatch(/text\/plain/)
    expect(text.startsWith('# Avasetu\n\n> Avasetu lists every housing project in Pune registered with MahaRERA')).toBe(true)
    expect(text.indexOf('in Lohegaon, Pune](')).toBeLessThan(text.indexOf('in Akurdi, Pune]('))
    expect(text).toContain('- [2 BHK flats in Lohegaon, Pune](' + getMarketingConfig().siteUrl + '/projects/area/lohegaon/2-bhk): 4 projects')
    expect(text).not.toContain('by-x')
    expect(text).not.toContain('Thin')
    expect(text).toContain('/pune-maharera-tracker')
  })

  it('lists our areas\' project pages: agent-listed first, then priced, then newest, never a page out of search', async () => {
    const text = await (await GET()).text()
    const site = getMarketingConfig().siteUrl
    expect(text).toContain(`- [Gera World of Joy, Kharadi, Pune](${site}/projects/gera-world-of-joy): by Gera Developments · MahaRERA P52100011111 · from ₹95`)
    expect(text).toContain(`- [Priced Old, Wagholi, Pune](${site}/projects/priced-old): by Rohan Builders · possession Oct 2029 · 244/416 booked · MahaRERA P2 · from ₹69`)
    const at = (s: string) => text.indexOf(`/projects/${s})`)
    expect(at('gera-world-of-joy')).toBeLessThan(at('priced-old'))
    expect(at('priced-old')).toBeLessThan(at('unpriced-new'))
    for (const gone of ['gera-tower-2', 'nobody-sells', 'thin-page', 'finished', 'all-booked', 'akurdi-one']) expect(text).not.toContain(`/projects/${gone})`)
  })
})
