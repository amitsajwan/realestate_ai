import React from 'react'
import EsriPastPictures from '@/components/site/EsriPastPictures'
import EsriWaybackOnTap from '@/components/site/EsriWaybackOnTap'
import type { EsriPast } from '@/lib/site/esriPast'
import FromAboveProof from '@/components/site/FromAboveProof'
import FromAboveVideo from '@/components/site/FromAboveVideo'
import { mapsEmbedKey, satelliteSrc } from '@/components/site/mapsEmbed'
import { jsonLdString } from '@/lib/marketing/seo'
import { shortMonth, videoPace, type FromAbove } from '@/lib/site/fromAbove'

const SHOWN_SEASONS = 3   // the newest seasons as the current reading; the rest sit in the proof badge, still page text

/** "<name> from above": Google's sharp satellite view first, as the picture a buyer looks at (Google's imagery is shown through
 *  its embed, never stored or read by us, and has no date), Esri's sharp past pictures on tap (EsriWaybackOnTap), then the newest Sentinel-2 season as the latest reading, with the
 *  project's registration and filed possession around it. The Sentinel timeline (10 m a pixel: proof that work went on, not a
 *  view of the plot) sits below as a badge that opens to the video and the yearly row; its season lines stay page text and the
 *  video's transcript, which is what search gets from it (owner 2026-11-21; docs/plan/satellite-view.md, "Google first, the
 *  timeline as proof"). */
export default function ProjectFromAbove({ view, shown, siteUrl, possession = '', esriPast = null }: {
  view: FromAbove; shown: string; siteUrl: string; possession?: string; esriPast?: EsriPast | null
}) {
  const first = view.frames[0]
  const last = view.frames[view.frames.length - 1]
  const site = siteUrl.replace(/\/$/, '')
  const video = view.video
  const seasons = view.seasons
  const latest = seasons[seasons.length - 1]
  const newest = seasons.slice(-SHOWN_SEASONS - 1, -1).reverse()
  const earlier = seasons.slice(0, Math.max(0, seasons.length - SHOWN_SEASONS - 1)).reverse()
  const key = mapsEmbedKey()
  const transcript = seasons.map((s) => `${s.label}: ${s.line}`).join(' ')
  const span = video ? `${shortMonth(video.from)} to ${shortMonth(video.to)}` : `${first.year} to ${last.year}`
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
  const dates = [view.registered ? `Registered with MahaRERA ${shortMonth(view.registered)}` : '',
    possession ? `possession filed for ${possession}` : ''].filter(Boolean)
  const media = (
    <>
      {video && (
        <figure className="m-0 mt-2">
          <FromAboveVideo src={video.src} poster={video.poster} width={video.width} height={video.height}
            label={`${shown} site from space, ${videoPace(video).by}, ${span}`} />
          <figcaption className="mt-1 text-center text-xs text-slate-600">
            {videoPace(video).title}, {span}: {videoPace(video).count}, October to May (the monsoon is under cloud).
          </figcaption>
        </figure>
      )}
      <ol className="mt-3 grid list-none grid-cols-3 gap-2 p-0 sm:grid-cols-6">
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
    </>
  )
  return (
    <section id="from-above" aria-labelledby="from-above-title" data-testid="from-above" className="scroll-mt-20">
      <h2 id="from-above-title" className="text-xl font-bold text-slate-900">{shown} from above, today</h2>
      {key && (
        <figure className="m-0 mt-3" data-testid="from-above-today">
          <iframe title={`${shown} today, Google satellite view`} src={satelliteSrc(key, view.pin.lat, view.pin.lon, 17)}
            loading="lazy" referrerPolicy="no-referrer-when-downgrade" allowFullScreen
            className="aspect-[4/3] w-full rounded-lg border border-slate-200 sm:aspect-[16/9]" />
          <figcaption className="mt-1 text-xs text-slate-600">
            Google satellite, centred on the project&apos;s map pin. Zoom in to see the site. Google does not date its picture,
            and it can be a year or more old: the latest reading below is from this season.
          </figcaption>
        </figure>
      )}
      {/* Esri's sharp pictures of the last few years, picked for the reader; Esri's own viewer only until they are looked up */}
      {esriPast ? <EsriPastPictures past={esriPast} lat={view.pin.lat} lon={view.pin.lon} name={shown} centredOn="the project's map pin" ringM={100} />
        : <EsriWaybackOnTap lat={view.pin.lat} lon={view.pin.lon} label={shown} />}
      {latest && (
        <div className="mt-3 rounded-lg border border-slate-200 p-3" data-testid="from-above-latest">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
            Latest reading from space, {latest.label.replace('-', '–')}{view.updated ? ` (looked ${shortMonth(view.updated)})` : ''}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-900">{latest.line}</p>
          {dates.length > 0 && <p className="mt-1 text-xs text-slate-600" data-testid="from-above-dates">{dates.join(' · ')}</p>}
        </div>
      )}
      <p className="mt-3 text-sm text-slate-700">{view.story}</p>
      {newest.length > 0 && (
        <div className="mt-2" data-testid="from-above-seasons">
          <h3 className="text-base font-semibold text-slate-900">The seasons before</h3>
          <ol className="mt-1 list-none p-0">{newest.map(line)}</ol>
        </div>
      )}
      <FromAboveProof media={media} summary={
        <>
          <span aria-hidden="true" className="text-emerald-700">✓</span>
          <span>Construction proof from space: {span}, Copernicus Sentinel-2{earlier.length > 0 ? ` (${earlier.length} earlier seasons)` : ''}</span>
        </>
      }>
        {earlier.length > 0 && <ol className="mt-2 list-none p-0" data-testid="from-above-earlier">{earlier.map(line)}</ol>}
        <p className="mt-2 text-xs text-slate-600">
          {view.where} The satellite sees 10 m a pixel, so this shows that the ground changed, not the towers themselves.
          Pictures are the middle of every clear pass, sharpened and colour-corrected by code; nothing is drawn in.
          The timeline starts a year before the project registered. The lines are written from the pictures and the MahaRERA
          filings, and say only what can be seen. {view.credit}.
        </p>
        <p className="mt-1 flex flex-wrap gap-x-5 text-sm">
          {video && (
            <a href={`/projects/${view.slug}/from-space`} className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary,#0f2340)] underline underline-offset-2"
              data-testid="from-above-watch">Open the full timeline</a>
          )}
          <a href="/projects/from-space" className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary,#0f2340)] underline underline-offset-2">
            More Pune projects from space</a>
        </p>
      </FromAboveProof>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
    </section>
  )
}
