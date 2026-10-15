import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound, permanentRedirect } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import FacetChips from '@/components/site/FacetChips'
import { getLocality } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getCatalog } from '@/lib/site/api'
import { facetFaq, getFacet, getFacets, placeChips } from '@/lib/site/facets'
import type { FacetPage, FacetRow } from '@/lib/site/facets'
import { livePages } from '@/lib/site/filters'
import { getRegisterPlaces, longDay, monthYear, placePath } from '@/lib/site/register'

// Area list pages (docs/plan/area-intent-pages.md): New launches, Top projects, Ready to move, Possession <year>, by builder, for
// any Pune place. The backend makes a page live only when people search for it and enough projects match (seo/grow.py); anything
// else is a 404. Rendered on first visit, then kept for 5 minutes, like the place pages.
export const revalidate = 300
export const dynamicParams = true
export async function generateStaticParams(): Promise<{ place: string; facet: string[] }[]> {
  return []
}

type Props = { params: Promise<{ place: string; facet: string[] }> }

async function load(params: Props['params']): Promise<FacetPage | null> {
  const { place, facet } = await params
  const got = await getFacet(place, facet)
  if (got && 'redirect_to' in got) permanentRedirect(got.redirect_to)
  return got
}

function description(p: FacetPage): string {
  const names = p.rows.slice(0, 3).map((r) => r.name).join(', ')
  return `${p.count} projects in ${p.place.name}, Pune from MahaRERA's records${names ? `: ${names}` : ''}. Registration date, possession filed and whether it moved, homes booked, read ${longDay(p.as_of)}.`.slice(0, 300)
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const p = await load(params)
  if (!p) return { title: 'List not found', robots: { index: false } }
  const meta = pageMetadata(getMarketingConfig(), { title: p.title, description: description(p), path: p.path })
  // under three projects, or held by the owner: a thin list stays out of search until it has more
  return p.indexable ? meta : { ...meta, robots: { index: false, follow: true } }
}

const n = (v: number | null | undefined) => (v == null ? null : v.toLocaleString('en-IN'))

function moved(r: FacetRow): string | null {
  if (!r.completion_now || !r.completion_at_registration || monthYear(r.completion_now) === monthYear(r.completion_at_registration)) return null
  return `moved from ${monthYear(r.completion_at_registration)}`
}

function Row({ r }: { r: FacetRow }) {
  const m = moved(r)
  return (
    <li className="flex gap-3 rounded-xl border border-slate-200 bg-white p-3 sm:p-4">
      <span aria-hidden className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-sm font-bold text-[#0f2340]">{r.rank}</span>
      <div className="min-w-0">
        <Link href={`/projects/${r.slug}`} className="text-lg font-semibold text-[#0f2340] underline underline-offset-2">{r.name}</Link>
        {r.promoter && (
          <span className="text-slate-700"> by {r.builder_slug ? <Link href={`/builders/${r.builder_slug}`} className="text-[#0f2340] underline underline-offset-2">{r.promoter}</Link> : r.promoter}</span>
        )}
        <p className="mt-1 text-sm font-medium text-slate-800">{r.reason} <span className="font-normal text-slate-500">({r.source})</span></p>
        <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-slate-700 sm:grid-cols-4">
          {r.registered_on && <div><dt className="text-xs text-slate-500">Registered</dt><dd>{monthYear(r.registered_on)}</dd></div>}
          {r.completion_now && <div><dt className="text-xs text-slate-500">Possession filed</dt><dd>{monthYear(r.completion_now)}{m ? <span className="block text-xs text-amber-800">{m}</span> : null}</dd></div>}
          {r.units_total != null && <div><dt className="text-xs text-slate-500">Homes</dt><dd>{n(r.units_total)}</dd></div>}
          {r.units_booked != null && r.units_total ? <div><dt className="text-xs text-slate-500">Booked</dt><dd>{n(r.units_booked)} ({Math.round((100 * r.units_booked) / r.units_total)}%)</dd></div> : null}
        </dl>
        <p className="mt-1 text-xs text-slate-500">MahaRERA {r.regno}{r.legal_name && r.legal_name.toLowerCase() !== r.name.toLowerCase() ? ` · registered as ${r.legal_name}` : ''}</p>
      </div>
    </li>
  )
}

const HOW: Record<string, string> = {
  'new-launches': 'Projects registered with MahaRERA in the last 12 months, newest first.',
  top: 'Projects still being built or finished within a year, ranked by homes booked in the last 90 days as MahaRERA shows them, then by the share of homes booked.',
  'ready-to-move': 'Projects whose completion date filed with MahaRERA passed in the last three years, newest first. MahaRERA does not show the occupancy certificate, so ask the builder for it.',
  all: 'Projects still being built, earliest filed completion date first.',
}

export default async function FacetPageView({ params }: Props) {
  const p = await load(params)
  if (!p) notFound()
  const cfg = getMarketingConfig()
  const [all, catalog, places] = await Promise.all([getFacets(), getCatalog().catch(() => []), getRegisterPlaces()])
  const guide = getLocality(p.place.slug) ? `/localities/${p.place.slug}` : null
  const chips = placeChips(p.place, all, livePages(catalog), guide)
  const zone = places.find((x) => x.key === p.place.key)?.zone
  const zoneKeys = new Set(places.filter((x) => x.zone === zone).map((x) => x.key))
  const nearby = all.filter((f) => f.indexable && f.place !== p.place.key && zoneKeys.has(f.place) && f.intent === p.intent
    && f.possession === p.possession && !f.builder).slice(0, 8)
  const placeName = (key: string) => places.find((x) => x.key === key)?.name ?? key
  const faq = facetFaq(p)
  const ld = [
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' },
      { name: p.place.name, path: placePath(p.place.slug) }, { name: p.h1, path: p.path }]),
    { '@context': 'https://schema.org', '@type': 'ItemList', name: p.h1, numberOfItems: p.rows.length,
      itemListElement: p.rows.map((r) => ({ '@type': 'ListItem', position: r.rank, url: `${cfg.siteUrl}/projects/${r.slug}`, name: r.name })) },
    { '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })) },
    { '@context': 'https://schema.org', '@type': 'WebPage', name: p.title, url: cfg.siteUrl + p.path,
      ...(p.page_updated ? { dateModified: p.page_updated } : {}) },
  ]
  return (
    <MarketingShell>
      <article className="mx-auto max-w-5xl px-4 py-8 sm:py-12" style={AVASETU_SITE_VARS}>
        {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
        <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
          <Link href="/projects" className="text-[#0f2340] underline underline-offset-2">Projects</Link>
          <span aria-hidden className="px-1 text-slate-400">/</span>
          <Link href={placePath(p.place.slug)} className="text-[#0f2340] underline underline-offset-2">{p.place.name}</Link>
        </nav>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{p.h1}</h1>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800" data-testid="facet-answer">{p.answer}</p>
        <FacetChips chips={chips} current={p.path} label={`Lists for ${p.place.name}`} />

        {p.rows.length > 0 ? (
          <section aria-labelledby="list-title" className="mt-8">
            <h2 id="list-title" className="text-2xl font-bold text-slate-900">{p.count} project{p.count === 1 ? '' : 's'}{p.count > p.rows.length ? `, first ${p.rows.length}` : ''}</h2>
            <ol className="mt-3 grid list-none gap-3 p-0" data-testid="facet-rows">
              {p.rows.map((r) => <Row key={r.slug} r={r} />)}
            </ol>
          </section>
        ) : (
          <p className="mt-8 rounded-xl bg-slate-50 p-4 text-slate-700">No project matches this list in MahaRERA&apos;s records right now.</p>
        )}

        {p.changes.length > 0 && (
          <section aria-labelledby="changes-title" className="mt-10">
            <h2 id="changes-title" className="text-xl font-semibold text-slate-900">What changed in the last month</h2>
            <ul className="mt-3 list-none space-y-2 p-0">
              {p.changes.map((c, i) => (
                <li key={i} className="text-slate-800">
                  <span className="text-sm text-slate-500">{longDay(c.at)}:</span>{' '}
                  <Link href={`/projects/${c.slug}`} className="text-[#0f2340] underline underline-offset-2">{c.text}</Link>{' '}
                  <span className="text-sm text-slate-500">({c.source})</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {p.intent === 'new-launches' && (
          <section aria-labelledby="prelaunch-title" className="mt-10 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5">
            <h2 id="prelaunch-title" className="text-xl font-semibold text-slate-900">Pre-launch offers in {p.place.name}: what is allowed</h2>
            <p className="mt-2 text-slate-800">
              Under RERA, a builder may not advertise, book or sell homes in a project before it is registered with MahaRERA. A
              &quot;pre-launch&quot; price for an unregistered project has no MahaRERA protection. Every project above is registered: the
              newest ones are where launch prices usually are. Check the MahaRERA number before you pay a booking amount.
            </p>
          </section>
        )}

        <section aria-labelledby="faq-title" className="mt-10">
          <h2 id="faq-title" className="text-xl font-semibold text-slate-900">Questions buyers ask</h2>
          <dl className="mt-3 space-y-4">
            {faq.map((f) => (
              <div key={f.q}>
                <dt className="font-semibold text-slate-900">{f.q}</dt>
                <dd className="mt-1 text-slate-800">{f.a}</dd>
              </div>
            ))}
          </dl>
        </section>

        {nearby.length > 0 && (
          <section aria-labelledby="nearby-title" className="mt-10">
            <h2 id="nearby-title" className="text-xl font-semibold text-slate-900">The same list near {p.place.name}</h2>
            <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
              {nearby.map((f) => (
                <li key={f.path}>
                  <Link href={f.path} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]">
                    {placeName(f.place)} ({f.count})
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section aria-labelledby="how-title" className="mt-10">
          <h2 id="how-title" className="text-xl font-semibold text-slate-900">How this list is made</h2>
          <p className="mt-2 text-slate-800">
            {HOW[p.intent]}{p.possession ? ` Only projects whose filed completion date is in ${p.possession}.` : ''}{p.builder_name ? ` Only projects by ${p.builder_name}.` : ''}{' '}
            Towers and phases of one project count once. From {p.source}, worked out on {longDay(p.as_of)}; each project&apos;s page shows the
            date we read its record. No builder pays to be on this list. This is general information, not investment or legal advice.
          </p>
        </section>
      </article>
    </MarketingShell>
  )
}
