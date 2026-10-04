import { INSIGHTS } from '@/lib/marketing/insights'
import { LOCALITIES, getLocality, localitiesByTier, localityByName, localitySource } from '@/lib/marketing/localities'
import { buildMarketingConfig } from '@/lib/marketing/config'
import { articleJsonLd, breadcrumbJsonLd } from '@/lib/marketing/seo'
import sitemap from '@/app/sitemap'
import robots from '@/app/robots'

describe('locality pages are safe to publish', () => {
  it('has the eight Pune areas (same list as backend/app/core/areas.py) with unique slugs and dated, sourced content', () => {
    expect(LOCALITIES.map((l) => l.slug)).toEqual(['kharadi', 'upper-kharadi', 'wagholi', 'lohegaon', 'keshav-nagar', 'hinjawadi', 'wakad', 'baner'])
    expect(localitiesByTier('affordable').map((l) => l.slug)).toEqual(['upper-kharadi', 'wagholi', 'lohegaon', 'keshav-nagar'])
    expect(localitiesByTier('it').map((l) => l.slug)).toEqual(['kharadi', 'hinjawadi', 'wakad', 'baner'])
    for (const l of LOCALITIES) {
      expect(l.sources.length).toBeGreaterThan(0)
      expect(l.updated).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(getLocality(l.slug)).toBe(l)
      for (const g of l.guides) expect(INSIGHTS.some((i) => i.slug === g)).toBe(true) // no dangling guide links
    }
  })

  it('never states prices, appreciation, predictions or hype', () => {
    const text = JSON.stringify(LOCALITIES)
    expect(text).not.toMatch(/₹|\bRs\.?\s?\d|appreciat|will (rise|increase|double)|invest now|guarantee|best |dream/i)
    expect(text).not.toMatch(/\b\d{2}%/)
  })

  it('always says approved metro is not running', () => {
    for (const l of LOCALITIES) {
      expect(JSON.stringify(l.gettingAround).toLowerCase()).toMatch(/approved is not (the same as )?running|approved lines take years/)
      for (const s of [...l.gettingAround, ...l.faqs.map((f) => f.a)]) {
        if (/metro|line 4|corridor 2b/i.test(s)) expect(s).toMatch(/approved|check the (current|latest) status|not yet|not running yet/i)
      }
    }
    expect(JSON.stringify(LOCALITIES)).not.toMatch(/metro (station )?(is|will be) (open|opening|ready)/i)
  })
})

describe('sitemap and robots', () => {
  const realFetch = global.fetch
  afterEach(() => { global.fetch = realFetch })

  function api(routes: Record<string, unknown>) {
    global.fetch = jest.fn(async (url: string) => {
      const hit = Object.keys(routes).find((k) => String(url).includes(k))
      const body = hit ? routes[hit] : {}
      return { ok: !!hit, status: hit ? 200 : 500, json: async () => body }
    }) as unknown as typeof fetch
  }

  it('lists the localities, guides and key pages; keeps the private app out of search', async () => {
    api({})
    const urls = (await sitemap()).map((s) => s.url)
    expect(urls.some((u) => u.endsWith('/localities/kharadi'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/localities/keshav-nagar'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/insights/kharadi-upper-kharadi-wagholi'))).toBe(true)
    expect(urls.some((u) => /studio|join|api/.test(u))).toBe(false)
    const r = robots()
    const rule = Array.isArray(r.rules) ? r.rules[0] : r.rules
    for (const p of ['/studio', '/dashboard', '/onboarding', '/profile', '/properties', '/analytics', '/social-publishing', '/i/']) {
      expect(rule.disallow).toContain(p)
    }
    expect(String(r.sitemap)).toMatch(/sitemap\.xml$/)
  })

  it('adds news stories and the agent, project and listing pages the backend says are indexable', async () => {
    api({
      '/public/news': [{ id: 'n1', kind: 'story', headline: 'Metro update', summary: 's', pillar: 'p', pillar_label: 'P', areas: [],
        source_name: 'PIB', source_url: null, as_of: '2026-10-01', image_url: null, permalinks: [], published_at: '2026-10-02T08:00:00Z' }],
      '/public/sitemap/listings': { items: [{ agent_slug: 'house-deal', id: 'L1', updated_at: '2026-10-01T00:00:00Z' }] },
      '/public/sitemap/projects': { items: [{ agent_slug: 'house-deal', slug: 'goyal-my-home', updated_at: '2026-10-03T00:00:00Z' }] },
    })
    const map = await sitemap()
    const urls = map.map((s) => s.url)
    expect(urls.some((u) => u.endsWith('/news/n1'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/agent/house-deal/projects/goyal-my-home'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/agent/house-deal/listings/L1'))).toBe(true)
    const home = map.find((s) => s.url.endsWith('/agent/house-deal'))!
    expect(urls.filter((u) => u.endsWith('/agent/house-deal'))).toHaveLength(1) // one entry per agent
    expect((home.lastModified as Date).toISOString()).toBe('2026-10-03T00:00:00.000Z') // their newest change
  })

  it('still lists the fixed pages when the API is down', async () => {
    api({})
    const urls = (await sitemap()).map((s) => s.url)
    expect(urls.some((u) => u.endsWith('/news'))).toBe(true)
    expect(urls.some((u) => u.includes('/agent/'))).toBe(false)
  })
})

describe('structured data and links between pages', () => {
  const cfg = buildMarketingConfig({ NEXT_PUBLIC_SITE_URL: 'https://avasetu.in' })

  it('finds the area guide for a locality however the agent typed it', () => {
    expect(localityByName(' upper kharadi ')?.slug).toBe('upper-kharadi')
    expect(localityByName('Hinjewadi')?.slug).toBe('hinjawadi')
    expect(localityByName('Keshav  Nagar')?.slug).toBe('keshav-nagar')
    expect(localityByName('Nashik')).toBeUndefined()
    expect(localityByName(null)).toBeUndefined()
  })

  it('tags an area enquiry with the area key, within the 40 characters the lead source holds', () => {
    expect(localitySource(getLocality('wagholi')!)).toBe('locality_wagholi')
    expect(localitySource(getLocality('keshav-nagar')!)).toBe('locality_keshav_nagar')
    for (const l of LOCALITIES) expect(localitySource(l)).toMatch(/^locality_[a-z0-9_]{1,31}$/)
  })

  it('builds a breadcrumb trail with absolute URLs', () => {
    const ld = breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Area guides', path: '/localities' }])
    expect(ld.itemListElement).toEqual([
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://avasetu.in' },
      { '@type': 'ListItem', position: 2, name: 'Area guides', item: 'https://avasetu.in/localities' },
    ])
  })

  it('describes a guide as an Article by the Avasetu team, dated as shown on the page', () => {
    const a = INSIGHTS[0]
    const ld = articleJsonLd(cfg, { title: a.title, summary: a.summary, path: `/insights/${a.slug}`, updated: a.updated })
    expect(ld).toMatchObject({ '@type': 'Article', dateModified: a.updated, mainEntityOfPage: `https://avasetu.in/insights/${a.slug}` })
    expect(String(ld.headline).length).toBeLessThanOrEqual(110)
  })
})
