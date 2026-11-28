import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getFacets } from '@/lib/site/facets'
import { getActive, type ActiveProject } from '@/lib/site/hubs'
import { getRegisterPlacesOrThrow, longDay, placePath, type RegisterPlace } from '@/lib/site/register'
import { getPlaceResearch, RESEARCH_KINDS, researchPath, type PlaceResearch, type ResearchKind } from '@/lib/site/research'
import { commuteJsonLd, researchHead, researchIndexable, rentJsonLd, schoolsJsonLd, uniqueSources, type ResearchHead } from '@/lib/site/researchPages'
import { BeingBuilt, ChangesList, CommuteTable, RentTable, SchoolsList } from './ResearchBlocks'

// A place's research pages beside its lists (/projects/area/<place>/schools, /commute, /rent; docs/plan/pune-intelligence.md C):
// one table of measured facts, a lead answer built from its numbers, the projects nearby, sources and the day measured. Up for
// visitors whenever the block exists; in search only when the backend says the block has enough (`pages.<kind>`).

export type ResearchProps = { params: Promise<{ place: string }> }

export interface Loaded { place: RegisterPlace; research: PlaceResearch; head: ResearchHead; path: string }

export async function loadResearch(kind: ResearchKind, params: ResearchProps['params']): Promise<Loaded | null> {
  const { place: slug } = await params
  const places = await getRegisterPlacesOrThrow()   // an outage is an error page, never a 404 for a real place
  const place = places.find((p) => p.slug === slug)
  if (!place) return null
  const got = await getPlaceResearch(place.slug)
  // the research could not be read: a temporary error (not kept), never a 404 that Google would drop the page for
  if (!got.ok) throw new Error('Research is temporarily unavailable')
  if (!got.data) return null
  const head = researchHead(kind, place.name, got.data)
  return head ? { place, research: got.data, head, path: researchPath(place.slug, kind) } : null
}

export async function researchMetadata(kind: ResearchKind, params: ResearchProps['params']): Promise<Metadata> {
  const got = await loadResearch(kind, params)
  if (!got) return { title: 'Page not found', robots: { index: false } }
  const meta = pageMetadata(getMarketingConfig(), { title: got.head.title, description: got.head.description, path: got.path })
  // a block with too little to say stays out of search until it has more (no thin pages indexed)
  return researchIndexable(kind, got.research) ? meta : { ...meta, robots: { index: false, follow: true } }
}

const LABEL: Record<ResearchKind, (place: string) => string> = {
  schools: (p) => `Schools in ${p}`, commute: (p) => `Commute from ${p}`, rent: (p) => `Rent in ${p}`,
}

const HOW: Record<ResearchKind, string> = {
  schools: "Schools from the boards' own lists of affiliated schools (named at the top), each placed on the map and "
    + 'measured in a straight line from the place centre. We show the board, the classes and the distance; no fees and no '
    + 'ratings, because fees are rarely published reliably and ratings are not ours to keep. Read again every three months.',
  commute: "Drive times are Google's typical traffic for a weekday leaving at 9 am, and coming back at 6 pm, from the place "
    + 'centre; a home at the edge of the place can be a few minutes either way. Distances are by road. Measured once a month.',
  rent: 'Asked rent is what owners ask on rental listings for the month shown, not what tenants end up paying. The range is the '
    + 'middle half of asks (a quarter ask less, a quarter more), counted only for sizes with 10 or more listings. Yield, when '
    + "shown, is a year's middle rent over the middle asking price for that size. Read again every month. Not investment advice.",
}

function JsonLd({ kind, got, siteUrl }: { kind: ResearchKind; got: Loaded; siteUrl: string }) {
  const { place, research: r, head, path } = got
  const b = r.blocks
  const updated = b[kind]?.updated
  const ld: Record<string, unknown>[] = [
    breadcrumbJsonLd(siteUrl, [{ name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' },
      { name: place.name, path: placePath(place.slug) }, { name: head.crumb, path }]),
    { '@context': 'https://schema.org', '@type': 'WebPage', name: head.title, url: siteUrl + path, ...(updated ? { dateModified: updated } : {}) },
  ]
  if (kind === 'schools' && b.schools) ld.push(schoolsJsonLd(siteUrl, path, head.h1, place.name, b.schools))
  if (kind === 'commute' && b.commute) ld.push(commuteJsonLd(siteUrl, path, head, place.name, b.commute))
  if (kind === 'rent' && b.rent) ld.push(rentJsonLd(siteUrl, path, head, place.name, b.rent))
  return <>{ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}</>
}

const LINK = 'inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]'

export function ResearchBody({ kind, got, nearby, topPath, siteUrl }: { kind: ResearchKind; got: Loaded; nearby: ActiveProject[]; topPath: string | null; siteUrl: string }) {
  const { place, research: r, head } = got
  const b = r.blocks
  const block = b[kind]
  const from = `from the ${place.name} centre`
  const sources = uniqueSources(block?.sources ?? [])
  const others = RESEARCH_KINDS.filter((k) => k !== kind && r.pages[k])
  return (
    <article className="mx-auto max-w-5xl px-4 py-8 sm:py-12" style={AVASETU_SITE_VARS} data-testid={`research-page-${kind}`}>
      <JsonLd kind={kind} got={got} siteUrl={siteUrl} />
      <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
        <Link href="/" className="text-[#0f2340] underline underline-offset-2">Home</Link>
        <span aria-hidden className="px-1 text-slate-400">/</span>
        <Link href="/projects" className="text-[#0f2340] underline underline-offset-2">Projects</Link>
        <span aria-hidden className="px-1 text-slate-400">/</span>
        <Link href={placePath(place.slug)} className="text-[#0f2340] underline underline-offset-2">{place.name}</Link>
        <span aria-hidden className="px-1 text-slate-400">/</span>
        <span>{head.crumb}</span>
      </nav>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{head.h1}</h1>
      <p className="mt-2 text-sm text-slate-600" data-testid="research-updated">
        Updated {longDay(block?.updated)}{sources.length ? ` · from ${sources.map((s) => s.name).join(', ')}` : ''}
      </p>
      {head.answer && <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800" data-testid="research-answer">{head.answer}</p>}

      <section aria-labelledby="table-title" className="mt-8">
        <h2 id="table-title" className="text-2xl font-bold text-slate-900">
          {kind === 'schools' ? `All ${b.schools?.schools.length ?? 0} schools, nearest first`
            : kind === 'commute' ? 'Drive times at 9 am and 6 pm' : 'Asked rent by flat size'}
        </h2>
        <div className="mt-3">
          {kind === 'schools' && <SchoolsList b={b.schools} from={from} limit={b.schools?.schools.length ?? 0} level={2} addresses />}
          {kind === 'commute' && <CommuteTable b={b.commute} from={from} level={2} />}
          {kind === 'rent' && <RentTable b={b.rent} level={2} />}
        </div>
      </section>

      {kind === 'commute' && r.changes.length > 0 && <div className="mt-10"><ChangesList changes={r.changes} heading={`Roads, metro and rules changing near ${place.name}`} /></div>}

      {(nearby.length > 0 || b.being_built) && (
        <section aria-labelledby="nearby-projects-title" className="mt-10" data-testid="research-projects">
          <h2 id="nearby-projects-title" className="text-xl font-semibold text-slate-900">Projects in {place.name}</h2>
          {nearby.length > 0 && (
            <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
              {nearby.map((a) => (
                <li key={a.slug}>
                  <Link href={`/projects/${a.slug}`} className="block min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
                    <span className="block font-semibold text-[#0f2340]">{a.name}</span>
                    <span className="text-sm text-slate-600">{a.fact}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {b.being_built && <div className="mt-6"><BeingBuilt b={b.being_built} /></div>}
        </section>
      )}

      <nav aria-label={`More on ${place.name}`} className="mt-10" data-testid="research-links">
        <h2 className="text-xl font-semibold text-slate-900">More on {place.name}</h2>
        <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
          <li><Link href={placePath(place.slug)} className={LINK}>All projects and flats in {place.name}</Link></li>
          {topPath && <li><Link href={topPath} className={LINK}>Top projects in {place.name}</Link></li>}
          {others.map((k) => <li key={k}><Link href={researchPath(place.slug, k)} className={LINK}>{LABEL[k](place.name)}</Link></li>)}
        </ul>
      </nav>

      <section aria-labelledby="how-title" className="mt-10">
        <h2 id="how-title" className="text-xl font-semibold text-slate-900">How this is measured</h2>
        <p className="mt-2 text-slate-800">{HOW[kind]} Every figure on this page is counted by code from the sources named, never written by a model.</p>
      </section>
    </article>
  )
}

export async function ResearchPage({ kind, params }: { kind: ResearchKind; params: ResearchProps['params'] }) {
  const got = await loadResearch(kind, params)
  if (!got) notFound()
  const [facets, nearby] = await Promise.all([getFacets().catch(() => []), getActive({ place: got.place.key }, 6).catch(() => [])])
  const top = facets.find((f) => f.place === got.place.key && f.intent === 'top' && !f.possession && !f.builder && !f.bhk && f.indexable)
  return (
    <MarketingShell hot={{ area: got.place.slug }}>
      <ResearchBody kind={kind} got={got} nearby={nearby} topPath={top?.path ?? null} siteUrl={getMarketingConfig().siteUrl} />
    </MarketingShell>
  )
}
