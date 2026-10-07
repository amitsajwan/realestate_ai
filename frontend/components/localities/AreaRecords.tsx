import React from 'react'
import { type AreaStats, longDate } from './areaStats'

const n = (v: number) => v.toLocaleString('en-IN')

/** "In the MahaRERA records": counts from MahaRERA's public register for one area. Renders nothing without data. */
export default function AreaRecords({ name, stats }: { name: string; stats: AreaStats | null }) {
  if (!stats || stats.projects <= 0) return null
  const asOf = longDate(stats.as_of)
  return (
    <section className="mt-9" aria-labelledby="records-title">
      <h2 id="records-title" className="text-xl font-semibold text-slate-900">In the MahaRERA records</h2>
      <p className="mt-3 leading-relaxed text-slate-800">
        <strong className="text-2xl font-bold text-slate-900">{n(stats.projects)}</strong>{' '}
        {stats.projects === 1 ? 'project' : 'projects'} in {name} on MahaRERA&apos;s public register.
      </p>

      {stats.completing.length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold text-slate-900">Completion dates filed with MahaRERA</h3>
          <ul className="mt-2 grid list-none grid-cols-2 gap-2 p-0 sm:grid-cols-4">
            {stats.completing.map((c) => (
              <li key={c.year} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                <span className="block text-sm text-slate-600">{c.year}</span>
                <span className="font-semibold text-slate-900">{n(c.projects)} {c.projects === 1 ? 'project' : 'projects'}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {stats.units_total !== null && stats.units_booked !== null && (
        <p className="mt-4 leading-relaxed text-slate-800">
          Homes booked, as the builders report them to MahaRERA: <strong>{n(stats.units_booked)}</strong> of {n(stats.units_total)}.
        </p>
      )}

      {stats.recent.length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold text-slate-900">Recently listed or updated on MahaRERA</h3>
          <ul className="mt-2 list-none space-y-3 p-0">
            {stats.recent.map((p) => (
              <li key={p.regno || p.name} className="min-w-0 rounded-xl border border-slate-200 p-3">
                {p.page ? (
                  <a href={p.page} className="break-words font-semibold text-[#0f2340] underline underline-offset-2">{p.name}</a>
                ) : p.url ? (
                  <a href={p.url} target="_blank" rel="noopener noreferrer" className="break-words font-semibold text-[#0f2340] underline underline-offset-2">{p.name}</a>
                ) : (
                  <span className="break-words font-semibold text-slate-900">{p.name}</span>
                )}
                <span className="mt-1 block break-words text-sm text-slate-600">
                  {[p.promoter, p.regno && `MahaRERA ${p.regno}`, p.completion && `completion filed for ${longDate(p.completion)}`,
                    p.updated && `listed or updated ${longDate(p.updated)}`].filter(Boolean).join(' · ')}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-4 text-sm text-slate-600">
        Source: {stats.source}{asOf ? `, as of ${asOf}` : ''}. Dates are what the builder filed; check each project on the MahaRERA website before you book.
      </p>
    </section>
  )
}
