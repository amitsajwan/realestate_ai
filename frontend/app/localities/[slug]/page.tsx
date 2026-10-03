import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import ListingCard from '@/components/site/ListingCard'
import { getMarketingConfig } from '@/lib/marketing/config'
import { INSIGHT_NOTE, getInsight } from '@/lib/marketing/insights'
import { LOCALITIES, getLocality } from '@/lib/marketing/localities'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { getLocalityListings } from '@/lib/site/api'

type Props = { params: Promise<{ slug: string }> }

export function generateStaticParams() {
  return LOCALITIES.map((l) => ({ slug: l.slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const l = getLocality((await params).slug)
  if (!l) return {}
  return pageMetadata(getMarketingConfig(), {
    title: `${l.name}, Pune: buyer guide`,
    description: `${l.summary.split('. ')[0]}. Who it suits, how to get around and what to check before you buy.`,
    path: `/localities/${l.slug}`,
  })
}

/** Where "I'm interested" leads: the house agent site's enquiry form (configurable at build time). */
const ENQUIRE = `/agent/${process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'}#enquire`

export default async function LocalityPage({ params }: Props) {
  const l = getLocality((await params).slug)
  if (!l) notFound()
  const listings = await getLocalityListings(l.listingName)
  const guides = l.guides.map((s) => getInsight(s)).filter((g): g is NonNullable<typeof g> => !!g)
  const faqLd = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: l.faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
  }
  return (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(faqLd) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(getMarketingConfig().siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Area guides', path: '/localities' }, { name: `${l.name}, Pune`, path: `/localities/${l.slug}` },
        ])) }} />
        <p className="text-sm"><Link href="/localities" className="text-[#0f2340] underline underline-offset-2">All localities</Link></p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{l.name}, Pune</h1>
        <p className="mt-1 font-semibold text-amber-700">{l.tagline}</p>
        <p className="mt-2 text-sm text-slate-600">Last updated: <time dateTime={l.updated}>{l.updatedLabel}</time></p>
        <p className="mt-5 text-lg leading-relaxed text-slate-800">{l.summary}</p>
        <a href={ENQUIRE} className="mt-5 inline-flex min-h-[48px] items-center rounded-full bg-amber-400 px-6 font-bold text-slate-900 no-underline">Tell us what you are looking for</a>

        <section className="mt-10"><h2 className="text-xl font-semibold text-slate-900">Who {l.name} suits</h2>
          <ul className="mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800">{l.suits.map((s) => <li key={s}>{s}</li>)}</ul></section>

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Getting around</h2>
          {l.gettingAround.map((p) => <p key={p} className="mt-3 leading-relaxed text-slate-800">{p}</p>)}</section>

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Homes in {l.name}</h2>
          {listings.length > 0 ? (
            <ul className="mt-4 grid list-none gap-4 p-0 sm:grid-cols-2">{listings.map((x) => x.agent?.slug ? <ListingCard key={x.id} slug={x.agent.slug} listing={x} /> : null)}</ul>
          ) : (
            <p className="mt-3 rounded-xl bg-slate-50 p-4 text-slate-700">We do not have live listings here yet. Tell us your budget and preferred type and we will send you options as they come.</p>
          )}</section>

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Before you visit or book</h2>
          <ul className="mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800">{l.checks.map((s) => <li key={s}>{s}</li>)}</ul></section>

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Questions buyers ask</h2>
          <dl className="mt-3 space-y-4">{l.faqs.map((f) => (<div key={f.q}><dt className="font-semibold text-slate-900">{f.q}</dt><dd className="mt-1 leading-relaxed text-slate-800">{f.a}</dd></div>))}</dl></section>

        {guides.length > 0 && (
          <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Related guides</h2>
            <ul className="mt-3 space-y-1">{guides.map((g) => <li key={g.slug}><Link href={`/insights/${g.slug}`} className="text-[#0f2340] underline underline-offset-2">{g.title}</Link></li>)}</ul></section>
        )}

        <section className="mt-10 border-t border-slate-200 pt-6"><h2 className="text-lg font-semibold text-slate-900">Sources</h2>
          <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">{l.sources.map((s) => <li key={s.href}><a href={s.href} target="_blank" rel="noopener noreferrer" className="text-[#0f2340] underline underline-offset-2">{s.label}</a></li>)}</ul></section>
        <p className="mt-8 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{INSIGHT_NOTE}</p>
        <AgentStrip />
      </article>
    </MarketingShell>
  )
}
