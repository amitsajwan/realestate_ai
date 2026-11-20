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
import { watchVideos, type WatchVideo } from '@/lib/site/projectVideos'
import { areaName, displayName, getRegisterProject, offerPrice, type Offer, type RegisterProject } from '@/lib/site/register'

// A project's video on a page of its own (owner 2026-11-20): Google shows a video in its video results only where the video is
// the page's main content, so the project page plays them and these pages are the ones the video sitemap names. The first
// video (the campaign's, else the agent's first) is /projects/<slug>/video; each further agent video /video/<key>
// (lib/site/projectVideos watchVideos).

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const KEY = /^[a-f0-9]{12}$/

type Got = { p: RegisterProject; w: WatchVideo; offer: Offer; all: WatchVideo[] }

/** The project and the asked video; null when either is missing. `key` null: the project's first video. */
export async function loadWatch(slug: string, key: string | null): Promise<Got | null> {
  if (!SLUG.test(slug) || (key !== null && !KEY.test(key))) return null
  const p = await getRegisterProject(slug)
  if (!p) return null
  const facts = await getPropertyFacts({ rera: p.regno, project: p.name, locality: p.area?.name }).catch(() => null)
  const offer = (facts as unknown as { offer?: Offer } | null)?.offer
  if (!offer) return null
  const all = watchVideos(p.slug, displayName(p), offer.main_video, offer.agent_videos)
  const w = key === null ? all[0] : all.find((x) => x.key === key)
    ?? (offer.agent_videos?.some((a) => a.key === key) ? all[0] : undefined)   // the first agent video's key: it lives at /video
  return w ? { p, w, offer, all } : null
}

const heading = (w: WatchVideo, area: string) => (area && w.key === null && w.title.includes(': homes,')
  ? w.title.replace(': homes,', `, ${area} video: homes,`) : w.title)

export async function watchMetadata(slug: string, key: string | null): Promise<Metadata> {
  const got = await loadWatch(slug, key)
  if (!got) return { title: 'Video not found', robots: { index: false } }
  const { p, w } = got
  const meta = pageMetadata(getMarketingConfig(), {
    title: heading(w, areaName(p) ?? ''),
    description: w.description,
    path: w.path,
  })
  return p.indexable ? meta : { ...meta, robots: { index: false, follow: true } }
}

export async function WatchPage({ slug, key }: { slug: string; key: string | null }) {
  const got = await loadWatch(slug, key)
  if (!got) notFound()
  const { p, w, offer, all } = got
  if (p.slug !== slug || (key !== null && w.key !== key)) permanentRedirect(w.path)
  const cfg = getMarketingConfig()
  const shown = displayName(p)
  const area = areaName(p) ?? ''
  const price = offerPrice(offer)
  const projectPath = `/projects/${p.slug}`
  const crumbs = breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' },
    { name: shown, path: projectPath }, { name: 'Video', path: w.path }])
  const others = all.filter((x) => x.path !== w.path)
  return (
    <MarketingShell hot={{ area: p.area?.slug, exclude: p.slug }}>
      <div className="mx-auto max-w-3xl px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(crumbs) }} />
        <nav aria-label="Breadcrumb" className="text-sm">
          <Link href={projectPath} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{shown}</Link>
        </nav>
        <h1 className="mt-1 text-3xl font-extrabold leading-tight text-slate-900">{heading(w, area)}</h1>
        <p className="mt-2 text-slate-800" data-testid="video-page-facts">
          {shown} is registered with MahaRERA as {p.regno}{area ? `, in ${area}, Pune` : ', Pune'}.
          {price ? ` Prices from ${price.from}.` : ''}
        </p>
        <ProjectVideo video={w.video} shown={shown} siteUrl={cfg.siteUrl} pageUrl={cfg.siteUrl + w.path} portrait={w.portrait}
          title={w.key === null && w.title.includes(': homes,') ? undefined : w.title} about={w.description} />
        {others.length > 0 && (
          <nav aria-label="More videos" className="mt-6" data-testid="video-page-more">
            <h2 className="text-lg font-semibold text-slate-900">More videos of {shown}</h2>
            <ul className="mt-1 list-none p-0">
              {others.map((x) => (
                <li key={x.path}>
                  <Link href={x.path} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{x.title}</Link>
                </li>
              ))}
            </ul>
          </nav>
        )}
        <p className="mt-6">
          <Link href={projectPath} className="inline-flex min-h-[48px] items-center rounded-full bg-[#f0b440] px-6 font-bold text-[#0f2340] no-underline">
            Full details, price sheet and MahaRERA status
          </Link>
        </p>
      </div>
    </MarketingShell>
  )
}

