import React from 'react'
import FromAboveVideo from '@/components/site/FromAboveVideo'
import { jsonLdString } from '@/lib/marketing/seo'
import { shortMonth, type FromAbove } from '@/lib/site/fromAbove'

/** "<name> from above": one satellite picture a year around the checked pin, the measured change in code-written words, and
 *  what the numbers cover. Pictures are Sentinel-2 at 10 m, made clearer without generated detail (satellite-view.md). */
export default function ProjectFromAbove({ view, shown, siteUrl }: { view: FromAbove; shown: string; siteUrl: string }) {
  const first = view.frames[0]
  const last = view.frames[view.frames.length - 1]
  const site = siteUrl.replace(/\/$/, '')
  const video = view.video
  const ld = {
    '@context': 'https://schema.org',
    '@graph': [
      ...view.frames.map((f) => ({
        '@type': 'ImageObject', contentUrl: site + f.src, datePublished: f.day, creditText: view.credit,
        caption: `${shown} site from above, ${shortMonth(f.day)}, Sentinel-2 satellite`,
      })),
      ...(video ? [{
        '@type': 'VideoObject', name: `${shown} from above, ${shortMonth(video.from)} to ${shortMonth(video.to)}`,
        description: view.story, contentUrl: site + video.src, thumbnailUrl: site + video.poster, uploadDate: video.to,
        creditText: view.credit,
      }] : []),
    ],
  }
  return (
    <section aria-labelledby="from-above-title" data-testid="from-above">
      <h2 id="from-above-title" className="text-xl font-bold text-slate-900">
        {shown} from above, {first.year} to {last.year}
      </h2>
      <p className="mt-1 text-sm text-slate-700">{view.story}</p>
      {video && (
        <figure className="m-0 mt-3">
          <FromAboveVideo src={video.src} poster={video.poster} width={video.width} height={video.height}
            label={`${shown} site from above, one clear satellite picture a month, ${shortMonth(video.from)} to ${shortMonth(video.to)}`} />
          <figcaption className="mt-1 text-xs text-slate-600">
            Month by month, {shortMonth(video.from)} to {shortMonth(video.to)}: {video.months} clear passes, October to May
            (the monsoon months are under cloud). Each year&apos;s measure is below.
          </figcaption>
        </figure>
      )}
      <ol className="mt-3 grid list-none grid-cols-3 gap-2 p-0 sm:grid-cols-6">
        {view.frames.map((f) => (
          <li key={f.year}>
            <figure className="m-0">
              <img src={f.src} width={f.width} height={f.height} loading="lazy" decoding="async"
                alt={`${shown} site from above, ${shortMonth(f.day)}: the yellow ring is the map pin`}
                className="h-auto w-full rounded-lg border border-slate-200" />
              <figcaption className="mt-1 text-xs text-slate-700">
                <span className="font-semibold text-slate-900">{shortMonth(f.day)}</span>
                <span className="block">{f.built}% roofs, concrete</span>
              </figcaption>
            </figure>
          </li>
        ))}
      </ol>
      <p className="mt-2 text-xs text-slate-600">
        {view.where} Pictures sharpened and colour-corrected by code; nothing is drawn in. {view.credit}.
      </p>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
    </section>
  )
}
