import React from 'react'
import Link from 'next/link'
import { HOME } from '@/lib/marketing/strings'
import { BRAND_NAME, LOGO, TAGLINE } from '@/lib/brand'
import { buyerEnquiryPath, wrap } from './shared'

const goldBtn =
  'inline-flex min-h-[52px] w-full items-center justify-center rounded-xl bg-[#f0b440] px-7 text-lg font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white sm:w-auto'
const ghostBtn =
  'inline-flex min-h-[52px] w-full items-center justify-center rounded-xl border-2 border-white/70 px-6 text-lg font-bold text-white no-underline hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white sm:w-auto'

/** Buyer hero: who we are, what a buyer gets here, and two actions. */
export default function HomeHero() {
  const H = HOME.hero
  return (
    <section aria-labelledby="hero-title" className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] text-white">
      <div className={wrap + ' py-10 sm:py-16'}>
        <p className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LOGO.mark} alt="" width={40} height={40} className="h-10 w-10" />
          <span className="leading-tight">
            <span className="block text-xl font-extrabold tracking-tight">{BRAND_NAME}</span>
            <span className="block text-sm font-medium text-[#f0b440]">{TAGLINE}</span>
          </span>
        </p>
        <p className="mt-6 text-xs font-bold uppercase tracking-wide text-[#f0b440]">{H.eyebrow}</p>
        <h1 id="hero-title" className="mt-2 max-w-3xl text-[2rem] font-extrabold leading-[1.15] tracking-tight sm:text-5xl">{H.title}</h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-slate-100 sm:text-lg">{H.lead}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <a href={buyerEnquiryPath()} className={goldBtn}>{H.cta}</a>
          <Link href="/localities" className={ghostBtn}>{H.secondary}</Link>
        </div>
        <ul className="mt-5 flex flex-wrap gap-2 p-0 text-sm font-medium text-white">
          {H.points.map((f) => (
            <li key={f} className="list-none rounded-full border border-white/40 px-3 py-1">{f}</li>
          ))}
        </ul>
      </div>
    </section>
  )
}
