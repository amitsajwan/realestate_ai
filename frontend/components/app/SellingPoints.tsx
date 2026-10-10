'use client'
import type { DraftSellingPoint, SellingPoint } from '@/lib/app/types'
import { t } from '@/lib/app/strings'

/** Points the agent can correct the amount of, right in the row. */
const AMOUNT_KEYS = new Set(['starting_price', 'booking_amount'])

/** Draft points from the brochure become listing points, all unticked: the agent ticks what is true. */
export function toSellingPoints(points: DraftSellingPoint[] | undefined): SellingPoint[] {
  return (points ?? []).map(({ source: _source, ...p }) => ({ ...p, confirmed: false }))
}

function formatInr(n: number): string {
  return `₹${n.toLocaleString('en-IN')}`
}

/** "Selling points from the brochure — tick what's true". Only ticked points are used in posts. */
export function SellingPoints({
  points,
  onChange,
  warnings = [],
}: {
  points: SellingPoint[]
  onChange: (next: SellingPoint[]) => void
  warnings?: string[]
}) {
  if (points.length === 0) return null
  const set = (i: number, patch: Partial<SellingPoint>) => onChange(points.map((p, j) => (j === i ? { ...p, ...patch } : p)))
  const allTicked = points.every((p) => p.confirmed)

  return (
    <section id="selling-points" className="scroll-mt-4 space-y-3" aria-label={t('spTitle')} data-testid="selling-points">
      {warnings.length > 0 && (
        <div role="alert" className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900" data-testid="selling-points-warnings">
          <p className="font-semibold">{t('spNotes')}</p>
          <ul className="list-disc pl-5">{warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
      )}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">{t('spTitle')}</h2>
          <p className="text-sm text-gray-600">{t('spHelp')}</p>
        </div>
        {!allTicked && (
          <button type="button" onClick={() => onChange(points.map((p) => ({ ...p, confirmed: true })))}
            className="min-h-[44px] shrink-0 rounded-lg px-3 text-sm font-semibold text-blue-700" data-testid="selling-points-tick-all">
            {t('spTickAll')}
          </button>
        )}
      </div>
      <ul className="divide-y divide-gray-100 rounded-xl border border-gray-200">
        {points.map((p, i) => (
          <li key={p.key} className="p-3" data-testid={`selling-point-${p.key}`}>
            <label className="flex min-h-[44px] items-center gap-3">
              <input type="checkbox" className="h-5 w-5 shrink-0" checked={p.confirmed} onChange={(e) => set(i, { confirmed: e.target.checked })} />
              <span className="min-w-0">
                <span className="block">{p.text_local || p.text}</span>
                {p.text_local && <span className="block text-xs text-gray-500">{p.text}</span>}
              </span>
            </label>
            {AMOUNT_KEYS.has(p.key) && (
              <label className="ml-8 mt-1 flex min-h-[44px] items-center gap-2 text-sm">
                <span className="text-gray-600">{t('spAmount')}</span>
                <input type="number" inputMode="numeric" min={0} className="min-h-[44px] w-36 rounded-lg border border-gray-300 px-2"
                  value={typeof p.value === 'number' ? p.value : ''}
                  onChange={(e) => {
                    const n = e.target.value === '' ? null : Number(e.target.value)
                    set(i, n === null ? { value: null } : { value: n, text: p.text.replace(/₹\s?[\d,]+/, formatInr(n)), ...(p.text_local ? { text_local: p.text_local.replace(/₹\s?[\d,]+/, formatInr(n)) } : {}) })
                  }}
                  aria-label={`${t('spAmount')}: ${p.text}`} />
              </label>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
