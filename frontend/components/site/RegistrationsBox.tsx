import React from 'react'
import { formatDay } from '@/lib/site/projects'
import type { FactSource, PublicProject } from '@/lib/site/types'

const WHO: Record<FactSource, string> = {
  builder: 'as listed by the builder',
  maharera: 'from MahaRERA',
  agent: 'as quoted by the agent',
  avasetu: 'our check',
  osm: 'OpenStreetMap',
}

/** "2030-07-31" -> "Jul 2030": the month is what a buyer plans around. */
const month = (iso?: string | null) => formatDay((iso || '').slice(0, 7))

/** A project sold under several MahaRERA registrations (one per tower): each tower, what it holds, its registration number
 *  linked to MahaRERA and the completion date filed there. Nothing for a one-registration project (ReraBox covers it). */
export default function RegistrationsBox({ p }: { p: PublicProject }) {
  const regs = p.registrations ?? []
  if (regs.length < 2) return null
  const sources = [...new Set(regs.map((r) => WHO[r.source]).filter(Boolean))]
  const read = [...new Set(regs.map((r) => r.checked_at).filter(Boolean))].sort().pop()
  return (
    <section aria-labelledby="regs-title" data-testid="registrations">
      <h2 id="regs-title" className="text-xl font-bold">MahaRERA registrations</h2>
      <p className="mt-1 text-slate-800">
        {p.name} is registered on MahaRERA as {regs.length} separate projects, one per tower. Each has its own completion date: ask which tower a home is in.
      </p>
      <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
        {regs.map((r) => (
          <li key={r.regno} className="rounded-xl border border-slate-200 p-3">
            <p className="flex flex-wrap items-baseline justify-between gap-x-3">
              <span className="font-bold">{r.tower}</span>
              {r.url ? (
                <a href={r.url} target="_blank" rel="noopener noreferrer" className="font-mono text-sm text-[var(--site-primary)] underline underline-offset-2">
                  {r.regno}<span className="sr-only"> on MahaRERA (opens in a new tab)</span>
                </a>
              ) : <span className="font-mono text-sm">{r.regno}</span>}
            </p>
            {r.holds && <p className="mt-1 text-sm text-slate-800">{r.holds}</p>}
            {month(r.completion) && <p className="mt-1 text-sm text-slate-600">Completion filed with MahaRERA: <span className="font-semibold text-slate-900">{month(r.completion)}</span></p>}
          </li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-slate-600">
        Towers and what each holds: {sources.join(', ') || 'as listed by the builder'}. Registration numbers and completion dates from MahaRERA&apos;s public record{read ? `, read on ${formatDay(read)}` : ''}.
      </p>
    </section>
  )
}
