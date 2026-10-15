import React from 'react'
import Link from 'next/link'

export interface Chip { path: string; label: string; count?: number | null }

/** The lists of one place as chips (docs/plan/area-intent-pages.md section 4): New launches · Top · Ready to move · 2 BHK ·
 *  budgets · All projects · area guide. They are the internal links that tie a place's pages together; the current page is
 *  shown, not linked. */
export default function FacetChips({ chips, current, label = 'More lists', className = 'mt-6' }: { chips: Chip[]; current?: string; label?: string; className?: string }) {
  if (chips.length < 2 && !chips.some((c) => c.path !== current)) return null
  return (
    <nav aria-label={label} className={className} data-testid="facet-chips">
      <ul className="flex list-none flex-wrap gap-2 p-0">
        {chips.map((c) => (
          <li key={c.path}>
            {c.path === current ? (
              <span aria-current="page" className="inline-flex min-h-[44px] items-center rounded-full bg-[#0f2340] px-4 text-sm font-semibold text-white">
                {c.label}{c.count != null ? ` (${c.count})` : ''}
              </span>
            ) : (
              <Link href={c.path} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]">
                {c.label}{c.count != null ? ` (${c.count})` : ''}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  )
}
