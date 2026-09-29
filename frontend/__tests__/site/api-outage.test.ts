/** An API outage must surface as an error, never as "not found" (wrong 404s get cached and can de-index pages). */
const ORIGINAL_ENV = process.env.NODE_ENV

function mockFetch(impl: () => Promise<unknown>) {
  ;(global as unknown as { fetch: unknown }).fetch = jest.fn(impl)
}
// jsdom has no Response: a minimal stand-in with what getJson reads
const json = (status: number, body: unknown = {}) =>
  Promise.resolve({ status, ok: status >= 200 && status < 300, json: async () => body })

async function load() {
  jest.resetModules()
  ;(process.env as Record<string, string>).NODE_ENV = 'production' // no dev fixture fallback
  delete process.env.SITE_USE_FIXTURES
  return import('@/lib/site/api')
}

afterAll(() => {
  ;(process.env as Record<string, string>).NODE_ENV = ORIGINAL_ENV as string
})

describe('site data access', () => {
  it('returns null only for a genuine 404', async () => {
    const api = await load()
    mockFetch(() => json(404))
    expect(await api.getAgent('nobody')).toBeNull()
    expect(await api.getListing('a', 'x')).toBeNull()
    expect(await api.getListings('nobody')).toEqual({ items: [], total: 0 })
  })

  it('throws (not 404) when the API returns 500', async () => {
    const api = await load()
    mockFetch(() => json(500))
    await expect(api.getAgent('a')).rejects.toThrow(/temporarily unavailable/)
    await expect(api.getListing('a', 'x')).rejects.toThrow(/temporarily unavailable/)
    await expect(api.getListings('a')).rejects.toThrow(/temporarily unavailable/)
  })

  it('throws when the API is unreachable', async () => {
    const api = await load()
    mockFetch(() => Promise.reject(new Error('ECONNREFUSED')))
    await expect(api.getAgent('a')).rejects.toThrow(/temporarily unavailable/)
  })

  it('returns data on success', async () => {
    const api = await load()
    mockFetch(() => json(200, { slug: 'a', agent_name: 'A' }))
    expect((await api.getAgent('a'))?.agent_name).toBe('A')
  })
})
