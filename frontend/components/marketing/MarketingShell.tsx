import React, { Suspense } from 'react'
import SiteHeader, { type HeaderCta } from './SiteHeader'
import SiteFooter from './SiteFooter'
import { getMarketingConfig } from '@/lib/marketing/config'
import { poppins } from '@/lib/marketing/font'
import ChatWidget from '@/components/site/ChatWidget'
import HotStrip from '@/components/site/HotStrip'
import TrackingBeacon from '@/components/site/TrackingBeacon'

/**
 * Standalone public surface in the Avasetu brand (navy, gold, cream, Poppins).
 * `data-surface="v2"` keeps the legacy phone CSS (forced white button text, dark headings) away from these pages.
 * The root layout already provides <main id="main-content">.
 * `cta` picks the header button by audience: 'buyer' (default: home, area guides, insights, news, posts, legal), 'agent' (/for-agents),
 * or 'none' (the invite form itself). `stickyBar` lifts the chat bubble on phones above a page's own bottom bar, and on buyer pages
 * takes the header's gold button off phones, since the bar already carries that action.
 * `hot` is the hot projects banner under the header (components/site/HotStrip): `area` (slug) puts that area's projects first,
 * `exclude` leaves out the page's own project; false hides it. Buyer pages show it by default, agent pages do not.
 * `search` is the project search in the header: on by default on buyer pages, off where the page is itself a search (/check, /projects).
 * Every page in this shell records its view and reading time for the Avasetu site (TrackingBeacon), like the agent pages do.
 */
export type HotOptions = { area?: string | null; exclude?: string | null } | false

const SITE_SLUG = process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'

export default function MarketingShell({ children, cta = 'buyer', stickyBar = false, hot, search }: { children: React.ReactNode; cta?: HeaderCta; stickyBar?: boolean; hot?: HotOptions; search?: boolean }) {
  const cfg = getMarketingConfig()
  const strip = hot ?? (cta === 'buyer' ? {} : false)
  return (
    <div data-surface="v2" lang="en" className={poppins.className + ' min-h-screen bg-white text-slate-900'}>
      <SiteHeader businessName={cfg.businessName} cta={cta} search={search ?? cta === 'buyer'} bottomBar={stickyBar} />
      {strip && <Suspense fallback={null}><HotStrip area={strip.area} exclude={strip.exclude} /></Suspense>}
      {children}
      <div data-print="hide" data-chat-bubble><ChatWidget agentSlug={SITE_SLUG} bottomBar={stickyBar} /></div>
      <TrackingBeacon agentSlug={SITE_SLUG} />
      <SiteFooter cfg={cfg} />
    </div>
  )
}
