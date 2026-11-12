import React from 'react'
import { longDay, mainRegistration, wholeProject } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

// What changed, as we read it (docs/plan/seo-system.md 8b, H1): MahaRERA shows only today's homes-booked count and today's
// completion date, so the dated readings below are the one record of how a project sold and how its date moved. Drawn on the
// server as plain SVG and text: no script, and a crawler or an AI fetcher reads the same numbers a buyer sees.

const n = (x: number) => x.toLocaleString('en-IN')

/** One bar per reading, the height its share of the project's homes (or of the highest reading when the total is unknown). */
function BookedChart({ rows, total }: { rows: { on: string; booked: number }[]; total: number | null | undefined }) {
  const top = Math.max(total || 0, ...rows.map((r) => r.booked), 1)
  const w = 320
  const h = 96
  const gap = 4
  const bw = (w - gap * (rows.length - 1)) / rows.length
  const first = rows[0]
  const last = rows[rows.length - 1]
  return (
    <svg viewBox={`0 0 ${w} ${h + 18}`} className="mt-3 h-auto w-full max-w-md" role="img" data-testid="booked-chart"
      aria-label={`Homes booked: ${n(first.booked)} on ${longDay(first.on)}, ${n(last.booked)} on ${longDay(last.on)}`}>
      {rows.map((r, i) => {
        const bh = Math.max(2, (r.booked / top) * h)
        return <rect key={r.on} x={i * (bw + gap)} y={h - bh} width={bw} height={bh} rx={2} fill="#0f2340" opacity={i === rows.length - 1 ? 1 : 0.55} />
      })}
      <text x={0} y={h + 14} fontSize={11} fill="#475569">{longDay(first.on)}</text>
      <text x={w} y={h + 14} fontSize={11} fill="#475569" textAnchor="end">{longDay(last.on)}</text>
    </svg>
  )
}

export default function ProjectHistory({ p, shown }: { p: RegisterProject; shown: string }) {
  // our dated readings are kept per MahaRERA record: the main registration's. On a page of several registrations they say so.
  const main = mainRegistration(p)
  const rows = main.booked_readings ?? []
  const moves = main.completion_moves ?? []
  const part = wholeProject(p) ? ` in ${p.regno}, one of its registrations` : ''
  if (rows.length < 2 && moves.length === 0) return null
  const first = rows[0]
  const last = rows[rows.length - 1]
  const rose = rows.length >= 2 ? last.booked - first.booked : 0
  return (
    <div role="group" aria-labelledby="history-title" data-testid="history">
      <h3 id="history-title" className="text-lg font-semibold text-slate-900">{shown}: what changed, as we read it</h3>
      {rows.length >= 2 && (
        <div className="mt-2" data-testid="booked-history">
          <p className="text-slate-800">
            {rose > 0 ? `${n(rose)} more homes booked between ${longDay(first.on)} and ${longDay(last.on)}: ${n(first.booked)} to ${n(last.booked)}`
              : rose < 0 ? `Homes booked went from ${n(first.booked)} to ${n(last.booked)} between ${longDay(first.on)} and ${longDay(last.on)} (MahaRERA shows cancellations this way)`
              : `${n(last.booked)} homes booked on every reading from ${longDay(first.on)} to ${longDay(last.on)}`}
            {main.units_total ? `, of ${n(main.units_total)} homes${part}.` : `${part}.`}
          </p>
          <BookedChart rows={rows} total={main.units_total} />
          <ul className="mt-2 grid list-none grid-cols-2 gap-x-6 p-0 text-sm text-slate-700 sm:grid-cols-3">
            {rows.slice().reverse().map((r) => <li key={r.on}>{longDay(r.on)}: {n(r.booked)} booked</li>)}
          </ul>
        </div>
      )}
      {moves.length > 0 && (
        <div className="mt-4" data-testid="date-history">
          <p className="font-semibold text-slate-900">Completion date filed with MahaRERA{part ? ` for ${p.regno}` : ''}</p>
          <ol className="mt-1 list-none space-y-1 p-0 text-slate-800">
            {moves.map((m) => (
              <li key={`${m.from}-${m.to}-${m.seen_on}`}>
                {longDay(m.from)} → <strong>{longDay(m.to)}</strong>
                <span className="text-sm text-slate-600">
                  {m.blanket ? ", by MahaRERA's August 2026 order for most projects (not the builder)" : ', filed by the builder'}
                  {m.seen_on ? `; we saw it on ${longDay(m.seen_on)}` : ''}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}
      <p className="mt-2 text-xs text-slate-500" data-testid="history-source">
        Read by Avasetu from MahaRERA on each date shown. MahaRERA shows only the latest figures, so earlier ones are our own readings.
      </p>
    </div>
  )
}
