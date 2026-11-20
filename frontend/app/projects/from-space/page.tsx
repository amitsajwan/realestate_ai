import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getFromSpace } from '@/lib/site/register'

// Every Pune project page that shows its site from space (backend areastats.fromabove), on one page: what no portal shows
// (owner 2026-11-20: "it can be our selling point, no one does it"). Each card links to the project's own section. A page
// other sites can link to; the projects' videos are also in /video-sitemap.xml.

export const revalidate = 600
const FROM_SPACE_PATH = '/projects/from-space'

export function generateMetadata(): Metadata {
  return pageMetadata(getMarketingConfig(), {
    title: 'Pune Projects From Space: Satellite Timelines, 2021 to Today',
    description: 'Watch Pune housing projects take shape from space: every clear Sentinel-2 satellite pass since 2021, month by month, with what changed each season, read against the MahaRERA filings.',
    path: FROM_SPACE_PATH,
  })
}

export default async function FromSpacePage() {
  const items = await getFromSpace()
  const cfg = getMarketingConfig()
  const ld = [
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' }, { name: 'From space', path: FROM_SPACE_PATH }]),
    { '@context': 'https://schema.org', '@type': 'ItemList', name: 'Pune projects from space',
      itemListElement: items.map((x, i) => ({ '@type': 'ListItem', position: i + 1, name: `${x.name} from space`,
        url: `${cfg.siteUrl}/projects/${x.slug}#from-above` })) },
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
        {items.length === 0 ? (
          <p className="text-slate-700">The first timelines are being made. <Link href="/projects" className="underline underline-offset-2">See all projects</Link>.</p>
        ) : (
          <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3" data-testid="from-space-list">
            {items.map((x) => (
              <li key={x.slug} className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                <Link href={`/projects/${x.slug}#from-above`} className="block no-underline">
                  <img src={x.picture} alt={`${x.name} from space, ${x.years[1]}`} width={600} height={600} loading="lazy"
                    className="aspect-square h-auto w-full object-cover" />
                  <div className="p-3">
                    <p className="font-semibold text-slate-900">{x.name}{x.place ? `, ${x.place}` : ''}</p>
                    <p className="text-xs font-semibold text-amber-700">{x.years[0]} to {x.years[1]}{x.video ? `, ${x.video.months} months` : ''}</p>
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
