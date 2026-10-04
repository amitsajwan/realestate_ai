import React from 'react'
import SiteHeader, { type HeaderCta } from './SiteHeader'
import SiteFooter from './SiteFooter'
import { getMarketingConfig } from '@/lib/marketing/config'
import { poppins } from '@/lib/marketing/font'
import ChatWidget from '@/components/site/ChatWidget'

/**
 * Standalone public surface in the Avasetu brand (navy, gold, cream, Poppins).
 * `data-surface="v2"` keeps the legacy phone CSS (forced white button text, dark headings) away from these pages.
 * The root layout already provides <main id="main-content">.
 * `cta` picks the header button by audience: 'buyer' (default: home, area guides, insights, news, posts, legal), 'agent' (/for-agents),
 * or 'none' (the invite form itself). `stickyBar` lifts the chat bubble on phones above a page's own bottom bar.
 */
export default function MarketingShell({ children, cta = 'buyer', stickyBar = false }: { children: React.ReactNode; cta?: HeaderCta; stickyBar?: boolean }) {
  const cfg = getMarketingConfig()
  return (
    <div data-surface="v2" lang="en" className={poppins.className + ' min-h-screen bg-white text-slate-900'}>
      <SiteHeader businessName={cfg.businessName} cta={cta} />
      {children}
      <div data-print="hide"><ChatWidget agentSlug={process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'} bottomBar={stickyBar} /></div>
      <SiteFooter cfg={cfg} />
    </div>
  )
}
