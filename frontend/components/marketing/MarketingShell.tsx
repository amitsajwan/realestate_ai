import React from 'react'
import SiteHeader from './SiteHeader'
import SiteFooter from './SiteFooter'
import { getMarketingConfig } from '@/lib/marketing/config'

/**
 * Standalone public surface. `data-surface="v2"` keeps the legacy phone CSS (forced white button text,
 * dark headings) away from these pages. The root layout already provides <main id="main-content">.
 */
export default function MarketingShell({ children, showInviteCta = true }: { children: React.ReactNode; showInviteCta?: boolean }) {
  const cfg = getMarketingConfig()
  return (
    <div data-surface="v2" lang="en" className="min-h-screen bg-white text-slate-900">
      <SiteHeader businessName={cfg.businessName} showInviteCta={showInviteCta} />
      {children}
      <SiteFooter cfg={cfg} />
    </div>
  )
}
