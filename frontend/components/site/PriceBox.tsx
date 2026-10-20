import React from 'react'
import { formatPrice } from '@/lib/site/format'
import { formatDay } from '@/lib/site/projects'
import type { ProjectPrices } from '@/lib/site/register'

/** Asked prices per home size (backend areastats/prices.py): from the builder's own site, or two property sites that agree.
 *  Only the builder's site is linked; a property site is named, not linked (owner 2026-10-20: we do not send buyers to portals). */
export default function PriceBox({ prices, name }: { prices: ProjectPrices | null | undefined; name: string }) {
  if (!prices || !prices.rows.length) return null
  return (
    <section aria-labelledby="prices-title" data-testid="prices">
      <h2 id="prices-title" className="text-xl font-bold">Prices of {name}</h2>
      <dl className="mt-3 grid gap-3 sm:grid-cols-2">
        {prices.rows.map((r) => (
          <div key={r.bhk} className="rounded-2xl border border-slate-200 bg-white p-4">
            <dt className="text-sm text-slate-600">{r.bhk}</dt>
            <dd className="mt-1 text-lg font-bold text-slate-900">
              {r.to_inr ? `${formatPrice(r.from_inr)} – ${formatPrice(r.to_inr)}` : `From ${formatPrice(r.from_inr)}`}
            </dd>
            <dd className="mt-1 text-xs text-slate-600">
              As listed on{' '}
              {r.sources.map((s, i) => (
                <React.Fragment key={s.site}>
                  {i > 0 && ' and '}
                  {s.url ? <a href={s.url} target="_blank" rel="noopener nofollow" className="underline underline-offset-2">{s.site} (the builder&apos;s site)</a> : s.site}
                </React.Fragment>
              ))}
            </dd>
          </div>
        ))}
      </dl>
      <p className="mt-2 text-xs text-slate-600">
        Asking prices as the sites showed them{prices.read_at ? ` on ${formatDay(prices.read_at)}` : ''}. Builders change prices often and
        add parking, floor-rise and other charges: ask for the current price sheet and the all-in cost before you book.
      </p>
    </section>
  )
}
