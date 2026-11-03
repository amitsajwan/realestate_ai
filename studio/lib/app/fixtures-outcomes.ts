/** Fixture-mode logic for deal outcomes (docs/contracts/outcomes.md), kept out of fixtures.ts. */
import type { LeadDetail, LeadOutcome, LeadPatch, Listing, LostReason, TodayResults } from './types'

const PERIOD_DAYS = 30

/** Outcome after a stage change: won/lost store one (with the details given), any other stage clears it. */
export function nextOutcome(lead: LeadDetail, patch: LeadPatch, listings: Listing[], now: string): LeadOutcome | null | undefined {
  const stage = patch.stage
  if (!stage) return undefined // no stage change: keep whatever is stored
  if (stage !== 'won' && stage !== 'lost') return null
  const o = patch.outcome
  if (stage === 'lost') {
    return { result: 'lost', deal_price_inr: null, listing_id: null, lost_reason: o?.lost_reason ?? null, closed_at: now }
  }
  // Same stage again without an outcome keeps the stored result (e.g. a re-save); otherwise won stores what was given.
  if (!o && lead.stage === 'won' && lead.outcome) return undefined
  const listingId = o ? (o.listing_id ?? lead.first_listing_id ?? null) : null
  return {
    result: 'won',
    deal_price_inr: o?.deal_price_inr ?? null,
    listing_id: listingId && listings.some((l) => l.id === listingId) ? listingId : null,
    lost_reason: null,
    closed_at: now,
  }
}

/** The listing owning a won deal: outcome.listing_id, else the enquired listing. */
export const dealListingId = (l: LeadDetail): string | null => l.outcome?.listing_id ?? l.first_listing_id ?? null

export function resultsFor(leads: LeadDetail[]): TodayResults {
  const since = Date.now() - PERIOD_DAYS * 86_400_000
  const recent = leads.filter((l) => l.outcome && new Date(l.outcome.closed_at).getTime() >= since)
  const won = recent.filter((l) => l.outcome!.result === 'won')
  const lost = recent.filter((l) => l.outcome!.result === 'lost')
  const bySource: Record<string, number> = {}
  for (const l of won) bySource[l.source || 'direct'] = (bySource[l.source || 'direct'] ?? 0) + 1
  const top = Object.entries(bySource).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0]
  const lost_reasons: Partial<Record<LostReason, number>> = {}
  for (const l of lost) {
    const r = l.outcome!.lost_reason
    if (r) lost_reasons[r] = (lost_reasons[r] ?? 0) + 1
  }
  return {
    period_days: PERIOD_DAYS,
    deals_won: won.length,
    deal_value_inr: won.reduce((n, l) => n + (l.outcome!.deal_price_inr ?? 0), 0),
    deals_lost: lost.length,
    top_source: top ? top[0] : null,
    lost_reasons,
  }
}

/** Per listing: won leads attributed to it, their total value (missing prices ignored) and the count by source. */
export function dealsForListing(listingId: string, leads: LeadDetail[]) {
  const won = leads.filter((l) => l.stage === 'won' && dealListingId(l) === listingId)
  const deals_by_source: Record<string, number> = {}
  for (const l of won) deals_by_source[l.source || 'direct'] = (deals_by_source[l.source || 'direct'] ?? 0) + 1
  return {
    deals: won.length,
    deal_value_inr: won.reduce((n, l) => n + (l.outcome?.deal_price_inr ?? 0), 0),
    deals_by_source,
  }
}
