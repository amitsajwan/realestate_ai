/** Fixture data for the listing activity screen: deterministic, privacy-safe ("Visitor 1"), consistent with performanceFor. */
import { istDateKey } from './activity'
import { sourceLabel } from './leads'
import type { ActivityEventType, ActivityFeedItem, LeadDetail, Listing, ListingActivity, PerformanceItem } from './types'

const DAY = 86_400_000
const HOUR = 3_600_000
const SOURCES = ['whatsapp', 'instagram', 'facebook', 'direct']
const SOURCE_WEIGHTS = [4, 3, 2, 1]
const EVENT_TYPE: Record<string, ActivityEventType> = {
  listing_view: 'view',
  whatsapp_click: 'whatsapp_click',
  call_click: 'call_click',
  share: 'share',
  inquiry: 'enquiry',
}

const seedOf = (id: string) => [...id].reduce((n, c) => n + c.charCodeAt(0), 0)

/** Split `total` across `weights` so the parts add up exactly (largest remainder). */
export function splitByWeights(total: number, weights: number[]): number[] {
  const sum = weights.reduce((a, b) => a + b, 0)
  if (total <= 0 || sum <= 0) return weights.map(() => 0)
  const raw = weights.map((w) => (total * w) / sum)
  const out = raw.map(Math.floor)
  let left = total - out.reduce((a, b) => a + b, 0)
  const order = raw.map((r, i) => ({ i, frac: r - Math.floor(r) })).sort((a, b) => b.frac - a.frac || a.i - b.i)
  for (const { i } of order) {
    if (left <= 0) break
    out[i] += 1
    left -= 1
  }
  return out
}

const sentence = (who: string, type: ActivityEventType, source: string | null): string => {
  const from = source ? ` from ${sourceLabel(source)}` : ''
  switch (type) {
    case 'view':
      return `${who} viewed this${from}`
    case 'whatsapp_click':
      return `${who} tapped WhatsApp`
    case 'call_click':
      return `${who} tapped Call`
    case 'share':
      return `${who} shared this`
    case 'enquiry':
      return `${who} sent an enquiry${from}`
  }
}

export function activityFor(
  l: Listing,
  leads: LeadDetail[],
  perf: PerformanceItem | undefined,
  now: Date = new Date(),
  limit = 50,
): ListingActivity {
  const seed = seedOf(l.id)
  const views = perf?.views ?? 0
  const enquirers = leads.filter((x) => x.first_listing_id === l.id)
  const touched = leads.filter((x) => x.first_listing_id === l.id || x.timeline.some((e) => e.listing_id === l.id))
  const leadEvents = touched.flatMap((x) => x.timeline.filter((e) => e.listing_id === l.id && EVENT_TYPE[e.type]).map((e) => ({ lead: x, e })))
  const count = (type: string) => leadEvents.filter(({ e }) => e.type === type).length

  // 14 India days, oldest first, zero-filled. Views follow a gentle weekly wave that leans to recent days.
  const dates = Array.from({ length: 14 }, (_, i) => istDateKey(now.getTime() - (13 - i) * DAY))
  const weights = dates.map((_, i) => 1 + ((seed * (i + 3)) % 5) + Math.floor(i / 4))
  const viewsPerDay = splitByWeights(views, weights)
  const enqPerDay = dates.map((d) => enquirers.filter((x) => istDateKey(x.created_at) === d).length)
  const daily = dates.map((date, i) => ({ date, views: viewsPerDay[i], enquiries: enqPerDay[i] }))

  const enqBySource: Record<string, number> = {}
  for (const x of enquirers) enqBySource[x.source || 'direct'] = (enqBySource[x.source || 'direct'] ?? 0) + 1
  const keys = [...new Set([...SOURCES, ...Object.keys(enqBySource)])]
  const viewsBySource = splitByWeights(views, keys.map((k) => SOURCE_WEIGHTS[SOURCES.indexOf(k)] ?? 1))
  const by_source: ListingActivity['by_source'] = {}
  keys.forEach((k, i) => {
    if (viewsBySource[i] > 0 || enqBySource[k]) by_source[k] = { views: viewsBySource[i], enquiries: enqBySource[k] ?? 0 }
  })

  // Feed: the buyers we know by name, plus a handful of anonymous visitors.
  const feed: ActivityFeedItem[] = leadEvents.map(({ lead, e }) => {
    const type = EVENT_TYPE[e.type]
    const source = e.source ?? lead.source ?? null
    return { ts: e.ts, type, who: { kind: 'lead', label: lead.name, lead_id: lead.id }, source, text: sentence(lead.name, type, source) }
  })
  const visitors = Math.min(8, Math.max(0, views - leadEvents.filter(({ e }) => e.type === 'listing_view').length))
  for (let n = 1; n <= visitors; n++) {
    const source = SOURCES[(seed + n) % SOURCES.length]
    const type: ActivityEventType = n % 5 === 0 ? 'whatsapp_click' : 'view'
    const label = `Visitor ${n}`
    feed.push({
      ts: new Date(now.getTime() - (1 + n * 5 + (seed % 3)) * HOUR).toISOString(),
      type,
      who: { kind: 'visitor', label },
      source,
      text: sentence(label, type, source),
    })
  }
  feed.sort((a, b) => b.ts.localeCompare(a.ts))

  const people = [...touched]
    .sort((a, b) => b.score - a.score || b.last_activity_at.localeCompare(a.last_activity_at))
    .slice(0, 10)
    .map((x) => ({
      lead_id: x.id, name: x.name, temperature: x.temperature, score: x.score,
      requirement_line: x.requirement_line ?? null, last_activity_at: x.last_activity_at,
    }))

  return {
    listing: { id: l.id, title: l.title, status: l.status, price_inr: l.price_inr },
    totals: {
      views,
      unique_visitors: perf?.unique_visitors ?? 0,
      enquiries: perf?.enquiries ?? enquirers.length,
      qualified: perf?.qualified ?? 0,
      site_visits: perf?.site_visits ?? 0,
      deals: perf?.deals ?? 0,
      whatsapp_clicks: count('whatsapp_click') + Math.round(views * 0.12),
      call_clicks: count('call_click') + Math.round(views * 0.04),
      shares: count('share') + Math.round(views * 0.05),
    },
    by_source,
    daily,
    feed: feed.slice(0, Math.min(100, Math.max(1, limit))),
    people,
  }
}
