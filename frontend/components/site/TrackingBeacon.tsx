'use client'

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { newViewId, readAttribution, startReading, trackEvent } from '@/lib/site/tracking'

/**
 * Fires page_view (or listing_view on a listing page) once per page path, then counts how long the page stays visible
 * (startReading). Keyed on the path too: moving between two pages of one route (/projects/a to /projects/b) keeps this
 * component mounted, and each is still its own view. Renders nothing.
 */
export default function TrackingBeacon({ agentSlug, listingId }: { agentSlug: string; listingId?: string }) {
  const path = usePathname()
  useEffect(() => {
    readAttribution() // remember ?src / utm_* for later clicks and the enquiry form
    const viewId = newViewId()
    trackEvent(listingId ? 'listing_view' : 'page_view', agentSlug, listingId, viewId)
    return startReading(agentSlug, viewId)
  }, [agentSlug, listingId, path])
  return null
}
