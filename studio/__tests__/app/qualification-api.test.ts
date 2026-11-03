import { createApiClient } from '@/lib/app/api'

function fakeFetch(status: number, body: unknown) {
  return jest.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  })) as unknown as jest.MockedFunction<typeof fetch>
}
const call = (f: jest.MockedFunction<typeof fetch>) => f.mock.calls[0] as unknown as [string, RequestInit]

describe('qualification client methods', () => {
  it('getToday GETs /inbox/today with the bearer header', async () => {
    const body = { counts: { hot: 1 }, hot_buyers: [], follow_ups: [], headline: 'x' }
    const f = fakeFetch(200, body)
    const api = createApiClient({ baseUrl: 'http://x', getToken: () => 'tok', fetchImpl: f })
    expect(await api.getToday()).toEqual(body)
    const [url, init] = call(f)
    expect(url).toBe('http://x/api/v1/inbox/today')
    expect(init.method).toBe('GET')
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  })

  it('createFollowupDraft POSTs the language (or an empty body for the default)', async () => {
    const f = fakeFetch(200, { message: 'hi', whatsapp_url: 'u', language: 'hi', based_on: [] })
    const api = createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })
    await api.createFollowupDraft('c1', 'hi')
    const [url, init] = call(f)
    expect(url).toBe('/api/v1/inbox/leads/c1/followup-draft')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({ language: 'hi' })
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok')

    const f2 = fakeFetch(200, {})
    await createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f2 }).createFollowupDraft('c1')
    expect(JSON.parse(call(f2)[1].body as string)).toEqual({})
  })

  it('updateLead PATCHes follow_up_at, and keeps the legacy (stage, note) form', async () => {
    const f = fakeFetch(200, { id: 'c1' })
    const api = createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })
    await api.updateLead('c1', { follow_up_at: '2026-10-01T10:00:00.000Z' })
    expect(call(f)[1].method).toBe('PATCH')
    expect(JSON.parse(call(f)[1].body as string)).toEqual({ follow_up_at: '2026-10-01T10:00:00.000Z' })

    const f2 = fakeFetch(200, { id: 'c1' })
    await createApiClient({ baseUrl: '', getToken: () => 't', fetchImpl: f2 }).updateLead('c1', 'site_visit')
    expect(JSON.parse(call(f2)[1].body as string)).toEqual({ stage: 'site_visit' })
  })

  it('maps errors (404, 401, network) like the other methods', async () => {
    const onUnauthorized = jest.fn()
    const api404 = createApiClient({ getToken: () => 'tok', fetchImpl: fakeFetch(404, { detail: 'Lead not found' }) })
    await expect(api404.createFollowupDraft('zz')).rejects.toMatchObject({ status: 404, detail: 'Lead not found' })
    const api401 = createApiClient({ getToken: () => 'tok', onUnauthorized, fetchImpl: fakeFetch(401, { detail: 'nope' }) })
    await expect(api401.getToday()).rejects.toMatchObject({ status: 401 })
    expect(onUnauthorized).toHaveBeenCalled()
    const down = createApiClient({ getToken: () => null, fetchImpl: jest.fn().mockRejectedValue(new TypeError('x')) as unknown as typeof fetch })
    await expect(down.getToday()).rejects.toMatchObject({ status: 0 })
  })
})
