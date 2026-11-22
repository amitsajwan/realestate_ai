import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import { notFound, permanentRedirect } from 'next/navigation'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import AreaCompareView, { PairLinks, compareLead, compareQuestions } from '@/components/localities/AreaCompare'
import { getMarketingConfig } from '@/lib/marketing/config'
import { getLocality } from '@/lib/marketing/localities'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { PAIR_SLUG, comparePath, getAreaCompare, type AreaCompare } from '@/lib/site/compare'

// Two neighbouring areas side by side (backend areastats/compare.py): rendered on first visit and kept for an hour, like the
// builder pages. Only pairs the backend makes exist; the other order of a pair is sent to its one address.
export const revalidate = 3600
export const dynamicParams = true
export async function generateStaticParams(): Promise<{ pair: string }[]> {
  return []
}

type Props = { params: Promise<{ pair: string }> }

async function load(pair: string): Promise<AreaCompare | null> {
  if (!PAIR_SLUG.test(pair)) return null
  const c = await getAreaCompare(pair)
  if (c && 'redirect' in c) permanentRedirect(comparePath(c.redirect))
  return c
}

const title = (c: AreaCompare) => `${c.sides[0].area.name} vs ${c.sides[1].area.name}, Pune: projects, homes booked and distances`

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const c = await load((await params).pair)
  if (!c) return { title: 'Area comparison', robots: { index: false, follow: true } }
  const [a, b] = c.sides
  return pageMetadata(getMarketingConfig(), {
    title: title(c),
    description: `${a.area.name} and ${b.area.name} side by side from MahaRERA's register: projects, homes booked, possession dates `
      + 'moved, the nearest running metro and distances to offices, malls, hospitals and the airport.',
    path: comparePath(c.slug),
  })
}

export default async function AreaComparePage({ params }: Props) {
  const c = await load((await params).pair)
  if (!c) notFound()
  const [a, b] = c.sides
  const faqs = compareQuestions(c)
  const base = getMarketingConfig().siteUrl
  return (
    <MarketingShell hot={{ area: a.area.slug }}>
      <article className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString({
          '@context': 'https://schema.org', '@type': 'FAQPage',
          mainEntity: faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
        }) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(base, [
          { name: 'Home', path: '/' }, { name: 'Area guides', path: '/localities' }, { name: `${a.area.name} vs ${b.area.name}`, path: comparePath(c.slug) },
        ])) }} />
        <p className="text-sm"><Link href="/localities" className="text-[#0f2340] underline underline-offset-2">All area guides</Link></p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{a.area.name} vs {b.area.name}, Pune</h1>
        <p className="mt-5 text-lg leading-relaxed text-slate-800">{compareLead(c)}</p>
        <p className="mt-3 leading-relaxed text-slate-700">
          Two columns of facts you can check, not a ranking: which area is right depends on where you work, your budget and how you
          travel. Try both commutes at 9:00 am and 6:30 pm on a weekday before you decide.
        </p>
        <a href={`/enquire?src=compare_${a.area.key}_${b.area.key}`} className="mt-5 inline-flex min-h-[48px] items-center rounded-full bg-amber-400 px-6 font-bold text-slate-900 no-underline">Tell us what you are looking for</a>

        <AreaCompareView c={c} guides={[getLocality(a.area.slug), getLocality(b.area.slug)]} />

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Questions buyers ask</h2>
          <dl className="mt-3 space-y-4">{faqs.map((f) => (<div key={f.q}><dt className="font-semibold text-slate-900">{f.q}</dt><dd className="mt-1 leading-relaxed text-slate-800">{f.a}</dd></div>))}</dl></section>

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">See the projects</h2>
          <ul className="mt-3 space-y-1">
            {[a, b].map((s) => <li key={s.area.slug}><Link href={`/projects/area/${s.area.slug}`} className="text-[#0f2340] underline underline-offset-2">Every project in {s.area.name}</Link></li>)}
          </ul></section>

        <PairLinks pairs={c.related} title="Compare other nearby areas" />
        <AgentStrip />
      </article>
    </MarketingShell>
  )
}
