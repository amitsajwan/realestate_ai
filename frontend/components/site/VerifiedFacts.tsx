import React from 'react'
import { formatPrice } from '@/lib/site/format'
import { formatDay } from '@/lib/site/projects'
import type { PropertyFactsView } from '@/lib/site/types'

const day = (iso?: string | null): string => formatDay((iso || '').slice(0, 10))
const km = (x: number): string => `${Number.isInteger(x) ? x : x.toFixed(1)} km`

/** The facts we checked for this property: MahaRERA's record, what is nearby, and a few numbers worked out for the buyer.
 *  Each block says where it comes from. Renders nothing when we have no facts. */
export default function VerifiedFacts({ f }: { f: PropertyFactsView | null }) {
  if (!f || !(f.maharera || f.nearby?.length || f.numbers)) return null
  const r = f.maharera
  const n = f.numbers || {}
  return (
    <section aria-labelledby="verified-title" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-950">
      <h2 id="verified-title" className="flex flex-wrap items-center gap-2 text-lg font-bold">
        <span aria-hidden className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-emerald-700 text-sm text-white">✓</span>
        Checked for you
      </h2>

      {r && (
        <div className="mt-3">
          <h3 className="text-sm font-bold uppercase tracking-wide text-emerald-800">On MahaRERA</h3>
          <dl className="mt-2 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            <Row k="Registration no." v={r.rera_no} />
            {r.project_type && <Row k="Project type" v={r.project_type} />}
            {r.completion_now && (
              <Row k="Completion date filed" v={day(r.completion_now) +
                (r.moved_months && r.completion_at_registration ? ` (was ${day(r.completion_at_registration)})` : '')} />
            )}
            {r.units_total != null && <Row k="Units in the project" v={String(r.units_total)} />}
            {r.registered_on && <Row k="Registered on" v={day(r.registered_on)} />}
            {r.promoter && <Row k="Promoter" v={r.promoter} />}
          </dl>
          <p className="mt-2 text-xs text-emerald-900">
            From MahaRERA&apos;s public record{r.read_at ? `, read ${day(r.read_at)}` : ''}.{' '}
            <a href={r.url} target="_blank" rel="noopener noreferrer" className="font-semibold underline underline-offset-2">Check it yourself</a>
          </p>
        </div>
      )}

      {f.nearby && f.nearby.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-bold uppercase tracking-wide text-emerald-800">Nearby</h3>
          <ul className="mt-2 grid list-none gap-2 p-0 text-sm sm:grid-cols-2">
            {f.nearby.map((p) => (
              <li key={p.label + p.name} className="flex items-baseline justify-between gap-3 rounded-lg bg-white/70 px-3 py-2">
                <span><span className="text-emerald-800">{p.label}:</span> <span className="font-semibold">{p.name}</span></span>
                <span className="whitespace-nowrap font-semibold">{km(p.km)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-emerald-900">
            Straight-line distance; the drive is longer. Map data ©{' '}
            <a href={f.nearby_source?.url} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">{f.nearby_source?.name}</a>.
          </p>
        </div>
      )}

      {(n.price_per_sqft || n.plot_guntha || n.emi) && (
        <div className="mt-4">
          <h3 className="text-sm font-bold uppercase tracking-wide text-emerald-800">Worked out for you</h3>
          <dl className="mt-2 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            {n.price_per_sqft != null && <Row k="Rate" v={`${formatPrice(n.price_per_sqft)} per sq.ft`} />}
            {n.plot_guntha != null && <Row k="Plot size" v={`${n.plot_guntha} guntha` + (n.plot_sqm ? ` (about ${n.plot_sqm} sq.m)` : '')} />}
            {n.emi && (
              <Row k="EMI, as an example" v={`${formatPrice(n.emi.emi)} a month`}
                note={`On a ${formatPrice(n.emi.loan)} loan (80% of the price) at ${n.emi.rate}% for ${n.emi.years} years. Ask your bank for its rate.`} />
            )}
          </dl>
        </div>
      )}
    </section>
  )
}

function Row({ k, v, note }: { k: string; v: string; note?: string }) {
  return (
    <div>
      <dt className="text-xs text-emerald-800">{k}</dt>
      <dd className="font-semibold">{v}</dd>
      {note && <dd className="text-xs text-emerald-900">{note}</dd>}
    </div>
  )
}
