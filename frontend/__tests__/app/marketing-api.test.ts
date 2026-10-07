import { createApiClient } from '@/lib/app/api'

function fakeFetch(status: number, body: unknown) {
  return jest.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  })) as unknown as jest.MockedFunction<typeof fetch>
}
const call = (f: jest.MockedFunction<typeof fetch>) => f.mock.calls[0] as unknown as [string, RequestInit]
const auth = (init: RequestInit) => (init.headers as Record<string, string>).Authorization

describe('marketing client methods', () => {
  it('createMarketingPack POSTs the language (or an empty body) with the bearer token', async () => {
    const f = fakeFetch(200, { listing_id: 'l1', language: 'hi', version: 2 })
    const api = createApiClient({ baseUrl: 'http://x', getToken: () => 'tok', fetchImpl: f })
    expect(await api.createMarketingPack('l1', 'hi')).toMatchObject({ version: 2 })
    const [url, init] = call(f)
    expect(url).toBe('http://x/api/v1/listings/l1/marketing')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({ language: 'hi' })
    expect(auth(init)).toBe('Bearer tok')

    const f2 = fakeFetch(200, {})
    await createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f2 }).createMarketingPack('l1')
    expect(JSON.parse(call(f2)[1].body as string)).toEqual({})
  })

  it('getMarketingPack GETs the pack and surfaces 404 and 409', async () => {
    const f = fakeFetch(200, { listing_id: 'l1' })
    const api = createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })
    await api.getMarketingPack('l1')
    expect(call(f)[0]).toBe('/api/v1/listings/l1/marketing')
    expect(call(f)[1].method).toBe('GET')
    expect(auth(call(f)[1])).toBe('Bearer tok')

    const nf = createApiClient({ getToken: () => 'tok', fetchImpl: fakeFetch(404, { detail: 'Not found' }) })
    await expect(nf.getMarketingPack('zz')).rejects.toMatchObject({ status: 404 })
    const conflict = createApiClient({ getToken: () => 'tok', fetchImpl: fakeFetch(409, { detail: 'Listing is not live' }) })
    await expect(conflict.createMarketingPack('l2')).rejects.toMatchObject({ status: 409, detail: 'Listing is not live' })
  })

  it('getMatchingLeads passes listing_id as a query parameter', async () => {
    const body = { listing: { id: 'l1' }, buyers: [] }
    const f = fakeFetch(200, body)
    const api = createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })
    expect(await api.getMatchingLeads('l 1')).toEqual(body)
    expect(call(f)[0]).toBe('/api/v1/inbox/matching-leads?listing_id=l+1')
    expect(auth(call(f)[1])).toBe('Bearer tok')
  })

  it('getPerformance unwraps items', async () => {
    const f = fakeFetch(200, { items: [{ listing_id: 'l1', views: 3 }] })
    const api = createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })
    expect(await api.getPerformance()).toEqual([{ listing_id: 'l1', views: 3 }])
    expect(call(f)[0]).toBe('/api/v1/inbox/performance')
  })

  it('maps 401 and network errors, and passes actions through getToday', async () => {
    const onUnauthorized = jest.fn()
    const a401 = createApiClient({ getToken: () => 'tok', onUnauthorized, fetchImpl: fakeFetch(401, { detail: 'no' }) })
    await expect(a401.getPerformance()).rejects.toMatchObject({ status: 401 })
    expect(onUnauthorized).toHaveBeenCalled()
    const down = createApiClient({ getToken: () => null, fetchImpl: jest.fn().mockRejectedValue(new TypeError('x')) as unknown as typeof fetch })
    await expect(down.getMatchingLeads('l1')).rejects.toMatchObject({ status: 0 })

    const actions = [{ type: 'call', title: 'Call X', detail: 'd', priority: 1, lead_id: 'c1' }]
    const t = createApiClient({ getToken: () => 'tok', fetchImpl: fakeFetch(200, { counts: {}, hot_buyers: [], follow_ups: [], headline: '', actions }) })
    expect((await t.getToday()).actions).toEqual(actions)
  })
})
