import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { TIER_LABELS, type LocalityTier, localitiesByTier } from '@/lib/marketing/localities'
import { pageMetadata } from '@/lib/marketing/seo'

/** Affordable belt first: that is where most of our buyers look. */
const TIERS: LocalityTier[] = ['affordable', 'it']

export function generateMetadata(): Metadata {
  return pageMetadata(getMarketingConfig(), {
    title: 'Pune area guides: Wagholi, Lohegaon, Kharadi, Hinjawadi and more',
    description: 'Plain-language guides to Pune areas, from the affordable eastern belt to the IT corridor: who each suits, how to get around, what to check before you buy.',
    path: '/localities',
  })
}

export default function LocalitiesPage() {
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Pune area guides</h1>
        <p className="mt-3 text-lg leading-relaxed text-slate-700">Who each area suits, how to get around and what to check before you buy. Facts come from official sources, listed on each page.</p>
        {TIERS.map((tier) => (
          <section key={tier} className="mt-10" aria-labelledby={`tier-${tier}`}>
            <h2 id={`tier-${tier}`} className="text-2xl font-semibold text-slate-900">{TIER_LABELS[tier].title}</h2>
            <p className="mt-1 text-slate-600">{TIER_LABELS[tier].blurb}</p>
            <ul className="mt-4 grid list-none gap-4 p-0 sm:grid-cols-2">
              {localitiesByTier(tier).map((l) => (
                <li key={l.slug}>
                  <Link href={`/localities/${l.slug}`} className="flex h-full flex-col rounded-2xl border border-slate-200 border-l-4 border-l-[#f0b440] bg-[#fbf6ea] p-5 no-underline hover:border-slate-400 hover:border-l-[#f0b440]">
                    <span className="text-xl font-semibold text-slate-900">{l.name}</span>
                    <span className="mt-1 text-sm text-slate-600">{l.tagline}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
        <AgentStrip />
      </div>
    </MarketingShell>
  )
}
