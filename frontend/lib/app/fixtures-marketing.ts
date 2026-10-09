/**
 * Fixture-mode builders for performance and recommended actions.
 * Deterministic and fact-only, like the backend: nothing is invented.
 */
import { dealsForListing } from './fixtures-outcomes'
import type { LeadDetail, Listing, PerformanceItem, RecommendedAction } from './types'

const VIEWS_BASE: Record<string, number> = { l1: 34, l3: 21, l4: 12, l5: 9 }
const LATE_STAGES = ['site_visit', 'negotiating', 'won']

export function performanceFor(listings: Listing[], leads: LeadDetail[]): PerformanceItem[] {
  return listings
    .filter((l) => l.status !== 'draft')
    .map((l) => {
      const enq = leads.filter((x) => x.first_listing_id === l.id)
      const viewEvents = leads.reduce((n, x) => n + x.timeline.filter((e) => e.type === 'listing_view' && e.listing_id === l.id).length, 0)
      const views = (VIEWS_BASE[l.id] ?? 0) + viewEvents
      const by_source: Record<string, number> = {}
      for (const x of enq) by_source[x.source || 'direct'] = (by_source[x.source || 'direct'] ?? 0) + 1
      const qualified = enq.filter((x) => x.temperature !== 'cold' || x.requirement?.budget_max_inr || x.requirement?.timeline).length
      return {
        listing_id: l.id, title: l.title, price_inr: l.price_inr, status: l.status, views,
        unique_visitors: Math.max(0, Math.round(views * 0.7)), enquiries: enq.length, qualified,
        site_visits: enq.filter((x) => LATE_STAGES.includes(x.stage)).length, by_source,
        ...dealsForListing(l.id, leads),
      }
    })
    .sort((a, b) => b.enquiries - a.enquiries || b.views - a.views)
}

export function actionsFor(
  listings: Listing[],
  leads: LeadDetail[],
): RecommendedAction[] {
  const out: RecommendedAction[] = []
  const open = leads.filter((l) => l.stage !== 'won' && l.stage !== 'lost')
  for (const l of open) {
    if (l.temperature === 'hot' && l.stage === 'new') {
      out.push({ type: 'call', title: `Call ${l.name}`, detail: 'Hot buyer who has not been contacted yet', priority: 1, lead_id: l.id })
    } else if (l.follow_up?.overdue) {
      out.push({ type: 'follow_up', title: `Follow up with ${l.name}`, detail: 'Their follow-up is overdue', priority: 1, lead_id: l.id })
    }
  }
  const live = listings.filter((l) => l.status === 'live')
  for (const l of live) {
    out.push({ type: 'create_marketing', title: `Start marketing for ${l.title}`, detail: 'Posts and reels from its checked facts, to bring in leads', priority: 3, listing_id: l.id })
  }
  return out.sort((a, b) => a.priority - b.priority).slice(0, 6)
}
