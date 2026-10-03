import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { PATHS } from '@/lib/marketing/strings'

/** The page to share in property groups: its link preview is the promo itself, and it sends agents to the invite form,
 *  carrying the ?src= tag so the owner sees which group or channel brought them. */
export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: 'Stop chasing “Price?” comments. Get buyers you can call. | Avasetu free pilot for Pune agents',
  description: 'Every enquiry becomes a lead card: budget, area, timing, and who to call first. Plus your own property website, and posts and reels made for you. Free during the pilot.',
  path: '/pilot',
  image: { path: '/promo/og-pilot.jpg', width: 1200, height: 630, alt: 'Stop chasing “Price?” comments. Get buyers you can call. A sample lead card: 2 BHK in Kharadi, 80 lakh to 1.2 crore, 1 to 3 months, home loan, call today.' },
})

const tag = (v: unknown) => (typeof v === 'string' ? v.toLowerCase().replace(/[^a-z0-9_-]/g, '').slice(0, 40) : '')

export default async function PilotPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const src = tag((await searchParams).src) || 'pilot'
  const join = `${PATHS.invite}?src=${encodeURIComponent(src)}`
  return (
    <MarketingShell>
      <section aria-labelledby="pilot-title" className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] text-white">
        <div className="mx-auto grid max-w-5xl items-center gap-8 px-4 py-10 sm:py-14 md:grid-cols-[1fr_0.9fr]">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-[#f0b440]">Free pilot for Pune property agents</p>
            <h1 id="pilot-title" className="mt-3 text-[2rem] font-extrabold leading-[1.15] tracking-tight sm:text-5xl">
              Stop chasing “Price?” comments. Get buyers you can call.
            </h1>
            <p className="mt-4 text-base leading-relaxed text-slate-100 sm:text-lg">
              Avasetu turns every enquiry into a lead card: budget, area, timing, and who to call first. You also get your own
              property website, and posts and reels made for you.
            </p>
            <ul className="mt-5 space-y-2 p-0 text-slate-100">
              {['Free during the pilot, low-cost after', 'No app to install: it works in your phone browser', 'Limited places for agents in Pune'].map((t) => (
                <li key={t} className="flex list-none items-start gap-2"><span aria-hidden className="text-[#f0b440]">✓</span>{t}</li>
              ))}
            </ul>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href={join} data-testid="pilot-join"
                className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl bg-[#f0b440] px-7 text-lg font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e] sm:w-auto">
                Join the free pilot
              </Link>
              <Link href="/agent/house-deal"
                className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl border-2 border-white/70 px-5 text-lg font-bold text-white no-underline hover:bg-white/10 sm:w-auto">
                See an example agent page
              </Link>
            </div>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/promo/group-lead.jpg" width={1080} height={1350}
            alt="Promo: Stop chasing Price comments. A sample lead card for a 2 BHK in Kharadi, budget 80 lakh to 1.2 crore, moving in 1 to 3 months, home loan, with Call and WhatsApp buttons. Free during the pilot."
            className="mx-auto h-auto w-full max-w-sm rounded-2xl shadow-2xl" />
        </div>
      </section>
    </MarketingShell>
  )
}
