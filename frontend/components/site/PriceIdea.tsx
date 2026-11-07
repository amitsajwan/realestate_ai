import React from 'react'
import { formatPrice } from '@/lib/site/format'
import { formatDay } from '@/lib/site/projects'
import type { PriceBand, PriceIdea as Idea } from '@/lib/site/register'

/** "about ₹2.2 – 2.6 Cr": one unit when both ends share it, so a band reads as a rough guide, not a quoted price. */
export function bandText(b: { low: number; high: number }): string {
  const [lo, loUnit] = formatPrice(b.low).split(' ')
  const hi = formatPrice(b.high)
  const [hiNum, hiUnit] = hi.split(' ')
  return loUnit && loUnit === hiUnit ? `about ${lo} – ${hiNum.replace('₹', '')} ${hiUnit}` : `about ${formatPrice(b.low)} – ${hi}`
}

/** The area's usual asking band per home size (backend areastats/priceidea.py area_bands): projects being sold there, published
 *  prices and single-site ones, middle half, rounded. Used on project pages and the area page. */
export function UsualBands({ place, rows, testId = 'usual-bands' }: { place: string; rows: PriceBand[]; testId?: string }) {
  if (!rows.length) return null
  return (
    <div className="rounded-2xl bg-slate-50 p-4" data-testid={testId}>
      <p className="text-sm font-semibold text-slate-700">What new homes in {place} usually ask</p>
      <ul className="mt-2 grid list-none gap-1 p-0 text-sm text-slate-800 sm:grid-cols-2">
        {rows.map((r) => (
          <li key={r.bhk}><span className="font-semibold">{r.bhk}</span> {bandText(r)} <span className="text-slate-600">({r.projects} projects)</span></li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-slate-600">
        Our own guide: the middle half of the starting prices we have read for projects being sold in {place}, rounded. Use it to
        judge an offer, not as a price.
      </p>
    </div>
  )
}

/** The rough price guide on a project page (owner 2026-10-31, "price idea"): the sizes no exact price can be published for (one
 *  site only), as rounded bands checked against the area, then the area's usual bands. Never in the hero price, the compare list
 *  or the JSON-LD offers. Who gets the exact price is the panel under it; where the band came from is in the Sources panel. */
export default function PriceIdea({ idea, shown }: { idea: Idea | null | undefined; shown: string }) {
  if (!idea || (!idea.rows.length && !idea.area.length)) return null
  const read = idea.read_at ? formatDay(idea.read_at) : ''
  return (
    <div className="space-y-3" data-testid="price-idea">
      {idea.rows.length > 0 && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-4">
          <p className="text-sm font-semibold text-slate-700">Rough price guide for {shown}</p>
          <ul className="mt-2 list-none space-y-1 p-0">
            {idea.rows.map((r) => (
              <li key={r.bhk} className="text-slate-900" data-testid="price-idea-row">
                <span className="font-semibold">{r.bhk}</span> {bandText(r)}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-slate-600">
            Our own rounded guide, checked against the area{read ? ` on ${read}` : ''}. It is not a quote: the exact price is on the
            builder&apos;s price sheet.
          </p>
        </div>
      )}
      {idea.place && <UsualBands place={idea.place} rows={idea.area} />}
    </div>
  )
}
