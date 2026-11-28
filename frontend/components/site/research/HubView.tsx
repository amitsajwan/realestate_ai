import React from 'react'
import Link from 'next/link'
import { breadcrumbJsonLd, jsonLdString } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { formatPrice } from '@/lib/site/format'
import { longDay, monthYear, placePath } from '@/lib/site/register'
import { HUBS_PATH, hubPath } from '@/lib/site/research'
import type { HubCard, HubPage } from '@/lib/site/research'
import { hubHead, hubJsonLd, kmText, minutes, rupees } from '@/lib/site/researchPages'
import { ChangesList, SmallPrint } from './ResearchBlocks'

// The work hub pages (/work-hubs and /work-hubs/<slug>; docs/plan/pune-intelligence.md C): the IT parks and job centres Pune
// buyers commute to, with the companies there, drive times from each place, homes and asked rent nearby. Every figure is the
// backend's measure with its source and date.

const TH = 'px-3 py-2 font-semibold'
const KIND: Record<HubCard['kind'], string> = {
  it_park: 'IT park', business_district: 'Business district', airport: 'Airport', station: 'Railway station', industrial: 'Industrial area',
}

export function HubBody({ h, placeName, placeLinked, siteUrl }: { h: HubPage; placeName: string; placeLinked: Set<string>; siteUrl: string }) {
  const head = hubHead(h, placeName)
  const ld = [
    breadcrumbJsonLd(siteUrl, [{ name: 'Home', path: '/' }, { name: 'Work hubs', path: HUBS_PATH }, { name: h.name, path: hubPath(h.slug) }]),
    hubJsonLd(siteUrl, h, placeName),
    { '@context': 'https://schema.org', '@type': 'WebPage', name: head.title, url: siteUrl + hubPath(h.slug), ...(h.updated ? { dateModified: h.updated } : {}) },
  ]
  const place = (slug: string, name: string) => (placeLinked.has(slug)
    ? <Link href={placePath(slug)} className="text-[#0f2340] underline underline-offset-2">{name}</Link> : <>{name}</>)
  return (
    <article className="mx-auto max-w-5xl px-4 py-8 sm:py-12" style={AVASETU_SITE_VARS} data-testid="hub-page">
      {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
      <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
        <Link href="/" className="text-[#0f2340] underline underline-offset-2">Home</Link>
        <span aria-hidden className="px-1 text-slate-400">/</span>
        <Link href={HUBS_PATH} className="text-[#0f2340] underline underline-offset-2">Work hubs</Link>
      </nav>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{head.h1}</h1>
      <p className="mt-2 text-sm text-slate-600">{KIND[h.kind] ?? 'Work hub'} in {place(h.place, placeName)}{h.updated ? ` · updated ${longDay(h.updated)}` : ''}</p>
      {h.summary && <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800" data-testid="hub-summary">{h.summary}</p>}

      {h.companies.length > 0 && (
        <section aria-labelledby="companies-title" className="mt-8" data-testid="hub-companies">
          <h2 id="companies-title" className="text-xl font-semibold text-slate-900">Companies at {h.name} ({h.companies.length})</h2>
          <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
            {h.companies.map((c) => <li key={c} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-800">{c}</li>)}
          </ul>
          {h.companies_source && <SmallPrint sources={[h.companies_source]} updated={h.companies_source.read_on} note="From the hub's own list of tenants." />}
        </section>
      )}

      {h.commute_from.length > 0 && (
        <section aria-labelledby="from-title" className="mt-10" data-testid="hub-commute">
          <h2 id="from-title" className="text-xl font-semibold text-slate-900">Drive to {h.name} from each place</h2>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full min-w-[420px] text-left text-sm">
              <thead><tr className="text-xs text-slate-500"><th className={TH}>From</th><th className={TH}>9 am</th><th className={TH}>6 pm, back</th></tr></thead>
              <tbody>
                {h.commute_from.map((r) => (
                  <tr key={r.place} className="border-t border-slate-200">
                    <th scope="row" className="px-3 py-2 font-semibold text-slate-900">{place(r.place, r.name)}</th>
                    <td className="px-3 py-2 text-slate-800">{minutes(r.am)}</td>
                    <td className="px-3 py-2 text-slate-800">{minutes(r.pm)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-slate-500">From each place&apos;s centre on a weekday, Google&apos;s typical traffic.</p>
        </section>
      )}

      {h.homes_nearby.length > 0 && (
        <section aria-labelledby="homes-title" className="mt-10" data-testid="hub-homes">
          <h2 id="homes-title" className="text-xl font-semibold text-slate-900">Projects near {h.name}</h2>
          <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
            {h.homes_nearby.map((x) => {
              const line = [kmText(x.km), x.price_from ? `from ${formatPrice(x.price_from)}` : null,
                x.possession ? `possession ${/^\d{4}-\d{2}/.test(x.possession) ? monthYear(x.possession) : x.possession}` : null].filter(Boolean).join(' · ')
              return (
                <li key={x.slug}>
                  <Link href={`/projects/${x.slug}`} className="block min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
                    <span className="block font-semibold text-[#0f2340]">{x.name}</span>
                    <span className="text-sm text-slate-600">{line}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
          <p className="mt-2 text-xs text-slate-500">Straight-line distance from the hub; possession as the builder filed it with MahaRERA.</p>
        </section>
      )}

      {(h.rent_nearby ?? []).length > 0 && (
        <section aria-labelledby="hub-rent-title" className="mt-10" data-testid="hub-rent">
          <h2 id="hub-rent-title" className="text-xl font-semibold text-slate-900">Asked rent near {h.name}</h2>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full min-w-[360px] text-left text-sm">
              <thead><tr className="text-xs text-slate-500"><th className={TH}>Size</th><th className={TH}>A month</th><th className={TH}>Listings</th></tr></thead>
              <tbody>
                {(h.rent_nearby ?? []).map((r) => (
                  <tr key={r.bhk} className="border-t border-slate-200">
                    <th scope="row" className="px-3 py-2 font-semibold text-slate-900">{r.bhk}</th>
                    <td className="px-3 py-2 text-slate-800">{rupees(r.low)} to {rupees(r.high)}</td>
                    <td className="px-3 py-2 text-slate-800">{r.listings}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            What owners ask on listings, not what tenants pay.
          </p>
        </section>
      )}

      {h.changes.length > 0 && <div className="mt-10"><ChangesList changes={h.changes} heading={`What's changing near ${h.name}`} /></div>}

      <SmallPrint sources={h.sources} updated={h.updated} testId="hub-print" />
    </article>
  )
}

export function HubList({ hubs, placeNames, siteUrl }: { hubs: HubCard[]; placeNames: Map<string, string>; siteUrl: string }) {
  const ld = [
    breadcrumbJsonLd(siteUrl, [{ name: 'Home', path: '/' }, { name: 'Work hubs', path: HUBS_PATH }]),
    { '@context': 'https://schema.org', '@type': 'ItemList', name: 'Work hubs in Pune', numberOfItems: hubs.length,
      itemListElement: hubs.map((h, i) => ({ '@type': 'ListItem', position: i + 1, url: siteUrl + hubPath(h.slug), name: h.name })) },
  ]
  return (
    <article className="mx-auto max-w-5xl px-4 py-8 sm:py-12" style={AVASETU_SITE_VARS} data-testid="hub-list">
      {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
      <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
        <Link href="/" className="text-[#0f2340] underline underline-offset-2">Home</Link>
      </nav>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Work hubs in Pune: IT parks and job centres</h1>
      <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800">
        {hubs.length ? `${hubs.length} places Pune commutes to, each with the companies there, drive times from each part of the city at 9 am and 6 pm, and the projects being built nearby.`
          : 'The work hubs are being measured; their pages come here as they are ready.'}
      </p>
      {hubs.length > 0 && (
        <ul className="mt-6 grid list-none gap-3 p-0 sm:grid-cols-2">
          {hubs.map((h) => (
            <li key={h.slug}>
              <Link href={hubPath(h.slug)} className="block min-h-[44px] rounded-xl border border-slate-200 bg-white px-4 py-3 no-underline hover:border-[#0f2340]">
                <span className="block text-lg font-semibold text-[#0f2340]">{h.name}</span>
                <span className="text-sm text-slate-600">{KIND[h.kind] ?? 'Work hub'} · {placeNames.get(h.place) ?? h.place}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </article>
  )
}
