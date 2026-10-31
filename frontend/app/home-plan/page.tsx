import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import HomePlanForm from '@/components/site/homeplan/HomePlanForm'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { parsePlan } from '@/lib/site/homeplan'

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: 'Free East Pune home plan for your family',
  description: 'Six questions about your office, budget and family, and a short list of East Pune projects that fit, with the MahaRERA facts behind each pick and what to check on the site visit.',
  path: '/home-plan',
  // a form, not an answer: out of search while the site recovers from the 2026-10-27 filter; reached from the East Pune pages
  noindex: true,
})

type Props = { searchParams?: Promise<Record<string, string | string[] | undefined>> }

/** The plan's questions. "Edit answers" on a plan links here with them in the address, so the form starts filled in. */
export default async function HomePlanPage({ searchParams }: Props) {
  const start = parsePlan((await searchParams) ?? {})
  return (
    <MarketingShell>
      <div className="mx-auto max-w-2xl px-4 py-10 sm:py-14" style={AVASETU_SITE_VARS}>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Your East Pune home plan</h1>
        <p className="mt-3 text-lg leading-relaxed text-slate-800">
          Answer six questions and we pick the East Pune projects that fit your family: near your office, in your budget, and
          with a MahaRERA record that holds up. Each pick says why, and what to check on the site visit.
        </p>
        <p className="mt-2 text-sm text-slate-600">
          Picked on facts only: MahaRERA&apos;s public record, published asking prices and distance. No builder pays to be on it.
        </p>
        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <HomePlanForm start={start} />
        </div>
      </div>
    </MarketingShell>
  )
}
