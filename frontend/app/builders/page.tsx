import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getBuilders } from '@/lib/site/hubs'
import type { BuilderCard } from '@/lib/site/hubs'

// Every builder page in one place (docs/plan/project-pages.md, from Housiey): the brands first, with their date record, then the
// other builders with two or more projects. Links every builder page within two clicks of the home page.
export const revalidate = 3600

const OTHERS = 200

export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata(getMarketingConfig(), {
    title: 'Builders in Pune: Projects, Possession Dates and Delays',
    description: 'Pune builders and their MahaRERA projects: how many each has, and how often each moved its completion date later.',
    path: '/builders',
  })
}

function record(b: BuilderCard): string {
  if (!b.record_ok) return `${b.projects} projects`
  return `${b.projects} projects · ${b.moved_later} of ${b.with_dates} moved their date${b.avg_months_later ? ` (${b.avg_months_later} months on average)` : ''}`
}

export default async function BuildersIndex() {
  const cfg = getMarketingConfig()
  const all = await getBuilders()
  const brands = all.filter((b) => b.brand).sort((a, b) => b.projects - a.projects)
  const others = all.filter((b) => !b.brand).slice(0, OTHERS)
  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl px-4 py-10 sm:py-14" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Builders', path: '/builders' },
        ])) }} />
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Builders in Pune</h1>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800">
          Every builder with projects in our MahaRERA register for Pune, and how often each moved its completion date 3 months or more later
          (MahaRERA&apos;s blanket extensions for all projects left out). A record is shown once 5 or more of a builder&apos;s projects have both dates.
        </p>
        {brands.length > 0 && (
          <section className="mt-10" aria-labelledby="brands-title">
            <h2 id="brands-title" className="text-2xl font-bold text-slate-900">Major builders</h2>
            <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2" data-testid="brands">
              {brands.map((b) => (
                <li key={b.slug}>
                  <Link href={`/builders/${b.slug}`} className="block h-full min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
                    <span className="block font-semibold text-[#0f2340]">{b.name}</span>
                    <span className="block text-sm text-slate-600">{record(b)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
        {others.length > 0 && (
          <section className="mt-10" aria-labelledby="others-title">
            <h2 id="others-title" className="text-2xl font-bold text-slate-900">Other builders</h2>
            <ul className="mt-3 list-none columns-1 p-0 sm:columns-2">
              {others.map((b) => (
                <li key={b.slug} className="break-inside-avoid py-1">
                  <Link href={`/builders/${b.slug}`} className="font-medium text-[#0f2340] underline underline-offset-2">{b.name}</Link>
                  <span className="ml-2 text-sm text-slate-600">{record(b)}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
        {all.length === 0 && <p className="mt-8 rounded-xl bg-slate-50 p-4 text-slate-700">The builder list is not available right now.</p>}
        <p className="mt-10 text-sm text-slate-600">From MahaRERA&apos;s public records. This is general information, not investment or legal advice.</p>
      </div>
    </MarketingShell>
  )
}
