import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import EsriPastPictures from '@/components/site/EsriPastPictures'
import EsriWaybackOnTap from '@/components/site/EsriWaybackOnTap'
import FromAboveVideo from '@/components/site/FromAboveVideo'
import { mapsEmbedKey, satelliteSrc } from '@/components/site/mapsEmbed'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { shortMonth, videoPace } from '@/lib/site/fromAbove'
import { areaFromSpacePath, getAreaFromSpace, type AreaFromSpace } from '@/lib/site/areaFromSpace'
import { areaGuidePath } from '@/lib/site/areaGuide'

// An area from space on a page of its own, the video first (as the projects' watch pages: Google shows a video result only
// from a page where the video is the main thing). The area guide keeps its section; the video sitemap points here. Made by
// the backend's daily pass (areastats/areaspace.py).

export const revalidate = 3600
export const dynamicParams = true
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  return []
}

type Props = { params: Promise<{ slug: string }> }

async function load(slug: string): Promise<AreaFromSpace | null> {
  const view = await getAreaFromSpace(slug)
  return view?.video ? view : null
}

const span = (v: AreaFromSpace) => `${v.frames[0].year} to ${v.frames[v.frames.length - 1].year}`

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const view = await load((await params).slug)
  if (!view) return { title: 'Not found', robots: { index: false } }
  return pageMetadata(getMarketingConfig(), {
    title: `${view.name}, Pune From Space: Satellite Timeline ${span(view)}`,
    description: `${view.story} Month-by-month Sentinel-2 satellite video of ${view.name} with what changed each season.`.slice(0, 300),
    path: areaFromSpacePath(view.slug),
    image: { path: view.video!.poster, width: view.video!.width, height: view.video!.height, alt: `${view.name} from space` },
  })
}

export default async function AreaFromSpacePage({ params }: Props) {
  const view = await load((await params).slug)
  if (!view) notFound()
  const video = view.video!
  const cfg = getMarketingConfig()
  const site = cfg.siteUrl.replace(/\/$/, '')
  const path = areaFromSpacePath(view.slug)
  const key = mapsEmbedKey()
  const ld = [
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Area guides', path: '/localities' },
      { name: `${view.name}, Pune`, path: areaGuidePath(view.slug) }, { name: 'From space', path }]),
    { '@context': 'https://schema.org', '@type': 'VideoObject', name: `${view.name}, Pune from space, ${shortMonth(video.from)} to ${shortMonth(video.to)}`,
      description: view.story, contentUrl: site + video.src, thumbnailUrl: site + video.poster, uploadDate: view.updated || video.to,
      creditText: view.credit, transcript: view.seasons.map((s) => `${s.label}: ${s.line}`).join(' ') || undefined },
  ]
  return (
    <MarketingShell>
      <div className="mx-auto max-w-4xl space-y-5 px-4 py-6 sm:py-8" style={AVASETU_SITE_VARS}>
        {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
        <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
          <Link href="/localities" className="underline underline-offset-2">Area guides</Link> /{' '}
          <Link href={areaGuidePath(view.slug)} className="underline underline-offset-2">{view.name}</Link>
        </nav>
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{view.name}, Pune from space, {span(view)}</h1>
        <FromAboveVideo src={video.src} poster={video.poster} width={video.width} height={video.height}
          label={`${view.name} from space, ${videoPace(video).by}, ${shortMonth(video.from)} to ${shortMonth(video.to)}`} />
        <p className="text-base leading-relaxed text-slate-800">{view.story}</p>
        {/* the video ends on the newest Sentinel pass; Google's sharper view of today follows it (shown, never stored) */}
        {key && (
          <figure className="m-0" data-testid="area-watch-today">
            <iframe title={`${view.name} today, Google satellite view`} src={satelliteSrc(key, view.middle.lat, view.middle.lon, 14)}
              loading="lazy" referrerPolicy="no-referrer-when-downgrade" allowFullScreen
              className="aspect-[4/3] w-full rounded-lg border border-slate-200 sm:aspect-[16/9]" />
            <figcaption className="mt-1 text-xs text-slate-600">Today, from Google satellite, centred on the same middle of {view.name}.</figcaption>
          </figure>
        )}
        {view.esriPast
          ? <EsriPastPictures past={view.esriPast} lat={view.middle.lat} lon={view.middle.lon} name={view.name} centredOn={`the middle of ${view.name}`} className="" />
          : <EsriWaybackOnTap lat={view.middle.lat} lon={view.middle.lon} label={view.name} zoom={14} centredOn={`the middle of ${view.name}`} />}
        <p className="text-sm text-slate-600">
          {videoPace(video).count}, {shortMonth(video.from)} to {shortMonth(video.to)}: every clear pass of the Sentinel-2
          satellite over {view.name}, October to May (the monsoon is under cloud). A new picture is added every season.
        </p>
        {view.seasons.length > 0 && (
          <section aria-labelledby="seasons-title">
            <h2 id="seasons-title" className="text-lg font-semibold text-slate-900">Season by season</h2>
            <ol className="mt-1 list-none p-0" data-testid="area-watch-seasons">
              {[...view.seasons].reverse().map((s) => (
                <li key={s.label} className="flex gap-3 border-b border-slate-100 py-1.5 last:border-0">
                  <span className="w-24 shrink-0 text-xs font-semibold text-slate-900">{s.label.replace('-', '–')}</span>
                  <span className="text-sm text-slate-700">{s.line}</span>
                </li>
              ))}
            </ol>
          </section>
        )}
        <p className="flex flex-wrap gap-x-5">
          <Link href={areaGuidePath(view.slug)} className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary,#0f2340)] underline underline-offset-2">
            {view.name} area guide: projects, MahaRERA counts and landmarks</Link>
          <Link href="/projects/from-space" className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary,#0f2340)] underline underline-offset-2">
            More of Pune from space</Link>
        </p>
        <p className="text-xs text-slate-600">
          {view.where} Pictures are the middle of every clear pass, sharpened and colour-corrected by code; nothing is drawn in.
          The lines are written from the pictures and the area&apos;s MahaRERA counts, and say only what can be seen. {view.credit}.
        </p>
      </div>
    </MarketingShell>
  )
}
