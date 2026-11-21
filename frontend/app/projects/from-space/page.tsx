import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getFromSpace } from '@/lib/site/register'
import { areaFromSpacePath, getAreasFromSpace } from '@/lib/site/areaFromSpace'
import { videoPace } from '@/lib/site/fromAbove'

// Every Pune project page that shows its site from space (backend areastats.fromabove), on one page: what no portal shows
// (owner 2026-11-20: "it can be our selling point, no one does it"). Each card links to the project's own section. A page
// other sites can link to; the projects' videos are also in /video-sitemap.xml. The areas we cover come first, each a few
// kilometres around its middle (backend areastats.areaspace), each card to the area's own watch page.

export const revalidate = 600
const FROM_SPACE_PATH = '/projects/from-space'

export function generateMetadata(): Metadata {
  return pageMetadata(getMarketingConfig(), {
    title: 'Pune Projects From Space: Satellite Timelines, 2021 to Today',
    description: 'Watch Pune areas and housing projects take shape from space: every clear Sentinel-2 satellite pass, month by month, with what changed each season, read against the MahaRERA filings.',
    path: FROM_SPACE_PATH,
  })
}

export default async function FromSpacePage() {
  const [items, areas] = await Promise.all([getFromSpace(), getAreasFromSpace()])
  const cfg = getMarketingConfig()
  const ld = [
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' }, { name: 'From space', path: FROM_SPACE_PATH }]),
    { '@context': 'https://schema.org', '@type': 'ItemList', name: 'Pune projects from space',
      itemListElement: [
        ...areas.map((x) => ({ name: `${x.name}, Pune from space`, url: `${cfg.siteUrl}${areaFromSpacePath(x.slug)}` })),
        ...items.map((x) => ({ name: `${x.name} from space`, url: `${cfg.siteUrl}/projects/${x.slug}/from-space` })),
      ].map((x, i) => ({ '@type': 'ListItem', position: i + 1, ...x })) },
  ]
  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
        <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
          <Link href="/" className="underline underline-offset-2">Home</Link> / <Link href="/projects" className="underline underline-offset-2">Projects</Link>
        </nav>
        <h1 className="text-3xl font-bold text-slate-900">Pune projects from space</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-slate-800">
          Every clear pass of the European Sentinel-2 satellite since 2021, month by month, over each project&apos;s own map pin:
          watch fields cleared and buildings appear, with a line for each season saying what changed, read against the
          project&apos;s MahaRERA filings. The pictures are 10 m to a pixel, sharpened by code with nothing drawn in. A new picture
          is added every season.
        </p>
        {areas.length > 0 && (
          <section aria-labelledby="areas-title" className="space-y-3">
            <h2 id="areas-title" className="text-xl font-semibold text-slate-900">Pune areas from space</h2>
            <p className="max-w-3xl text-slate-700">A few kilometres around the middle of each area we cover, season by season:
              where fields gave way to new homes, read against how many projects registered with MahaRERA each year.</p>
            <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-4" data-testid="areas-from-space-list">
              {areas.map((x) => (
                <li key={x.slug} className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                  <Link href={areaFromSpacePath(x.slug)} className="block no-underline">
                    <img src={x.picture} alt={`${x.name}, Pune from space, ${x.years[1]}`} width={600} height={600} loading="lazy"
                      className="aspect-square h-auto w-full object-cover" />
                    <div className="p-3">
                      <p className="font-semibold text-slate-900">{x.name}</p>
                      <p className="text-xs font-semibold text-amber-700">{x.years[0]} to {x.years[1]}{x.video ? `, ${videoPace(x.video).count}` : ''}</p>
                      <p className="mt-1 line-clamp-3 text-sm text-slate-700">{x.story}</p>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
        {areas.length > 0 && items.length > 0 && <h2 className="text-xl font-semibold text-slate-900">Projects from space</h2>}
        {items.length === 0 ? (
          <p className="text-slate-700">The first timelines are being made. <Link href="/projects" className="underline underline-offset-2">See all projects</Link>.</p>
        ) : (
          <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3" data-testid="from-space-list">
            {items.map((x) => (
              <li key={x.slug} className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                <Link href={`/projects/${x.slug}/from-space`} className="block no-underline">
                  <img src={x.picture} alt={`${x.name} from space, ${x.years[1]}`} width={600} height={600} loading="lazy"
                    className="aspect-square h-auto w-full object-cover" />
                  <div className="p-3">
                    <p className="font-semibold text-slate-900">{x.name}{x.place ? `, ${x.place}` : ''}</p>
                    <p className="text-xs font-semibold text-amber-700">{x.years[0]} to {x.years[1]}{x.video ? `, ${videoPace(x.video).count}` : ''}</p>
                    <p className="mt-1 line-clamp-3 text-sm text-slate-700">{x.story}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
        <p className="text-xs text-slate-600">Contains modified Copernicus Sentinel data. Each project&apos;s ring is 100 m around its map pin and takes in neighbouring plots.</p>
      </div>
    </MarketingShell>
  )
}
