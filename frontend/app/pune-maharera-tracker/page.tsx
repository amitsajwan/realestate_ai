import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import { type AreaStats, getCityStats, longDate } from '@/components/localities/areaStats'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'

/** Pune's new-home projects by area, from MahaRERA's public records, kept current by the register refresh. A page others can
 *  cite and link to: facts only, each area linked to its guide, a ready-made citation. Rebuilt every 5 minutes at most. */
export const revalidate = 300
const PATH = '/pune-maharera-tracker'
const TITLE = 'Pune MahaRERA tracker: new home projects by area'
const DESCRIPTION = 'How many MahaRERA-registered projects each Pune area has, how many homes are booked and when projects are due to complete. From MahaRERA public records, updated as they change.'

export async function generateMetadata(): Promise<Metadata> {
  const meta = pageMetadata(getMarketingConfig(), { title: TITLE, description: DESCRIPTION, path: PATH })
  // no figures (API down): keep the empty page out of search until they are back
  return (await getCityStats()) ? meta : { ...meta, robots: { index: false, follow: true } }
}

const fmt = (n: number) => n.toLocaleString('en-IN')

function due(a: AreaStats, year: number): number {
  return a.completing.find((c) => c.year === year)?.projects ?? 0
}

export default async function TrackerPage() {
  const cfg = getMarketingConfig()
  const city = await getCityStats()
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
    variableMeasured: ['MahaRERA-registered projects', 'Homes registered', 'Homes booked', 'Projects due to complete by year'],
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
                      <th scope="row" className="p-3 font-medium"><Link href={`/localities/${a.area.slug}`} className="text-[#0f2340] underline underline-offset-2">{a.area.name}</Link></th>
                      <td className="p-3 text-right">{fmt(a.projects)}</td>
                      <td className="p-3 text-right">{a.units_total !== null && a.units_booked !== null ? `${fmt(a.units_booked)} of ${fmt(a.units_total)}` : 'n/a'}</td>
                      <td className="p-3 text-right">{fmt(due(a, year))}</td>
                      <td className="p-3 text-right">{fmt(due(a, year + 1))}</td>
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
