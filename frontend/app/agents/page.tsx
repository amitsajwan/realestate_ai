import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import LeadCardMock from '@/components/marketing/LeadCardMock'
import RequestInviteForm from '@/components/marketing/RequestInviteForm'
import StickyJoinBar from '@/components/marketing/StickyJoinBar'
import NewsSection from '@/components/news/NewsSection'
import PostsSection from '@/components/site/PostsSection'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { LANDING as L, LIVE, PATHS } from '@/lib/marketing/strings'
import { BRAND_NAME, TAGLINE } from '@/lib/brand'

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: L.metaTitle,
  description: L.metaDescription,
  path: PATHS.agents,
  image: { path: '/brand/og-landing.jpg', width: 1200, height: 630, alt: `${BRAND_NAME}: ${TAGLINE}. Homes, guides and trusted local agents in Pune.` },
})

// Navy + gold brand (the same as every post and reel), laid out as calm editorial rows: only the lead card and the form are cards.
// One heading weight and solid navy, no gradients, like the buyers' home (owner 2026-10-28, "professional, not as if AI made").
const goldBtn =
  'inline-flex min-h-[52px] items-center justify-center rounded-xl bg-[#f0b440] px-7 text-[17px] font-semibold text-[#0f2340] no-underline hover:bg-[#f5c75e] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white'
const outlineOnNavy =
  'inline-flex min-h-[52px] items-center justify-center rounded-xl border border-white/60 px-6 text-[17px] font-semibold text-white no-underline hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white'
const wrap = 'mx-auto max-w-6xl px-4 sm:px-6 lg:px-8'
const section = 'scroll-mt-16 py-14 sm:py-20'
const eyebrow = 'text-sm font-semibold text-[#8a5d00]'
const h2 = 'text-[1.625rem] font-semibold leading-tight tracking-tight text-slate-900 sm:text-[2rem]'

export const revalidate = 3600

/** The agents' home (it was the site's home page until 2026-10-22; / is now the buyers' home). */
export default function LandingPage() {
  const cfg = getMarketingConfig()
  const H = L.hero
  return (
    <MarketingShell cta="agent" stickyBar>

      {/* Hero: the promise, one gold button, the lead card */}
      <section aria-labelledby="hero-title" className="bg-[#0f2340] text-white">
        <div className={wrap + ' grid items-center gap-10 pt-8 pb-12 sm:py-16 md:grid-cols-[1.2fr_1fr] lg:gap-14'}>
          <div>
            <p className="flex flex-wrap items-center gap-2 text-sm font-semibold text-white/75">
              <span>{H.eyebrow}</span>
              <span className="rounded-full px-2.5 py-0.5 text-[#f5c75e] ring-1 ring-inset ring-[#f0b440]/50">{H.pilot}</span>
            </p>
            <h1 id="hero-title" className="mt-4 text-[2.1rem] font-semibold leading-[1.12] tracking-tight [text-wrap:balance] sm:text-[2.75rem] lg:text-[3.25rem]">
              {H.titleLines.map((t) => <span key={t} className="block">{t}</span>)}
            </h1>
            <p className="mt-5 max-w-[52ch] text-lg leading-8 text-slate-100 sm:text-xl">{H.lead}</p>
            <div id="hero-ctas" className="mt-7 flex flex-wrap gap-3">
              <a href="/trial" className={goldBtn + ' w-full sm:w-auto'}>{H.cta}</a>
              {cfg.whatsappUrl ? (
                <a href={cfg.whatsappUrl} target="_blank" rel="noopener noreferrer" className={outlineOnNavy + ' w-full sm:w-auto'}>
                  {H.whatsapp}<span className="sr-only"> (opens in a new tab)</span>
                </a>
              ) : (
                <Link href={LIVE.links.page} className={outlineOnNavy + ' w-full sm:w-auto'}>{H.secondary}</Link>
              )}
            </div>
            <p className="mt-5 text-sm leading-relaxed text-slate-300">{H.facts}</p>
            <p className="mt-1.5 text-sm text-slate-300">
              {H.signInLead}{' '}
              <a href={PATHS.signIn} aria-label={`${H.signInLead} ${H.signIn}`} className="font-semibold text-white underline underline-offset-4">{H.signIn}</a>
            </p>
            <p className="mt-1.5 text-sm text-slate-300">
              <Link href="/for-agents/guide" className="font-semibold text-white underline underline-offset-4">Read the guide for agents and channel partners</Link>
            </p>
          </div>
          <LeadCardMock />
        </div>
      </section>

      {/* The agent's problem, as three rows */}
      <section aria-labelledby="problem-title" className={'bg-[#fbf6ea] ' + section}>
        <div className={wrap}>
          <h2 id="problem-title" className={h2}>{L.problem.heading}</h2>
          <ul className="mt-8 grid border-t-2 border-[#0f2340] p-0 md:grid-cols-3 md:divide-x md:divide-[#ead9ae]">
            {L.problem.items.map((p) => (
              <li key={p.title} className="list-none border-b border-[#ead9ae] py-6 md:border-b-0 md:px-6 md:first:pl-0">
                <h3 className="text-lg font-semibold text-slate-900 sm:text-xl">{p.title}</h3>
                <p className="mt-2 text-base leading-7 text-slate-700">{p.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* A real agent page: the proof before the explanation */}
      <section id={LIVE.id} aria-labelledby="live-title" className={section}>
        <div className={wrap}>
          <p className={eyebrow}>{LIVE.eyebrow}</p>
          <h2 id="live-title" className={h2 + ' mt-2'}>{LIVE.heading}</h2>
          <p className="mt-3 max-w-3xl text-lg leading-8 text-slate-700">{LIVE.lead}</p>
          <ul className="mt-8 gap-6 [display:grid] [grid-template-columns:repeat(3,minmax(0,1fr))] max-sm:snap-x max-sm:gap-4 max-sm:overflow-x-auto max-sm:pb-3 max-sm:[display:flex]" tabIndex={0} aria-label={LIVE.heading}>
            {LIVE.cards.map((c) => (
              <li key={c.src} className="list-none max-sm:w-[78%] max-sm:flex-none max-sm:snap-start">
                <figure className="m-0">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={c.src} alt={c.alt} width={720} height={900} loading="lazy"
                    className="aspect-[4/5] h-auto w-full rounded-xl object-cover ring-1 ring-black/10" />
                  <figcaption className="mt-3">
                    <span className="block text-lg font-semibold text-slate-900">{c.title}</span>
                    <span className="mt-1 block leading-relaxed text-slate-700">{c.body}</span>
                  </figcaption>
                </figure>
              </li>
            ))}
          </ul>
          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <Link href={LIVE.links.page} className="inline-flex min-h-[52px] items-center justify-center rounded-xl bg-[#0f2340] px-7 text-[17px] font-semibold text-white no-underline hover:bg-[#183a5d]">
              {LIVE.links.pageLabel}
            </Link>
          </div>
        </div>
      </section>

      {/* Create -> Get discovered -> Get qualified leads -> Close, as numbered rows */}
      <section id={L.steps.id} aria-labelledby="steps-title" className={'bg-[#fbf6ea] ' + section}>
        <div className={wrap}>
          <h2 id="steps-title" className={h2}>{L.steps.heading}</h2>
          <ol className="mt-8 border-t-2 border-[#0f2340] p-0">
            {L.steps.items.map((s, i) => (
              <li key={s.key} className="grid list-none grid-cols-[2.5rem_1fr] gap-x-3 border-b border-[#ead9ae] py-6 lg:grid-cols-[4rem_minmax(0,22rem)_minmax(0,1fr)] lg:items-baseline lg:gap-x-12">
                <span aria-hidden="true" className="text-base font-semibold tabular-nums text-slate-400">{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <p className={eyebrow}>{s.label}</p>
                  <h3 className="mt-1 text-lg font-semibold text-slate-900 sm:text-xl">{s.title}</h3>
                </div>
                <p className="col-start-2 mt-2 max-w-[52ch] text-base leading-7 text-slate-700 lg:col-start-3 lg:mt-0">{s.body}</p>
              </li>
            ))}
          </ol>
          <p className="mt-6 text-base leading-7 text-slate-700">{L.steps.noApp}</p>
        </div>
      </section>

      {/* Proof that Avasetu publishes every day */}
      <PostsSection />

      {/* Cost, in one line */}
      <section id={L.cost.id} aria-labelledby="cost-title" className="scroll-mt-16 border-y border-[#ead9ae] bg-[#fbf6ea] py-10 sm:py-14">
        <div className={wrap + ' flex flex-wrap items-baseline gap-x-10 gap-y-3'}>
          <h2 id="cost-title" className={h2}>{L.cost.title}</h2>
          <p className="max-w-[56ch] text-lg leading-8 text-slate-700">{L.cost.body}</p>
        </div>
      </section>

      {/* FAQ */}
      <section id={L.faq.id} aria-labelledby="faq-title" className={section}>
        <div className={wrap + ' grid gap-8 lg:grid-cols-[1fr_2fr]'}>
          <div>
            <h2 id="faq-title" className={h2 + ' lg:sticky lg:top-24'}>{L.faq.heading}</h2>
          </div>
          <div className="min-w-0">
            <div className="divide-y divide-slate-200 border-y-2 border-y-[#0f2340]">
              {L.faq.items.map((f) => (
                <details key={f.q} className="group py-1">
                  <summary className="flex min-h-[52px] cursor-pointer list-none items-center justify-between gap-4 text-lg font-medium text-slate-900 [&::-webkit-details-marker]:hidden">
                    {f.q}
                    <span aria-hidden="true" className="text-2xl text-[#8a5d00] group-open:hidden">+</span>
                    <span aria-hidden="true" className="hidden text-2xl text-[#8a5d00] group-open:inline">&minus;</span>
                  </summary>
                  <p className="max-w-[60ch] pb-4 text-base leading-7 text-slate-700">{f.a}</p>
                </details>
              ))}
            </div>
            <p className="mt-5 flex flex-wrap gap-x-6 text-sm">
              <Link href={PATHS.privacy} className="flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{L.faq.privacyLink}</Link>
              <Link href={PATHS.deletion} className="flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{L.faq.deletionLink}</Link>
            </p>
          </div>
        </div>
      </section>

      {/* The short form, right here */}
      <section id="invite" aria-labelledby="cta-title" className="scroll-mt-16 bg-[#0f2340] py-14 sm:py-20">
        <div className={wrap + ' grid items-start gap-8 md:grid-cols-2 lg:gap-16'}>
          <div className="text-white">
            <h2 id="cta-title" className="text-[2rem] font-semibold leading-[1.1] tracking-tight sm:text-[2.75rem]">
              {L.finalCta.titleLines.map((t) => <span key={t} className="block">{t}</span>)}
            </h2>
            <p className="mt-4 text-lg leading-8 text-slate-100">{L.finalCta.body}</p>
            <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-base">
              {cfg.whatsappUrl && (
                <a href={cfg.whatsappUrl} target="_blank" rel="noopener noreferrer" className="flex min-h-[44px] items-center font-semibold text-white underline underline-offset-4">
                  {L.finalCta.whatsapp}<span className="sr-only"> (opens in a new tab)</span>
                </a>
              )}
              <Link href={PATHS.invite} className="flex min-h-[44px] items-center text-slate-200 underline underline-offset-4">{L.finalCta.fullForm}</Link>
            </div>
          </div>
          <div className="rounded-2xl bg-white p-5 text-slate-900 shadow-2xl shadow-black/30 sm:p-8">
            <RequestInviteForm idPrefix="lp" short />
          </div>
        </div>
      </section>

      {/* a buyer who lands here: the buyers' home has the areas, projects and builders */}
      <p className={wrap + ' py-6 text-slate-700'}>
        Buying a home in Pune? <Link href={PATHS.home} className="font-semibold text-[#0f2340] underline underline-offset-4">See projects, areas and builders</Link>
      </p>
      <NewsSection quiet />

      <StickyJoinBar watchId="hero-ctas" formId="invite" href="/trial" label={L.sticky.cta} whatsappUrl={cfg.whatsappUrl} whatsappLabel={L.sticky.whatsapp} />
    </MarketingShell>
  )
}
