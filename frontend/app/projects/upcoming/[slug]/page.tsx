import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import EnquiryForm from '@/components/site/EnquiryForm'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getUpcoming, type UpcomingProject } from '@/lib/site/hubs'

// An upcoming project MahaRERA has not registered yet (backend areastats/upcoming.py). The RERA Act does not let anyone advertise
// or sell an unregistered project, so this page shows no prices and takes no booking: the only ask is "tell me when it registers".
// It stays out of search (noindex, not in any sitemap) until the project registers and gets its own register page.

export const revalidate = 300
export const dynamicParams = true
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  return []
}

type Props = { params: Promise<{ slug: string }> }

const HOUSE_AGENT = process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const u = await getUpcoming((await params).slug).catch(() => null)
  if (!u) return { title: 'Project not found', robots: { index: false } }
  const meta = pageMetadata(getMarketingConfig(), {
    title: `${u.name}: upcoming, not yet MahaRERA registered`,
    description: `${u.name} by ${u.builder}, ${u.area_name}, Pune. Announced by the builder, not yet registered with MahaRERA. What is known so far, with sources.`,
    path: `/projects/upcoming/${u.slug}`,
  })
  return { ...meta, robots: { index: false, follow: true } }
}

function ToConfirm() {
  return <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">to be confirmed</span>
}

function bhkLabel(b: number) {
  return `${Number.isInteger(b) ? b : b.toFixed(1)} BHK`
}

function Pictures({ u }: { u: UpcomingProject }) {
  if (!u.pictures.length) return null
  return (
    <section aria-labelledby="pics-title">
      <h2 id="pics-title" className="text-xl font-semibold text-slate-900">Pictures</h2>
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {u.pictures.map((p) => (
          <figure key={p.url} className="relative overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={p.url} alt={p.caption || u.name} loading="lazy" decoding="async" className="aspect-[16/10] w-full object-cover" />
            {p.illustrative && (
              <span className="absolute left-2 top-2 rounded-full bg-black/70 px-2 py-0.5 text-xs text-white">Illustration, not this project&apos;s design</span>
            )}
            {p.caption && <figcaption className="px-3 py-2 text-sm text-slate-600">{p.caption}</figcaption>}
          </figure>
        ))}
      </div>
    </section>
  )
}

export default async function UpcomingProjectPage({ params }: Props) {
  const u = await getUpcoming((await params).slug)
  if (!u) notFound()
  const url = `${getMarketingConfig().siteUrl}/projects/upcoming/${u.slug}`
  return (
    <MarketingShell hot={{ area: u.area_slug, exclude: `upcoming/${u.slug}` }}>
      <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
          <Link href="/" className="underline underline-offset-2">Home</Link> / <Link href="/projects" className="underline underline-offset-2">Projects</Link>
          {' / '}<Link href={`/projects/area/${u.area_slug}`} className="underline underline-offset-2">{u.area_name}</Link>
        </nav>

        <header>
          <p className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-900" data-testid="upcoming-badge">
            Coming soon · Not yet registered with MahaRERA
          </p>
          <h1 className="mt-3 text-3xl font-bold text-slate-900">{u.name}, {u.area_name}</h1>
          <p className="mt-1 text-slate-700">by {u.builder}{u.address ? ` · ${u.address}` : ''}</p>
          <p className="mt-4 max-w-3xl text-slate-800">{u.summary}</p>
        </header>

        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4" data-testid="upcoming-warning">
          <h2 className="font-semibold text-amber-950">Before you pay anything</h2>
          <p className="mt-1 text-sm text-amber-950">
            This project has no MahaRERA registration yet, so no one may sell or take a booking for it. Prices are not published.
            Do not pay a token or booking amount until it has a MahaRERA number; we will tell you the day it registers.
          </p>
        </section>

        <Pictures u={u} />

        {u.homes.length > 0 && (
          <section aria-labelledby="homes-title">
            <h2 id="homes-title" className="text-xl font-semibold text-slate-900">Homes planned</h2>
            <ul className="mt-3 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
              {u.homes.map((h) => (
                <li key={h.bhk + h.carpet_sqft} className="flex flex-wrap items-baseline justify-between gap-2 px-4 py-3">
                  <span className="font-medium text-slate-900">{bhkLabel(h.bhk)}{h.to_confirm && <ToConfirm />}</span>
                  <span className="text-slate-700">{h.carpet_sqft ? `${h.carpet_sqft} sq ft carpet` : 'size not announced'}</span>
                  <span className="w-full text-xs text-slate-500">Source: {h.source}</span>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-sm text-slate-600">Price: announced at launch, after MahaRERA registration.</p>
          </section>
        )}

        {u.facts.length > 0 && (
          <section aria-labelledby="facts-title">
            <h2 id="facts-title" className="text-xl font-semibold text-slate-900">What is known so far</h2>
            <dl className="mt-3 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
              {u.facts.map((f) => (
                <div key={f.label} className="grid grid-cols-1 gap-1 px-4 py-3 sm:grid-cols-3">
                  <dt className="text-slate-600">{f.label}</dt>
                  <dd className="sm:col-span-2">
                    <span className="font-medium text-slate-900">{f.value}</span>{f.to_confirm && <ToConfirm />}
                    <span className="block text-xs text-slate-500">Source: {f.source}</span>
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        {u.highlights.length > 0 && (
          <section aria-labelledby="hl-title">
            <h2 id="hl-title" className="text-xl font-semibold text-slate-900">What the builder says</h2>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-slate-800">{u.highlights.map((h) => <li key={h}>{h}</li>)}</ul>
          </section>
        )}

        {u.amenities.length > 0 && (
          <section aria-labelledby="am-title">
            <h2 id="am-title" className="text-xl font-semibold text-slate-900">Amenities listed<ToConfirm /></h2>
            <ul className="mt-3 flex flex-wrap gap-2">
              {u.amenities.map((a) => <li key={a} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-slate-800">{a}</li>)}
            </ul>
          </section>
        )}

        {u.nearby.length > 0 && (
          <section aria-labelledby="near-title">
            <h2 id="near-title" className="text-xl font-semibold text-slate-900">Nearby</h2>
            <ul className="mt-3 space-y-1 text-slate-800">
              {u.nearby.map((n) => <li key={n.name}>{n.name}{n.km ? `: about ${n.km} km` : ''} <span className="text-xs text-slate-500">({n.source})</span></li>)}
            </ul>
          </section>
        )}

        <section id="enquire" aria-labelledby="enq-title" className="scroll-mt-20 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
          <h2 id="enq-title" className="text-xl font-semibold text-slate-900">Tell me when it registers</h2>
          <p className="mt-1 text-sm text-slate-600">We message you once {u.name} has a MahaRERA number, with the checked facts. We never share your number without your OK.</p>
          <div className="mt-4">
            <EnquiryForm agentSlug={HOUSE_AGENT} agentName="Avasetu" topic={`${u.name} (upcoming, not yet MahaRERA registered): tell me when it registers`}
              waMessage={`Hi, please tell me when ${u.name} (${u.area_name}) is registered with MahaRERA: ${url}`} />
          </div>
        </section>

        <footer className="border-t border-slate-200 pt-4 text-sm text-slate-600">
          Sources:{' '}
          {u.sources.map((s, i) => (
            <span key={s.name}>
              {i > 0 && '; '}
              {s.url ? <a href={s.url} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">{s.name}<span className="sr-only"> (opens in a new tab)</span></a> : s.name}
              {' '}(read {s.read_on})
            </span>
          ))}
          . Plans change before registration; MahaRERA&apos;s record, once filed, is the one that counts.
        </footer>
      </div>
    </MarketingShell>
  )
}
