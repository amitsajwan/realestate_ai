import { INSIGHTS } from '@/lib/marketing/insights'
import { LOCALITIES, getLocality } from '@/lib/marketing/localities'
import sitemap from '@/app/sitemap'
import robots from '@/app/robots'

describe('locality pages are safe to publish', () => {
  it('has the three east-Pune localities with unique slugs and dated, sourced content', () => {
    expect(LOCALITIES.map((l) => l.slug)).toEqual(['kharadi', 'upper-kharadi', 'wagholi'])
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
    for (const l of LOCALITIES) expect(JSON.stringify(l.gettingAround).toLowerCase()).toMatch(/approved/)
    expect(JSON.stringify(LOCALITIES)).not.toMatch(/metro (station )?(is|will be) (open|opening|ready)/i)
  })
})

describe('sitemap and robots', () => {
  it('lists the localities, guides and key pages; keeps the private app out of search', () => {
    const urls = sitemap().map((s) => s.url)
    expect(urls.some((u) => u.endsWith('/localities/kharadi'))).toBe(true)
    expect(urls.some((u) => u.endsWith('/insights/kharadi-upper-kharadi-wagholi'))).toBe(true)
    expect(urls.some((u) => /studio|join|api/.test(u))).toBe(false)
    const r = robots()
    const rule = Array.isArray(r.rules) ? r.rules[0] : r.rules
    expect(JSON.stringify(rule)).toContain('/studio')
    expect(String(r.sitemap)).toMatch(/sitemap\.xml$/)
  })
})
