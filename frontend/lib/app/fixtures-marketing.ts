/**
 * Fixture-mode builders for reverse matching, performance and recommended actions.
 * Deterministic and fact-only, like the backend: nothing is invented.
 */
import { formatInr } from './format'
import { dealsForListing } from './fixtures-outcomes'
import { budgetRange } from './leads'
import type { LeadDetail, LeadMatch, Listing, MatchingBuyer, PerformanceItem, RecommendedAction } from './types'

/** Reverse matching draft: only says "fits your budget" when the price is inside the stated budget. */
export function buyerDraft(l: Listing, lead: LeadDetail, shareUrl: string): string {
  const first = lead.name.split(' ')[0]
  const r = lead.requirement
  const hi = r?.budget_max_inr ?? null
  const lo = r?.budget_min_inr ?? 0
  const inBudget = hi != null && l.price_inr >= lo && l.price_inr <= hi
  const budget = budgetRange(r?.budget_min_inr, r?.budget_max_inr).replace(/₹| /g, '')
  const fit = inBudget && budget ? `; it fits your ${budget} budget` : ''
  return `Hi ${first}, I have a new ${l.title} at ${formatInr(l.price_inr).replace(' ', '')}${fit}. Details: ${shareUrl}`
}

export function matchingFor(
  l: Listing,
  leads: LeadDetail[],
  score: (r: NonNullable<LeadDetail['requirement']>, l: Listing) => LeadMatch,
  shareUrl: string,
  waUrl: (phone: string, text: string) => string,
): MatchingBuyer[] {
  return leads
    .filter((x) => x.stage !== 'won' && x.stage !== 'lost' && x.requirement)
    .map((x) => ({ lead: x, m: score(x.requirement!, l) }))
    .filter(({ m }) => m.match_pct >= 60)
    .sort((a, b) => b.m.match_pct - a.m.match_pct || b.lead.score - a.lead.score)
    .slice(0, 10)
    .map(({ lead, m }) => {
      const message = buyerDraft(l, lead, shareUrl)
      return {
        lead_id: lead.id, name: lead.name, phone: lead.phone, temperature: lead.temperature, score: lead.score,
        requirement_line: lead.requirement_line ?? null, match_pct: m.match_pct, reasons: m.reasons,
        draft: { message, whatsapp_url: waUrl(lead.phone, message) },
      }
    })
}

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
  buyerCount: (l: Listing) => number,
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
    const n = buyerCount(l)
    const fresh = Date.now() - new Date(l.created_at).getTime() < 3 * 86_400_000
    if (fresh && n >= 1) {
      out.push({ type: 'send_property', title: `Send the ${l.title} to ${n} matching buyer${n > 1 ? 's' : ''}`, detail: 'New listing that fits what they asked for', priority: 2, listing_id: l.id, buyer_count: n })
    }
  }
  for (const l of live) {
    out.push({ type: 'create_marketing', title: `Create marketing for ${l.title}`, detail: 'Get ready-to-share posts and a WhatsApp message', priority: 3, listing_id: l.id })
  }
  return out.sort((a, b) => a.priority - b.priority).slice(0, 6)
}
