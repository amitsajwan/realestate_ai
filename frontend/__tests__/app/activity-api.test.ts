import { createApiClient } from '@/lib/app/api'
import { createFixtureApi, FIXTURE_STATE_KEY } from '@/lib/app/fixtures'
import { splitByWeights } from '@/lib/app/fixtures-activity'

function fakeFetch(status: number, body: unknown) {
  return jest.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    text: async () => (body === undefined ? '' : JSON.stringify(body)),
  })) as unknown as jest.MockedFunction<typeof fetch>
}

const mem = () => {
  const m: Record<string, string> = {}
  return { m, getItem: (k: string) => m[k] ?? null, setItem: (k: string, v: string) => void (m[k] = v) }
}

describe('activity + freshness: real client', () => {
  it('getListingActivity GETs /inbox/listings/{id}/activity with the limit', async () => {
    const body = { listing: { id: 'l1' }, totals: {}, by_source: {}, daily: [], feed: [], people: [] }
    const f = fakeFetch(200, body)
    const api = createApiClient({ baseUrl: 'http://x', getToken: () => 'tok', fetchImpl: f })
    expect(await api.getListingActivity('l1', 20)).toEqual(body)
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://x/api/v1/inbox/listings/l1/activity?limit=20')
    expect(init.method ?? 'GET').toBe('GET')
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  })

  it('getListingActivity without a limit sends no query string', async () => {
    const f = fakeFetch(200, {})
    await createApiClient({ baseUrl: 'http://x', getToken: () => null, fetchImpl: f }).getListingActivity('l9')
    expect((f.mock.calls[0] as unknown as [string])[0]).toBe('http://x/api/v1/inbox/listings/l9/activity')
  })

  it('getListingActivity surfaces a 404 (another agent\'s listing)', async () => {
    const api = createApiClient({ getToken: () => 't', fetchImpl: fakeFetch(404, { detail: 'Listing not found' }) })
    await expect(api.getListingActivity('nope')).rejects.toMatchObject({ status: 404, detail: 'Listing not found' })
  })

  it('confirmAvailable POSTs to /listings/{id}/confirm-available and returns the listing', async () => {
    const listing = { id: 'l3', status: 'live', freshness: 'fresh', days_since_confirmed: 0 }
    const f = fakeFetch(200, listing)
    const api = createApiClient({ baseUrl: 'http://x', getToken: () => 'tok', fetchImpl: f })
    expect(await api.confirmAvailable('l3')).toEqual(listing)
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://x/api/v1/listings/l3/confirm-available')
    expect(init.method).toBe('POST')
    expect(init.body).toBeUndefined()
  })

  it('confirmAvailable surfaces a 409 for a listing that is not live', async () => {
    const api = createApiClient({ getToken: () => 't', fetchImpl: fakeFetch(409, { detail: 'Listing is not live' }) })
    await expect(api.confirmAvailable('l2')).rejects.toMatchObject({ status: 409 })
  })
})

describe('activity + freshness: fixture api', () => {
  it('uses a new storage key so old demo data is replaced', async () => {
    expect(FIXTURE_STATE_KEY).toBe('app_fixture_state_v6')
    const s = mem()
    await createFixtureApi(s).listListings()
    // nothing is written until something changes; a change is stored under the new key only
    await createFixtureApi(s).confirmAvailable('l3')
    expect(Object.keys(s.m)).toEqual(['app_fixture_state_v6'])
  })

  it('listings carry freshness: fresh, confirm and hidden, with days since confirmed', async () => {
    const api = createFixtureApi(mem())
    const by = Object.fromEntries((await api.listListings()).map((l) => [l.id, l]))
    expect(by.l1.freshness).toBe('fresh')
    expect(by.l5.freshness).toBe('fresh')
    expect(by.l3).toMatchObject({ freshness: 'confirm', days_since_confirmed: 30 })
    expect(by.l4).toMatchObject({ freshness: 'hidden', days_since_confirmed: 52 })
    expect(by.l2.freshness).toBe('fresh') // a draft is never asked
    expect((await api.getListing('l4')).freshness).toBe('hidden')
  })

  it('confirmAvailable stamps the listing fresh and persists it', async () => {
    const s = mem()
    const api = createFixtureApi(s)
    const out = await api.confirmAvailable('l4')
    expect(out).toMatchObject({ id: 'l4', freshness: 'fresh', days_since_confirmed: 0 })
    expect(new Date(out.freshness_confirmed_at!).getTime()).toBeGreaterThan(Date.now() - 5000)
    expect((await createFixtureApi(s).getListing('l4')).freshness).toBe('fresh')
    expect((await api.listListings()).find((l) => l.id === 'l4')!.freshness).toBe('fresh')
  })

  it('confirmAvailable is a 409 for draft, paused and sold listings, and a 404 for an unknown id', async () => {
    const api = createFixtureApi(mem())
    await expect(api.confirmAvailable('l2')).rejects.toMatchObject({ status: 409 }) // draft
    await api.setListingStatus('l3', 'paused')
    await expect(api.confirmAvailable('l3')).rejects.toMatchObject({ status: 409 })
    await api.setListingStatus('l4', 'sold')
    await expect(api.confirmAvailable('l4')).rejects.toMatchObject({ status: 409 })
    await expect(api.confirmAvailable('zzz')).rejects.toMatchObject({ status: 404 })
  })

  it('a listing under offer can be confirmed; marking sold or paused makes it "fresh" (nothing to ask)', async () => {
    const api = createFixtureApi(mem())
    await api.setListingStatus('l3', 'under_offer')
    expect((await api.getListing('l3')).freshness).toBe('confirm')
    expect((await api.confirmAvailable('l3')).freshness).toBe('fresh')
    expect((await api.setListingStatus('l4', 'sold')).freshness).toBe('fresh')
    expect((await api.setListingStatus('l4', 'paused')).status).toBe('paused')
  })

  it('reactivating a paused listing re-stamps freshness (contract)', async () => {
    const api = createFixtureApi(mem())
    await api.setListingStatus('l4', 'paused')
    const live = await api.setListingStatus('l4', 'live')
    expect(live).toMatchObject({ status: 'live', freshness: 'fresh', days_since_confirmed: 0 })
  })

  it('an update carrying computed freshness fields does not store them', async () => {
    const api = createFixtureApi(mem())
    const out = await api.updateListing('l4', { title: 'Renamed', freshness: 'fresh', days_since_confirmed: 0 } as never)
    expect(out.title).toBe('Renamed')
    expect(out.freshness).toBe('hidden') // still computed from the dates
  })

  it('a new listing is fresh once published', async () => {
    const api = createFixtureApi(mem())
    const l = await api.createListing({ title: 'Flat', transaction: 'sale', property_type: 'apartment', price_inr: 5_000_000, city: 'Pune', locality: 'Baner', description: { en: 'Nice' } })
    expect((await api.publishListing(l.id)).freshness).toBe('fresh')
  })

  describe('getListingActivity', () => {
    it('returns the contract shape with a 14-day IST series, oldest first', async () => {
      const a = await createFixtureApi(mem()).getListingActivity('l1')
      expect(a.listing).toEqual({ id: 'l1', title: '2 BHK in Baner', status: 'live', price_inr: 8_500_000 })
      expect(Object.keys(a.totals).sort()).toEqual(
        ['call_clicks', 'deals', 'enquiries', 'qualified', 'shares', 'site_visits', 'unique_visitors', 'views', 'whatsapp_clicks'],
      )
      expect(a.daily).toHaveLength(14)
      const dates = a.daily.map((d) => d.date)
      expect(dates).toEqual([...dates].sort())
      expect(new Set(dates).size).toBe(14)
      for (const d of a.daily) expect(d.date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    })

    it('daily views and by_source views both add up to the total', async () => {
      const a = await createFixtureApi(mem()).getListingActivity('l1')
      expect(a.totals.views).toBeGreaterThan(0)
      expect(a.daily.reduce((n, d) => n + d.views, 0)).toBe(a.totals.views)
      expect(Object.values(a.by_source).reduce((n, s) => n + s.views, 0)).toBe(a.totals.views)
      expect(Object.values(a.by_source).reduce((n, s) => n + s.enquiries, 0)).toBe(a.totals.enquiries)
      expect(a.daily.reduce((n, d) => n + d.enquiries, 0)).toBe(a.totals.enquiries)
    })

    it('matches the performance list for the same listing', async () => {
      const api = createFixtureApi(mem())
      const perf = (await api.getPerformance()).find((p) => p.listing_id === 'l1')!
      const a = await api.getListingActivity('l1')
      expect(a.totals).toMatchObject({
        views: perf.views, unique_visitors: perf.unique_visitors, enquiries: perf.enquiries,
        qualified: perf.qualified, site_visits: perf.site_visits,
      })
    })

    it('feed has visitors and leads, newest first, with plain-language text', async () => {
      const a = await createFixtureApi(mem()).getListingActivity('l1')
      const times = a.feed.map((f) => f.ts)
      expect(times).toEqual([...times].sort().reverse())
      const visitors = a.feed.filter((f) => f.who.kind === 'visitor')
      const leads = a.feed.filter((f) => f.who.kind === 'lead')
      expect(visitors.length).toBeGreaterThan(0)
      expect(leads.length).toBeGreaterThan(0)
      for (const v of visitors) {
        expect(v.who.label).toMatch(/^Visitor \d+$/)
        expect(v.who.lead_id).toBeUndefined()
        expect(v.text.startsWith(v.who.label)).toBe(true)
      }
      for (const l of leads) {
        expect(l.who.lead_id).toBeTruthy()
        expect(l.text.startsWith(l.who.label)).toBe(true)
      }
      expect(a.feed.map((f) => f.text)).toEqual(expect.arrayContaining(['Rohit Deshmukh sent an enquiry from Instagram', 'Rohit Deshmukh tapped WhatsApp']))
      expect(a.feed.some((f) => /^Visitor \d+ viewed this from \w+/.test(f.text))).toBe(true)
      // privacy: nothing that looks like an id, IP or agent string
      expect(JSON.stringify(a)).not.toMatch(/anon|user_agent|\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/i)
    })

    it('honours the limit (and caps it at 100)', async () => {
      const api = createFixtureApi(mem())
      expect((await api.getListingActivity('l1', 3)).feed).toHaveLength(3)
      expect((await api.getListingActivity('l1', 500)).feed.length).toBeLessThanOrEqual(100)
    })

    it('people are the leads who enquired or interacted, hottest first', async () => {
      const a = await createFixtureApi(mem()).getListingActivity('l1')
      expect(a.people.length).toBeGreaterThan(0)
      const scores = a.people.map((p) => p.score)
      expect(scores).toEqual([...scores].sort((x, y) => y - x))
      expect(a.people[0]).toMatchObject({ lead_id: 'c4', name: 'Priya Nair', temperature: 'hot', score: 85 })
      expect(Object.keys(a.people[0]).sort()).toEqual(['last_activity_at', 'lead_id', 'name', 'requirement_line', 'score', 'temperature'])
    })

    it('a quiet listing has zeros, an empty feed and no people', async () => {
      const api = createFixtureApi(mem())
      const a = await api.getListingActivity('l2') // the draft
      expect(a.totals.views).toBe(0)
      expect(a.totals.enquiries).toBe(0)
      expect(a.feed).toEqual([])
      expect(a.people).toEqual([])
      expect(a.by_source).toEqual({})
      expect(a.daily).toHaveLength(14)
      expect(a.daily.every((d) => d.views === 0 && d.enquiries === 0)).toBe(true)
    })

    it('is a 404 for an unknown listing', async () => {
      await expect(createFixtureApi(mem()).getListingActivity('nope')).rejects.toMatchObject({ status: 404 })
    })
  })
})

describe('splitByWeights', () => {
  it('splits a total exactly', () => {
    expect(splitByWeights(10, [1, 1, 1]).reduce((a, b) => a + b, 0)).toBe(10)
    expect(splitByWeights(36, [4, 3, 2, 1])).toEqual([14, 11, 7, 4])
  })
  it('handles zero totals and zero weights', () => {
    expect(splitByWeights(0, [1, 2])).toEqual([0, 0])
    expect(splitByWeights(5, [0, 0])).toEqual([0, 0])
  })
})
