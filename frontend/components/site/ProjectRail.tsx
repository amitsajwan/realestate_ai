import React from 'react'
import Link from 'next/link'
import type { FacetRow } from '@/lib/site/facets'
import { RailCard } from './ListCard'

/** A row of project cards that the buyer swipes on a phone (a grid on a laptop), with "See all" to the list it comes from.
 *  It never moves by itself: rolling content gets skipped and is hard to use with a screen reader. Hidden under MIN cards,
 *  like a thin list page. */
const MIN = 3

export default function ProjectRail({ id, title, sub, href, count, rows, ranked = false, className = 'mt-10' }: {
  id: string; title: string; sub?: string; href: string; count: number; rows: FacetRow[]; ranked?: boolean; className?: string
}) {
  if (rows.length < MIN) return null
  return (
    <section aria-labelledby={`${id}-title`} className={className} data-testid={`rail-${id}`}>
      <div className="flex items-baseline justify-between gap-3">
        <div className="min-w-0">
          <h2 id={`${id}-title`} className="text-xl font-bold text-slate-900">{title}</h2>
          {sub && <p className="text-sm text-slate-600">{sub}</p>}
        </div>
        <Link href={href} className="shrink-0 text-sm font-semibold text-[#0f2340] underline underline-offset-2">See all {count}</Link>
      </div>
      <ul className="-mx-4 mt-3 flex list-none snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2 sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:px-0 lg:grid-cols-4">
        {rows.slice(0, 4).map((r, i) => (
          <li key={r.slug} className="w-[72%] max-w-[260px] shrink-0 snap-start sm:w-auto sm:max-w-none">
            <RailCard r={r} rank={ranked ? i + 1 : undefined} />
          </li>
        ))}
      </ul>
    </section>
  )
}
