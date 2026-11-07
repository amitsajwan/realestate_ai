import React from 'react'
import SourceKind from './SourceKind'
import CostBreakdown from '@/components/site/CostBreakdown'
import type { Stage } from '@/lib/site/allin'
import { formatPrice } from '@/lib/site/format'
import { formatDay } from '@/lib/site/projects'
import { priceRowLabel, type ProjectPrices } from '@/lib/site/register'

const sqft = (x: number) => `${x.toLocaleString('en-IN')} sq ft`

/** Asked prices per home size (backend areastats/prices.py): from the builder's own site, or two property sites that agree. A row
 *  per size with its size, price range and ₹ per sq ft, and when it was read. The section around it (the register page's "<name>
 *  price") gives the heading and the panel that says who gets the exact price. Only the builder's site is named on a row and
 *  linked (owner 2026-10-20: we do not send buyers to portals); the other sources are in the page's Sources panel, so a row does
 *  not read as copied from another site. Each price folds out its all-in cost (CostBreakdown); a plot's does not (GST and the
 *  affordable rate work differently). */
export default function PriceBox({ prices, stage }: { prices: ProjectPrices | null | undefined; stage: Stage }) {
  if (!prices || !prices.rows.length) return null
  const read = prices.read_at ? formatDay(prices.read_at) : ''
  return (
    <div data-testid="prices">
      <ul className="grid list-none gap-3 p-0 sm:grid-cols-2">
        {prices.rows.map((r) => {
          const builder = r.sources.find((s) => s.url)
          return (
          <li key={r.bhk} className="rounded-2xl border border-slate-200 bg-white p-4" data-testid="price-row">
            <p className="text-sm font-semibold text-slate-600">{priceRowLabel(r.bhk)}</p>
            <p className="mt-1 text-lg font-bold text-slate-900">
              {r.to_inr && r.to_inr !== r.from_inr ? `${formatPrice(r.from_inr)} – ${formatPrice(r.to_inr)}` : `From ${formatPrice(r.from_inr)}`}
            </p>
            {(r.sqft || r.per_sqft) ? (
              <p className="mt-0.5 text-sm text-slate-700">
                {[r.sqft ? `from ${sqft(r.sqft)}` : null, r.per_sqft ? `${formatPrice(r.per_sqft)}/sq ft` : null].filter(Boolean).join(' · ')}
              </p>
            ) : null}
            {builder ? (
              <p className="mt-1 text-xs text-slate-600">As listed on <SourceKind sources={[builder]} />{read ? `, ${read}` : ''}</p>
            ) : read ? <p className="mt-1 text-xs text-slate-600">Last checked {read}</p> : null}
            {r.bhk !== 'Plot' && (
              <CostBreakdown price={r.from_inr} stage={stage} sqft={r.sqft}
                what={`${/^all homes$/i.test(r.bhk) ? 'a home' : `the ${r.bhk}`} at ${formatPrice(r.from_inr)}`} />
            )}
          </li>
          )
        })}
      </ul>
      <p className="mt-2 text-xs text-slate-600">
        Starting asking prices: the final price depends on the tower and floor, and parking, floor-rise and other charges can be extra.
        ₹ per sq ft is the lowest price over that size, which may be carpet or saleable area.
      </p>
    </div>
  )
}
