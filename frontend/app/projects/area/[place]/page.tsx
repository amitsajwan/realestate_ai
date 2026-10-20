import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import ActiveProjects from '@/components/site/ActiveProjects'
import CheckBadge from '@/components/site/CheckBadge'
import FacetChips from '@/components/site/FacetChips'
import { getLocality } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getCatalog } from '@/lib/site/api'
import { getFacets, placeChips } from '@/lib/site/facets'
import { livePages } from '@/lib/site/filters'
import { getActive } from '@/lib/site/hubs'
import { displayName, getRegisterPlaces, getRegisterProjects, placePath, projectSummary, STAGE_LABEL, STAGE_NOTE, STAGES } from '@/lib/site/register'
import type { RegisterListItem, RegisterPlace } from '@/lib/site/register'

export const revalidate = 300

type Props = { params: Promise<{ place: string }> }

async function load(slug: string): Promise<{ place: RegisterPlace; projects: RegisterListItem[] } | null> {
  const places = await getRegisterPlaces()
  const place = places.find((p) => p.slug === slug)
  if (!place) return null
  const projects = await getRegisterProjects(undefined, true, place.key)
  return { place, projects }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { place: slug } = await params
  const got = await load(slug)
  if (!got) return { title: 'Projects in Pune' }
  const { place } = got
  // once the place has its own New launches page, that page answers "new projects in <place>" and this one is the full list
  // (docs/plan/area-intent-pages.md section 5): two of our pages never aim at the same search
  const launches = (await getFacets()).some((f) => f.place === place.key && f.intent === 'new-launches' && !f.possession && !f.builder && f.indexable)
  const meta = pageMetadata(getMarketingConfig(), {
    title: launches ? `Residential Projects in ${place.name}, Pune: all ${place.projects} on MahaRERA`
      : `New Projects in ${place.name}, Pune: Price, Possession, MahaRERA (${place.projects})`,
    description: `All ${place.projects} MahaRERA projects in ${place.name}, Pune: builder, possession date filed with MahaRERA, whether it moved, and homes booked, for each project.`,
    path: placePath(place.slug),
  })
  // an area with no project that has real facts yet stays out of search until it has one
  return place.indexable > 0 ? meta : { ...meta, robots: { index: false, follow: true } }
}

function Row({ r }: { r: RegisterListItem }) {
  return (
    <li className="break-inside-avoid py-1.5">
      <Link href={`/projects/${r.slug}`} className="font-medium text-[#0f2340] underline underline-offset-2">{displayName(r)}</Link>
      {' '}<CheckBadge checked={r.checked} total={r.checks_total} compact />
      <span className="block text-sm text-slate-600">{projectSummary(r)}</span>
    </li>
  )
}

export default async function PlaceProjectsPage({ params }: Props) {
  const { place: slug } = await params
  const got = await load(slug)
  if (!got) notFound()
  const { place, projects } = got
  const cfg = getMarketingConfig()
  const [active, facets, catalog] = await Promise.all([getActive({ place: place.key }), getFacets(), getCatalog().catch(() => [])])
  const chips = placeChips(place, facets, livePages(catalog), getLocality(place.slug) ? `/localities/${place.slug}` : null)
  const launches = facets.some((f) => f.place === place.key && f.intent === 'new-launches' && !f.possession && !f.builder && f.indexable)
  const building = projects.filter((r) => r.active !== false && !r.sold_out).sort((a, b) => displayName(a).localeCompare(displayName(b)))
  const soldOut = projects.filter((r) => r.active !== false && r.sold_out).sort((a, b) => displayName(a).localeCompare(displayName(b)))
  // Housiey-style stage groups (docs/plan/project-pages.md): by dates, with the ones we cannot place last
  const groups = [...STAGES.map((st) => ({ key: st, title: STAGE_LABEL[st], items: building.filter((r) => r.stage === st) })),
    { key: 'unknown', title: 'Dates not read yet', items: building.filter((r) => !r.stage) }].filter((g) => g.items.length > 0)
  const finished = projects.filter((r) => r.active === false).sort((a, b) => displayName(a).localeCompare(displayName(b)))
  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl px-4 py-10 sm:py-14" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' }, { name: place.name, path: placePath(place.slug) },
        ])) }} />
        <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
          <Link href="/projects" className="text-[#0f2340] underline underline-offset-2">Projects</Link>
          <span aria-hidden className="px-1 text-slate-400">/</span> {place.zone}
        </nav>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{launches ? 'Residential projects' : 'New projects'} in {place.name}, Pune</h1>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800">
          Every project MahaRERA lists in {place.name}: {building.length + soldOut.length} being built or recently finished
          {finished.length > 0 ? `, and ${finished.length} older ones` : ''}. Each page shows the completion date the builder filed with
          MahaRERA, whether it has moved, and how many homes are booked, with the date we read the record.
        </p>

        <FacetChips chips={chips} current={placePath(place.slug)} label={`Lists for ${place.name}`} />

        <ActiveProjects title={`Most active projects in ${place.name}`} items={active} className="mt-10" />

        {building.length > 0 && (
          <section aria-labelledby="building-title" className="mt-10">
            <h2 id="building-title" className="text-2xl font-bold text-slate-900">Being built ({building.length})</h2>
            {groups.length > 1 && (
              <nav aria-label="Stages" className="mt-3 flex flex-wrap gap-2">
                {groups.map((g) => (
                  <a key={g.key} href={`#stage-${g.key}`} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 bg-white px-4 text-sm font-semibold text-[#0f2340] no-underline">
                    {g.title} ({g.items.length})
                  </a>
                ))}
              </nav>
            )}
            <div data-testid="place-projects">
              {groups.map((g) => (
                <div key={g.key} id={`stage-${g.key}`} className="mt-6 scroll-mt-20">
                  <h3 className="text-lg font-semibold text-slate-900">{g.title} ({g.items.length})</h3>
                  <ul className="mt-2 list-none columns-1 p-0 sm:columns-2">
                    {g.items.map((r) => <Row key={r.slug} r={r} />)}
                  </ul>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-slate-600">{STAGE_NOTE}</p>
          </section>
        )}
        {soldOut.length > 0 && (
          <details className="mt-8 rounded-xl border border-slate-200 bg-white p-4" data-testid="sold-out">
            <summary className="flex min-h-[44px] cursor-pointer items-center text-lg font-semibold text-slate-900">
              Sold out on MahaRERA ({soldOut.length})
            </summary>
            <ul className="mt-3 list-none columns-1 p-0 sm:columns-2">
              {soldOut.map((r) => <Row key={r.slug} r={r} />)}
            </ul>
          </details>
        )}
        {finished.length > 0 && (
          <details className="mt-8 rounded-xl border border-slate-200 bg-white p-4">
            <summary className="flex min-h-[44px] cursor-pointer items-center text-lg font-semibold text-slate-900">
              Finished more than a year ago ({finished.length})
            </summary>
            <ul className="mt-3 list-none columns-1 p-0 sm:columns-2">
              {finished.map((r) => <Row key={r.slug} r={r} />)}
            </ul>
          </details>
        )}
        {projects.length === 0 && <p className="mt-8 rounded-xl bg-slate-50 p-4 text-slate-700">No projects are in our register here yet.</p>}

        <p className="mt-10 text-sm text-slate-600">
          From MahaRERA&apos;s public records, read on the date shown on each project&apos;s page. A project is listed under the area of the
          pincode it is filed under. This is general information, not investment or legal advice.
        </p>
      </div>
    </MarketingShell>
  )
}
