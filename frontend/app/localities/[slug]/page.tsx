import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import ListingCard from '@/components/site/ListingCard'
import { getMarketingConfig } from '@/lib/marketing/config'
import { INSIGHT_NOTE, getInsight } from '@/lib/marketing/insights'
import { LOCALITIES, type Locality, type LocalityTier, getLocality, localitiesByTier, localityNameFromSlug, localitySource, localitySourceFromSlug } from '@/lib/marketing/localities'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import ProjectCard from '@/components/site/ProjectCard'
import AreaLatest from '@/components/localities/AreaLatest'
import AreaRecords from '@/components/localities/AreaRecords'
import { getAreaNews, getAreaPosts } from '@/components/localities/areaFeed'
import { getAreaStats } from '@/components/localities/areaStats'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getCatalog, getLocalityListings } from '@/lib/site/api'
import { livePages } from '@/lib/site/filters'

type Props = { params: Promise<{ slug: string }> }
type PageLocality = (Locality & { fallback?: false }) | {
  fallback: true
  slug: string
  key: string
  name: string
  tier: LocalityTier
  listingName: string
  tagline: string
  summary: string
  suits: string[]
  gettingAround: string[]
  checks: string[]
  faqs: { q: string; a: string }[]
  guides: string[]
  sources: { label: string; href: string }[]
  updated?: string
  updatedLabel?: string
}

function pageLocality(slug: string): PageLocality {
  const l = getLocality(slug)
  return l ? { ...l, fallback: false } : fallbackLocality(slug)
}

/** "Other <word> areas we cover" (the tier titles in TIER_LABELS read badly there). */
const TIER_WORD: Record<LocalityTier, string> = { affordable: 'affordable', it: 'IT corridor' }

export function generateStaticParams() {
  return LOCALITIES.map((l) => ({ slug: l.slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = (await params).slug
  const l = getLocality(slug)
  if (!l) {
    const name = localityNameFromSlug(slug)
    return pageMetadata(getMarketingConfig(), {
      title: `${name}, Pune: live listings and projects`,
      description: `Listings and projects agents have added in ${name}, Pune, with buyer checks before you visit or book.`,
      path: `/localities/${slug}`,
    })
  }
  return pageMetadata(getMarketingConfig(), {
    title: `${l.name}, Pune: projects, MahaRERA records and buyer guide`,
    description: `${l.summary.split('. ')[0].replace(/\.$/, '')}. Projects, MahaRERA records, getting around and what to check before you buy.`,
    path: `/localities/${l.slug}`,
  })
}

/** Where "I'm interested" leads: the house agent site's enquiry form (configurable at build time). `?src=locality_<key>` is
 *  picked up by the site's attribution (lib/site/tracking.ts readAttribution) and stored as the lead's source. */
const enquireHref = (l: { key: string }) =>
  `/agent/${process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'}?src=${localitySource(l)}#enquire`

const fallbackEnquireHref = (slug: string) =>
  `/agent/${process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'}?src=${localitySourceFromSlug(slug)}#enquire`

const validSlug = (slug: string) => /^[a-z0-9]+(?:-[a-z0-9]+){0,8}$/.test(slug)

function fallbackLocality(slug: string): PageLocality {
  const name = localityNameFromSlug(slug)
  return {
    fallback: true,
    slug, key: slug.replace(/-/g, '_'), name, tier: 'affordable', listingName: name,
    tagline: 'Live listings and projects agents have added',
    summary: `We do not have a full buyer guide for ${name} yet. This page shows live listings and projects agents have added, plus the checks every buyer should do before a visit or booking.`,
    suits: ['Buyers shortlisting homes in this locality', 'Buyers who want a working page to share listings from agents', 'Buyers ready to verify project details before paying a token amount'],
    gettingAround: ['We do not quote travel times. Try your own commute at 9:00 am and 6:30 pm on a weekday before you decide.'],
    checks: [
      'RERA registration number of the project, looked up on the MahaRERA website',
      'Carpet area in the agreement, and the price per sq ft of carpet area',
      'Where the water comes from, and what the power backup covers',
      'Possession date in the agreement compared with the one on the RERA page',
      'The full cost: stamp duty, registration, GST where applicable, parking and maintenance deposit',
    ],
    faqs: [
      { q: `Do you have a full guide for ${name}?`, a: 'Not yet. Until we have sourced locality facts, this page shows only live listings, projects agents have added and general buyer checks.' },
      { q: 'What should I verify before visiting?', a: 'Check the RERA number, the exact carpet area, possession date, water and power backup, and the full cost sheet before you pay anything.' },
    ],
    guides: [], sources: [],
  }
}

export default async function LocalityPage({ params }: Props) {
  const slug = (await params).slug
  if (!validSlug(slug)) notFound()
  const l = pageLocality(slug)
  const [listings, projects, stats, posts, news] = await Promise.all([
    getLocalityListings(l.listingName), getCatalog(l.listingName), l.fallback ? Promise.resolve(null) : getAreaStats(l.slug),
    l.fallback ? Promise.resolve([]) : getAreaPosts(l, 6), l.fallback ? Promise.resolve([]) : getAreaNews(l, 5),
  ])
  if (l.fallback && listings.length === 0 && projects.length === 0) notFound()
  const sameTier = localitiesByTier(l.tier).filter((o) => o.slug !== l.slug)
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
        {l.updated && l.updatedLabel && <p className="mt-2 text-sm text-slate-600">Last updated: <time dateTime={l.updated}>{l.updatedLabel}</time></p>}
        <p className="mt-5 text-lg leading-relaxed text-slate-800">{l.summary}</p>
        <a href={l.fallback ? fallbackEnquireHref(l.slug) : enquireHref(l)} className="mt-5 inline-flex min-h-[48px] items-center rounded-full bg-amber-400 px-6 font-bold text-slate-900 no-underline">Tell us what you are looking for</a>

        <section className="mt-10"><h2 className="text-xl font-semibold text-slate-900">Who {l.name} suits</h2>
          <ul className="mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800">{l.suits.map((s) => <li key={s}>{s}</li>)}</ul></section>

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Getting around</h2>
          {l.gettingAround.map((p) => <p key={p} className="mt-3 leading-relaxed text-slate-800">{p}</p>)}</section>

        <AreaRecords name={l.name} stats={stats} />

        {projects.length > 0 && (
          <section className="mt-9" style={AVASETU_SITE_VARS} aria-labelledby="projects-title">
            <h2 id="projects-title" className="text-xl font-semibold text-slate-900">New projects in {l.name}</h2>
            <p className="mt-1 text-sm text-slate-600">With the completion date filed on MahaRERA and how many homes are booked.</p>
            <ul className="mt-4 grid list-none gap-4 p-0 sm:grid-cols-2">
              {projects.map((p) => <li key={p.slug}><ProjectCard p={p} href={`/projects/${p.slug}`} /></li>)}
            </ul>
            {!l.fallback && livePages(projects, [l]).length > 0 && (
              <ul className="mt-4 flex list-none flex-wrap gap-2 p-0">
                {livePages(projects, [l]).map((f) => (
                  <li key={f.path}><Link href={f.path} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]">{f.title.replace(/, Pune$/, '')} ({f.count})</Link></li>
                ))}
              </ul>
            )}
            <p className="mt-3"><Link href="/projects" className="font-semibold text-[#0f2340] underline underline-offset-2">All projects</Link></p>
          </section>
        )}
        <AreaLatest name={l.name} posts={posts} news={news} />

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Homes in {l.name}</h2>
          {listings.length > 0 ? (
            <ul className="mt-4 grid list-none gap-4 p-0 sm:grid-cols-2">{listings.map((x) => x.agent?.slug ? <ListingCard key={x.id} slug={x.agent.slug} listing={x} /> : null)}</ul>
          ) : (
            <p className="mt-3 rounded-xl bg-slate-50 p-4 text-slate-700">{projects.length > 0 ? 'No individual homes are listed here yet; the new projects above have prices. ' : 'We do not have live listings here yet. '}Tell us your budget and preferred type and we will send you options as they come.</p>
          )}</section>

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Before you visit or book</h2>
          <ul className="mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800">{l.checks.map((s) => <li key={s}>{s}</li>)}</ul></section>

        <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Questions buyers ask</h2>
          <dl className="mt-3 space-y-4">{l.faqs.map((f) => (<div key={f.q}><dt className="font-semibold text-slate-900">{f.q}</dt><dd className="mt-1 leading-relaxed text-slate-800">{f.a}</dd></div>))}</dl></section>

        {guides.length > 0 && (
          <section className="mt-9"><h2 className="text-xl font-semibold text-slate-900">Related guides</h2>
            <ul className="mt-3 space-y-1">{guides.map((g) => <li key={g.slug}><Link href={`/insights/${g.slug}`} className="text-[#0f2340] underline underline-offset-2">{g.title}</Link></li>)}</ul></section>
        )}

        {/* Same tier only, never "nearby" or a distance: the IT corridor spans both ends of the city. */}
        <section className="mt-9" aria-labelledby="other-areas-title">
          <h2 id="other-areas-title" className="text-xl font-semibold text-slate-900">{l.fallback ? 'Pune area guides we cover' : `Other ${TIER_WORD[l.tier]} areas we cover`}</h2>
          <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
            {sameTier.map((o) => (
              <li key={o.slug}><Link href={`/localities/${o.slug}`} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]">{o.name}</Link></li>
            ))}
            <li><Link href="/localities" className="inline-flex min-h-[44px] items-center px-2 text-sm font-semibold text-[#0f2340] underline underline-offset-2">All Pune area guides</Link></li>
          </ul>
        </section>

        {l.sources.length > 0 && (
          <section className="mt-10 border-t border-slate-200 pt-6"><h2 className="text-lg font-semibold text-slate-900">Sources</h2>
            <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">{l.sources.map((s) => <li key={s.href}><a href={s.href} target="_blank" rel="noopener noreferrer" className="text-[#0f2340] underline underline-offset-2">{s.label}</a></li>)}</ul></section>
        )}
        <p className="mt-8 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{INSIGHT_NOTE}</p>
        <AgentStrip />
      </article>
    </MarketingShell>
  )
}
