// jsdom has no Response: a minimal stand-in is enough to read the body and the headers
;(global as any).Response = class {
  body: string; headers: Headers
  constructor(b: string, init: any) { this.body = b; this.headers = new Headers(init.headers) }
  async text() { return this.body }
}

// eslint-disable-next-line @typescript-eslint/no-var-requires
const { GET } = require('@/app/news-sitemap.xml/route')

beforeAll(() => { process.env.SITE_USE_FIXTURES = '1' })
afterAll(() => { delete process.env.SITE_USE_FIXTURES })

test('/news-sitemap.xml is served as XML in the news namespace', async () => {
  const res = await GET()
  expect(res.headers.get('Content-Type')).toMatch(/application\/xml/)
  const xml = await res.text()
  expect(xml).toMatch(/^<\?xml version="1.0" encoding="UTF-8"\?>\n<urlset /)
  expect(xml).toContain('xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"')
})
