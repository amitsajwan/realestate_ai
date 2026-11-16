'use client'

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { newViewId, readAttribution, readStep, startReading, trackEvent, watchNavigation } from '@/lib/site/tracking'

/**
 * Fires page_view (or listing_view on a listing page) once per page path, then counts how long the page stays visible
 * (startReading). Keyed on the path too: moving between two pages of one route (/projects/a to /projects/b) keeps this
 * component mounted, and each is still its own view. A 404 is not a view: scripts guessing addresses showed in Studio as
 * visitors (2026-11-06, twelve in three seconds). Each view says how it was reached (readStep: the page before, a tapped link and
 * its words, Back, a new tab), so Studio can tell a visit step by step. Renders nothing.
 */
export default function TrackingBeacon({ agentSlug, listingId }: { agentSlug: string; listingId?: string }) {
  const path = usePathname()
  useEffect(() => {
    if (document.querySelector('[data-page-not-found]')) return
    watchNavigation()
    readAttribution() // remember ?src / utm_* for later clicks and the enquiry form
    const viewId = newViewId()
    trackEvent(listingId ? 'listing_view' : 'page_view', agentSlug, listingId, viewId, readStep())
    return startReading(agentSlug, viewId)
  }, [agentSlug, listingId, path])
  return null
}
