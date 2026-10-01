import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { LOCALITIES } from '@/lib/marketing/localities'
import { pageMetadata } from '@/lib/marketing/seo'

export function generateMetadata(): Metadata {
  return pageMetadata(getMarketingConfig(), {
    title: 'Pune localities: Kharadi, Upper Kharadi, Wagholi',
    description: 'Plain-language guides to east Pune localities: who each suits, how to get around, what to check before you buy.',
    path: '/localities',
  })
}

export default function LocalitiesPage() {
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Pune localities</h1>
        <p className="mt-3 text-lg leading-relaxed text-slate-700">We start with the east Pune corridor: Kharadi, Upper Kharadi and Wagholi. More areas will follow.</p>
        <ul className="mt-8 grid gap-4 sm:grid-cols-3">
          {LOCALITIES.map((l) => (
            <li key={l.slug}>
              <Link href={`/localities/${l.slug}`} className="flex h-full flex-col rounded-2xl border border-slate-200 border-l-4 border-l-[#f0b440] bg-[#fbf6ea] p-5 no-underline hover:border-slate-400 hover:border-l-[#f0b440]">
                <span className="text-xl font-semibold text-slate-900">{l.name}</span>
                <span className="mt-1 text-sm text-slate-600">{l.tagline}</span>
              </Link>
            </li>
          ))}
        </ul>
        <AgentStrip />
      </div>
    </MarketingShell>
  )
}
