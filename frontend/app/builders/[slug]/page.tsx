import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound, permanentRedirect } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getBuilder } from '@/lib/site/hubs'
import type { BuilderPage } from '@/lib/site/hubs'
import { monthYear } from '@/lib/site/register'

// One page per builder (docs/plan/rank-loop.md R6): every Pune project of the brand (backend areastats/brands.py), else of the
// MahaRERA promoter, in our register, towers merged, with the date record (docs/plan/project-pages.md, from Housiey).
// Rendered on first visit and kept for an hour, like the project pages.
export const revalidate = 3600
export const dynamicParams = true
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  return []
}

type Props = { params: Promise<{ slug: string }> }

const n = (v: number | null | undefined) => (v == null ? null : v.toLocaleString('en-IN'))

async function load(slug: string): Promise<BuilderPage | null> {
  const b = await getBuilder(slug)
  if (b && 'redirect' in b) permanentRedirect(`/builders/${b.redirect}`)   // a company now counted under its brand
  return b
}

/** The record in one sentence; null when too few projects have both dates to state one. */
function recordLine(b: BuilderPage): string | null {
  if (!b.record_ok) return null
  if (b.moved_later === 0) return `None of ${b.name}'s ${b.with_dates} Pune projects with both dates on MahaRERA moved its completion date ${b.moved_min} months or more later.`
  return `${b.moved_later} of ${b.name}'s ${b.with_dates} Pune projects with both dates on MahaRERA moved the completion date ${b.moved_min} months or more later`
    + (b.avg_months_later ? `, by ${b.avg_months_later} months on average.` : '.')
}

/** Questions buyers search about a builder, answered from the page's facts only. */
function faq(b: BuilderPage): { q: string; a: string }[] {
  const out: { q: string; a: string }[] = []
  const building = b.projects.filter((p) => p.active)
  out.push({ q: `How many projects does ${b.name} have in Pune?`,
    a: `MahaRERA lists ${b.projects_count} Pune project${b.projects_count === 1 ? '' : 's'} by ${b.name} in our register (towers and phases counted once)`
      + `${b.areas.length ? `, in ${b.areas.join(', ')}` : ''}; ${b.active} ${b.active === 1 ? 'is' : 'are'} being built or recently finished.` })
  const rec = recordLine(b)
  if (rec) out.push({ q: `Does ${b.name} deliver on time in Pune?`,
    a: `${rec} That compares the completion date filed today with the one filed at registration, leaving out MahaRERA's blanket extensions for all projects. MahaRERA does not publish handover dates, so check the occupancy certificate for a finished project.` })
  if (building.length) out.push({ q: `Which ${b.name} projects are being built in Pune?`,
    a: building.slice(0, 8).map((p) => p.name + (p.completion_now ? ` (completion filed ${monthYear(p.completion_now)})` : '')).join('; ')
      + (building.length > 8 ? `; and ${building.length - 8} more on this page.` : '.') })
  if (b.brand && b.companies.length > 1) out.push({ q: `Which companies does ${b.name} register its Pune projects under?`,
    a: `On MahaRERA, ${b.name}'s Pune projects are filed by ${b.companies.length} companies, including ${b.companies.slice(0, 4).map((c) => c.name).join(', ')}.` })
  return out
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const b = await load((await params).slug)
  if (!b) return { title: 'Builder not found', robots: { index: false } }
  const rec = b.record_ok ? ` ${b.moved_later} of ${b.with_dates} moved their completion date ${b.moved_min}+ months.` : ''
  const meta = pageMetadata(getMarketingConfig(), {
    title: b.record_ok ? `${b.name} Projects in Pune (${b.projects_count}): Possession Dates and Delays`
      : `${b.name} projects in Pune: ${b.projects_count} on MahaRERA`,
    description: `Every Pune project by ${b.name} on MahaRERA: ${b.projects_count} projects, completion dates, homes booked.${rec}`,
    path: `/builders/${b.slug}`,
  })
  return b.indexable ? meta : { ...meta, robots: { index: false, follow: true } }   // one project only: the project page is enough
}

export default async function BuilderPageView({ params }: Props) {
  const b = await load((await params).slug)
  if (!b) notFound()
  const cfg = getMarketingConfig()
  const qa = faq(b)
  const rec = recordLine(b)
  const ld = {
    '@context': 'https://schema.org', '@type': 'Organization', name: b.name, url: `${cfg.siteUrl}/builders/${b.slug}`,
    areaServed: 'Pune',
    owns: b.projects.slice(0, 50).map((p) => ({ '@type': 'ApartmentComplex', name: p.name, url: `${cfg.siteUrl}/projects/${p.slug}` })),
  }
  const active = b.projects.filter((p) => p.active)
  const done = b.projects.filter((p) => !p.active)
  const moved = b.projects.filter((p) => (p.months_later ?? 0) >= b.moved_min).sort((x, y) => (y.months_later ?? 0) - (x.months_later ?? 0))
  return (
    <MarketingShell>
      <article className="mx-auto max-w-4xl px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Builders', path: '/builders' }, { name: b.name, path: `/builders/${b.slug}` },
        ])) }} />
        {qa.length > 0 && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString({
          '@context': 'https://schema.org', '@type': 'FAQPage',
          mainEntity: qa.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
        }) }} />}
        <nav aria-label="Breadcrumb" className="text-sm">
          <Link href="/builders" className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">All builders in Pune</Link>
        </nav>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{b.name} projects in Pune</h1>
        <p className="mt-3 text-lg text-slate-800">
          Our MahaRERA register holds {b.projects_count} Pune project{b.projects_count === 1 ? '' : 's'} by {b.name}
          {b.areas.length > 0 && <> in {b.areas.join(', ')}</>}; {b.active} still being built or recently finished.
        </p>
        <dl className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white p-3"><dt className="text-xs text-slate-600">Projects</dt><dd className="text-lg font-semibold">{b.projects_count}</dd></div>
          {b.units_total ? <div className="rounded-xl border border-slate-200 bg-white p-3"><dt className="text-xs text-slate-600">Homes listed</dt><dd className="text-lg font-semibold">{n(b.units_total)}</dd></div> : null}
          {b.units_booked ? <div className="rounded-xl border border-slate-200 bg-white p-3"><dt className="text-xs text-slate-600">Homes booked</dt><dd className="text-lg font-semibold">{n(b.units_booked)}</dd></div> : null}
          {b.record_ok && (
            <div className="rounded-xl border border-slate-200 bg-white p-3"><dt className="text-xs text-slate-600">Completion date moved {b.moved_min}+ months</dt>
              <dd className="text-lg font-semibold">{b.moved_later} of {b.with_dates}</dd>
              {b.avg_months_later ? <dd className="text-xs text-slate-600">by {b.avg_months_later} months on average</dd> : null}</div>
          )}
        </dl>

        <section className="mt-9" aria-labelledby="record-title" data-testid="record">
          <h2 id="record-title" className="text-xl font-semibold text-slate-900">{b.name}&apos;s date record</h2>
          {rec ? <p className="mt-2 text-slate-800">{rec}</p>
            : <p className="mt-2 text-slate-800">Only {b.with_dates} of these projects have both dates on MahaRERA: too few to judge {b.name}&apos;s record. Each project&apos;s page shows its own dates.</p>}
          {moved.length > 0 && (
            <ul className="mt-3 list-none space-y-1 p-0">
              {moved.slice(0, 10).map((p) => (
                <li key={p.slug}><Link href={`/projects/${p.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">{p.name}</Link>
                  <span className="ml-2 text-sm text-slate-600">moved {p.months_later} months later{p.completion_now ? `, now ${monthYear(p.completion_now)}` : ''}</span></li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-slate-600">
            How we count: the completion date the builder files with MahaRERA today against the one filed at registration. Moves under {b.moved_min} months
            and MahaRERA&apos;s blanket extensions for all projects (4 months in 2026) are left out. MahaRERA does not publish handover dates, so a date
            that did not move is not proof of an on-time handover.
          </p>
        </section>

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

        {b.brand && b.companies.length > 0 && (
          <section className="mt-9" aria-labelledby="companies-title" data-testid="companies">
            <h2 id="companies-title" className="text-xl font-semibold text-slate-900">Companies on MahaRERA</h2>
            <p className="mt-2 text-slate-800">Builders often register each project under its own company. We count a project as {b.name}&apos;s when the
              company&apos;s name says so, or the project is sold under the {b.name} name.</p>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-slate-800">
              {b.companies.map((c) => <li key={c.name}>{c.name} <span className="text-sm text-slate-600">({c.projects} project{c.projects === 1 ? '' : 's'})</span></li>)}
            </ul>
          </section>
        )}

        {qa.length > 0 && (
          <section className="mt-9" aria-labelledby="faq-title">
            <h2 id="faq-title" className="text-xl font-semibold text-slate-900">Questions buyers ask</h2>
            <div className="mt-3 space-y-2">
              {qa.map((f) => (
                <details key={f.q} className="rounded-xl border border-slate-200 bg-white px-4 py-2">
                  <summary className="min-h-[44px] cursor-pointer py-2 font-semibold text-slate-900">{f.q}</summary>
                  <p className="pb-2 text-slate-800">{f.a}</p>
                </details>
              ))}
            </div>
          </section>
        )}

        <p className="mt-10 border-t border-slate-200 pt-4 text-sm text-slate-600">
          Source: {b.source}. Towers and phases of one project are counted once. Check each project&apos;s MahaRERA record and your
          agreement before you book.
        </p>
      </article>
    </MarketingShell>
  )
}
