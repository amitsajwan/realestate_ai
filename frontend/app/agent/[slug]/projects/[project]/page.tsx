import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import ContactButtons from '@/components/site/ContactButtons'
import EnquiryForm from '@/components/site/EnquiryForm'
import ReraBox from '@/components/site/ReraBox'
import SiteShell from '@/components/site/SiteShell'
import StickyBar from '@/components/site/StickyBar'
import TrackingBeacon from '@/components/site/TrackingBeacon'
import { getAgent, getProject } from '@/lib/site/api'
import { formatPrice, groupIndian } from '@/lib/site/format'
import { bhkRange, formatDay, mapsLink, possessionLines, priceRange, projectWhatsAppMessage, sourceLabel } from '@/lib/site/projects'
import { jsonLdString, projectMetadata } from '@/lib/site/seo'
import { breadcrumbJsonLd } from '@/lib/marketing/seo'
import { localityByName } from '@/lib/marketing/localities'
import { agentPath, normalizeSlug, siteOrigin } from '@/lib/site/slug'
import { displayName } from '@/lib/site/theme'
import { BRAND_NAME } from '@/lib/brand'
import DemoRibbon from '../../DemoRibbon'

interface Props {
  params: Promise<{ slug: string; project: string }>
}

async function load(params: Props['params']) {
  const { slug: rawSlug, project } = await params
  const slug = normalizeSlug(rawSlug)
  const agent = slug ? await getAgent(slug) : null
  const p = slug && agent ? await getProject(slug, project) : null
  return { slug, agent, p }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { agent, p } = await load(params)
  if (!agent || !p) return { title: 'Project not found', robots: { index: false } }
  return projectMetadata(agent, p, priceRange(p) + ', ' + bhkRange(p.bhk_options))
}

export default async function ProjectPage({ params }: Props) {
  const { slug, agent, p } = await load(params)
  if (!slug || !agent || !p) notFound()
  const name = displayName(agent)
  const url = siteOrigin() + agentPath(slug, 'projects/' + p.slug)
  const msg = projectWhatsAppMessage(p, url)
  const quoted = sourceLabel('agent', name)
  const possession = possessionLines(p, name)
  const photo = p.media.find((m) => m.kind === 'image')
  const ld = {
    '@context': 'https://schema.org', '@type': 'ApartmentComplex', name: p.name, url,
    address: { '@type': 'PostalAddress', streetAddress: p.address, addressLocality: p.locality, addressRegion: 'Maharashtra', postalCode: p.pincode, addressCountry: 'IN' },
    image: photo ? [/^https?:/.test(photo.url) ? photo.url : siteOrigin() + photo.url] : undefined,
    numberOfAccommodationUnits: p.rera?.units_total ?? undefined,
  }
  const area = localityByName(p.locality)
  const crumbs = breadcrumbJsonLd(siteOrigin(), [
    { name: 'Home', path: '/' }, { name: name, path: agentPath(slug) }, { name: p.name, path: agentPath(slug, 'projects/' + p.slug) },
  ])

  return (
    <SiteShell agent={agent} bottomPad>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(crumbs) }} />
      <TrackingBeacon agentSlug={slug} />
      <DemoRibbon agent={agent} />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-6">
        <p className="text-sm">
          <Link href={agentPath(slug) + '#projects'} className="inline-flex min-h-[44px] items-center text-[var(--site-primary)]">&larr; All projects</Link>
        </p>

        <header>
          <p className="text-sm font-bold uppercase tracking-wide text-[var(--site-accent-text)]">{p.locality}, Pune</p>
          <h1 className="mt-1 text-3xl font-extrabold leading-tight">{p.name}</h1>
          <p className="mt-1 text-slate-600">by {p.builder}{p.rera?.promoter ? ` (promoter on MahaRERA: ${p.rera.promoter})` : ''}</p>
          <p className="mt-3 text-2xl font-extrabold text-[var(--site-primary)]">{priceRange(p)} <span className="text-base font-semibold text-slate-700">· {bhkRange(p.bhk_options)}</span></p>
          {p.positioning && <p className="mt-2 max-w-2xl text-lg text-slate-800">{p.positioning}</p>}
          {area && (
            <p className="mt-2 text-sm">
              <Link href={`/localities/${area.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary)] underline underline-offset-2">
                Buyer guide to {area.name}: who it suits, commute and what to check
              </Link>
            </p>
          )}
          <div className="mt-4 hidden max-w-sm md:flex">
            <ContactButtons agentSlug={slug} phone={agent.phone} waMessage={msg} size="md" />
          </div>
        </header>

        {photo && (
          <figure className="overflow-hidden rounded-2xl bg-slate-100">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={photo.url} alt={photo.caption} className="aspect-[16/7] w-full object-cover" />
            <figcaption className="px-3 py-2 text-xs text-slate-600">
              {photo.caption}{photo.credit ? ' · ' + photo.credit : ''}
            </figcaption>
          </figure>
        )}

        <section aria-labelledby="prices-title">
          <h2 id="prices-title" className="text-xl font-bold">Prices and sizes</h2>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr><th className="px-2 py-2 font-semibold sm:px-3">Home</th><th className="px-2 py-2 font-semibold sm:px-3">Carpet</th><th className="px-2 py-2 font-semibold sm:px-3">Price</th><th className="px-2 py-2 font-semibold sm:px-3">Per sq ft</th></tr>
              </thead>
              <tbody>
                {p.configurations.map((c) => (
                  <tr key={c.label + c.carpet_sqft} className="border-t border-slate-100">
                    <td className="px-2 py-2 sm:px-3 font-semibold">{c.label}</td>
                    <td className="px-2 py-2 sm:px-3">{groupIndian(c.carpet_sqft)} sq ft</td>
                    <td className="px-2 py-2 sm:px-3 font-semibold">{formatPrice(c.price_inr)}</td>
                    <td className="px-2 py-2 sm:px-3">₹{groupIndian(c.price_per_sqft)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-slate-600">{quoted}. Builders change prices often: confirm the price, the floor and any extra charges (parking, GST, stamp duty) before you book.</p>
        </section>

        <ReraBox p={p} />

        {possession.length > 0 && (
          <section aria-labelledby="when-title">
            <h2 id="when-title" className="text-xl font-bold">When could you move in?</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-800">
              {possession.map((l) => <li key={l}>{l}</li>)}
            </ul>
            <p className="mt-2 text-xs text-slate-600">Under RERA (section 18), if possession is late beyond the date in your agreement for sale, you can claim interest for the delay or withdraw with a refund.</p>
          </section>
        )}

        {(p.who_it_suits.length > 0 || p.highlights.length > 0) && (
          <section aria-labelledby="fit-title" className="grid gap-4 sm:grid-cols-2">
            {p.who_it_suits.length > 0 && (
              <div className="rounded-2xl border border-slate-200 p-4">
                <h2 id="fit-title" className="text-lg font-bold">Who it suits</h2>
                <ul className="mt-2 list-disc space-y-1 pl-5">{p.who_it_suits.map((w) => <li key={w}>{w}</li>)}</ul>
                <p className="mt-2 text-xs text-slate-500">{sourceLabel('avasetu', name)}, from the facts on this page.</p>
              </div>
            )}
            {p.highlights.length > 0 && (
              <div className="rounded-2xl border border-slate-200 p-4">
                <h2 className="text-lg font-bold">Worth knowing</h2>
                <ul className="mt-2 list-disc space-y-1 pl-5">{p.highlights.map((w) => <li key={w}>{w}</li>)}</ul>
              </div>
            )}
          </section>
        )}

        <section aria-labelledby="where-title">
          <h2 id="where-title" className="text-xl font-bold">Location</h2>
          {p.address && <p className="mt-1 text-slate-800">{p.address} <span className="text-xs text-slate-500">({quoted})</span></p>}
          {p.nearby.length > 0 && (
            <ul className="mt-3 grid gap-2 sm:grid-cols-2">
              {p.nearby.map((n) => (
                <li key={n.name} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-sm">
                  <span>{n.name}</span>
                  <span className="font-semibold">{n.km != null ? `${n.km} km by road` : ''}</span>
                </li>
              ))}
            </ul>
          )}
          {p.nearby.some((n) => n.km != null) && (
            <p className="mt-2 text-xs text-slate-500">Road distances from {p.place?.note || 'the project'} (OpenStreetMap routing, no traffic).</p>
          )}
          <a href={mapsLink(p)} target="_blank" rel="noopener noreferrer"
            className="mt-3 inline-flex min-h-[44px] items-center rounded-xl border border-slate-300 px-4 font-semibold text-[var(--site-primary)] no-underline">
            Find it on Google Maps
          </a>
        </section>

        {p.amenities.length > 0 && (
          <section aria-labelledby="amen-title">
            <h2 id="amen-title" className="text-xl font-bold">Amenities</h2>
            <ul className="mt-2 flex list-none flex-wrap gap-2 p-0">
              {p.amenities.map((a) => <li key={a} className="rounded-full bg-slate-100 px-3 py-1.5 text-sm">{a}</li>)}
            </ul>
            <p className="mt-2 text-xs text-slate-500">{quoted}.</p>
          </section>
        )}

        {Object.keys(p.specs).length > 0 && (
          <section aria-labelledby="spec-title">
            <h2 id="spec-title" className="text-xl font-bold">Project details</h2>
            <dl className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {Object.entries(p.specs).map(([k, v]) => (
                <div key={k} className="rounded-xl bg-slate-50 px-3 py-2">
                  <dt className="text-xs text-slate-500">{k}</dt>
                  <dd className="font-semibold">{v}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-2 text-xs text-slate-500">{quoted}.{p.possession_target ? ` Builder's target possession: ${formatDay(p.possession_target)}.` : ''}</p>
          </section>
        )}

        <p className="text-sm">
          <Link href={agentPath(slug, 'projects/compare')} className="font-semibold text-[var(--site-primary)]">Compare all projects side by side &rarr;</Link>
        </p>

        <EnquiryForm agentSlug={slug} agentName={BRAND_NAME} agentPhone={agent.phone} topic={`${p.name} (${p.rera_no})`} waMessage={msg} id="enquire" />
      </div>
      <StickyBar agentSlug={slug} phone={agent.phone} waMessage={msg} />
    </SiteShell>
  )
}
