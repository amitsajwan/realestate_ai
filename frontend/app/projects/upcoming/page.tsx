import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import MarketingShell from '@/components/marketing/MarketingShell'
import { ComingSoonView } from '@/components/site/ComingSoonBand'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getUpcomingBriefs } from '@/lib/site/hubs'

// Every project on the coming-soon band, in one place. Out of search like each project's own page (areastats/upcoming.py).

export const revalidate = 300

export function generateMetadata(): Metadata {
  const meta = pageMetadata(getMarketingConfig(), {
    title: 'Coming soon in East Pune: not yet MahaRERA registered',
    description: 'Projects planned in East Pune that MahaRERA has not registered yet. We tell you the day each one registers.',
    path: '/projects/upcoming',
  })
  return { ...meta, robots: { index: false, follow: true } }
}

export default async function UpcomingProjectsPage() {
  const items = await getUpcomingBriefs()
  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
          <Link href="/" className="underline underline-offset-2">Home</Link> / <Link href="/projects" className="underline underline-offset-2">Projects</Link>
        </nav>
        <h1 className="text-3xl font-bold text-slate-900">Coming soon in East Pune</h1>
        {items.length ? <ComingSoonView items={items} /> : <p className="text-slate-700">Nothing is waiting to register right now. <Link href="/projects" className="underline underline-offset-2">See registered projects</Link>.</p>}
      </div>
    </MarketingShell>
  )
}
