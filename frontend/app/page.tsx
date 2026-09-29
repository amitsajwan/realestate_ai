import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import PhoneFrame from '@/components/marketing/PhoneFrame'
import { getMarketingConfig } from '@/lib/marketing/config'
import { jsonLdString, organizationJsonLd, pageMetadata } from '@/lib/marketing/seo'
import { LANDING as L, PATHS, SAMPLE_NOTE, SHOTS } from '@/lib/marketing/strings'

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: L.metaTitle,
  description: L.metaDescription,
  path: '/',
  image: { path: SHOTS.market.src, width: SHOTS.market.width, height: SHOTS.market.height, alt: SHOTS.market.alt },
})

const primaryBtn =
  'inline-flex min-h-[52px] items-center justify-center rounded-xl bg-blue-700 px-7 text-lg font-bold text-white no-underline hover:bg-blue-800'
const wrap = 'mx-auto max-w-5xl px-4'
const h2 = 'text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl'

const STEP_SHOTS: Record<string, (typeof SHOTS)[keyof typeof SHOTS][]> = {
  create: [SHOTS.create],
  market: [SHOTS.market],
  attract: [SHOTS.site],
  close: [SHOTS.lead, SHOTS.match],
}

export default function LandingPage() {
  const cfg = getMarketingConfig()
  return (
    <MarketingShell>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(organizationJsonLd(cfg, L.metaOrgDescription)) }} />

      {/* Hero */}
      <section aria-labelledby="hero-title" className="bg-gradient-to-b from-blue-50 to-white">
        <div className={wrap + ' grid items-center gap-10 py-12 sm:py-16 md:grid-cols-[1.2fr_1fr]'}>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-800">{L.hero.eyebrow}</p>
            <h1 id="hero-title" className="mt-3 text-4xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-5xl">{L.hero.title}</h1>
            <p className="mt-5 text-lg leading-relaxed text-slate-700">{L.hero.lead}</p>
            <div className="mt-7 flex flex-wrap items-center gap-x-6 gap-y-3">
              <Link href={PATHS.invite} className={primaryBtn}>{L.hero.cta}</Link>
              <Link href={PATHS.signIn} className="flex min-h-[44px] items-center font-medium text-blue-800 underline underline-offset-4">{L.hero.signIn}</Link>
            </div>
            <ul className="mt-6 flex flex-wrap gap-2 text-sm font-medium text-slate-800">
              {L.hero.facts.map((f) => (
                <li key={f} className="rounded-full border border-slate-300 bg-white px-3 py-1">{f}</li>
              ))}
            </ul>
          </div>
          <PhoneFrame shot={SHOTS.home} eager />
        </div>
        <p className={wrap + ' pb-6 text-center text-sm text-slate-600'}>{SAMPLE_NOTE}</p>
      </section>

      {/* What it does */}
      <section id={L.steps.id} aria-labelledby="steps-title" className="scroll-mt-16 py-14 sm:py-20">
        <div className={wrap}>
          <h2 id="steps-title" className={h2}>{L.steps.heading}</h2>
          <p className="mt-2 text-lg text-slate-700">{L.steps.lead}</p>
          <ol className="mt-10 space-y-16">
            {L.steps.items.map((s, i) => (
              <li key={s.key} className="grid items-center gap-8 md:grid-cols-2">
                <div className={i % 2 ? 'md:order-2' : ''}>
                  <p className="flex items-center gap-3 text-sm font-semibold uppercase tracking-wide text-blue-800">
                    <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-700 text-base font-bold text-white">{i + 1}</span>
                    {s.label}
                  </p>
                  <h3 className="mt-3 text-xl font-bold text-slate-900 sm:text-2xl">{s.title}</h3>
                  <p className="mt-3 text-lg leading-relaxed text-slate-700">{s.body}</p>
                </div>
                <div className={'flex justify-center gap-4 ' + (i % 2 ? 'md:order-1' : '')}>
                  {STEP_SHOTS[s.key].map((sh) => (
                    <PhoneFrame key={sh.src} shot={sh} className={STEP_SHOTS[s.key].length > 1 ? 'max-w-[10.5rem] sm:max-w-[12rem]' : ''} />
                  ))}
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* How it works for an agent */}
      <section id={L.how.id} aria-labelledby="how-title" className="scroll-mt-16 bg-slate-50 py-14 sm:py-20">
        <div className={wrap}>
          <h2 id="how-title" className={h2}>{L.how.heading}</h2>
          <p className="mt-2 max-w-2xl text-lg text-slate-700">{L.how.lead}</p>
          <ol className="mt-8 grid gap-5 md:grid-cols-3">
            {L.how.items.map((s, i) => (
              <li key={s.title} className="rounded-2xl border border-slate-200 bg-white p-5">
                <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-900">{i + 1}</span>
                <h3 className="mt-3 text-lg font-bold text-slate-900">{s.title}</h3>
                <p className="mt-2 leading-relaxed text-slate-700">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Cost */}
      <section id={L.cost.id} aria-labelledby="cost-title" className="scroll-mt-16 py-14 sm:py-20">
        <div className={wrap}>
          <h2 id="cost-title" className={h2}>{L.cost.heading}</h2>
          <div className="mt-6 max-w-2xl rounded-2xl border border-blue-200 bg-blue-50 p-6">
            <p className="text-2xl font-bold text-slate-900">{L.cost.title}</p>
            <p className="mt-2 text-lg leading-relaxed text-slate-800">{L.cost.body}</p>
          </div>
        </div>
      </section>

      {/* What's coming */}
      <section id={L.coming.id} aria-labelledby="coming-title" className="scroll-mt-16 bg-slate-50 py-14 sm:py-20">
        <div className={wrap}>
          <h2 id="coming-title" className={h2}>{L.coming.heading}</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <h3 className="text-lg font-bold text-slate-900">{L.coming.today}</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 leading-relaxed text-slate-800">
                {L.coming.todayItems.map((t) => <li key={t}>{t}</li>)}
              </ul>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <h3 className="text-lg font-bold text-slate-900">{L.coming.next}</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 leading-relaxed text-slate-800">
                {L.coming.nextItems.map((t) => <li key={t}>{t}</li>)}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id={L.faq.id} aria-labelledby="faq-title" className="scroll-mt-16 py-14 sm:py-20">
        <div className={wrap + ' max-w-3xl'}>
          <h2 id="faq-title" className={h2}>{L.faq.heading}</h2>
          <div className="mt-6 divide-y divide-slate-200 border-y border-slate-200">
            {L.faq.items.map((f) => (
              <details key={f.q} className="group py-1">
                <summary className="flex min-h-[52px] cursor-pointer items-center justify-between gap-4 text-lg font-semibold text-slate-900">
                  {f.q}
                  <span aria-hidden="true" className="text-2xl text-blue-800 group-open:hidden">+</span>
                  <span aria-hidden="true" className="hidden text-2xl text-blue-800 group-open:inline">&minus;</span>
                </summary>
                <p className="pb-4 leading-relaxed text-slate-700">{f.a}</p>
              </details>
            ))}
          </div>
          <p className="mt-5 flex flex-wrap gap-x-6 text-sm">
            <Link href={PATHS.privacy} className="flex min-h-[44px] items-center text-blue-800 underline underline-offset-2">{L.faq.privacyLink}</Link>
            <Link href={PATHS.deletion} className="flex min-h-[44px] items-center text-blue-800 underline underline-offset-2">{L.faq.deletionLink}</Link>
          </p>
        </div>
      </section>

      {/* Final CTA */}
      <section aria-labelledby="cta-title" className="bg-slate-900 py-14 text-center sm:py-16">
        <div className={wrap + ' max-w-2xl'}>
          <h2 id="cta-title" className="text-2xl font-bold text-white sm:text-3xl">{L.finalCta.title}</h2>
          <p className="mt-3 text-lg text-slate-200">{L.finalCta.body}</p>
          <Link href={PATHS.invite} className="mt-7 inline-flex min-h-[52px] items-center justify-center rounded-xl bg-white px-7 text-lg font-bold text-blue-900 no-underline hover:bg-blue-50">
            {L.finalCta.cta}
          </Link>
        </div>
      </section>
    </MarketingShell>
  )
}
