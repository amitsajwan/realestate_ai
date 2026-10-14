import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getBuilder } from '@/lib/site/hubs'
import { monthYear } from '@/lib/site/register'

// One page per builder (docs/plan/rank-loop.md R6): every Pune project of the promoter in our MahaRERA register, towers merged.
// Rendered on first visit and kept for an hour, like the project pages.
export const revalidate = 3600
export const dynamicParams = true
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  return []
}

type Props = { params: Promise<{ slug: string }> }

const n = (v: number | null | undefined) => (v == null ? null : v.toLocaleString('en-IN'))

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const b = await getBuilder((await params).slug)
  if (!b) return { title: 'Builder not found', robots: { index: false } }
  const meta = pageMetadata(getMarketingConfig(), {
    title: `${b.name} projects in Pune: ${b.projects_count} on MahaRERA`,
    description: `Every Pune project by ${b.name} in the MahaRERA register: completion dates, homes booked` +
      (b.with_dates ? `, and how often the date moved (${b.moved_later} of ${b.with_dates}).` : '.'),
    path: `/builders/${b.slug}`,
  })
  return b.indexable ? meta : { ...meta, robots: { index: false, follow: true } }   // one project only: the project page is enough
}

export default async function BuilderPageView({ params }: Props) {
  const b = await getBuilder((await params).slug)
  if (!b) notFound()
  const cfg = getMarketingConfig()
  const ld = {
    '@context': 'https://schema.org', '@type': 'Organization', name: b.name, url: `${cfg.siteUrl}/builders/${b.slug}`,
    areaServed: 'Pune',
    owns: b.projects.slice(0, 50).map((p) => ({ '@type': 'ApartmentComplex', name: p.name, url: `${cfg.siteUrl}/projects/${p.slug}` })),
  }
  const active = b.projects.filter((p) => p.active)
  const done = b.projects.filter((p) => !p.active)
  return (
    <MarketingShell>
      <article className="mx-auto max-w-4xl px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' }, { name: b.name, path: `/builders/${b.slug}` },
        ])) }} />
        <nav aria-label="Breadcrumb" className="text-sm">
          <Link href="/projects" className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">All projects</Link>
        </nav>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{b.name}: projects in Pune</h1>
        <p className="mt-3 text-lg text-slate-800">
          Our MahaRERA register holds {b.projects_count} Pune project{b.projects_count === 1 ? '' : 's'} by {b.name}
          {b.areas.length > 0 && <> in {b.areas.join(', ')}</>}; {b.active} still being built or recently finished.
        </p>
        <dl className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white p-3"><dt className="text-xs text-slate-600">Projects</dt><dd className="text-lg font-semibold">{b.projects_count}</dd></div>
          {b.units_total ? <div className="rounded-xl border border-slate-200 bg-white p-3"><dt className="text-xs text-slate-600">Homes listed</dt><dd className="text-lg font-semibold">{n(b.units_total)}</dd></div> : null}
          {b.units_booked ? <div className="rounded-xl border border-slate-200 bg-white p-3"><dt className="text-xs text-slate-600">Homes booked</dt><dd className="text-lg font-semibold">{n(b.units_booked)}</dd></div> : null}
          {b.with_dates > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-3"><dt className="text-xs text-slate-600">Completion date moved later</dt>
              <dd className="text-lg font-semibold">{b.moved_later} of {b.with_dates}</dd>
              {b.avg_months_later ? <dd className="text-xs text-slate-600">by {b.avg_months_later} months on average</dd> : null}</div>
          )}
        </dl>

        {[['Projects being built', active], ['Finished more than a year ago', done]].map(([title, list]) => (list as typeof b.projects).length > 0 && (
          <section key={title as string} className="mt-9" aria-label={title as string}>
            <h2 className="text-xl font-semibold text-slate-900">{title as string}</h2>
            <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
              {(list as typeof b.projects).map((p) => (
                <li key={p.slug}>
                  <Link href={`/projects/${p.slug}`} className="block h-full min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
                    <span className="block font-semibold text-[#0f2340]">{p.name}</span>
                    <span className="block text-sm text-slate-600">
                      {[p.area, p.completion_now ? `possession filed ${monthYear(p.completion_now)}` : null,
                        p.units_total ? (p.units_booked != null ? `${n(p.units_booked)}/${n(p.units_total)} booked` : `${n(p.units_total)} homes`) : null,
                        p.months_later ? `moved ${p.months_later} months later` : null].filter(Boolean).join(' · ')}
                    </span>
                    <span className="block font-mono text-xs text-slate-500">MahaRERA {p.regno}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}

        <p className="mt-10 border-t border-slate-200 pt-4 text-sm text-slate-600">
          Source: {b.source}. Towers and phases of one project are counted once. Check each project&apos;s MahaRERA record and your
          agreement before you book.
        </p>
      </article>
    </MarketingShell>
  )
}
