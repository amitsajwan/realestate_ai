import { createFixtureApi } from '@/lib/app/fixtures'
import { actionHref } from '@/lib/app/marketing'

const mem = () => {
  const m: Record<string, string> = {}
  return { getItem: (k: string) => m[k] ?? null, setItem: (k: string, v: string) => void (m[k] = v) }
}

describe('fixture performance and actions', () => {
  it('returns performance rows for non-draft listings, most enquiries first', async () => {
    const api = createFixtureApi(mem())
    const rows = await api.getPerformance()
    expect(rows.map((r) => r.listing_id)).not.toContain('l2')
    const l1 = rows.find((r) => r.listing_id === 'l1')!
    expect(l1).toMatchObject({ enquiries: 3, status: 'live' })
    expect(l1.views).toBeGreaterThan(0)
    expect(l1.unique_visitors).toBeLessThanOrEqual(l1.views)
    expect(l1.qualified).toBeLessThanOrEqual(l1.enquiries)
    expect(l1.by_source).toEqual({ instagram: 1, facebook: 1, whatsapp: 1 })
    const enq = rows.map((r) => r.enquiries)
    expect([...enq].sort((a, b) => b - a)).toEqual(enq)
  })

  it('getToday carries prioritised actions of every type', async () => {
    const api = createFixtureApi(mem())
    const { actions } = await api.getToday()
    const list = actions!
    expect(list.length).toBeLessThanOrEqual(6)
    const pri = list.map((a) => a.priority)
    expect([...pri].sort()).toEqual(pri)
    const byType = (t: string) => list.filter((a) => a.type === t)
    expect(byType('call')[0]).toMatchObject({ lead_id: 'c1', priority: 1 })
    expect(byType('follow_up')[0]).toMatchObject({ lead_id: 'c2', priority: 1 })
    expect(byType('create_marketing').some((a) => a.listing_id === 'l1')).toBe(true)
  })
})

describe('marketing helpers', () => {
  it('actionHref targets', () => {
    const a = (type: string, extra = {}) => actionHref({ type, title: '', detail: '', priority: 1, ...extra } as never)
    expect(a('call', { lead_id: 'c1' })).toBe('/studio/leads/c1')
    expect(a('follow_up', { lead_id: 'c2' })).toBe('/studio/leads/c2')
    expect(a('create_marketing', { listing_id: 'l3' })).toBe('/studio/listings/l3/marketing')
    expect(a('call')).toBe('/studio/leads')
  })
})
