import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import ProjectCard from '@/components/site/ProjectCard'
import { getMarketingConfig } from '@/lib/marketing/config'
import { getLocality } from '@/lib/marketing/localities'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getCatalog } from '@/lib/site/api'
import { type AnyFilter, MIN_PROJECTS, filterPath, filterProjects, filterTitle } from '@/lib/site/filters'
import { formatPrice, groupIndian } from '@/lib/site/format'
import { formatDay } from '@/lib/site/projects'

/** The matching projects, or null when the area is unknown or fewer than MIN_PROJECTS match (the page is then a 404). */
async function load(f: AnyFilter | null, areaSlug: string) {
  const area = getLocality(areaSlug)
  if (!f || !area) return null
  const matches = filterProjects(await getCatalog(area.listingName), area, f)
  return matches.length >= MIN_PROJECTS ? { area, matches } : null
}

export async function filterMetadata(f: AnyFilter | null, areaSlug: string): Promise<Metadata> {
  const r = await load(f, areaSlug)
  if (!f || !r) return { title: 'Not found', robots: { index: false } }
  const title = filterTitle(f, r.area)
  const what = f.kind === 'bhk' ? `${f.bhk} BHK homes` : `homes ${f.band.label}`
  return pageMetadata(getMarketingConfig(), {
    title: `${title}: ${r.matches.length} projects compared`,
    description: `${r.matches.length} projects in ${r.area.name} with ${what}: carpet area, price and price per sq ft as quoted by local agents, and each project's MahaRERA completion date.`,
    path: filterPath(f, r.area),
  })
}

/** "2 BHK in Wagholi": every matching home across the area's checked projects in one table, then the projects themselves. */
export default async function FilterPage({ filter, areaSlug }: { filter: AnyFilter | null; areaSlug: string }) {
  const r = await load(filter, areaSlug)
  if (!filter || !r) notFound()
  const { area, matches } = r
  const cfg = getMarketingConfig()
  const title = filterTitle(filter, area)
  const path = filterPath(filter, area)
  const rows = matches.flatMap((m) => m.homes.map((h) => ({ p: m.project, h })))
  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl px-4 py-10 sm:py-14" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Area guides', path: '/localities' }, { name: `${area.name}, Pune`, path: `/localities/${area.slug}` }, { name: title, path },
        ])) }} />
        <nav aria-label="Breadcrumb" className="text-sm">
          <Link href={`/localities/${area.slug}`} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{area.name} buyer guide</Link>
        </nav>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{title}</h1>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800">
          {matches.length} projects in {area.name}, compared on carpet area and price per sq ft, with the completion date each builder has filed on MahaRERA.
          Compare the price per sq ft of carpet area, not the headline price.
        </p>

        <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-2 py-2 font-semibold sm:px-3">Project</th><th className="px-2 py-2 font-semibold sm:px-3">Home</th>
                <th className="px-2 py-2 font-semibold sm:px-3">Carpet</th><th className="px-2 py-2 font-semibold sm:px-3">Price</th>
                <th className="px-2 py-2 font-semibold sm:px-3">Per sq ft</th><th className="px-2 py-2 font-semibold sm:px-3">MahaRERA date</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ p, h }) => (
                <tr key={p.slug + h.label + h.carpet_sqft} className="border-t border-slate-100">
                  <td className="px-2 py-2 sm:px-3"><Link href={`/projects/${p.slug}`} className="font-semibold text-[#0f2340] underline underline-offset-2">{p.name}</Link></td>
                  <td className="px-2 py-2 sm:px-3">{h.label}</td>
                  <td className="px-2 py-2 sm:px-3">{groupIndian(h.carpet_sqft)} sq ft</td>
                  <td className="px-2 py-2 font-semibold sm:px-3">{formatPrice(h.price_inr)}</td>
                  <td className="px-2 py-2 sm:px-3">₹{groupIndian(h.price_per_sqft)}</td>
                  <td className="px-2 py-2 sm:px-3">{formatDay(p.rera?.completion_now) || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-slate-600">
          Prices as quoted by the agent named on each project page; builders change them often. Confirm the price, the floor and extra charges
          (parking, GST, stamp duty) before you book. MahaRERA dates are from the public record on the date shown on each project page.
        </p>

        <ul className="mt-8 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {matches.map((m) => <li key={m.project.slug}><ProjectCard p={m.project} href={`/projects/${m.project.slug}`} /></li>)}
        </ul>

        <p className="mt-8">
          <Link href={`/localities/${area.slug}`} className="font-semibold text-[#0f2340] underline underline-offset-2">Who {area.name} suits, how to get around and what to check</Link>
        </p>
      </div>
    </MarketingShell>
  )
}
