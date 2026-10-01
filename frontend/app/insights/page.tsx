import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { INSIGHTS, INSIGHT_NOTE } from '@/lib/marketing/insights'
import { pageMetadata } from '@/lib/marketing/seo'

export function generateMetadata(): Metadata {
  return pageMetadata(getMarketingConfig(), {
    title: 'Pune property insights',
    description: 'Plain-language guides for buying a home in Pune: Kharadi, Upper Kharadi, Wagholi, metro, RERA and site visits.',
    path: '/insights',
  })
}

export default function InsightsPage() {
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Pune property insights</h1>
        <p className="mt-3 text-lg leading-relaxed text-slate-700">
          Plain-language guides for buying a home in Pune, starting with Kharadi, Upper Kharadi and Wagholi. Sources are cited, and we do not guess prices.
        </p>
        <ul className="mt-8 space-y-5">
          {INSIGHTS.map((a) => (
            <li key={a.slug}>
              <Link href={`/insights/${a.slug}`} className="block rounded-2xl border border-slate-200 p-5 hover:border-slate-400">
                <h2 className="text-xl font-semibold text-slate-900">{a.title}</h2>
                <p className="mt-2 text-slate-700">{a.summary}</p>
                <p className="mt-3 text-sm text-slate-600">Updated {a.updatedLabel}</p>
              </Link>
            </li>
          ))}
        </ul>
        <p className="mt-10 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{INSIGHT_NOTE}</p>
        <AgentStrip />
      </div>
    </MarketingShell>
  )
}
