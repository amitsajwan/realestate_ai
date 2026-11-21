import React from 'react'
import EsriWaybackOnTap from '@/components/site/EsriWaybackOnTap'
import FromAboveProof from '@/components/site/FromAboveProof'
import FromAboveVideo from '@/components/site/FromAboveVideo'
import { shortMonth, type FromAboveSeason } from '@/lib/site/fromAbove'
import { areaFromSpacePath, type AreaFromSpace as View } from '@/lib/site/areaFromSpace'

const SHOWN_SEASONS = 3   // the newest seasons as the current reading; the rest sit in the proof badge, still page text
const ESRI_ZOOM = 14      // a few kilometres in Esri's viewer: the area, not one plot

/** "<area> from space" on the area guide (backend areastats/areaspace.py), laid out as the project section is since
 *  2026-11-21 (ProjectFromAbove, docs/plan/satellite-view.md "Google first, the timeline as proof"): the guide already shows
 *  Google's sharp view near its top, so here the newest Sentinel-2 season comes first as the latest reading, then the summary,
 *  the seasons before and Esri's sharp past pictures on tap. The 10 m timeline itself sits in a closed badge: opening it makes
 *  the video (nothing downloads before), and it holds the earlier season lines, the method and the watch page, where the video
 *  comes first for Google's video results. Every season line is in the page either way. Nothing until a look has a video. */
export default function AreaFromSpace({ view, className = 'mt-9' }: { view: View | null; className?: string }) {
  if (!view?.video) return null
  const v = view.video
  const span = `${shortMonth(v.from)} to ${shortMonth(v.to)}`
  const seasons = view.seasons
  const latest = seasons[seasons.length - 1]
  const newest = seasons.slice(-SHOWN_SEASONS - 1, -1).reverse()
  const earlier = seasons.slice(0, Math.max(0, seasons.length - SHOWN_SEASONS - 1)).reverse()
  const line = (s: FromAboveSeason) => (
    <li key={s.label} className="flex gap-3 border-b border-slate-100 py-1.5 last:border-0">
      <span className="w-24 shrink-0 text-xs font-semibold text-slate-900">{s.label.replace('-', '–')}</span>
      <span className="text-sm text-slate-700">{s.line}</span>
    </li>
  )
  return (
    <section className={className} aria-labelledby="area-from-space-title" data-testid="area-from-space">
      <h2 id="area-from-space-title" className="text-xl font-semibold text-slate-900">{view.name} from space</h2>
      {latest && (
        <div className="mt-3 rounded-lg border border-slate-200 p-3" data-testid="area-from-space-latest">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
            Latest reading from space, {latest.label.replace('-', '–')}{view.updated ? ` (looked ${shortMonth(view.updated)})` : ''}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-900">{latest.line}</p>
        </div>
      )}
      <p className="mt-3 leading-relaxed text-slate-800">{view.story}</p>
      {newest.length > 0 && (
        <div className="mt-2" data-testid="area-from-space-seasons">
          <h3 className="text-base font-semibold text-slate-900">The seasons before</h3>
          <ol className="mt-1 list-none p-0">{newest.map(line)}</ol>
        </div>
      )}
      <EsriWaybackOnTap lat={view.middle.lat} lon={view.middle.lon} label={view.name} zoom={ESRI_ZOOM}
        centredOn={`the middle of ${view.name}`} />
      <FromAboveProof media={
        <figure className="m-0 mt-2">
          <FromAboveVideo src={v.src} poster={v.poster} width={v.width} height={v.height}
            label={`${view.name} from space, month by month, ${span}`} />
          <figcaption className="mt-1 text-center text-xs text-slate-600">
            Month by month, {span}: {v.months} clear months, October to May (the monsoon is under cloud).
          </figcaption>
        </figure>
      } summary={
        <>
          <span aria-hidden="true" className="text-emerald-700">✓</span>
          <span>How {view.name} changed from space: {span}, Copernicus Sentinel-2{earlier.length > 0 ? ` (${earlier.length} earlier seasons)` : ''}</span>
        </>
      }>
        {earlier.length > 0 && <ol className="mt-2 list-none p-0" data-testid="area-from-space-earlier">{earlier.map(line)}</ol>}
        <p className="mt-2 text-xs text-slate-600">
          {view.where} Pictures are the middle of every clear pass, sharpened and colour-corrected by code; nothing is drawn in.
          The lines are written from the pictures and the area&apos;s MahaRERA counts, and say only what can be seen. {view.credit}.
        </p>
        <p className="mt-1 flex flex-wrap gap-x-5 text-sm">
          <a href={areaFromSpacePath(view.slug)} data-testid="area-from-space-watch"
            className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">
            Open the full timeline</a>
          <a href="/projects/from-space" className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">
            More of Pune from space</a>
        </p>
      </FromAboveProof>
    </section>
  )
}
