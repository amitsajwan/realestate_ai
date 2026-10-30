import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import ProjectSearch from '@/components/site/ProjectSearch'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import HomeFinder from '@/components/site/finder/HomeFinder'
import { BRAND_NAME } from '@/lib/brand'
import { getAgent, getListings, getSitemapEntries } from '@/lib/site/api'
import { parseQuery } from '@/lib/site/finder'
import { fromRegister, type AgentOffer } from '@/lib/site/finderItems'
import { isSampleListing } from '@/lib/site/format'
import { getAreaMap } from '@/lib/site/hubs'
import { getRegisterPlaces, getRegisterProjects, placePath, searchPlace, searchRegister } from '@/lib/site/register'
import type { RegisterPlace } from '@/lib/site/register'
import { enquiryName } from '@/lib/site/theme'
import type { PublicListing } from '@/lib/site/types'

export const revalidate = 300

export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata(getMarketingConfig(), {
    title: 'New projects in Pune, checked on MahaRERA',
    description: 'Every MahaRERA project in Kharadi, Wagholi, Lohegaon, Hinjawadi, Wakad, Baner and more: the completion date filed, homes booked, and prices quoted by local agents.',
    path: '/projects',
  })
}

type Props = { searchParams?: Promise<Record<string, string | string[] | undefined>> }

/** The live listings of every agent in the sitemap, by MahaRERA number: on this list an agent-listed project shows their sheet. */
async function agentOffers(): Promise<Map<string, AgentOffer>> {
  const entries = (await getSitemapEntries()).listings
  const slugs = Array.from(new Set(entries.filter((e) => e.rera_no).map((e) => e.agent_slug)))
  const out = new Map<string, AgentOffer>()
  for (const slug of slugs) {
    const [agent, { items }] = await Promise.all([getAgent(slug).catch(() => null), getListings(slug).catch(() => ({ items: [] as PublicListing[] }))])
    if (!agent) continue
    for (const l of items) {
      const regno = (l.rera_no || '').trim().toUpperCase()
      if (regno && !out.has(regno) && !isSampleListing(l.title)) out.set(regno, { agentName: enquiryName(agent), listing: l })
    }
  }
  return out
}

export default async function ProjectsPage({ searchParams }: Props) {
  const cfg = getMarketingConfig()
  const sp = (await searchParams) ?? {}
  // ?q= is the search box without JavaScript: answered here from the backend search
  const raw = sp.q
  const q = (Array.isArray(raw) ? raw[0] : raw ?? '').trim().slice(0, 80)
  const fq = parseQuery(sp)
  const [hits, place] = await Promise.all([q.length >= 2 ? searchRegister(q) : Promise.resolve([]), q.length >= 3 ? searchPlace(q) : Promise.resolve(null)])
  // the register holds all of Pune district; the finder is our covered areas, the rest is by place below
  const [all, places, offers] = await Promise.all([getRegisterProjects(undefined, true), getRegisterPlaces(), agentOffers()])
  const zones = places.reduce<[string, RegisterPlace[]][]>((acc, p) => {
    const last = acc[acc.length - 1]
    if (last && last[0] === p.zone) last[1].push(p)
    else acc.push([p.zone, [p]])
    return acc
  }, [])
  const ours = all.filter((r) => r.area && ((r.indexable && r.active !== false) || offers.has(r.regno.toUpperCase())))
  const finished = all.filter((r) => r.area && r.active === false).length
  const items = fromRegister(ours, offers)
  const mapData = fq.area ? await getAreaMap(fq.area.replace(/-/g, '_')).catch(() => null) : null
  const maps = mapData && fq.area ? { [fq.area]: { name: mapData.name, map: mapData.map, box: mapData.box, attribution: mapData.attribution } } : {}
  return (
    <MarketingShell search={false}>
      <div className="mx-auto max-w-5xl px-4 py-10 sm:py-14" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' },
        ])) }} />
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">New projects, checked on MahaRERA</h1>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800">
          For each project we show the price as quoted by a local agent, and what MahaRERA&apos;s public record says: the completion
          date the builder has filed, whether it has moved, and how many homes are booked. When the builder&apos;s own target is
          earlier than the MahaRERA date, we say so.
        </p>

        <ProjectSearch initialQ={q} initialHits={hits} initialPlace={place} />
        <p className="mt-3 text-slate-700">
          Already bought?{' '}
          <Link href="/check" className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">Check your project&apos;s possession date on MahaRERA</Link>
        </p>

        {/* the home finder (lib/site/finder), the same rules as an agent's site: our areas' projects, agent-listed first */}
        <div className="mt-10">
          <HomeFinder id="find" title="Find a project" q={fq} basePath="/projects" items={items} maps={maps}
            lead={{ agentSlug: process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu', agentName: BRAND_NAME }} />
          <p className="mt-4 max-w-3xl text-sm text-slate-600">
            {items.length} projects being built or just finished in our areas, each with its MahaRERA record and the date we read it.
            {finished > 0 && <> {finished} older, finished projects are left out; search finds them.</>}
          </p>
        </div>

        {zones.length > 0 && (
          <section aria-labelledby="pune-title" className="mt-14" data-testid="pune-places">
            <h2 id="pune-title" className="text-2xl font-bold text-slate-900">Projects across Pune, by area</h2>
            <p className="mt-2 max-w-3xl text-slate-700">
              Every MahaRERA project in Pune district, grouped by the area it is filed under ({all.length.toLocaleString('en-IN')} projects).
              Each area page lists its projects with the completion date filed with MahaRERA.
            </p>
            {zones.map(([zone, ps]) => (
              <div key={zone} className="mt-6">
                <h3 className="text-lg font-semibold text-slate-900">{zone}</h3>
                <ul className="mt-2 flex list-none flex-wrap gap-2 p-0">
                  {ps.map((p) => (
                    <li key={p.key}>
                      <Link href={placePath(p.slug)} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 bg-white px-3 text-[#0f2340] hover:border-[#0f2340]">
                        {p.name} <span className="ml-1 text-sm text-slate-500">{p.projects}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </section>
        )}

        <p className="mt-10 text-sm text-slate-600">
          Prices change often and are as quoted by the agent named on each project. MahaRERA facts are read from the public record on the
          date shown on each page. This is general information, not investment or legal advice.
        </p>
      </div>
    </MarketingShell>
  )
}
