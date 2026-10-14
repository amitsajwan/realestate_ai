import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import { longDate } from '@/components/localities/areaStats'
import { getCommunities, getCommunity } from '@/components/localities/communities'
import ActiveProjects from '@/components/site/ActiveProjects'
import { getNearGuide } from '@/lib/site/hubs'
import { getMarketingConfig } from '@/lib/marketing/config'
import { INSIGHT_NOTE } from '@/lib/marketing/insights'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'

/** A neighbourhood inside one of our areas, written by the communities bot from OpenStreetMap and MahaRERA facts only
 *  (backend/app/modules/communities). Only published, checked articles exist; anything else is a 404. */
export const revalidate = 300

type Props = { params: Promise<{ slug: string; community: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, community } = await params
  const c = await getCommunity(slug, community).catch(() => null)
  if (!c) return { title: 'Neighbourhood guide', robots: { index: false } }
  return pageMetadata(getMarketingConfig(), {
    title: c.title,
    description: c.summary || `${c.name}, ${c.area_name}, Pune: what is nearby and the MahaRERA projects named after it.`,
    path: `/localities/${c.area_slug}/${c.slug}`,
  })
}

export default async function CommunityPage({ params }: Props) {
  const { slug, community } = await params
  const c = await getCommunity(slug, community)
  if (!c || c.area_slug !== slug) notFound()
  const cfg = getMarketingConfig()
  const path = `/localities/${c.area_slug}/${c.slug}`
  const [all, nearby] = await Promise.all([getCommunities(c.area), getNearGuide(c.area_slug, c.slug)])
  const others = all.filter((o) => o.slug !== c.slug).slice(0, 8)
  const article = {
    '@context': 'https://schema.org', '@type': 'Article', headline: c.title, url: cfg.siteUrl + path,
    datePublished: c.published ?? undefined, dateModified: c.updated ?? undefined,
    author: { '@type': 'Organization', name: cfg.businessName, url: cfg.siteUrl },
    about: { '@type': 'Place', name: `${c.name}, ${c.area_name}, Pune`, containedInPlace: { '@type': 'Place', name: `${c.area_name}, Pune` } },
  }
  return (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(article) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Area guides', path: '/localities' },
          { name: `${c.area_name}, Pune`, path: `/localities/${c.area_slug}` }, { name: c.name, path },
        ])) }} />
        <p className="text-sm"><Link href={`/localities/${c.area_slug}`} className="text-[#0f2340] underline underline-offset-2">{c.area_name} area guide</Link></p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{c.title}</h1>
        {c.updated && <p className="mt-2 text-sm text-slate-600">Last updated: <time dateTime={c.updated}>{longDate(c.updated)}</time></p>}
        {c.paragraphs.map((p) => <p key={p} className="mt-5 text-lg leading-relaxed text-slate-800">{p}</p>)}

        {c.facts.nearby.length > 0 && (
          <section className="mt-10" aria-labelledby="nearby">
            <h2 id="nearby" className="text-xl font-semibold text-slate-900">Nearby, by straight-line distance</h2>
            <ul className="mt-3 divide-y divide-slate-200 rounded-2xl border border-slate-200">
              {c.facts.nearby.map((n) => (
                <li key={n.kind + n.name} className="flex items-baseline justify-between gap-3 px-4 py-2">
                  <span><span className="text-sm text-slate-500">{n.kind}</span><br /><span className="text-slate-900">{n.name}</span></span>
                  <span className="whitespace-nowrap text-slate-700">about {n.km} km</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        <ActiveProjects title={`Projects near ${c.name}`} items={nearby} />

        {c.facts.projects.length > 0 && (
          <section className="mt-9" aria-labelledby="projects">
            <h2 id="projects" className="text-xl font-semibold text-slate-900">MahaRERA projects named after {c.name}</h2>
            <ul className="mt-3 space-y-2">
              {c.facts.projects.map((p) => (
                <li key={p.regno} className="rounded-xl bg-slate-50 px-4 py-3">
                  {p.page ? <Link href={p.page} className="font-semibold text-[#0f2340] underline underline-offset-2">{p.name}</Link> : <span className="font-semibold">{p.name}</span>}
                  <span className="block text-sm text-slate-600">{[p.promoter, p.completion ? `completion filed for ${longDate(p.completion)}` : null, `MahaRERA ${p.regno}`].filter(Boolean).join(' · ')}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {others.length > 0 && (
          <section className="mt-9" aria-labelledby="more">
            <h2 id="more" className="text-xl font-semibold text-slate-900">More neighbourhoods in {c.area_name}</h2>
            <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
              {others.map((o) => <li key={o.slug}><Link href={`/localities/${o.area_slug}/${o.slug}`} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]">{o.name}</Link></li>)}
            </ul>
          </section>
        )}
        <p className="mt-6"><Link href="/pune-maharera-tracker" className="font-semibold text-[#0f2340] underline underline-offset-2">Compare all areas in the Pune MahaRERA tracker</Link></p>

        <section className="mt-10 border-t border-slate-200 pt-6">
          <h2 className="text-lg font-semibold text-slate-900">Sources</h2>
          <p className="mt-2 text-sm text-slate-700">Written automatically from {c.sources.join(' and ') || 'public records'}{c.facts.as_of ? `, MahaRERA as of ${longDate(c.facts.as_of)}` : ''}, and checked so that it states only facts from those sources. Distances are straight-line, not by road.{c.osm_url && <> <a href={c.osm_url} target="_blank" rel="noopener noreferrer" className="text-[#0f2340] underline underline-offset-2">{c.name} on OpenStreetMap</a>.</>}</p>
        </section>
        <p className="mt-8 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{INSIGHT_NOTE}</p>
        <AgentStrip />
      </article>
    </MarketingShell>
  )
}
