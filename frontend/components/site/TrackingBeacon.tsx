'use client'

import { useEffect, useRef } from 'react'
import Script from 'next/script'
import { usePathname } from 'next/navigation'
import { useReportWebVitals } from 'next/web-vitals'
import { gaId, gaScriptSrc, gaVital } from '@/lib/site/ga'
import { isStaff, newViewId, readAttribution, readStep, startReading, trackEvent, watchNavigation } from '@/lib/site/tracking'

/**
 * Fires page_view (or listing_view on a listing page) once per page path, then counts how long the page stays visible
 * (startReading). Keyed on the path too: moving between two pages of one route (/projects/a to /projects/b) keeps this
 * component mounted, and each is still its own view. A 404 is not a view: scripts guessing addresses showed in Studio as
 * visitors (2026-11-06, twelve in three seconds). Each view says how it was reached (readStep: the page before, a tapped link and
 * its words, Back, a new tab), so Studio can tell a visit step by step.
 *
 * It is also where Google Analytics 4 runs (docs/plan/ga4.md): only the public pages render this, so Studio and the old
 * dashboard never load the tag. trackEvent sends each view on to GA4; this loads gtag.js and reports each visit's Core Web
 * Vitals. Renders only that script, and nothing when GA4 is off (dev, tests).
 */
export default function TrackingBeacon({ agentSlug, listingId }: { agentSlug: string; listingId?: string }) {
  const path = usePathname()
  const slug = useRef(agentSlug)
  slug.current = agentSlug
  // one stable callback for the life of the page, as useReportWebVitals asks, or a metric is reported twice
  const reportVital = useRef((m: { id: string; name: string; value: number; rating?: string }) => {
    if (!isStaff()) gaVital(m, slug.current)
  }).current
  useReportWebVitals(reportVital)
  useEffect(() => {
    if (document.querySelector('[data-page-not-found]')) return
    watchNavigation()
    readAttribution() // remember ?src / utm_* for later clicks and the enquiry form
    const viewId = newViewId()
    trackEvent(listingId ? 'listing_view' : 'page_view', agentSlug, listingId, viewId, readStep())
    return startReading(agentSlug, viewId)
  }, [agentSlug, listingId, path])
  const ga = gaId()
  return ga ? <Script id="ga4" src={gaScriptSrc(ga)} strategy="afterInteractive" /> : null
}
