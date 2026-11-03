import {
  activityIsEmpty,
  activityTime,
  axisLabels,
  chartScale,
  chartSummary,
  dayLabel,
  istDateKey,
  niceMax,
  sourceRows,
} from '@/lib/app/activity'
import { computeFreshness, confirmAction, freshnessOf, needingConfirmation, withConfirmAction } from '@/lib/app/freshness'
import { actionHref } from '@/lib/app/marketing'
import type { ListingActivity, Listing, RecommendedAction } from '@/lib/app/types'

const day = (date: string, views: number, enquiries = 0) => ({ date, views, enquiries })

describe('dayLabel / istDateKey', () => {
  it('formats a calendar date without shifting it', () => {
    expect(dayLabel('2026-10-03')).toBe('3 Oct')
    expect(dayLabel('2026-01-31')).toBe('31 Jan')
    expect(dayLabel('not-a-date')).toBe('not-a-date')
  })
  it('gives the India date of an instant (IST = UTC+5:30)', () => {
    expect(istDateKey('2026-10-03T18:29:00Z')).toBe('2026-10-03')
    expect(istDateKey('2026-10-03T18:31:00Z')).toBe('2026-10-04') // just past midnight in India
    expect(istDateKey(Date.UTC(2026, 0, 1, 0, 0))).toBe('2026-01-01')
  })
})

describe('niceMax / chartScale', () => {
  it('rounds a maximum up to a tidy ceiling, never below 4', () => {
    expect(niceMax(0)).toBe(4)
    expect(niceMax(3)).toBe(4)
    expect(niceMax(5)).toBe(5)
    expect(niceMax(6)).toBe(10)
    expect(niceMax(11)).toBe(20)
    expect(niceMax(34)).toBe(50)
    expect(niceMax(51)).toBe(100)
    expect(niceMax(101)).toBe(200)
    expect(niceMax(NaN)).toBe(4)
  })

  it('scales bars to the tidy maximum and totals the series', () => {
    const m = chartScale([day('2026-10-01', 0), day('2026-10-02', 5, 1), day('2026-10-03', 10, 2)])
    expect(m.max).toBe(10)
    expect(m.bars.map((b) => b.height)).toEqual([0, 0.5, 1])
    expect(m.totalViews).toBe(15)
    expect(m.totalEnquiries).toBe(3)
  })

  it('an all-zero or missing series gives flat bars, not NaN', () => {
    const m = chartScale([day('2026-10-01', 0), day('2026-10-02', 0)])
    expect(m.max).toBe(4)
    expect(m.bars.every((b) => b.height === 0)).toBe(true)
    expect(chartScale(undefined)).toEqual({ max: 4, bars: [], totalViews: 0, totalEnquiries: 0 })
  })

  it('a small series still leaves headroom (2 views is half of 4, not a full bar)', () => {
    expect(chartScale([day('2026-10-01', 2)]).bars[0].height).toBe(0.5)
  })
})

describe('chartSummary / axisLabels', () => {
  it('reads out the totals and the busiest day', () => {
    const s = chartSummary([day('2026-10-01', 2, 0), day('2026-10-02', 9, 1), day('2026-10-03', 4, 2)])
    expect(s).toBe('Last 14 days: 15 views and 3 enquiries. Busiest day: 2 Oct with 9 views.')
  })
  it('uses singular words for one', () => {
    expect(chartSummary([day('2026-10-01', 1, 1)])).toBe('Last 14 days: 1 view and 1 enquiry. Busiest day: 1 Oct with 1 view.')
  })
  it('says so when nothing happened', () => {
    expect(chartSummary([day('2026-10-01', 0), day('2026-10-02', 0)])).toBe('No views in the last 14 days.')
    expect(chartSummary([])).toBe('No views in the last 14 days.')
  })
  it('labels the first, middle and last day', () => {
    const days = Array.from({ length: 14 }, (_, i) => day(`2026-10-${String(i + 1).padStart(2, '0')}`, 1))
    expect(axisLabels(days)).toEqual(['1 Oct', '7 Oct', '14 Oct'])
    expect(axisLabels([day('2026-10-01', 1)])).toEqual(['1 Oct'])
    expect(axisLabels([])).toEqual([])
  })
})

describe('activityTime (relative time)', () => {
  const now = new Date('2026-10-20T12:00:00Z')
  it('reads like a person would say it', () => {
    expect(activityTime('2026-10-20T11:59:40Z', now)).toBe('just now')
    expect(activityTime('2026-10-20T11:55:00Z', now)).toBe('5m ago')
    expect(activityTime('2026-10-20T09:00:00Z', now)).toBe('3h ago')
    expect(activityTime('2026-10-19T09:00:00Z', now)).toBe('Yesterday')
    expect(activityTime('2026-10-17T12:00:00Z', now)).toBe('3d ago')
  })
  it('falls back to a date after a week', () => {
    expect(activityTime('2026-10-05T12:00:00Z', now)).toBe('5 Oct')
  })
  it('treats a timestamp without a zone as UTC and survives junk', () => {
    expect(activityTime('2026-10-20T09:00:00', now)).toBe('3h ago')
    expect(activityTime('garbage', now)).toBe('')
    expect(activityTime('2026-10-21T12:00:00Z', now)).toBe('just now') // clock skew: never negative
  })
})

describe('sourceRows', () => {
  it('sorts by views, labels direct, and scales the bar to the top source', () => {
    const rows = sourceRows({ direct: { views: 5, enquiries: 0 }, whatsapp: { views: 20, enquiries: 3 }, instagram: { views: 10, enquiries: 1 } })
    expect(rows.map((r) => r.label)).toEqual(['WhatsApp', 'Instagram', 'Direct'])
    expect(rows.map((r) => r.share)).toEqual([1, 0.5, 0.25])
    expect(rows[0]).toMatchObject({ key: 'whatsapp', views: 20, enquiries: 3 })
  })
  it('breaks ties by enquiries, tolerates an unknown source name and empty input', () => {
    const rows = sourceRows({ a: { views: 3, enquiries: 0 }, b: { views: 3, enquiries: 2 }, olx: { views: 1, enquiries: 0 } })
    expect(rows.map((r) => r.key)).toEqual(['b', 'a', 'olx'])
    expect(rows[2].label).toBe('Olx')
    expect(sourceRows({})).toEqual([])
    expect(sourceRows(undefined)).toEqual([])
    expect(sourceRows({ x: { views: 0, enquiries: 0 } })[0].share).toBe(0)
  })
})

describe('activityIsEmpty', () => {
  const base = (over: Partial<ListingActivity['totals']>, feed: ListingActivity['feed'] = []): ListingActivity => ({
    listing: { id: 'l', title: 'T', status: 'live', price_inr: 1 },
    totals: { views: 0, unique_visitors: 0, enquiries: 0, qualified: 0, site_visits: 0, deals: 0, whatsapp_clicks: 0, call_clicks: 0, shares: 0, ...over },
    by_source: {}, daily: [], feed, people: [],
  })
  it('is empty only when there are no views, enquiries or events', () => {
    expect(activityIsEmpty(base({}))).toBe(true)
    expect(activityIsEmpty(base({ views: 1 }))).toBe(false)
    expect(activityIsEmpty(base({ enquiries: 1 }))).toBe(false)
    expect(activityIsEmpty(base({}, [{ ts: '2026-10-01T00:00:00Z', type: 'share', who: { kind: 'visitor', label: 'Visitor 1' }, source: null, text: 'x' }]))).toBe(false)
  })
})

describe('freshness helpers', () => {
  const now = new Date('2026-10-30T00:00:00Z')
  const daysAgo = (n: number) => new Date(now.getTime() - n * 86_400_000).toISOString()
  const at = (n: number, status: Listing['status'] = 'live') =>
    computeFreshness({ status, freshness_confirmed_at: daysAgo(n), published_at: daysAgo(100), created_at: daysAgo(100) }, now)

  it('follows the contract: <21 fresh, 21..44 confirm, >=45 hidden', () => {
    expect(at(0)).toEqual({ freshness: 'fresh', days_since_confirmed: 0 })
    expect(at(20).freshness).toBe('fresh')
    expect(at(21).freshness).toBe('confirm')
    expect(at(44).freshness).toBe('confirm')
    expect(at(45).freshness).toBe('hidden')
    expect(at(90)).toEqual({ freshness: 'hidden', days_since_confirmed: 90 })
  })
  it('falls back from confirmed to published to created', () => {
    expect(computeFreshness({ status: 'live', published_at: daysAgo(30), created_at: daysAgo(90) }, now).freshness).toBe('confirm')
    expect(computeFreshness({ status: 'live', published_at: null, created_at: daysAgo(50) }, now).freshness).toBe('hidden')
    expect(computeFreshness({ status: 'live', created_at: 'garbage' }, now)).toEqual({ freshness: 'fresh', days_since_confirmed: null })
  })
  it('only live and under-offer listings are ever asked', () => {
    expect(at(60, 'under_offer').freshness).toBe('hidden')
    for (const s of ['draft', 'paused', 'sold', 'rented', 'expired'] as const) expect(at(60, s).freshness).toBe('fresh')
  })
  it('freshnessOf treats a missing field (older backend) and closed listings as fresh', () => {
    expect(freshnessOf({ status: 'live' })).toBe('fresh')
    expect(freshnessOf({ status: 'live', freshness: 'hidden' })).toBe('hidden')
    expect(freshnessOf({ status: 'sold', freshness: 'hidden' })).toBe('fresh')
  })

  const L = (id: string, freshness: Listing['freshness'], days: number, status: Listing['status'] = 'live') =>
    ({ id, status, freshness, days_since_confirmed: days, title: id }) as Listing
  it('needingConfirmation lists hidden first, then the longest unconfirmed', () => {
    const out = needingConfirmation([L('a', 'confirm', 25), L('b', 'fresh', 1), L('c', 'hidden', 46), L('d', 'confirm', 40), L('e', 'hidden', 60)])
    expect(out.map((l) => l.id)).toEqual(['e', 'c', 'd', 'a'])
  })
  it('confirmAction: none when all fresh, one listing links to it, several link to the list', () => {
    expect(confirmAction([L('a', 'fresh', 2)])).toBeNull()
    expect(confirmAction([])).toBeNull()
    expect(confirmAction([L('a', 'confirm', 25), L('b', 'fresh', 1)])).toEqual({
      type: 'confirm_listing',
      title: 'Listings that need your confirmation',
      detail: '1 listing needs a quick check.',
      priority: 2,
      listing_id: 'a',
    })
    const many = confirmAction([L('a', 'confirm', 25), L('b', 'hidden', 50)])!
    expect(many.listing_id).toBeUndefined()
    expect(many.priority).toBe(1)
    expect(many.detail).toBe('2 listings need a quick check. 1 hidden from buyers until you confirm.')
  })
  it('withConfirmAction adds it once, in priority order, and defers to a backend one', () => {
    const backend: RecommendedAction[] = [
      { type: 'call', title: 'Call X', detail: '', priority: 1, lead_id: 'c1' },
      { type: 'create_marketing', title: 'M', detail: '', priority: 3, listing_id: 'l1' },
    ]
    const out = withConfirmAction(backend, [L('a', 'confirm', 25)])!
    expect(out.map((a) => a.type)).toEqual(['call', 'confirm_listing', 'create_marketing'])
    expect(backend).toHaveLength(2) // input not mutated
    const own = [{ type: 'confirm_listing', title: 'Server says', detail: '', priority: 2 } as RecommendedAction]
    expect(withConfirmAction(own, [L('a', 'hidden', 60)])).toBe(own)
    expect(withConfirmAction(backend, [L('a', 'fresh', 1)])).toBe(backend)
    expect(withConfirmAction(undefined, [L('a', 'hidden', 60)])).toHaveLength(1)
    expect(withConfirmAction(undefined, [])).toBeUndefined()
  })
  it('a confirm_listing action leads to the listing, or to the Listings screen card', () => {
    expect(actionHref({ type: 'confirm_listing', title: '', detail: '', priority: 2, listing_id: 'l3' })).toBe('/studio/listings/l3')
    expect(actionHref({ type: 'confirm_listing', title: '', detail: '', priority: 2 })).toBe('/studio/listings#confirm')
  })
})
