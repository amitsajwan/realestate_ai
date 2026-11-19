/** A place page (/projects/area/<place>) 404s on an unknown place, so an outage must throw, never read as "no such place": Search
 *  Console reported real area pages from the sitemap as "Not found (404)" when the places call failed under a crawl. */
export {}
const ENV_BEFORE = process.env.NODE_ENV

function mockFetchOnce(impl: () => Promise<unknown>) {
  ;(global as unknown as { fetch: unknown }).fetch = jest.fn(impl)
}
const reply = (status: number, body: unknown = {}) =>
  Promise.resolve({ status, ok: status >= 200 && status < 300, json: async () => body })

async function loadRegisterModule() {
  jest.resetModules()
  ;(process.env as Record<string, string>).NODE_ENV = 'production'
  delete process.env.SITE_USE_FIXTURES
  return import('@/lib/site/register')
}

afterAll(() => {
  ;(process.env as Record<string, string>).NODE_ENV = ENV_BEFORE as string
})

it('the places for a place page throw when the API fails, while the quiet list stays empty', async () => {
  const reg = await loadRegisterModule()
  jest.useFakeTimers()
  try {
    mockFetchOnce(() => Promise.reject(new Error('ECONNREFUSED')))
    const strict = expect(reg.getRegisterPlacesOrThrow()).rejects.toThrow(/temporarily unavailable/)
    const quiet = reg.getRegisterPlaces()
    await jest.advanceTimersByTimeAsync(30000)
    await strict
    expect(await quiet).toEqual([])
  } finally {
    jest.useRealTimers()
  }
})

it('the places come back when the API answers', async () => {
  const reg = await loadRegisterModule()
  const kharadi = { key: 'kharadi', slug: 'kharadi', name: 'Kharadi', zone: 'east', projects: 90, indexable: 40 }
  mockFetchOnce(() => reply(200, [kharadi]))
  expect(await reg.getRegisterPlacesOrThrow()).toEqual([kharadi])
})
