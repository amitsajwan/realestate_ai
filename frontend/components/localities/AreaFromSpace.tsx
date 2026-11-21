import React from 'react'
import Link from 'next/link'
import FromAboveVideo from '@/components/site/FromAboveVideo'
import { shortMonth } from '@/lib/site/fromAbove'
import { areaFromSpacePath, type AreaFromSpace as View } from '@/lib/site/areaFromSpace'

/** "<area> from space" on the area guide (backend areastats/areaspace.py): the month-by-month video, the summary and the
 *  newest season's line, with a link to the watch page that has every season. Nothing until the area has a look with a video. */
export default function AreaFromSpace({ view, className = 'mt-9' }: { view: View | null; className?: string }) {
  if (!view?.video) return null
  const v = view.video
  const latest = view.seasons[view.seasons.length - 1]
  return (
    <section className={className} aria-labelledby="area-from-space-title" data-testid="area-from-space">
      <h2 id="area-from-space-title" className="text-xl font-semibold text-slate-900">{view.name} from space</h2>
      <p className="mt-1 text-sm text-slate-600">
        {v.months} clear months of the Sentinel-2 satellite, {shortMonth(v.from)} to {shortMonth(v.to)}
        {view.sideKm ? `, ${view.sideKm} km across` : ''}
      </p>
      <div className="mt-3">
        <FromAboveVideo src={v.src} poster={v.poster} width={v.width} height={v.height}
          label={`${view.name} from space, month by month, ${shortMonth(v.from)} to ${shortMonth(v.to)}`} />
      </div>
      <p className="mt-3 leading-relaxed text-slate-800">{view.story}</p>
      {latest && <p className="mt-2 text-sm text-slate-700"><span className="font-semibold">{latest.label.replace('-', '–')}:</span> {latest.line}</p>}
      <p className="mt-2">
        <Link href={areaFromSpacePath(view.slug)} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">
          Every season of {view.name} from space</Link>
      </p>
      <p className="text-xs text-slate-600">{view.credit}.</p>
    </section>
  )
}
