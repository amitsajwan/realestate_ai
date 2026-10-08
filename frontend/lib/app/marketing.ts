/** Where a "Today" recommendation card leads. Nothing here sends anything. */
import type { RecommendedAction } from './types'

/** Where an AI recommendation card leads. Call opens the buyer (their number and Call button are on that screen). */
export function actionHref(a: RecommendedAction): string {
  switch (a.type) {
    case 'call':
    case 'follow_up':
      return a.lead_id ? `/studio/leads/${a.lead_id}` : '/studio/leads'
    case 'send_property':
    case 'create_marketing':
      return a.listing_id ? `/studio/listings/${a.listing_id}/marketing` : '/studio/listings'
    case 'confirm_listing':
      // The listing screen opens with the "Is this still available?" card on top; several listings share the Listings screen.
      return a.listing_id ? `/studio/listings/${a.listing_id}` : '/studio/listings#confirm'
  }
}
