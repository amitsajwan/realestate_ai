import React from 'react'
import Link from 'next/link'
import { longDay } from '@/lib/site/register'
import type { BuilderPage } from '@/lib/site/hubs'

// Every completion date the builder filed later, as we saw it happen (docs/plan/seo-system.md 8b, H3). MahaRERA shows each
// project's latest date only, so this dated list exists because we kept reading.
export default function BuilderDateMoves({ b }: { b: Pick<BuilderPage, 'name' | 'date_moves'> }) {
  const moves = b.date_moves ?? []
  if (moves.length === 0) return null
  return (
    <div className="mt-4" data-testid="date-moves">
      <h3 className="text-lg font-semibold text-slate-900">Date changes we saw {b.name} file</h3>
      <ol className="mt-2 list-none space-y-1 p-0">
        {moves.map((m) => (
          <li key={`${m.slug}-${m.from}-${m.to}`}>
            <Link href={`/projects/${m.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">{m.name}</Link>
            <span className="ml-2 text-sm text-slate-700">{longDay(m.from)} → {longDay(m.to)}{m.seen_on ? `, seen ${longDay(m.seen_on)}` : ''}</span>
          </li>
        ))}
      </ol>
      <p className="mt-2 text-xs text-slate-600">Read by Avasetu from MahaRERA on each date shown. MahaRERA&apos;s 2026 extension for most projects is left out.</p>
    </div>
  )
}
