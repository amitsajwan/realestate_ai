import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound, permanentRedirect } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import FacetChips from '@/components/site/FacetChips'
import { ListPicture, RailCard, RankedCard } from '@/components/site/ListCard'
import ProjectRail, { READY_SUB, READY_TITLE } from '@/components/site/ProjectRail'
import { getLocality } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getCatalog } from '@/lib/site/api'
import { facetFaq, getFacet, getFacetQuiet, getFacets, otherProjects, placeChips } from '@/lib/site/facets'
import type { FacetPage, FacetRow } from '@/lib/site/facets'
import { livePages } from '@/lib/site/filters'
import { fitDescription, formatPrice } from '@/lib/site/format'
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

// Over ~160 characters the date read (or price source) goes first, then the third and second project names, "Registration date",
// "MahaRERA's records" becomes "MahaRERA", and last the first name: the count, possession and bookings always stay
function description(p: FacetPage): string {
  const lows = p.rows.map((r) => r.price_from).filter((v): v is number => v != null)
  const names = (has: (n: number) => boolean) => {
    const shown = p.rows.slice(0, has(2) ? 3 : has(3) ? 2 : has(6) ? 1 : 0).map((r) => r.name).join(', ')
    return shown ? `: ${shown}` : ''
  }
  if (p.bhk && lows.length) {
    return fitDescription((has) => `${p.count} new projects in ${p.place.name}, Pune with ${p.bhk} BHK flats from ${formatPrice(Math.min(...lows))}${names(has)}. ${has(1) ? "Price from the builder's site, possession" : 'Possession'} filed with MahaRERA and homes booked.`)
  }
  const what = { 'new-launches': 'new launch projects and flats', top: 'top residential projects', 'ready-to-move': 'ready to move flats and projects', all: 'projects' }[p.intent]
  return fitDescription((has) => `${p.count} ${what} in ${p.place.name}, Pune ${has(5) ? "from MahaRERA's records" : 'on MahaRERA'}${names(has)}. ${has(4) ? 'Registration date, possession' : 'Possession'} filed and whether it moved, homes booked${has(1) ? `, read ${longDay(p.as_of)}` : ''}.`)
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

function Row({ r, priceList }: { r: FacetRow; priceList: boolean }) {
  const m = moved(r)
  return (
    <li className="overflow-hidden rounded-xl border border-slate-200 bg-white sm:grid sm:grid-cols-[220px_1fr]" data-testid="facet-row">
      <ListPicture r={r} rank={r.rank} tall />
      <div className="min-w-0 p-3 sm:p-4">
        <Link href={`/projects/${r.slug}`} className="text-lg font-semibold text-[#0f2340] underline underline-offset-2">{r.name}</Link>
        {r.promoter && (
          <span className="text-slate-700"> by {r.builder_slug ? <Link href={`/builders/${r.builder_slug}`} className="text-[#0f2340] underline underline-offset-2">{r.promoter}</Link> : r.promoter}</span>
        )}
        {/* on a size list the reason is the price, which the Price cell already shows */}
        {!priceList && <p className="mt-1 text-sm font-medium text-slate-800">{r.reason}</p>}
        <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-slate-700 sm:grid-cols-4">
          {r.price_from != null && <div><dt className="text-xs text-slate-500">Price</dt><dd><span className="font-semibold text-slate-900">{formatPrice(r.price_from)}{r.price_to ? ` to ${formatPrice(r.price_to)}` : ''}</span></dd></div>}
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

const TOP_CARDS = 10

// "Sold out or nearly": a project that cannot be bought from the builder stays findable, with a way to ask about resale
function SoldOut({ p }: { p: FacetPage }) {
  const rows = p.sold_out ?? []
  if (!rows.length) return null
  return (
    <section aria-labelledby="soldout-title" className="mt-10 rounded-2xl bg-slate-100 p-4 sm:p-5" data-testid="facet-sold-out">
      <h2 id="soldout-title" className="text-xl font-semibold text-slate-900">Sold out or nearly: {p.sold_out_count ?? rows.length} project{(p.sold_out_count ?? rows.length) === 1 ? '' : 's'}</h2>
      <p className="mt-1 text-sm text-slate-700">Fewer than 10 homes left with the builder, as MahaRERA shows. A resale flat or a cancelled booking can still come up.</p>
      <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead><tr className="text-xs text-slate-500"><th className="px-3 py-2 font-semibold">Project</th><th className="px-3 py-2 font-semibold">Builder</th><th className="px-3 py-2 font-semibold">Booked</th><th className="px-3 py-2 font-semibold">Possession filed</th><th className="px-3 py-2"><span className="sr-only">Ask</span></th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.slug} className="border-t border-slate-200">
                <td className="px-3 py-2"><Link href={`/projects/${r.slug}`} className="font-semibold text-[#0f2340] underline underline-offset-2">{r.name}</Link></td>
                <td className="px-3 py-2 text-slate-700">{r.promoter ?? ''}</td>
                <td className="px-3 py-2">{r.units_booked != null && r.units_total ? `${n(r.units_booked)} of ${n(r.units_total)}` : ''}</td>
                <td className="px-3 py-2 text-slate-700">{monthYear(r.completion_now)}</td>
                <td className="px-3 py-2 text-right"><Link href={`/projects/${r.slug}#enquire`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">Ask about resale</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

const HOW: Record<string, string> = {
  'new-launches': 'Projects registered with MahaRERA in the last 12 months, newest first.',
  top: 'Projects still being built or finished within a year that have 10 or more homes not booked and 40 or more homes in all, one row per project, ranked by homes booked in the last 90 days where two of our readings of MahaRERA show it, else by homes booked a month since registration (a project registered under six months counts as six months old). Each row says whether the builder moved the completion date and how many of the builder\'s Pune projects kept theirs. Booked counts are the builders\' own, filed on MahaRERA each quarter. Projects with fewer homes open are listed apart, never ranked. Offices and shops are left out.',
  'ready-to-move': 'Projects whose completion date filed with MahaRERA passed in the last three years and that still have 10 or more homes not booked, newest first. Offices and shops are left out. MahaRERA does not show the occupancy certificate, so ask the builder for it.',
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
    && f.possession === p.possession && (f.bhk ?? null) === (p.bhk ?? null) && !f.builder).slice(0, 8)
  const placeName = (key: string) => places.find((x) => x.key === key)?.name ?? key
  const faq = facetFaq(p)
  // the Top list is the buyer's shortlist: ranked cards, then rows into the other lists of the place, then the sold out ones
  const top = p.intent === 'top' && !p.bhk && !p.possession && !p.builder
  const [launches, ready, twoBhk] = top
    ? await Promise.all([getFacetQuiet(p.place.slug, ['new-launches']), getFacetQuiet(p.place.slug, ['ready-to-move']), getFacetQuiet(p.place.slug, ['2-bhk'])])
    : [null, null, null]
  // the size list holds only projects with a checked price for that size: the others still being sold follow it, marked as such
  const sizeList = !!p.bhk && p.intent === 'all' && !p.possession && !p.builder
  const others = sizeList ? otherProjects(await getFacetQuiet(p.place.slug, ['top']), p) : []
  const cards = top ? p.rows.slice(0, TOP_CARDS) : []
  const rest = top ? p.rows.slice(TOP_CARDS) : p.rows
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
    <MarketingShell hot={{ area: p.place.slug }}>
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

        {cards.length > 0 && (
          <section aria-labelledby="top-title" className="mt-8">
            <h2 id="top-title" className="text-2xl font-bold text-slate-900">Top {cards.length} you can still buy</h2>
            <p className="text-sm text-slate-600">Most homes booked first (booked lately, where MahaRERA shows it), among projects with 10 or more homes open</p>
            <ol className="mt-3 grid list-none gap-4 p-0" data-testid="facet-cards">
              {cards.map((r) => <RankedCard key={r.slug} r={r} />)}
            </ol>
          </section>
        )}

        {top && (
          <>
            <ProjectRail id="launches" title="Just launched" sub="Registered with MahaRERA in the last 12 months" href={launches?.path ?? ''} count={launches?.count ?? 0} rows={launches?.rows ?? []} />
            <ProjectRail id="ready" title={READY_TITLE} sub={READY_SUB} href={ready?.path ?? ''} count={ready?.count ?? 0} rows={ready?.rows ?? []} />
            <ProjectRail id="two-bhk" title="2 BHK, cheapest first" sub="Prices from the builder's site or two property sites that agree" href={twoBhk?.path ?? ''} count={twoBhk?.count ?? 0} rows={twoBhk?.rows ?? []} />
          </>
        )}

        {rest.length > 0 ? (
          <section aria-labelledby="list-title" className="mt-8">
            <h2 id="list-title" className="text-2xl font-bold text-slate-900">{top
              ? `More projects with homes open (${rest.length})`
              : <>{p.count} project{p.count === 1 ? '' : 's'}{p.count > p.rows.length ? `, first ${p.rows.length}` : ''}</>}</h2>
            <ol className="mt-3 grid list-none gap-3 p-0" data-testid="facet-rows">
              {rest.map((r) => <Row key={r.slug} r={r} priceList={!!p.bhk && p.intent === 'all'} />)}
            </ol>
          </section>
        ) : cards.length > 0 ? null : (
          <p className="mt-8 rounded-xl bg-slate-50 p-4 text-slate-700">No project matches this list in MahaRERA&apos;s records right now.</p>
        )}

        {others.length > 0 && (
          <section aria-labelledby="others-title" className="mt-10" data-testid="facet-others">
            <h2 id="others-title" className="text-xl font-bold text-slate-900">More projects being sold in {p.place.name} ({others.length})</h2>
            <p className="text-sm text-slate-600">We have no checked {p.bhk} BHK price for these, and MahaRERA does not show home sizes, so ask whether they have {p.bhk} BHK homes.</p>
            <ul className="mt-3 grid list-none gap-3 p-0 sm:grid-cols-2 lg:grid-cols-3">
              {others.map((r) => <li key={r.slug}><RailCard r={r} /></li>)}
            </ul>
          </section>
        )}

        {top && <SoldOut p={p} />}

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
            {p.bhk ? `Only projects with a ${p.bhk} BHK price (${p.bhk}.5 BHK counts) that the builder's own site states, or that two property sites agree on, read in the last 45 days. ` : ''}
            {p.bhk && p.intent === 'all' ? 'Projects still being sold, cheapest first.' : HOW[p.intent]}{p.possession ? ` Only projects whose filed completion date is in ${p.possession}.` : ''}{p.builder_name ? ` Only projects by ${p.builder_name}.` : ''}{' '}
            Towers and phases of one project count once. From {p.source}, worked out on {longDay(p.as_of)}; each project&apos;s page shows the
            date we read its record. No builder pays to be on this list. This is general information, not investment or legal advice.
          </p>
        </section>
      </article>
    </MarketingShell>
  )
}
