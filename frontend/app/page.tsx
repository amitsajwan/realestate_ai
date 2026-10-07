import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import LeadCardMock from '@/components/marketing/LeadCardMock'
import RequestInviteForm from '@/components/marketing/RequestInviteForm'
import StickyJoinBar from '@/components/marketing/StickyJoinBar'
import NewsSection from '@/components/news/NewsSection'
import PostsSection from '@/components/site/PostsSection'
import { socialLinks } from '@/lib/marketing/social'
import { getMarketingConfig } from '@/lib/marketing/config'
import { jsonLdString, organizationJsonLd, pageMetadata } from '@/lib/marketing/seo'
import { BUYERS, LANDING as L, LIVE, PATHS } from '@/lib/marketing/strings'
import { TIER_LABELS, localitiesByTier } from '@/lib/marketing/localities'
import { BRAND_NAME, TAGLINE } from '@/lib/brand'

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: L.metaTitle,
  description: L.metaDescription,
  path: '/',
  image: { path: '/brand/og-landing.jpg', width: 1200, height: 630, alt: `${BRAND_NAME}: ${TAGLINE}. Homes, guides and trusted local agents in Pune.` },
})

// Navy + gold brand (the same as every post and reel), laid out as calm editorial rows: only the lead card and the form are cards.
const goldBtn =
  'inline-flex min-h-[52px] items-center justify-center rounded-xl bg-[#f0b440] px-7 text-[17px] font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white'
const outlineOnNavy =
  'inline-flex min-h-[52px] items-center justify-center rounded-xl border-2 border-white/70 px-6 text-[17px] font-bold text-white no-underline hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white'
const wrap = 'mx-auto max-w-6xl px-4 sm:px-6 lg:px-8'
const section = 'scroll-mt-16 py-14 sm:py-20'
const eyebrow = 'text-[13px] font-bold uppercase tracking-[0.08em] text-[#8a5d00]'
const h2 = 'text-[1.75rem] font-extrabold leading-tight tracking-tight text-[#0f2340] sm:text-4xl'

export default function LandingPage() {
  const cfg = getMarketingConfig()
  const H = L.hero
  return (
    <MarketingShell cta="agent" stickyBar>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(organizationJsonLd(cfg, L.metaOrgDescription, Object.values(socialLinks()))) }} />

      {/* Hero: the promise, one gold button, the lead card */}
      <section aria-labelledby="hero-title" className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] text-white">
        <div className={wrap + ' grid items-center gap-10 pt-10 pb-14 sm:py-20 md:grid-cols-[1.15fr_1fr] lg:gap-16'}>
          <div>
            <p className="flex flex-wrap items-center gap-2 text-[13px] font-bold uppercase tracking-[0.08em] text-[#f0b440]">
              <span>{H.eyebrow}</span>
              <span className="rounded-full bg-[#f0b440] px-2.5 py-0.5 text-[#0f2340]">{H.pilot}</span>
            </p>
            <h1 id="hero-title" className="mt-4 text-[2.25rem] font-extrabold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.75rem]">
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
            <p className="mt-5 text-sm leading-relaxed text-slate-300">
              {H.facts} · {H.signInLead}{' '}
              <Link href={PATHS.signIn} aria-label={`${H.signInLead} ${H.signIn}`} className="font-semibold text-white underline underline-offset-4">{H.signIn}</Link>
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
                <h3 className="text-xl font-bold text-[#0f2340] sm:text-2xl">{p.title}</h3>
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
                    <span className="block text-lg font-bold text-[#0f2340]">{c.title}</span>
                    <span className="mt-1 block leading-relaxed text-slate-700">{c.body}</span>
                  </figcaption>
                </figure>
              </li>
            ))}
          </ul>
          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <Link href={LIVE.links.page} className="inline-flex min-h-[52px] items-center justify-center rounded-xl bg-[#0f2340] px-7 text-[17px] font-bold text-white no-underline hover:bg-[#183a5d]">
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
                <span aria-hidden="true" className="text-lg font-extrabold text-[#8a5d00]">{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <p className={eyebrow}>{s.label}</p>
                  <h3 className="mt-1 text-xl font-bold text-[#0f2340] sm:text-2xl">{s.title}</h3>
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
                  <summary className="flex min-h-[52px] cursor-pointer list-none items-center justify-between gap-4 text-lg font-semibold text-[#0f2340] [&::-webkit-details-marker]:hidden">
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
      <section id="invite" aria-labelledby="cta-title" className="scroll-mt-16 bg-gradient-to-b from-[#0f2340] to-[#183a5d] py-14 sm:py-20">
        <div className={wrap + ' grid items-start gap-8 md:grid-cols-2 lg:gap-16'}>
          <div className="text-white">
            <h2 id="cta-title" className="text-[2.25rem] font-extrabold leading-[1.06] tracking-tight sm:text-5xl">
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

      {/* Buyers who land here: every area page (the hubs search engines and buyers need), then projects and news */}
      <section aria-labelledby="buyers-title" className="border-b border-[#ead9ae] bg-[#fbf6ea] py-10">
        <div className={wrap}>
          <h2 id="buyers-title" className="text-xl font-extrabold text-[#0f2340] sm:text-2xl">{BUYERS.title}</h2>
          <p className="mt-1 text-slate-700">{BUYERS.body}</p>
          {(['affordable', 'it'] as const).map((tier) => ({ tier, areas: localitiesByTier(tier) })).map(({ tier, areas }) => (
            <div key={tier} className="mt-5">
              <h3 className={eyebrow}>{TIER_LABELS[tier].title}</h3>
              <ul className="mt-2 flex flex-wrap gap-2 p-0">
                {areas.map((a) => (
                  <li key={a.slug} className="list-none">
                    <Link href={`/localities/${a.slug}`} className="inline-flex min-h-[44px] items-center rounded-full border-2 border-[#0f2340] bg-white px-4 font-semibold text-[#0f2340] no-underline hover:bg-[#0f2340] hover:text-white">{a.name}</Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <p className="mt-5 flex flex-wrap gap-x-6 gap-y-1">
            <Link href="/projects" className="flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-4">{BUYERS.projects}</Link>
            <Link href="/news" className="flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-4">{BUYERS.news}</Link>
          </p>
        </div>
      </section>
      <NewsSection />

      <StickyJoinBar watchId="hero-ctas" formId="invite" href="/trial" label={L.sticky.cta} whatsappUrl={cfg.whatsappUrl} whatsappLabel={L.sticky.whatsapp} />
    </MarketingShell>
  )
}
