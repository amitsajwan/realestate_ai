import React from 'react'
import Link from 'next/link'
import EnquiryForm from '@/components/site/EnquiryForm'
import VerifiedFacts from '@/components/site/VerifiedFacts'
import { breadcrumbJsonLd, jsonLdString } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import type { RegisterProject } from '@/lib/site/register'
import { longDay, projectFaq } from '@/lib/site/register'
import type { Faq } from '@/lib/site/register'
import type { PropertyFactsView } from '@/lib/site/types'
import { formatPrice } from '@/lib/site/format'

/** The agent's offer as kept on the property's fact sheet (propertyfacts public view): what campaign posts quote. */
interface Offer {
  transaction?: string | null
  property_type?: string | null
  price_inr?: number | null
  plot_sqft?: number | null
  carpet_sqft?: number | null
  bhk?: number | null
  source?: string | null
  read_at?: string | null
}

function OfferBox({ facts }: { facts: PropertyFactsView | null }) {
  const o = (facts as unknown as { offer?: Offer } | null)?.offer
  if (!o || !(o.price_inr || o.plot_sqft || o.carpet_sqft || o.bhk)) return null
  const what = [o.bhk ? `${o.bhk} BHK` : null, o.property_type, o.plot_sqft ? `plot ${o.plot_sqft.toLocaleString('en-IN')} sq ft` : null,
    o.carpet_sqft ? `${o.carpet_sqft.toLocaleString('en-IN')} sq ft carpet` : null].filter(Boolean).join(' · ')
  return (
    <section aria-labelledby="offer-title" className="rounded-2xl border border-amber-200 bg-amber-50 p-4" data-testid="offer">
      <h2 id="offer-title" className="text-lg font-bold text-slate-900">On offer</h2>
      {o.price_inr ? <p className="mt-1 text-2xl font-extrabold text-slate-900">{formatPrice(o.price_inr)}</p> : null}
      {what && <p className="mt-1 text-slate-800">{what}</p>}
      <p className="mt-2 text-xs text-slate-600">From {o.source || "the agent's listing"}{o.read_at ? `, ${longDay(o.read_at)}` : ''}. Prices change: confirm before you book.</p>
    </section>
  )
}

const HOUSE_AGENT = process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'

function Row({ label, value, note }: { label: string; value: React.ReactNode; note?: string }) {
  return (
    <div className="min-w-0 border-b border-slate-200 py-3">
      <dt className="text-sm text-slate-600">{label}</dt>
      <dd className="mt-0.5 text-lg font-semibold text-slate-900">{value}</dd>
      {note && <dd className="mt-0.5 text-xs text-slate-500">{note}</dd>}
    </div>
  )
}

const H2 = 'text-xl font-semibold text-slate-900'
const n = (v: number | null | undefined) => (v == null ? null : v.toLocaleString('en-IN'))
const months = (m: number) => `${m} month${m === 1 ? '' : 's'}`

function Cell({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3">
      <dt className="text-xs text-slate-600">{label}</dt>
      <dd className="mt-0.5 text-lg font-semibold text-slate-900">{value}</dd>
    </div>
  )
}

/** Towers, floors, flats, booked share, dates: from MahaRERA's buildings summary and the register record. */
function DetailsGrid({ p }: { p: RegisterProject }) {
  const d = p.details
  if (!d) return null
  const moved = d.completion_moved_months
  const cells: [string, React.ReactNode][] = []
  if (d.towers) cells.push(['Towers', n(d.towers)])
  if (d.max_floors) cells.push(['Floors (tallest)', n(d.max_floors)])
  if (d.units_total) cells.push(['Units', n(d.units_total)])
  if (d.units_residential != null && d.towers) cells.push(['Residential units', n(d.units_residential)])
  if (d.units_other) cells.push(['Other units (shops, offices)', n(d.units_other)])
  if (d.booked_pct != null) cells.push(['Booked', `${d.booked_pct}%`])
  if (d.registered_on) cells.push(['Registered on', longDay(d.registered_on)])
  if (p.completion_now) cells.push(['Completion filed', <>{longDay(p.completion_now)}{moved != null && <span className="block text-xs font-normal text-slate-600">{moved > 0 ? `moved ${months(moved)} later since registration` : 'not moved since registration'}</span>}</>])
  if (cells.length < 2) return null
  return (
    <section aria-labelledby="details-title">
      <h2 id="details-title" className={H2}>Project details</h2>
      <dl className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
        {cells.map(([label, value]) => <Cell key={label} label={label} value={value} />)}
      </dl>
      <p className="mt-2 text-xs text-slate-500">Source: MahaRERA public records.</p>
    </section>
  )
}

function BuildingsTable({ p }: { p: RegisterProject }) {
  const rows = p.buildings ?? []
  if (!rows.length) return null
  return (
    <section aria-labelledby="buildings-title">
      <h2 id="buildings-title" className={H2}>Buildings</h2>
      <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr><th className="px-3 py-2 font-semibold">Building</th><th className="px-3 py-2 font-semibold">Floors</th><th className="px-3 py-2 font-semibold">Homes</th><th className="px-3 py-2 font-semibold">Other</th></tr>
          </thead>
          <tbody>
            {rows.map((b, i) => (
              <tr key={i} className="border-t border-slate-200">
                <td className="px-3 py-2 font-semibold text-slate-900">{[b.name, b.wing].filter(Boolean).join(', ') || `Building ${i + 1}`}</td>
                <td className="px-3 py-2">{n(b.floors) ?? '-'}</td>
                <td className="px-3 py-2">{n(b.units_residential) ?? '-'}</td>
                <td className="px-3 py-2">{n(b.units_other) ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-slate-500">As filed with MahaRERA (sanctioned floors).</p>
    </section>
  )
}

/** OpenStreetMap embed around the checked position (no Google key). */
function MapBox({ p }: { p: RegisterProject }) {
  const m = p.map
  if (!m) return null
  const d = 0.01
  const bbox = [m.lon - d, m.lat - d, m.lon + d, m.lat + d].map((x) => x.toFixed(5)).join(',')
  const src = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${m.lat.toFixed(5)},${m.lon.toFixed(5)}`
  const link = `https://www.openstreetmap.org/?mlat=${m.lat.toFixed(5)}&mlon=${m.lon.toFixed(5)}#map=15/${m.lat.toFixed(5)}/${m.lon.toFixed(5)}`
  return (
    <section aria-labelledby="map-title">
      <h2 id="map-title" className={H2}>Map</h2>
      <iframe title={`Map around ${p.name}`} src={src} loading="lazy" className="mt-3 h-64 w-full rounded-xl border border-slate-200 sm:h-80" />
      <p className="mt-2 text-xs text-slate-500">
        Approximate area, from OpenStreetMap; not the exact plot.{' '}
        <a href={link} target="_blank" rel="noopener noreferrer" className="text-[#0f2340] underline underline-offset-2">Open the map<span className="sr-only"> (opens in a new tab)</span></a>
      </p>
    </section>
  )
}

function BuilderBox({ p }: { p: RegisterProject }) {
  const b = p.builder
  if (!b || !b.count) return null
  const others = b.projects.filter((x) => !x.this)
  return (
    <section aria-labelledby="builder-title">
      <h2 id="builder-title" className={H2}>About the builder</h2>
      <p className="mt-2 text-slate-800">
        {b.name} has {b.count} project{b.count === 1 ? '' : 's'} in our MahaRERA register for Pune.
        {b.with_dates > 0 && <> {b.moved_later} of {b.with_dates} with both dates moved the completion date later{b.avg_months_later ? `, by ${months(b.avg_months_later)} on average` : ''}.</>}
      </p>
      {others.length > 0 && (
        <ul className="mt-3 space-y-1 p-0">
          {others.map((x) => (
            <li key={x.regno} className="list-none">
              {x.slug ? <Link href={`/projects/${x.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">{x.name}</Link>
                : <span className="font-semibold text-slate-900">{x.name}</span>}
              <span className="ml-2 text-sm text-slate-600">
                {x.completion_now ? `completion filed ${longDay(x.completion_now)}` : x.regno}
                {x.months_later ? `, moved ${months(x.months_later)} later` : ''}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-xs text-slate-500">Counted from MahaRERA records we hold; projects outside Pune are not included.</p>
    </section>
  )
}

function FaqBox({ faq }: { faq: Faq[] }) {
  if (!faq.length) return null
  return (
    <section aria-labelledby="faq-title">
      <h2 id="faq-title" className={H2}>FAQ</h2>
      <div className="mt-3 space-y-2">
        {faq.map((f) => (
          <details key={f.q} className="rounded-xl border border-slate-200 bg-white p-3">
            <summary className="min-h-[44px] cursor-pointer py-2 font-semibold text-slate-900">{f.q}</summary>
            <p className="mt-1 text-slate-800">{f.a}</p>
          </details>
        ))}
      </div>
    </section>
  )
}

/** Avasetu's own page for a MahaRERA project: our facts first (each with source and date), then the official record. */
export default function RegisterProjectPage({ p, siteUrl, facts }: { p: RegisterProject; siteUrl: string; facts: PropertyFactsView | null }) {
  const url = `${siteUrl}/projects/${p.slug}`
  const read = p.details_read_at ? `MahaRERA, read ${longDay(p.details_read_at)}` : 'MahaRERA'
  const moved = p.completion_now && p.completion_at_registration && p.completion_now !== p.completion_at_registration
  const crumbs = [{ name: 'Home', path: '/' }, ...(p.area ? [{ name: `${p.area.name}, Pune`, path: `/localities/${p.area.slug}` }] : []),
    { name: p.name, path: `/projects/${p.slug}` }]
  const ld = {
    '@context': 'https://schema.org', '@type': 'ApartmentComplex', name: p.name, url,
    address: { '@type': 'PostalAddress', addressLocality: p.area ? p.area.name : 'Pune', addressRegion: 'Maharashtra', postalCode: p.pincode || undefined, addressCountry: 'IN' },
    ...(p.units_total ? { numberOfAccommodationUnits: p.units_total } : {}),
  }
  const faq = projectFaq(p, (facts as unknown as { nearby?: { label: string; name: string; km: number }[] } | null)?.nearby ?? [])
  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(siteUrl, crumbs)) }} />
      {faq.length > 0 && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString({
        '@context': 'https://schema.org', '@type': 'FAQPage',
        mainEntity: faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
      }) }} />}
      <nav aria-label="Breadcrumb" className="text-sm">
        <Link href="/" className="text-[#0f2340] underline underline-offset-2">Home</Link>
        {p.area && <> <span aria-hidden className="px-1 text-slate-400">/</span> <Link href={`/localities/${p.area.slug}`} className="text-[#0f2340] underline underline-offset-2">{p.area.name}</Link></>}
      </nav>

      <header>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{p.name}</h1>
        <p className="mt-1 font-semibold text-amber-700">{[p.promoter, p.area ? `${p.area.name}, Pune` : 'Pune district', `MahaRERA ${p.regno}`].filter(Boolean).join(' · ')}</p>
        <p className="mt-5 text-lg leading-relaxed text-slate-800" data-testid="paragraph">{p.paragraph}</p>
        <a href="#enquire" className="mt-5 inline-flex min-h-[48px] items-center rounded-full bg-amber-400 px-6 font-bold text-slate-900 no-underline">Ask about this project</a>
      </header>

      <section aria-labelledby="facts-title">
        <h2 id="facts-title" className="text-xl font-semibold text-slate-900">The facts</h2>
        <dl className="mt-2">
          {p.completion_now && <Row label="Completion date filed with MahaRERA" value={longDay(p.completion_now)}
            note={moved ? `At registration: ${longDay(p.completion_at_registration)}. ${read}.` : `${read}.`} />}
          {p.units_total ? <Row label="Homes booked" value={p.units_booked != null ? `${p.units_booked} of ${p.units_total}` : `Not reported (${p.units_total} homes)`} note={`${read}.`} /> : null}
          <Row label="MahaRERA registration" value={p.regno} note={p.listed_or_updated ? `Listed or updated on MahaRERA ${longDay(p.listed_or_updated)}.` : undefined} />
          {p.promoter && <Row label="Promoter (builder)" value={p.promoter} />}
          {p.pincode && <Row label="Pincode" value={p.pincode} />}
        </dl>
        {p.completion_passed && <p className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">The filed completion date has passed. Ask for the occupancy certificate (OC) before you book.</p>}
        {!p.completion_now && <p className="mt-3 text-sm text-slate-600">We are still reading this project&apos;s details from MahaRERA; this page fills in by itself.</p>}
      </section>

      <DetailsGrid p={p} />
      <BuildingsTable p={p} />
      <MapBox p={p} />
      <BuilderBox p={p} />
      <FaqBox faq={faq} />

      <OfferBox facts={facts} />
      <VerifiedFacts f={facts} />

      {p.same_area.length > 0 && p.area && (
        <section aria-labelledby="same-title">
          <h2 id="same-title" className="text-xl font-semibold text-slate-900">Other projects in {p.area.name}</h2>
          <ul className="mt-3 space-y-2 p-0">
            {p.same_area.map((s) => (
              <li key={s.slug} className="list-none">
                <Link href={`/projects/${s.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">{s.name}</Link>
                {s.completion_now && <span className="ml-2 text-sm text-slate-600">completion filed {longDay(s.completion_now)}</span>}
              </li>
            ))}
          </ul>
          <Link href={`/localities/${p.area.slug}`} className="mt-3 inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{p.area.name} area guide</Link>
        </section>
      )}

      <section id="enquire" aria-labelledby="enq-title" className="scroll-mt-20 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
        <h2 id="enq-title" className="text-xl font-semibold text-slate-900">Ask about {p.name}</h2>
        <p className="mt-1 text-sm text-slate-600">Tell us what you are looking for. A local agent calls you back; we never share your number without your OK.</p>
        <div className="mt-4">
          <EnquiryForm agentSlug={HOUSE_AGENT} agentName="Avasetu" topic={`${p.name} (MahaRERA ${p.regno})`}
            waMessage={`Hi, I want to know about ${p.name} (MahaRERA ${p.regno}): ${url}`} />
        </div>
      </section>

      <footer className="border-t border-slate-200 pt-4 text-sm text-slate-600">
        Source: {p.source}.{' '}
        {p.maharera_url && <a href={p.maharera_url} target="_blank" rel="noopener noreferrer" className="text-[#0f2340] underline underline-offset-2">See the official MahaRERA record<span className="sr-only"> (opens in a new tab)</span></a>}
        {' '}Facts can change; check the record and your agreement before you book.
      </footer>
    </div>
  )
}
