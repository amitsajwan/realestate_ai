/** Deal outcome helpers: client-side guards (mirroring the API's 422s), labels and summary text. */
import { formatPrice } from './format'
import { t, type StringKey } from './strings'
import type { LeadOutcome, LeadPatch, Listing, LostReason, TodayResults } from './types'

export const LOST_REASONS: Array<{ key: LostReason; label: StringKey }> = [
  { key: 'price', label: 'reasonPrice' },
  { key: 'bought_elsewhere', label: 'reasonBoughtElsewhere' },
  { key: 'not_responding', label: 'reasonNotResponding' },
  { key: 'changed_mind', label: 'reasonChangedMind' },
  { key: 'other', label: 'reasonOther' },
]

const REASON_SHORT: Record<LostReason, StringKey> = {
  price: 'reasonPriceShort',
  bought_elsewhere: 'reasonBoughtElsewhereShort',
  not_responding: 'reasonNotRespondingShort',
  changed_mind: 'reasonChangedMindShort',
  other: 'reasonOtherShort',
}

const REASON_KEYS: string[] = LOST_REASONS.map((r) => r.key)

/**
 * The contract's rules for PATCH `outcome`, or null when the patch is fine. Used by the real client (fail fast, no
 * pointless request) and by the fixture API, so both refuse the same things.
 */
export function outcomePatchError(patch: LeadPatch): string | null {
  const o = patch.outcome
  if (o === undefined) return null
  if (patch.stage !== 'won' && patch.stage !== 'lost') return 'A deal result can only be saved when marking a lead won or lost.'
  if (patch.stage === 'lost' && (o.deal_price_inr !== undefined || o.listing_id !== undefined)) {
    return 'A lost lead cannot have a deal price or property.'
  }
  if (patch.stage === 'won' && o.lost_reason !== undefined) return 'A won lead cannot have a lost reason.'
  if (o.deal_price_inr !== undefined && !(Number.isInteger(o.deal_price_inr) && o.deal_price_inr > 0)) {
    return 'The deal price must be a whole number of rupees above 0.'
  }
  if (o.lost_reason !== undefined && !REASON_KEYS.includes(o.lost_reason)) return 'Unknown lost reason.'
  return null
}

export const reasonLabel = (r: LostReason) => t(REASON_SHORT[r])

/** "Won: ₹85 L on the 2 BHK in Baner" / "Lost: bought elsewhere". `title` is the listing's title when known. */
export function outcomeSummary(o: LeadOutcome, title?: string | null): string {
  if (o.result === 'lost') return o.lost_reason ? `${t('outcomeLost')}: ${reasonLabel(o.lost_reason)}` : t('outcomeLost')
  const price = o.deal_price_inr ? formatPrice(o.deal_price_inr) : ''
  const where = title ? `${t('outcomeOnThe')} ${title}` : ''
  const parts = [price, where].filter(Boolean).join(' ')
  return parts ? `${t('outcomeWon')}: ${parts}` : t('outcomeWon')
}

/** "Most lost on price"; falls back to a plain count when no reasons were given. */
export function lostHint(results: TodayResults): string {
  if (results.deals_lost <= 0) return ''
  let best: LostReason | null = null
  let bestN = 0
  for (const { key } of LOST_REASONS) {
    const n = results.lost_reasons?.[key] ?? 0
    if (n > bestN) {
      best = key
      bestN = n
    }
  }
  if (best) return `${t('mostLost')} ${reasonLabel(best)}`
  return `${results.deals_lost} ${results.deals_lost === 1 ? t('lostOne') : t('lostMany')}`
}

/** True when there is nothing to show yet (a new agent). */
export const resultsEmpty = (r?: TodayResults | null) => !r || (r.deals_won <= 0 && r.deals_lost <= 0)

/** Listings a deal can be attributed to: live, under offer, sold or rented, plus the one the buyer enquired about. */
export function dealListings(listings: Listing[], firstListingId?: string | null): Listing[] {
  const ok = ['live', 'under_offer', 'sold', 'rented']
  return listings.filter((l) => ok.includes(l.status) || l.id === firstListingId)
}
