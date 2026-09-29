/** "Is this still available?" helpers (docs/contracts/activity.md section 2). */
import { t } from './strings'
import type { Freshness, Listing, RecommendedAction } from './types'

export const CONFIRM_AFTER_DAYS = 21
export const HIDE_AFTER_DAYS = 45

const isOpen = (l: Pick<Listing, 'status'>) => l.status === 'live' || l.status === 'under_offer'

/** What the server told us; a missing field (older backend) or a closed listing counts as fresh. */
export function freshnessOf(l: Pick<Listing, 'status' | 'freshness'>): Freshness {
  return isOpen(l) ? l.freshness ?? 'fresh' : 'fresh'
}

/**
 * The contract's rule, for the fixture API: days since freshness_confirmed_at (else published_at, else created_at);
 * under 21 fresh, 21..44 confirm, 45 or more hidden. Only live / under offer listings are ever anything but fresh.
 */
export function computeFreshness(
  l: Pick<Listing, 'status' | 'freshness_confirmed_at' | 'published_at' | 'created_at'>,
  now: Date = new Date(),
): { freshness: Freshness; days_since_confirmed: number | null } {
  const stamp = l.freshness_confirmed_at ?? l.published_at ?? l.created_at
  const ms = stamp ? new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(stamp) ? stamp : stamp + 'Z').getTime() : NaN
  if (isNaN(ms)) return { freshness: 'fresh', days_since_confirmed: null }
  const days = Math.max(0, Math.floor((now.getTime() - ms) / 86_400_000))
  if (!isOpen(l)) return { freshness: 'fresh', days_since_confirmed: days }
  return { freshness: days >= HIDE_AFTER_DAYS ? 'hidden' : days >= CONFIRM_AFTER_DAYS ? 'confirm' : 'fresh', days_since_confirmed: days }
}

/** Listings that need the agent's answer, hidden ones first, then the longest unconfirmed. */
export function needingConfirmation(listings: Listing[]): Listing[] {
  return listings
    .filter((l) => freshnessOf(l) !== 'fresh')
    .sort((a, b) => {
      const rank = (l: Listing) => (freshnessOf(l) === 'hidden' ? 0 : 1)
      return rank(a) - rank(b) || (b.days_since_confirmed ?? 0) - (a.days_since_confirmed ?? 0)
    })
}

/**
 * The "Listings that need your confirmation" item for the home AI list, built from the listings list.
 * Null when nothing needs confirming. One listing links straight to it; several link to the Listings screen.
 */
export function confirmAction(listings: Listing[]): RecommendedAction | null {
  const need = needingConfirmation(listings)
  if (need.length === 0) return null
  const hidden = need.filter((l) => freshnessOf(l) === 'hidden').length
  const count = `${need.length} ${need.length === 1 ? t('actConfirmOne') : t('actConfirmMany')}`
  return {
    type: 'confirm_listing',
    title: t('actConfirmTitle'),
    detail: hidden > 0 ? `${count}. ${hidden} ${t('actConfirmHidden')}.` : `${count}.`,
    priority: hidden > 0 ? 1 : 2,
    ...(need.length === 1 ? { listing_id: need[0].id } : {}),
  }
}

/** Add our client-side item unless the backend already sent a confirm_listing action. Keeps the list ordered by priority. */
export function withConfirmAction(actions: RecommendedAction[] | undefined, listings: Listing[]): RecommendedAction[] | undefined {
  if (actions?.some((a) => a.type === 'confirm_listing')) return actions
  const extra = confirmAction(listings)
  if (!extra) return actions
  return [...(actions ?? []), extra].sort((a, b) => a.priority - b.priority)
}
