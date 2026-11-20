import React from 'react'
import FromAboveVideo from '@/components/site/FromAboveVideo'
import { mapsEmbedKey, satelliteSrc } from '@/components/site/mapsEmbed'
import { jsonLdString } from '@/lib/marketing/seo'
import { shortMonth, type FromAbove } from '@/lib/site/fromAbove'

const SHOWN_SEASONS = 6   // the newest seasons in full; the earlier ones fold away

/** "<name> from space": the site season by season from Sentinel-2 (a median of every clear pass, made clearer by classic
 *  means, nothing drawn in), a line a season written from the pictures and the project's MahaRERA facts and checked
 *  (backend areastats/fromabove.py), one picture a year, and today's sharper view through Google's own embed (Google's
 *  imagery is shown, never stored). Nobody else shows a project this way, so the season lines are page text and the
 *  video's transcript (docs/plan/satellite-view.md, "Selling point"). */
export default function ProjectFromAbove({ view, shown, siteUrl }: { view: FromAbove; shown: string; siteUrl: string }) {
  const first = view.frames[0]
  const last = view.frames[view.frames.length - 1]
  const site = siteUrl.replace(/\/$/, '')
  const video = view.video
  const seasons = view.seasons
  const newest = seasons.slice(-SHOWN_SEASONS).reverse()
  const earlier = seasons.slice(0, Math.max(0, seasons.length - SHOWN_SEASONS)).reverse()
  const key = mapsEmbedKey()
  const transcript = seasons.map((s) => `${s.label}: ${s.line}`).join(' ')
  const ld = {
    '@context': 'https://schema.org',
    '@graph': [
      ...view.frames.map((f) => ({
        '@type': 'ImageObject', contentUrl: site + f.src, datePublished: f.day, creditText: view.credit,
        caption: `${shown} site from space, ${shortMonth(f.day)}, Sentinel-2 satellite`,
      })),
      ...(video ? [{
        '@type': 'VideoObject', name: `${shown} from space, ${shortMonth(video.from)} to ${shortMonth(video.to)}`,
        description: view.story, contentUrl: site + video.src, thumbnailUrl: site + video.poster,
        uploadDate: view.updated || video.to, creditText: view.credit, ...(transcript ? { transcript } : {}),
      }] : []),
    ],
  }
  const line = (s: { label: string; line: string }) => (
    <li key={s.label} className="flex gap-3 border-b border-slate-100 py-1.5 last:border-0">
      <span className="w-24 shrink-0 text-xs font-semibold text-slate-900">{s.label.replace('-', '–')}</span>
      <span className="text-sm text-slate-700">{s.line}</span>
    </li>
  )
  return (
    <section id="from-above" aria-labelledby="from-above-title" data-testid="from-above" className="scroll-mt-20">
      <h2 id="from-above-title" className="text-xl font-bold text-slate-900">
        {shown} from space, {first.year} to {last.year}
      </h2>
      <p className="mt-1 text-sm text-slate-700">{view.story}</p>
      {video && (
        <figure className="m-0 mt-3">
          <FromAboveVideo src={video.src} poster={video.poster} width={video.width} height={video.height}
            label={`${shown} site from space, month by month, ${shortMonth(video.from)} to ${shortMonth(video.to)}`} />
          <figcaption className="mt-1 text-center text-xs text-slate-600">
            Month by month, {shortMonth(video.from)} to {shortMonth(video.to)}: {video.months} clear months, October to May
            (the monsoon is under cloud).
          </figcaption>
        </figure>
      )}
      {newest.length > 0 && (
        <div className="mt-4" data-testid="from-above-seasons">
          <h3 className="text-base font-semibold text-slate-900">Season by season</h3>
          <ol className="mt-1 list-none p-0">{newest.map(line)}</ol>
          {earlier.length > 0 && (
            <details className="mt-1">
              <summary className="cursor-pointer text-sm font-semibold text-[var(--site-primary,#0f2340)]">
                Earlier seasons ({earlier.length})
              </summary>
              <ol className="mt-1 list-none p-0">{earlier.map(line)}</ol>
            </details>
          )}
        </div>
      )}
      <ol className="mt-4 grid list-none grid-cols-3 gap-2 p-0 sm:grid-cols-6">
        {view.frames.map((f) => (
          <li key={f.year}>
            <figure className="m-0">
              <img src={f.src} width={f.width} height={f.height} loading="lazy" decoding="async"
                alt={`${shown} site from space, ${shortMonth(f.day)}: the yellow ring is 100 m around the map pin`}
                className="h-auto w-full rounded-lg border border-slate-200" />
              <figcaption className="mt-1 text-xs font-semibold text-slate-900">{shortMonth(f.day)}</figcaption>
            </figure>
          </li>
        ))}
      </ol>
      {key && (
        <figure className="m-0 mt-4" data-testid="from-above-today">
          <iframe title={`${shown} today, Google satellite view`} src={satelliteSrc(key, view.pin.lat, view.pin.lon, 17)}
            loading="lazy" referrerPolicy="no-referrer-when-downgrade" allowFullScreen
            className="aspect-[4/3] w-full rounded-lg border border-slate-200 sm:aspect-[16/9]" />
          <figcaption className="mt-1 text-xs text-slate-600">Today, in Google&apos;s sharper satellite view, centred on the same pin.</figcaption>
        </figure>
      )}
      <p className="mt-2 text-xs text-slate-600">
        {view.where} Pictures are the middle of every clear pass, sharpened and colour-corrected by code; nothing is drawn in.
        The lines are written from the pictures and the MahaRERA filings, and say only what can be seen. {view.credit}.
      </p>
      <p className="mt-2 text-sm">
        <a href="/projects/from-space" className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary,#0f2340)] underline underline-offset-2">
          More Pune projects from space</a>
      </p>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
    </section>
  )
}
