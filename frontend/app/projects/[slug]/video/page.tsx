import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound, permanentRedirect } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import ProjectVideo from '@/components/site/ProjectVideo'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getPropertyFacts } from '@/lib/site/api'
import { videoPagePath } from '@/lib/site/projectVideos'
import { areaName, displayName, getRegisterProject, offerPrice, type MainVideo, type Offer, type RegisterProject } from '@/lib/site/register'

export const revalidate = 3600
export const dynamicParams = true

type Props = { params: Promise<{ slug: string }> }

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

/** The project and its kept listing video (propertyfacts mainvideo.py); null when either is missing. */
async function load(params: Props['params']): Promise<{ p: RegisterProject; video: MainVideo; offer: Offer } | null> {
  const { slug } = await params
  if (!SLUG.test(slug)) return null
  const p = await getRegisterProject(slug)
  if (!p) return null
  const facts = await getPropertyFacts({ rera: p.regno, project: p.name, locality: p.area?.name }).catch(() => null)
  const offer = (facts as unknown as { offer?: Offer } | null)?.offer
  return offer?.main_video ? { p, video: offer.main_video, offer } : null
}

const title = (shown: string, area: string) => `${shown}${area ? `, ${area}` : ''} video: homes, prices and MahaRERA details`

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const got = await load(params)
  if (!got) return { title: 'Video not found', robots: { index: false } }
  const { p, video } = got
  const shown = displayName(p)
  const meta = pageMetadata(getMarketingConfig(), {
    title: title(shown, areaName(p) ?? ''),
    description: video.headline || `A short video of ${shown}, Pune: the homes, the prices and the MahaRERA registration ${p.regno}.`,
    path: videoPagePath(p.slug),
  })
  return p.indexable ? meta : { ...meta, robots: { index: false, follow: true } }
}

/** A project's listing video on a page of its own (owner 2026-11-20): Google shows a video in its video results only where the
 *  video is the page's main content, so the project page plays it and this page is the one the video sitemap names. */
export default async function ProjectVideoPage({ params }: Props) {
  const got = await load(params)
  if (!got) notFound()
  const { p, video, offer } = got
  const { slug } = await params
  if (p.slug !== slug) permanentRedirect(videoPagePath(p.slug))
  const cfg = getMarketingConfig()
  const shown = displayName(p)
  const area = areaName(p) ?? ''
  const price = offerPrice(offer)
  const projectPath = `/projects/${p.slug}`
  const crumbs = breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' },
    { name: shown, path: projectPath }, { name: 'Video', path: videoPagePath(p.slug) }])
  return (
    <MarketingShell hot={{ area: p.area?.slug, exclude: p.slug }}>
      <div className="mx-auto max-w-3xl px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(crumbs) }} />
        <nav aria-label="Breadcrumb" className="text-sm">
          <Link href={projectPath} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{shown}</Link>
        </nav>
        <h1 className="mt-1 text-3xl font-extrabold leading-tight text-slate-900">{title(shown, area)}</h1>
        <p className="mt-2 text-slate-800" data-testid="video-page-facts">
          {shown} is registered with MahaRERA as {p.regno}{area ? `, in ${area}, Pune` : ', Pune'}.
          {price ? ` Prices from ${price.from}.` : ''}
        </p>
        <ProjectVideo video={video} shown={shown} siteUrl={cfg.siteUrl} pageUrl={cfg.siteUrl + videoPagePath(p.slug)} />
        <p className="mt-6">
          <Link href={projectPath} className="inline-flex min-h-[48px] items-center rounded-full bg-[#f0b440] px-6 font-bold text-[#0f2340] no-underline">
            Full details, price sheet and MahaRERA status
          </Link>
        </p>
      </div>
    </MarketingShell>
  )
}
