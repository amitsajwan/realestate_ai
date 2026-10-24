import React from 'react'
import Link from 'next/link'
import { longDay, type RegisterProject } from '@/lib/site/register'

const months = (m: number) => `${m} month${m === 1 ? '' : 's'}`
const n = (v: number) => v.toLocaleString('en-IN')

/** How far booked the project is, in the same bands as the guides' tags: 95%+ is mostly resale, under 30% most homes are open. */
export function bookedBand(pct: number): { label: string; bar: string } {
  if (pct >= 95) return { label: 'Nearly sold out: mostly resale', bar: 'bg-rose-500' }
  if (pct < 30) return { label: 'Most homes not yet booked', bar: 'bg-emerald-500' }
  return { label: 'Partly booked', bar: 'bg-amber-500' }
}

/** The filed date's path since registration, split into MahaRERA's 2026 blanket extension and the builder's own move. */
function DateTrail({ p }: { p: RegisterProject }) {
  const first = p.completion_at_registration
  const now = p.completion_now
  if (!now) return null
  const moved = p.details?.completion_moved_months ?? null
  const ext = p.details?.extension_months ?? 0
  if (!first || first === now) {
    return (
      <div data-testid="date-trail">
        <p className="text-sm text-slate-600">Completion date filed with MahaRERA</p>
        <p className="mt-1 text-lg font-semibold text-slate-900">{longDay(now)}</p>
        {first && <p className="mt-2 inline-block rounded-lg bg-emerald-50 px-2.5 py-1 text-sm font-semibold text-emerald-900">✓ Not moved since registration</p>}
      </div>
    )
  }
  const why = [
    ext > 0 ? `+${months(ext)}: MahaRERA's blanket extension (Order 66/2026), not the builder's request` : null,
    moved != null && moved > 0 ? `+${months(moved)}: moved later by the builder` : null,
  ].filter(Boolean) as string[]
  return (
    <div data-testid="date-trail">
      <ol className="flex list-none flex-col gap-2 p-0 sm:flex-row sm:items-center">
        <li className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
          <span className="block text-xs text-slate-600">At registration</span>
          <span className="font-semibold text-slate-900">{longDay(first)}</span>
        </li>
        <li aria-hidden className="text-center text-xl text-slate-400 sm:px-1">➔</li>
        <li className="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2">
          <span className="block text-xs text-amber-900">Filed now{ext > 0 ? ' (extension added)' : ''}</span>
          <span className="font-semibold text-slate-900">{longDay(now)}</span>
        </li>
      </ol>
      {why.length > 0 && (
        <ul className="mt-2 list-none space-y-0.5 p-0 text-sm text-slate-700">
          {why.map((w) => <li key={w}>{w}</li>)}
        </ul>
      )}
    </div>
  )
}

/** Homes booked against homes registered, as a bar: a buyer sees at once whether most homes are still open or only a few are left. */
function BookedBar({ p }: { p: RegisterProject }) {
  const total = p.units_total
  const sold = p.units_booked
  if (!total || sold == null || sold > total) return null
  const pct = Math.round((100 * sold) / total)
  const band = bookedBand(pct)
  return (
    <div data-testid="booked-bar">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm text-slate-600">Homes booked on MahaRERA</p>
        <p className="text-sm font-semibold text-slate-900">{band.label}</p>
      </div>
      <div role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label={`${pct}% of homes booked`}
        className="mt-2 h-3 overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full rounded-full ${band.bar}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-1.5 text-sm text-slate-800">
        <strong>{n(sold)} of {n(total)}</strong> booked ({pct}%) · {n(total - sold)} not yet booked
      </p>
    </div>
  )
}

/** The two moving numbers of a MahaRERA record, at the top of the page: where the completion date went since registration, and how
 *  much is booked. Both are read from the record; nothing here is a forecast. */
export default function ProjectTracker({ p }: { p: RegisterProject }) {
  if (!p.completion_now && !(p.units_total && p.units_booked != null)) return null
  return (
    <section aria-labelledby="tracker-title" className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5" data-testid="tracker">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="tracker-title" className="text-lg font-semibold text-slate-900">MahaRERA tracker</h2>
        {p.details_read_at && <span className="text-xs text-slate-600">Read from MahaRERA {longDay(p.details_read_at)}</span>}
      </div>
      <div className="mt-3 grid gap-5 sm:grid-cols-2">
        <DateTrail p={p} />
        <BookedBar p={p} />
      </div>
    </section>
  )
}

/** For an agent browsing a project they sell: the way into the free trial (page, posts and a Reel made for a property). */
export function AgentBridge({ name }: { name: string }) {
  return (
    <section aria-labelledby="agent-bridge-title" className="rounded-2xl border border-[#0f2340]/20 bg-slate-50 p-4" data-testid="agent-bridge">
      <h2 id="agent-bridge-title" className="text-base font-semibold text-slate-900">Are you an agent selling homes in {name}?</h2>
      <p className="mt-1 text-sm text-slate-700">Give us the property: we make its page, Facebook and Instagram posts and a Reel, and enquiries come to you.</p>
      <Link href="/trial?src=project-page" className="mt-2 inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">
        Try it free for a month
      </Link>
    </section>
  )
}
