import React from 'react'
import { formatDay } from '@/lib/site/projects'
import type { PublicProject } from '@/lib/site/types'

/** What MahaRERA's public record says about the project, with the date we read it and a link to check it yourself. */
export default function ReraBox({ p }: { p: PublicProject }) {
  const r = p.rera
  return (
    <section aria-labelledby="rera-title" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-950">
      <h2 id="rera-title" className="flex flex-wrap items-center gap-2 text-lg font-bold">
        <span aria-hidden className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-emerald-700 text-sm text-white">✓</span>
        Checked on MahaRERA
      </h2>
      {r ? (
        <>
          <dl className="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            <Row k="Registration no." v={r.regno} />
            <Row k="Name on MahaRERA" v={r.name} />
            {r.promoter && <Row k="Promoter" v={r.promoter} />}
            {r.registered_on && <Row k="Registered on" v={formatDay(r.registered_on)} />}
            {r.completion_now && <Row k="Completion date filed" v={formatDay(r.completion_now)} />}
            {r.units_total != null && (
              <Row k="Homes booked" v={`${r.units_booked ?? 0} of ${r.units_total}` + (p.booked_pct != null ? ` (${p.booked_pct}%)` : '')} />
            )}
          </dl>
          {p.scope_note && <p className="mt-3 text-sm">{p.scope_note}</p>}
          <p className="mt-3 text-xs text-emerald-900">
            Read from MahaRERA&apos;s public record on {formatDay(r.checked_at) || 'the date shown'}. Bookings are as reported by the builder to MahaRERA.{' '}
            <a href={r.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-emerald-900 underline underline-offset-2">See the record on MahaRERA</a>
          </p>
        </>
      ) : (
        <p className="mt-2 text-sm">Registration no. {p.rera_no}. We are reading the MahaRERA record; check back shortly.</p>
      )}
    </section>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-xs text-emerald-800">{k}</dt>
      <dd className="font-semibold">{v}</dd>
    </div>
  )
}
