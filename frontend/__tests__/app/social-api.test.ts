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

describe('social client methods', () => {
  it('getSocialStatus GETs /social/status with the bearer token', async () => {
    const status = { dry_run: true, channels: { facebook_page: true, instagram: false }, brand: 'PUNE Property', media_url_ok: false }
    const f = fakeFetch(200, status)
    const api = createApiClient({ baseUrl: 'http://x', getToken: () => 'tok', fetchImpl: f })
    expect(await api.getSocialStatus()).toEqual(status)
    const [url, init] = call(f)
    expect(url).toBe('http://x/api/v1/social/status')
    expect(init.method).toBe('GET')
    expect(auth(init)).toBe('Bearer tok')
  })

  it('publishToSocial POSTs channels, approve, consent and force, and unwraps publications', async () => {
    const f = fakeFetch(200, { publications: [{ id: 'p1', channel: 'instagram', status: 'dry_run' }] })
    const api = createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })
    const res = await api.publishToSocial('l1', { channels: ['facebook_page', 'instagram'], approve: true, consent: true })
    expect(res).toEqual([{ id: 'p1', channel: 'instagram', status: 'dry_run' }])
    const [url, init] = call(f)
    expect(url).toBe('/api/v1/social/listings/l1/publish')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({ channels: ['facebook_page', 'instagram'], approve: true, consent: true, force: false })
    expect(auth(init)).toBe('Bearer tok')

    const f2 = fakeFetch(200, { publications: [] })
    await createApiClient({ getToken: () => 'tok', fetchImpl: f2 }).publishToSocial('l1', { channels: ['instagram'], approve: true, consent: true, force: true })
    expect(JSON.parse(call(f2)[1].body as string).force).toBe(true)
  })

  it('listPublications GETs the listing history and returns items', async () => {
    const f = fakeFetch(200, { items: [{ id: 'p2' }, { id: 'p1' }] })
    const api = createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })
    expect(await api.listPublications('l9')).toEqual([{ id: 'p2' }, { id: 'p1' }])
    expect(call(f)[0]).toBe('/api/v1/social/listings/l9/publications')
    expect(call(f)[1].method).toBe('GET')
    expect(auth(call(f)[1])).toBe('Bearer tok')
  })

  it('retryPublication POSTs to /social/publications/{id}/retry', async () => {
    const f = fakeFetch(200, { id: 'p3', status: 'published' })
    const api = createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })
    expect(await api.retryPublication('p3')).toMatchObject({ status: 'published' })
    expect(call(f)[0]).toBe('/api/v1/social/publications/p3/retry')
    expect(call(f)[1].method).toBe('POST')
    expect(auth(call(f)[1])).toBe('Bearer tok')
  })

  it('surfaces 409, 404 and network errors, and reports a 401 to onUnauthorized', async () => {
    const conflict = createApiClient({ getToken: () => 'tok', fetchImpl: fakeFetch(409, { detail: 'No marketing pack yet' }) })
    await expect(conflict.publishToSocial('l1', { channels: ['instagram'], approve: true, consent: true })).rejects.toMatchObject({
      status: 409,
      detail: 'No marketing pack yet',
    })
    const nf = createApiClient({ getToken: () => 'tok', fetchImpl: fakeFetch(404, { detail: 'Not found' }) })
    await expect(nf.listPublications('zz')).rejects.toMatchObject({ status: 404 })

    const onUnauthorized = jest.fn()
    const unauth = createApiClient({ getToken: () => 'tok', onUnauthorized, fetchImpl: fakeFetch(401, { detail: 'Not authenticated' }) })
    await expect(unauth.getSocialStatus()).rejects.toMatchObject({ status: 401 })
    expect(onUnauthorized).toHaveBeenCalledTimes(1)

    const down = createApiClient({ getToken: () => 'tok', fetchImpl: jest.fn().mockRejectedValue(new Error('offline')) as unknown as typeof fetch })
    await expect(down.getSocialStatus()).rejects.toMatchObject({ status: 0 })
  })
})
