import React from 'react'
import Link from 'next/link'
import { jsonLdString } from '@/lib/marketing/seo'
import type { MainVideo } from '@/lib/site/register'

/** ISO 8601 length for schema.org ("PT24S", "PT1M5S"); undefined when unknown. */
export function isoDuration(seconds?: number | null): string | undefined {
  if (!seconds || seconds <= 0) return undefined
  const s = Math.round(seconds)
  return s >= 60 ? `PT${Math.floor(s / 60)}M${s % 60 ? `${s % 60}S` : ''}` : `PT${s}S`
}

/** The VideoObject Google reads for the video on this page: name, picture, date and file are what it needs to show it. */
export function projectVideoJsonLd(video: MainVideo, shown: string, siteUrl: string, pageUrl: string): Record<string, unknown> | null {
  if (!video.poster || !video.uploaded_at) return null
  const site = siteUrl.replace(/\/$/, '')
  return {
    '@context': 'https://schema.org', '@type': 'VideoObject',
    name: `${shown}: homes, prices and MahaRERA details`,
    description: video.headline || `A short video of ${shown}, Pune: the homes, the prices and the MahaRERA registration.`,
    thumbnailUrl: site + video.poster, uploadDate: video.uploaded_at, contentUrl: site + video.url,
    duration: isoDuration(video.seconds), url: pageUrl,
  }
}

/** Our marketing video of the listing, played from our own server (owner 2026-11-20: stored by us rather than a YouTube or
 *  Facebook embed, so Google credits this page). Nothing loads until the buyer presses play: the poster stands in.
 *  `ld`: the page is the project's own (an agent's copy of it carries no structured data). */
export default function ProjectVideo({ video, shown, siteUrl, pageUrl, ld = true, watchHref }: {
  video: MainVideo; shown: string; siteUrl: string; pageUrl: string; ld?: boolean
  /** the video's own page (/projects/<slug>/video), linked from the project page so Google finds it */
  watchHref?: string
}) {
  const data = ld ? projectVideoJsonLd(video, shown, siteUrl, pageUrl) : null
  return (
    <section aria-labelledby="project-video-title" className="mt-8 max-w-md" data-testid="project-video">
      {data && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(data) }} />}
      <h2 id="project-video-title" className="text-xl font-bold text-slate-900">{shown} in a short video</h2>
      <figure className="m-0 mt-3">
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <video controls playsInline preload="none" poster={video.poster ?? undefined} src={video.url}
          aria-label={`${shown}: homes, prices and MahaRERA details`}
          className="aspect-[9/16] max-h-[75vh] w-full rounded-2xl bg-black object-contain" />
        <figcaption className="mt-1 text-sm text-slate-700">
          {video.headline || `${shown}: the homes, prices and MahaRERA number`}
          {video.seconds ? <span className="text-slate-500"> · {video.seconds} seconds</span> : null}
        </figcaption>
      </figure>
      {watchHref && (
        <Link href={watchHref} className="mt-1 inline-flex min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline underline-offset-2"
          data-testid="project-video-page">Open the video on its own page</Link>
      )}
    </section>
  )
}
