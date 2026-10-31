import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import HomePlanForm, { RESULT_PATH } from '@/components/site/homeplan/HomePlanForm'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { hubSummaries, NEAR_KM, parsePlan, toPlanSearch, type HubSummary } from '@/lib/site/homeplan'
import { eastItems } from '@/lib/site/homeplanData'
import { longDay } from '@/lib/site/register'

export const revalidate = 300

// in search from 2026-10-31 (owner: "publish, that can help us gain position"): the page answers "projects near <office>"
// with dated counts from the register, not only a form; each family's plan (/home-plan/result) stays noindex
export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: 'Homes near EON IT Park, Magarpatta & Airport: East Pune plan',
  description: 'How many East Pune projects being sold are within 10 km of EON IT Park, Magarpatta and Pune airport, and a free plan that picks the ones for your family on MahaRERA facts.',
  path: '/home-plan',
})

type Props = { searchParams?: Promise<Record<string, string | string[] | undefined>> }

/** Two ready answers per office, the commonest asks (a 2 BHK under 1 Cr, a 3 BHK at 1 to 1.5 Cr): each opens a plan. */
const EXAMPLES = [
  { label: '2 BHK under ₹1 Cr', budget: '75l-1cr', bhk: '2' },
  { label: '3 BHK, ₹1 – 1.5 Cr', budget: '1-1.5cr', bhk: '3' },
] as const

const places = (s: HubSummary) => s.places.map((p) => `${p.name} (${p.count})`).join(', ')

/** "As of 31 Oct 2026, 42 East Pune projects being sold are within 10 km of EON IT Park, Kharadi …": the hub's dated answer. */
function hubAnswer(s: HubSummary, asOf: string): string {
  return `As of ${longDay(asOf)}, ${s.near} East Pune ${s.near === 1 ? 'project' : 'projects'} being sold ${s.near === 1 ? 'is' : 'are'} within ${NEAR_KM} km of ${s.hub} in a straight line`
    + `, ${s.priced} of them with a published price` + (s.places.length ? `. Most are in ${places(s)}.` : '.')
}

const HOW = 'We take every MahaRERA project in East Pune that is still being sold and keep the ones with a home of your size in your '
  + 'budget, within 25 km of your office. They are ranked on facts only: distance to your office, whether the builder has moved the '
  + 'MahaRERA completion date, how many homes are booked, and how soon it is due when you have young children or parents at home. '
  + 'A partner agent listing a project does not move it up.'

/** The plan's questions, with what the register says about each office, and the plan's own rules. "Edit answers" on a plan links
 *  here with the answers in the address, so the form starts filled in. */
export default async function HomePlanPage({ searchParams }: Props) {
  const cfg = getMarketingConfig()
  const start = parsePlan((await searchParams) ?? {})
  const asOf = new Date().toISOString().slice(0, 10)
  const hubs = hubSummaries((await eastItems().catch(() => ({ items: [] }))).items).filter((s) => s.near > 0)
  const faq = [
    ...hubs.map((s) => ({ q: `How many new projects are near ${s.hub}?`, a: hubAnswer(s, asOf) })),
    { q: 'How does the Avasetu home plan pick projects?', a: HOW },
    { q: 'Do I need to give my phone number?', a: 'No. The plan shows on screen as soon as you answer. You can ask us to send it on WhatsApp with today’s prices if you want.' },
  ]
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl px-4 py-10 sm:py-14" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'East Pune home plan', path: '/home-plan' },
        ])) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString({
          '@context': 'https://schema.org', '@type': 'FAQPage',
          mainEntity: faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
        }) }} />
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Homes near your office in East Pune: a free plan for your family</h1>
        <p className="mt-3 text-lg leading-relaxed text-slate-800">
          Answer six questions and see the East Pune projects that fit your family: near your office, in your budget, and with a
          MahaRERA record that holds up. Each pick says why, and what to check on the site visit. No phone number needed.
        </p>
        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <HomePlanForm start={start} />
        </div>

        {hubs.length > 0 && (
          <section aria-labelledby="near-title" className="mt-10" data-testid="plan-hubs">
            <h2 id="near-title" className="text-2xl font-bold text-slate-900">Projects near East Pune&apos;s offices</h2>
            <p className="mt-1 text-sm text-slate-600">Counted on {longDay(asOf)} from MahaRERA&apos;s register; straight-line distance from our checked map positions.</p>
            <div className="mt-4 space-y-4">
              {hubs.map((s) => (
                <article key={s.key} className="rounded-2xl border border-slate-200 bg-white p-5">
                  <h3 className="text-lg font-bold text-slate-900">Near {s.hub}</h3>
                  <p className="mt-1 leading-relaxed text-slate-800">{hubAnswer(s, asOf)}</p>
                  <ul className="mt-3 flex list-none flex-wrap gap-3 p-0">
                    {EXAMPLES.map((x) => (
                      <li key={x.label}>
                        <Link href={RESULT_PATH + toPlanSearch({ work: s.key, budget: x.budget, bhk: x.bhk })}
                          className="inline-flex min-h-[44px] items-center rounded-full border border-[#0f2340] px-4 font-semibold text-[#0f2340] no-underline">
                          {x.label} near here
                        </Link>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </section>
        )}

        <section aria-labelledby="how-title" className="mt-10">
          <h2 id="how-title" className="text-2xl font-bold text-slate-900">How we pick</h2>
          <p className="mt-2 leading-relaxed text-slate-800">{HOW}</p>
          <p className="mt-2 leading-relaxed text-slate-800">
            Prices are the asking prices builders and property sites publish; homes booked is what the builder last filed on
            MahaRERA. Our team can confirm today&apos;s price for any pick. Looking elsewhere in Pune?{' '}
            <Link href="/projects" className="font-semibold text-[#0f2340] underline underline-offset-2">Every project, with the same checks</Link>.
          </p>
        </section>

        <section aria-labelledby="faq-title" className="mt-10">
          <h2 id="faq-title" className="text-2xl font-bold text-slate-900">Questions</h2>
          <dl className="mt-3 space-y-4">
            {faq.map((f) => (
              <div key={f.q}>
                <dt className="font-semibold text-slate-900">{f.q}</dt>
                <dd className="m-0 mt-1 leading-relaxed text-slate-800">{f.a}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </MarketingShell>
  )
}
