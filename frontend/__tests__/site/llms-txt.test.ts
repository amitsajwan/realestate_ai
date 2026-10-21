// /llms.txt: a map of the site for AI assistants from the same lists as the sitemap (app/llms.txt/route.ts)
jest.mock('@/lib/site/facets', () => ({
  getFacets: async () => [
    { key: 'lohegaon|all|bhk=2', path: '/projects/area/lohegaon/2-bhk', place: 'lohegaon', place_slug: 'lohegaon', intent: 'all', possession: null,
      builder: null, bhk: 2, label: '2 BHK flats', count: 4, indexable: true, page_updated: null },
    { key: 'lohegaon|top|builder=x', path: '/projects/area/lohegaon/top/by-x', place: 'lohegaon', place_slug: 'lohegaon', intent: 'top', possession: null,
      builder: 'x', label: 'Top projects', count: 3, indexable: true, page_updated: null },
  ],
}))
jest.mock('@/lib/site/register', () => ({
  getRegisterPlaces: async () => [
    { key: 'akurdi', slug: 'akurdi', name: 'Akurdi', zone: 'PCMC', projects: 90, indexable: 50 },
    { key: 'lohegaon', slug: 'lohegaon', name: 'Lohegaon', zone: 'East Pune', projects: 20, indexable: 12 },
    { key: 'thin', slug: 'thin', name: 'Thin', zone: 'East Pune', projects: 3, indexable: 0 },
  ],
  placePath: (s: string) => `/projects/area/${s}`,
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
})
