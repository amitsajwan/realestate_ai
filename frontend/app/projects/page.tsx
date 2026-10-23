import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import ProjectCard from '@/components/site/ProjectCard'
import ProjectSearch from '@/components/site/ProjectSearch'
import CheckBadge from '@/components/site/CheckBadge'
import { getMarketingConfig } from '@/lib/marketing/config'
import { LOCALITIES, localityByName } from '@/lib/marketing/localities'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { buyerEnquirePath } from '@/components/marketing/siteLinks'
import { getCatalog } from '@/lib/site/api'
import { byLocality } from '@/lib/site/projects'
import { displayName, getRegisterPlaces, getRegisterProjects, placePath, projectSummary, searchRegister } from '@/lib/site/register'
import type { RegisterListItem, RegisterPlace } from '@/lib/site/register'

export const revalidate = 300

export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata(getMarketingConfig(), {
    title: 'New projects in Pune, checked on MahaRERA',
    description: 'Every MahaRERA project in Kharadi, Wagholi, Lohegaon, Hinjawadi, Wakad, Baner and more: the completion date filed, homes booked, and prices quoted by local agents.',
    path: '/projects',
  })
}

const PER_AREA = 12

/** Biggest projects first (the ones most buyers look for), then by name. */
const byUnits = (a: RegisterListItem, b: RegisterListItem) => (b.units_total ?? 0) - (a.units_total ?? 0) || displayName(a).localeCompare(displayName(b))

type Props = { searchParams?: Promise<{ q?: string | string[] }> }

export default async function ProjectsPage({ searchParams }: Props) {
  const cfg = getMarketingConfig()
  // ?q= is the search box without JavaScript: answered here from the backend search
  const raw = (await searchParams)?.q
  const q = (Array.isArray(raw) ? raw[0] : raw ?? '').trim().slice(0, 80)
  const [catalog, hits] = await Promise.all([getCatalog(), q.length >= 2 ? searchRegister(q) : Promise.resolve([])])
  const groups = byLocality(catalog)
  const listed = new Set(catalog.map((p) => p.rera_no))
  // the register holds all of Pune district; the lists and search on this page are our covered areas, the rest is by place below
  const [all, places] = await Promise.all([getRegisterProjects(undefined, true), getRegisterPlaces()])
  const everything = all.filter((r) => r.area)
  const zones = places.reduce<[string, RegisterPlace[]][]>((acc, p) => {
    const last = acc[acc.length - 1]
    if (last && last[0] === p.zone) last[1].push(p)
    else acc.push([p.zone, [p]])
    return acc
  }, [])
  const register = everything.filter((r) => r.indexable && r.active !== false && !listed.has(r.regno))
  const finished = everything.filter((r) => r.active === false).length
  // each locality's Pune place hub (/projects/area/{place}) for the "All N projects" link
  const hubFor = (l: { key: string; name: string }) => places.find((p) => p.key === l.key || p.name.toLowerCase() === l.name.toLowerCase())
  const byArea = LOCALITIES.map((l) => ({ l, hub: hubFor(l), items: register.filter((r) => r.area === l.key).sort(byUnits) }))
    .filter((g) => g.items.length > 0)
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

        <ProjectSearch initialQ={q} initialHits={hits} />
        <p className="mt-3 text-slate-700">
          Already bought?{' '}
          <Link href="/check" className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">Check your project&apos;s possession date on MahaRERA</Link>
        </p>

        {groups.length === 0 ? (
          <p className="mt-8 rounded-xl bg-slate-50 p-4 text-slate-700">
            No projects are listed yet. <a href={buyerEnquirePath()} className="font-semibold text-[#0f2340] underline underline-offset-2">Tell us what you are looking for</a> and
            we will send you options as they come.
          </p>
        ) : groups.map(([locality, items]) => {
          const area = localityByName(locality)
          return (
            <section key={locality} aria-labelledby={`area-${locality}`} className="mt-10">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 id={`area-${locality}`} className="text-2xl font-bold text-slate-900">Projects in {locality}</h2>
                {area && (
                  <Link href={`/localities/${area.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">
                    {area.name} buyer guide
                  </Link>
                )}
              </div>
              <ul className="mt-4 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((p) => <li key={p.slug}><ProjectCard p={p} href={`/projects/${p.slug}`} /></li>)}
              </ul>
            </section>
          )
        })}

        {byArea.length > 0 && (
          <section aria-labelledby="register-title" className="mt-14">
            <h2 id="register-title" className="text-2xl font-bold text-slate-900">Every MahaRERA project in our areas</h2>
            <p className="mt-2 max-w-3xl text-slate-700">
              Our page for each project: the completion date filed with MahaRERA and how many homes are booked, with the date we read
              the record. {register.length} projects being built or just finished; new ones are added as MahaRERA lists them.
              {finished > 0 && <> {finished} older, finished projects are left out of these lists; search finds them.</>} Every page starts from MahaRERA;
              <span className="whitespace-nowrap"> <CheckBadge checked={4} total={4} compact /></span> means our crawler has also checked it
              against other sources (buildings, location, nearby places).
            </p>
            {byArea.map(({ l, hub, items }) => (
              <section key={l.key} aria-labelledby={`reg-${l.key}`} className="mt-6 rounded-xl border border-slate-200 bg-white p-4">
                <h3 id={`reg-${l.key}`} className="text-lg font-semibold text-slate-900">
                  {l.name} <span className="font-normal text-slate-600">· {items.length} projects</span>
                </h3>
                <ul className="mt-3 list-none columns-1 p-0 sm:columns-2" data-testid={`register-${l.key}`}>
                  {items.slice(0, PER_AREA).map((r: RegisterListItem) => (
                    <li key={r.slug} className="break-inside-avoid py-1.5">
                      <Link href={`/projects/${r.slug}`} className="font-medium text-[#0f2340] underline underline-offset-2">{displayName(r)}</Link>
                      {' '}<CheckBadge checked={r.checked} total={r.checks_total} compact />
                      <span className="block text-sm text-slate-600">{projectSummary(r)}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-2 flex flex-wrap gap-x-5">
                  {hub && <Link href={placePath(hub.slug)} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">All {items.length} projects in {l.name} →</Link>}
                  <Link href={`/localities/${l.slug}`} className="inline-flex min-h-[44px] items-center text-sm text-[#0f2340] underline underline-offset-2">{l.name} buyer guide</Link>
                </div>
              </section>
            ))}
          </section>
        )}

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
