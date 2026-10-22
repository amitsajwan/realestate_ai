import robots, { PRIVATE_PATHS } from '@/app/robots'

// robots.txt rules match by prefix: '/register' also shuts '/registered-...', so a new private path must never be the start of a
// page buyers and Google should reach. Every public page family, with a real-looking path each.
const PUBLIC = [
  '/', '/projects', '/projects/lodha-camelot-kharadi', '/projects/area/kharadi', '/projects/area/kharadi/new-launches',
  '/localities', '/localities/kharadi', '/localities/kharadi/eon-free-zone', '/builders', '/builders/lodha',
  '/2-bhk/kharadi', '/3-bhk/wagholi', '/price/under-80-lakh/wagholi', '/check', '/check/lodha-camelot-kharadi',
  '/news', '/insights', '/posts', '/guides/stamp-duty-pune', '/pune-maharera-tracker', '/agent/avasetu',
  '/sitemap.xml', '/sitemaps/kharadi.xml', '/llms.txt',
]

describe('robots.txt never shuts a public page', () => {
  it.each(PUBLIC)('%s stays open to crawlers', (path) => {
    expect(PRIVATE_PATHS.filter((p) => path.startsWith(p))).toEqual([])
  })

  it('allows everything else and names the sitemap index', () => {
    const r = robots()
    const rule = Array.isArray(r.rules) ? r.rules[0] : r.rules
    expect(rule.allow).toBe('/')
    expect(String(r.sitemap)).toMatch(/\/sitemap\.xml$/)
  })
})
