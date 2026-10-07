import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { claimHref } from '@/lib/marketing/trial'

/** Claim your free trial. The main button opens WhatsApp with "TRIAL" typed in: the agent sends it, and our WhatsApp assistant replies
 *  at once with his sign-up code (backend onboarding/trial.py). Without a platform WhatsApp number the button falls back to the request
 *  form. The ?src= tag travels along so the owner sees which post or group brought the agent. */
export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: 'Claim your free trial: your first 3 properties marketed free | Avasetu for Pune agents',
  description: 'Give Avasetu one property and watch it become a property page, posts for Facebook and Instagram, a Reel and a WhatsApp message. Buyers get answered and enquiries come to you. Your first 3 properties free, no card.',
  path: '/trial',
  image: { path: '/promo/og-pilot.jpg', width: 1200, height: 630, alt: 'Stop chasing “Price?” comments. Get buyers you can call. A sample lead card: 2 BHK in Kharadi, 80 lakh to 1.2 crore, 1 to 3 months, home loan, call today.' },
})

const tag = (v: unknown) => (typeof v === 'string' ? v.toLowerCase().replace(/[^a-z0-9_-]/g, '').slice(0, 40) : '')

const POINTS = [
  'Your first 3 properties marketed free, no card',
  'Your code comes back on WhatsApp at once',
  'No app to install: it works in your phone browser',
]

export default async function TrialPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const src = tag((await searchParams).src) || 'trial'
  const claim = claimHref(src, process.env.NEXT_PUBLIC_WHATSAPP_NUMBER)
  return (
    <MarketingShell>
      <section aria-labelledby="trial-title" className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] text-white">
        <div className="mx-auto grid max-w-5xl items-center gap-8 px-4 py-10 sm:py-14 md:grid-cols-[1fr_0.9fr]">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-[#f0b440]">Free trial for Pune property agents</p>
            <h1 id="trial-title" className="mt-3 text-[2rem] font-extrabold leading-[1.15] tracking-tight sm:text-5xl">
              Give us one property. Watch it go live.
            </h1>
            <p className="mt-4 text-base leading-relaxed text-slate-100 sm:text-lg">
              Type or say the details and add photos. Avasetu makes the property page, Facebook and Instagram posts, a Reel and a
              WhatsApp message. One tap puts it live on Avasetu&apos;s Facebook and Instagram with your name; buyers&apos; questions
              get answered and every enquiry comes to you.
            </p>
            <ul className="mt-5 space-y-2 p-0 text-slate-100">
              {POINTS.map((t) => (
                <li key={t} className="flex list-none items-start gap-2"><span aria-hidden className="text-[#f0b440]">✓</span>{t}</li>
              ))}
            </ul>
            <div className="mt-6 flex flex-wrap gap-3">
              <a href={claim} data-testid="trial-claim"
                className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl bg-[#f0b440] px-7 text-lg font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e] sm:w-auto">
                Claim your free trial
              </a>
              <Link href="/agent/house-deal"
                className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl border-2 border-white/70 px-5 text-lg font-bold text-white no-underline hover:bg-white/10 sm:w-auto">
                See an example agent page
              </Link>
            </div>
            <p className="mt-3 text-sm text-slate-300">Already have your code? <Link href="/join" className="font-semibold text-white underline">Sign in</Link></p>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/promo/group-lead.jpg" width={1080} height={1350}
            alt="Promo: Stop chasing Price comments. A sample lead card for a 2 BHK in Kharadi, budget 80 lakh to 1.2 crore, moving in 1 to 3 months, home loan, with Call and WhatsApp buttons."
            className="mx-auto h-auto w-full max-w-sm rounded-2xl shadow-2xl" />
        </div>
      </section>
    </MarketingShell>
  )
}
