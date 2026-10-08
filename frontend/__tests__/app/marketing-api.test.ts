import { createApiClient } from '@/lib/app/api'

function fakeFetch(status: number, body: unknown) {
  return jest.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  })) as unknown as jest.MockedFunction<typeof fetch>
}
const call = (f: jest.MockedFunction<typeof fetch>) => f.mock.calls[0] as unknown as [string, RequestInit]

describe('marketing client methods', () => {
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
    await expect(down.getPerformance()).rejects.toMatchObject({ status: 0 })

    const actions = [{ type: 'call', title: 'Call X', detail: 'd', priority: 1, lead_id: 'c1' }]
    const t = createApiClient({ getToken: () => 'tok', fetchImpl: fakeFetch(200, { counts: {}, hot_buyers: [], follow_ups: [], headline: '', actions }) })
    expect((await t.getToday()).actions).toEqual(actions)
  })
})
