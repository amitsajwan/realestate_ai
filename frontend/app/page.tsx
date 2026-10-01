import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import PostsSection from '@/components/site/PostsSection'
import MarketingShell from '@/components/marketing/MarketingShell'
import LeadCardMock from '@/components/marketing/LeadCardMock'
import PhoneFrame from '@/components/marketing/PhoneFrame'
import RequestInviteForm from '@/components/marketing/RequestInviteForm'
import { socialLinks } from '@/lib/marketing/social'
import { getMarketingConfig } from '@/lib/marketing/config'
import { jsonLdString, organizationJsonLd, pageMetadata } from '@/lib/marketing/seo'
import { LANDING as L, PATHS, SAMPLE_NOTE, SHOTS } from '@/lib/marketing/strings'

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: L.metaTitle,
  description: L.metaDescription,
  path: '/',
  image: { path: '/brand/og-landing.jpg', width: 1200, height: 630, alt: 'A buyer comments INTERESTED and it becomes a lead card. PUNE Property, free invite-only pilot for agents in Pune.' },
})

const goldBtn =
  'inline-flex min-h-[52px] items-center justify-center rounded-xl bg-[#f0b440] px-7 text-lg font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white'
const wrap = 'mx-auto max-w-5xl px-4'
const h2 = 'text-2xl font-extrabold tracking-tight text-[#0f2340] sm:text-3xl'

export default function LandingPage() {
  const cfg = getMarketingConfig()
  return (
    <MarketingShell>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(organizationJsonLd(cfg, L.metaOrgDescription, Object.values(socialLinks()))) }} />

      {/* Hero: the agent's problem, the product, one CTA */}
      <section aria-labelledby="hero-title" className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] text-white">
        <div className={wrap + ' grid items-center gap-10 py-10 sm:py-16 md:grid-cols-[1.15fr_1fr]'}>
          <div>
            <p className="flex flex-wrap items-center gap-2 text-xs font-bold uppercase tracking-wide text-[#f0b440]">
              <span>{L.hero.eyebrow}</span>
              <span className="rounded-full bg-[#f0b440] px-2.5 py-0.5 text-[#0f2340]">{L.hero.pilot}</span>
            </p>
            <h1 id="hero-title" className="mt-4 text-[2rem] font-extrabold leading-[1.15] tracking-tight sm:text-5xl">{L.hero.title}</h1>
            <p className="mt-4 text-base leading-relaxed text-slate-100 sm:text-lg">{L.hero.lead}</p>
            <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2">
              <Link href={PATHS.invite} className={goldBtn + ' w-full sm:w-auto'}>{L.hero.cta}</Link>
              <Link href={PATHS.signIn} className="flex min-h-[44px] items-center font-medium text-white underline underline-offset-4">{L.hero.signIn}</Link>
            </div>
            <ul className="mt-5 flex flex-wrap gap-2 p-0 text-sm font-medium text-white">
              {L.hero.facts.map((f) => (
                <li key={f} className="list-none rounded-full border border-white/40 px-3 py-1">{f}</li>
              ))}
            </ul>
          </div>
          <LeadCardMock />
        </div>
      </section>

      {/* The agent's problem */}
      <section aria-labelledby="problem-title" className="bg-[#fbf6ea] py-12 sm:py-16">
        <div className={wrap}>
          <h2 id="problem-title" className={h2}>{L.problem.heading}</h2>
          <ul className="mt-6 grid gap-4 p-0 md:grid-cols-3">
            {L.problem.items.map((p) => (
              <li key={p.title} className="list-none rounded-2xl border border-[#ead9ae] bg-white p-5">
                <h3 className="text-lg font-bold text-[#0f2340]">{p.title}</h3>
                <p className="mt-2 leading-relaxed text-slate-700">{p.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Create -> Attract -> Qualify -> Close */}
      <section id={L.steps.id} aria-labelledby="steps-title" className="scroll-mt-16 py-12 sm:py-16">
        <div className={wrap}>
          <h2 id="steps-title" className={h2}>{L.steps.heading}</h2>
          <p className="mt-2 text-lg text-slate-700">{L.steps.lead}</p>
          <ol className="mt-8 grid gap-4 p-0 sm:grid-cols-2 lg:grid-cols-4">
            {L.steps.items.map((s, i) => (
              <li key={s.key} className="list-none rounded-2xl bg-[#0f2340] p-5 text-white">
                <p className="flex items-center gap-3 text-sm font-bold uppercase tracking-wide text-[#f0b440]">
                  <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-full bg-[#f0b440] text-base font-extrabold text-[#0f2340]">{i + 1}</span>
                  {s.label}
                </p>
                <h3 className="mt-3 text-lg font-bold">{s.title}</h3>
                <p className="mt-2 leading-relaxed text-slate-100">{s.body}</p>
              </li>
            ))}
          </ol>
          <p className="mt-6 flex items-start gap-3 rounded-2xl bg-[#e6f4f1] p-4 text-[#0b3f3a]">
            <span aria-hidden="true" className="mt-0.5 text-xl">&#10003;</span>
            <span><strong>{L.whatsapp.title}.</strong> {L.whatsapp.body}</span>
          </p>
        </div>
      </section>

      {/* Real product screens: horizontal strip, lazy */}
      <section aria-labelledby="screens-title" className="bg-slate-50 py-12 sm:py-16">
        <div className={wrap}>
          <h2 id="screens-title" className={h2}>{L.screens.heading}</h2>
          <p className="mt-2 text-slate-700">{L.screens.lead}</p>
        </div>
        <ul className="mx-auto mt-6 flex max-w-5xl snap-x gap-4 overflow-x-auto px-4 pb-4 p-0" tabIndex={0} aria-label={L.screens.heading}>
          {Object.values(SHOTS).map((sh) => (
            <li key={sh.src} className="w-44 flex-none snap-start list-none sm:w-52">
              <PhoneFrame shot={sh} className="max-w-none" />
            </li>
          ))}
        </ul>
        <p className={wrap + ' text-sm text-slate-600'}>{SAMPLE_NOTE}</p>
      </section>

      <PostsSection />

      {/* How it works for an agent */}
      <section id={L.how.id} aria-labelledby="how-title" className="scroll-mt-16 py-12 sm:py-16">
        <div className={wrap}>
          <h2 id="how-title" className={h2}>{L.how.heading}</h2>
          <p className="mt-2 max-w-2xl text-lg text-slate-700">{L.how.lead}</p>
          <ol className="mt-8 grid gap-5 p-0 md:grid-cols-3">
            {L.how.items.map((s, i) => (
              <li key={s.title} className="list-none rounded-2xl border border-[#ead9ae] bg-[#fbf6ea] p-5">
                <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-full bg-[#0f2340] font-bold text-white">{i + 1}</span>
                <h3 className="mt-3 text-lg font-bold text-[#0f2340]">{s.title}</h3>
                <p className="mt-2 leading-relaxed text-slate-700">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Cost + status, honest */}
      <section id={L.cost.id} aria-labelledby="cost-title" className="scroll-mt-16 bg-slate-50 py-12 sm:py-16">
        <div className={wrap + ' grid gap-6 md:grid-cols-2'}>
          <div>
            <h2 id="cost-title" className={h2}>{L.cost.heading}</h2>
            <div className="mt-6 rounded-2xl border border-[#ead9ae] bg-[#fbf6ea] p-6">
              <p className="text-2xl font-extrabold text-[#0f2340]">{L.cost.title}</p>
              <p className="mt-2 text-lg leading-relaxed text-slate-800">{L.cost.body}</p>
            </div>
          </div>
          <div id={L.coming.id} className="scroll-mt-16">
            <h2 className={h2}>{L.coming.heading}</h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-2 md:grid-cols-1">
              <div className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-bold text-[#0f2340]">{L.coming.today}</h3>
                <ul className="mt-3 list-disc space-y-2 pl-5 leading-relaxed text-slate-800">
                  {L.coming.todayItems.map((t) => <li key={t}>{t}</li>)}
                </ul>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-bold text-[#0f2340]">{L.coming.next}</h3>
                <ul className="mt-3 list-disc space-y-2 pl-5 leading-relaxed text-slate-800">
                  {L.coming.nextItems.map((t) => <li key={t}>{t}</li>)}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id={L.faq.id} aria-labelledby="faq-title" className="scroll-mt-16 py-12 sm:py-16">
        <div className={wrap + ' max-w-3xl'}>
          <h2 id="faq-title" className={h2}>{L.faq.heading}</h2>
          <div className="mt-6 divide-y divide-slate-200 border-y border-slate-200">
            {L.faq.items.map((f) => (
              <details key={f.q} className="group py-1">
                <summary className="flex min-h-[52px] cursor-pointer items-center justify-between gap-4 text-lg font-semibold text-[#0f2340]">
                  {f.q}
                  <span aria-hidden="true" className="text-2xl text-[#b7791f] group-open:hidden">+</span>
                  <span aria-hidden="true" className="hidden text-2xl text-[#b7791f] group-open:inline">&minus;</span>
                </summary>
                <p className="pb-4 leading-relaxed text-slate-700">{f.a}</p>
              </details>
            ))}
          </div>
          <p className="mt-5 flex flex-wrap gap-x-6 text-sm">
            <Link href={PATHS.privacy} className="flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{L.faq.privacyLink}</Link>
            <Link href={PATHS.deletion} className="flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{L.faq.deletionLink}</Link>
          </p>
        </div>
      </section>

      {/* Final CTA with the short form right here */}
      <section id="invite" aria-labelledby="cta-title" className="scroll-mt-16 bg-gradient-to-b from-[#0f2340] to-[#183a5d] py-12 sm:py-16">
        <div className={wrap + ' grid items-start gap-8 md:grid-cols-2'}>
          <div className="text-white">
            <h2 id="cta-title" className="text-2xl font-extrabold sm:text-3xl">{L.finalCta.title}</h2>
            <p className="mt-3 text-lg text-slate-100">{L.finalCta.body}</p>
            <p className="mt-4 text-sm text-slate-200">
              <Link href={PATHS.invite} className="text-white underline underline-offset-2">Open the full form</Link>
            </p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-xl text-slate-900">
            <RequestInviteForm idPrefix="lp" />
          </div>
        </div>
      </section>
    </MarketingShell>
  )
}
