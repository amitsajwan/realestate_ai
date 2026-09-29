'use client'

import { useEffect } from 'react'
import { readAttribution, trackEvent } from '@/lib/site/tracking'

/** Fires page_view (home) or listing_view (listing page) once on mount. Renders nothing. */
export default function TrackingBeacon({ agentSlug, listingId }: { agentSlug: string; listingId?: string }) {
  useEffect(() => {
    readAttribution() // remember ?src / utm_* for later clicks and the enquiry form
    trackEvent(listingId ? 'listing_view' : 'page_view', agentSlug, listingId)
  }, [agentSlug, listingId])
  return null
}
