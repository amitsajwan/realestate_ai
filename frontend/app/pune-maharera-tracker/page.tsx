import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import { type AreaStats, type CityStats, type DateMoves, type RecordLinks, getCityStats, longDate, recordLinks } from '@/components/localities/areaStats'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { fixturesForced } from '@/lib/site/api'
import { getFacets } from '@/lib/site/facets'
import { getRegisterPlaces } from '@/lib/site/register'
import { areaGuidePath } from '@/lib/site/areaGuide'

/** Pune's new-home projects by area, from MahaRERA's public records, kept current by the register refresh. A page others can
 *  cite and link to: facts only, each area linked to its guide, a ready-made citation. Rendered per request (the figures are
 *  cached 5 minutes): built statically, the image build (which cannot reach the API) baked in the noindex page, served to the
 *  first reader after every deploy. */
export const dynamic = 'force-dynamic'
const PATH = '/pune-maharera-tracker'
const TITLE = 'Pune MahaRERA tracker: new home projects by area'
const DESCRIPTION = 'How many MahaRERA-registered projects each Pune area has, how many homes are booked, when projects are due to complete and how many builders moved their possession date. From MahaRERA public records, updated as they change.'

/** The figures, or an error page when none have been read since the site started: Google reads a 5xx again later, while a
 *  noindex it happens to read drops the page from search. Only fixture mode (no API at all) shows the empty, noindex page. */
async function figures(): Promise<CityStats | null> {
  const city = await getCityStats()
  if (!city && !fixturesForced()) throw new Error('Tracker figures are temporarily unavailable')
  return city
}

export async function generateMetadata(): Promise<Metadata> {
  const meta = pageMetadata(getMarketingConfig(), { title: TITLE, description: DESCRIPTION, path: PATH })
  return (await figures()) ? meta : { ...meta, robots: { index: false, follow: true } }
}

const fmt = (n: number) => n.toLocaleString('en-IN')

function due(a: AreaStats, year: number): number {
  return a.completing.find((c) => c.year === year)?.projects ?? 0
}

/** A count, linked to the list it counts when that page exists (the list gives its own, current count). */
function Count({ value, href, label }: { value: number; href?: string | null; label: string }) {
  if (!href || value === 0) return <>{fmt(value)}</>
  return <a href={href} aria-label={label} className="text-[#0f2340] underline underline-offset-2">{fmt(value)}</a>
}

const months = (m: number) => `${m} month${m === 1 ? '' : 's'}`

/** Possession dates that moved, area by area (docs/plan/visibility-base.md step 3): the figure only our dated readings of
 *  MahaRERA give, set out so a journalist can quote it. The builder's own moves only: MahaRERA's 2026 blanket extension is
 *  counted apart, never as a move. */
function DateMovesReport({ city, asOf }: { city: CityStats; asOf: string }) {
  const rows = city.areas.filter((a) => a.date_moves && a.date_moves.with_dates > 0)
  if (!rows.length) return null
  const sum = (k: 'with_dates' | 'moved' | 'extension_only') => rows.reduce((s, a) => s + (a.date_moves?.[k] ?? 0), 0)
  const all = sum('with_dates')
  const moved = sum('moved')
  const biggest = rows.flatMap((a) => (a.date_moves?.biggest ?? []).map((b) => ({ ...b, area: a.area.name })))
    .sort((x, y) => y.months - x.months || x.name.localeCompare(y.name)).slice(0, 8)
  return (
    <section className="mt-10" aria-labelledby="moves" data-testid="date-moves">
      <h2 id="moves" className="text-2xl font-semibold text-slate-900">Possession dates that moved</h2>
      <p className="mt-2 text-slate-700" data-testid="date-moves-answer">
        As of {asOf}, the builders of {fmt(moved)} of {fmt(all)} home projects still being built in these areas ({all ? Math.round((100 * moved) / all) : 0}%)
        have moved their filed completion date 3 months or more later than at registration, not counting the 4 months MahaRERA
        added to most projects in August 2026 (Order 66/2026).
      </p>
      <div className="mt-4 overflow-x-auto rounded-2xl border border-slate-200">
        <table className="w-full min-w-[560px] border-collapse text-left text-sm">
          <caption className="sr-only">Home projects being built whose possession date moved, by Pune area, as of {asOf}</caption>
          <thead className="bg-[#fbf6ea] text-slate-900">
            <tr>
              <th scope="col" className="p-3 font-semibold">Area</th>
              <th scope="col" className="p-3 text-right font-semibold">Being built</th>
              <th scope="col" className="p-3 text-right font-semibold">Moved by the builder</th>
              <th scope="col" className="p-3 text-right font-semibold">Usual move</th>
              <th scope="col" className="p-3 text-right font-semibold">Only MahaRERA&apos;s extension</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => {
              const m = a.date_moves as DateMoves
              return (
                <tr key={a.area.key} className="border-t border-slate-200">
                  <th scope="row" className="p-3 font-medium"><Link href={areaGuidePath(a.area.slug)} className="text-[#0f2340] underline underline-offset-2">{a.area.name}</Link></th>
                  <td className="p-3 text-right">{fmt(m.with_dates)}</td>
                  <td className="p-3 text-right">{fmt(m.moved)}{m.with_dates ? ` (${Math.round((100 * m.moved) / m.with_dates)}%)` : ''}</td>
                  <td className="p-3 text-right">{m.median_months != null ? months(m.median_months) : '–'}</td>
                  <td className="p-3 text-right">{fmt(m.extension_only)}</td>
                </tr>
              )
            })}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-slate-300 font-semibold">
              <th scope="row" className="p-3">All areas</th>
              <td className="p-3 text-right">{fmt(all)}</td>
              <td className="p-3 text-right">{fmt(moved)}{all ? ` (${Math.round((100 * moved) / all)}%)` : ''}</td>
              <td className="p-3 text-right" />
              <td className="p-3 text-right">{fmt(sum('extension_only'))}</td>
            </tr>
          </tfoot>
        </table>
      </div>
      <p className="mt-2 text-sm text-slate-600">&ldquo;Usual move&rdquo; is the middle move among the projects whose date moved. Each project counts once, however many towers it registered.</p>
      {biggest.length > 0 && (
        <>
          <h3 className="mt-6 text-lg font-semibold text-slate-900">The biggest moves</h3>
          <ul className="mt-2 list-none space-y-2 p-0">
            {biggest.map((b) => (
              <li key={b.regno} className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-800">
                {b.page ? <Link href={b.page} className="font-semibold text-[#0f2340] underline underline-offset-2">{b.name}</Link> : <span className="font-semibold">{b.name}</span>}
                {' '}({b.area}): filed for {longDate(b.from)} at registration, now {longDate(b.to)}, {months(b.months)} later by the builder
                <span className="block text-xs text-slate-500">MahaRERA {b.regno}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}

export default async function TrackerPage() {
  const cfg = getMarketingConfig()
  const city = await figures()
  const [places, facets] = city ? await Promise.all([getRegisterPlaces(), getFacets()]) : [[], []]
  const links = new Map<string, RecordLinks>((city?.areas ?? []).map((a) => [a.area.key, recordLinks(a.area, places, facets)]))
  const url = cfg.siteUrl + PATH
  const year = city ? Number(city.asOf.slice(0, 4)) : new Date().getFullYear()
  const asOf = city ? longDate(city.asOf) : ''
  const total = city ? city.areas.reduce((s, a) => s + a.projects, 0) : 0
  const allUnits = !!city && city.areas.every((a) => a.units_total !== null)
  const dataset = city && {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: TITLE,
    description: DESCRIPTION,
    url,
    creator: { '@type': 'Organization', name: cfg.businessName, url: cfg.siteUrl },
    isBasedOn: 'https://maharera.maharashtra.gov.in/',
    spatialCoverage: { '@type': 'Place', name: 'Pune, Maharashtra, India' },
    dateModified: city.asOf,
    isAccessibleForFree: true,
    variableMeasured: ['MahaRERA-registered projects', 'Homes registered', 'Homes booked', 'Projects due to complete by year', 'Projects whose possession date the builder moved'],
  }
  return (
    <MarketingShell>
      <article className="mx-auto max-w-4xl px-4 py-10 sm:py-14">
        {dataset && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(dataset) }} />}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Area guides', path: '/localities' }, { name: 'Pune MahaRERA tracker', path: PATH },
        ])) }} />
        <p className="text-sm"><Link href="/localities" className="text-[#0f2340] underline underline-offset-2">All area guides</Link></p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Pune MahaRERA tracker</h1>
        <p className="mt-3 text-lg leading-relaxed text-slate-700">New home projects registered with MahaRERA in the Pune areas we cover: how many there are, how many homes are booked and when they are due to complete.</p>
        {!city ? (
          <p className="mt-8 rounded-xl bg-amber-50 p-4 text-amber-900">The figures are being refreshed. Please check back shortly.</p>
        ) : (
          <>
            <p className="mt-2 text-sm text-slate-600">As of <time dateTime={city.asOf}>{asOf}</time>. Source: {city.source}.</p>
            <div className="mt-6 overflow-x-auto rounded-2xl border border-slate-200">
              <table className="w-full min-w-[560px] border-collapse text-left text-sm">
                <caption className="sr-only">MahaRERA-registered projects by Pune area, as of {asOf}</caption>
                <thead className="bg-[#fbf6ea] text-slate-900">
                  <tr>
                    <th scope="col" className="p-3 font-semibold">Area</th>
                    <th scope="col" className="p-3 text-right font-semibold">Projects</th>
                    <th scope="col" className="p-3 text-right font-semibold">Homes booked</th>
                    <th scope="col" className="p-3 text-right font-semibold">Due {year}</th>
                    <th scope="col" className="p-3 text-right font-semibold">Due {year + 1}</th>
                  </tr>
                </thead>
                <tbody>
                  {city.areas.map((a) => (
                    <tr key={a.area.key} className="border-t border-slate-200">
                      <th scope="row" className="p-3 font-medium"><Link href={areaGuidePath(a.area.slug)} className="text-[#0f2340] underline underline-offset-2">{a.area.name}</Link></th>
                      <td className="p-3 text-right"><Count value={a.projects} href={links.get(a.area.key)?.all} label={`${fmt(a.projects)} projects in ${a.area.name}`} /></td>
                      <td className="p-3 text-right">{a.units_total !== null && a.units_booked !== null ? `${fmt(a.units_booked)} of ${fmt(a.units_total)}` : 'n/a'}</td>
                      {[year, year + 1].map((y) => (
                        <td key={y} className="p-3 text-right">
                          <Count value={due(a, y)} href={links.get(a.area.key)?.years[y]} label={`${fmt(due(a, y))} projects in ${a.area.name} due ${y}`} />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-slate-300 font-semibold">
                    <th scope="row" className="p-3">All areas</th>
                    <td className="p-3 text-right">{fmt(total)}</td>
                    <td className="p-3 text-right">{allUnits ? `${fmt(city.areas.reduce((s, a) => s + (a.units_booked ?? 0), 0))} of ${fmt(city.areas.reduce((s, a) => s + (a.units_total ?? 0), 0))}` : 'n/a'}</td>
                    <td className="p-3 text-right">{fmt(city.areas.reduce((s, a) => s + due(a, year), 0))}</td>
                    <td className="p-3 text-right">{fmt(city.areas.reduce((s, a) => s + due(a, year + 1), 0))}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <p className="mt-2 text-sm text-slate-600">&ldquo;n/a&rdquo;: MahaRERA did not give booked homes for every project in that area, so no total is shown rather than a partial one.</p>
            <DateMovesReport city={city} asOf={asOf} />
          </>
        )}
        <section className="mt-10" aria-labelledby="how">
          <h2 id="how" className="text-2xl font-semibold text-slate-900">How these numbers are made</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-slate-700">
            <li>Every project MahaRERA lists under each area&apos;s pincodes or name is read from its public project pages, and read again when MahaRERA marks it changed.</li>
            <li>&ldquo;Due&rdquo; is the completion date the developer has currently filed with MahaRERA. Filed dates can move; each project&apos;s page shows both the first and the current date.</li>
            <li>Nothing is estimated: a figure MahaRERA did not publish for every project is left out.</li>
          </ul>
        </section>
        {city && (
          <section className="mt-10 rounded-2xl border border-slate-200 bg-slate-50 p-5" aria-labelledby="cite">
            <h2 id="cite" className="text-xl font-semibold text-slate-900">Use these figures</h2>
            <p className="mt-2 text-slate-700">Journalists, bloggers and agents are welcome to quote this page. Please credit and link it:</p>
            <p className="mt-3 rounded-lg bg-white p-3 text-sm text-slate-800">Source: {cfg.businessName} Pune MahaRERA tracker ({url}), from MahaRERA public records, as of {asOf}.</p>
            <p className="mt-3 text-sm text-slate-700">HTML for a website:</p>
            <pre className="mt-1 overflow-x-auto whitespace-pre-wrap break-all rounded-lg bg-white p-3 text-xs text-slate-800">{`<a href="${url}">${cfg.businessName} Pune MahaRERA tracker</a>`}</pre>
          </section>
        )}
        <AgentStrip />
      </article>
    </MarketingShell>
  )
}
