import React from 'react'
import Link from 'next/link'
import EnquiryForm from '@/components/site/EnquiryForm'
import VerifiedFacts from '@/components/site/VerifiedFacts'
import { breadcrumbJsonLd, jsonLdString } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import type { RegisterProject } from '@/lib/site/register'
import { longDay } from '@/lib/site/register'
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
  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(siteUrl, crumbs)) }} />
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
          {p.units_total ? <Row label="Homes booked" value={`${p.units_booked ?? '?'} of ${p.units_total}`} note={`${read}.`} /> : null}
          <Row label="MahaRERA registration" value={p.regno} note={p.listed_or_updated ? `Listed or updated on MahaRERA ${longDay(p.listed_or_updated)}.` : undefined} />
          {p.promoter && <Row label="Promoter (builder)" value={p.promoter} />}
          {p.pincode && <Row label="Pincode" value={p.pincode} />}
        </dl>
        {!p.completion_now && <p className="mt-3 text-sm text-slate-600">We are still reading this project&apos;s details from MahaRERA; this page fills in by itself.</p>}
      </section>

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
