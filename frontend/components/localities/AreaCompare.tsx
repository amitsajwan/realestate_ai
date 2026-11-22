import React from 'react'
import Link from 'next/link'
import type { Locality } from '@/lib/marketing/localities'
import { comparePath, type AreaCompare, type AreaPair, type CompareSide } from '@/lib/site/compare'
import { longDate } from './areaStats'

/**
 * "<A> vs <B>" (lib/site/compare.ts): two columns of facts a buyer can check, never a score or a winner. MahaRERA's counts as the
 * areas' own guides show them, possession dates that moved, the metro with trains today, then the same places measured from both
 * middles, and the hand-written "who it suits" of each guide.
 */

const n = (v: number) => v.toLocaleString('en-IN')
const pct = (part: number, whole: number) => Math.round((100 * part) / whole)
const kmText = (v: number) => `${v} km`

function booked(s: CompareSide): string {
  if (s.units_total === null || s.units_booked === null) return 'Not reported for every project'
  return `${n(s.units_booked)} of ${n(s.units_total)} (${pct(s.units_booked, s.units_total)}%)`
}

function moved(s: CompareSide): string {
  if (!s.dates) return 'No project being built with both dates'
  const d = s.dates
  return `${n(d.moved)} of ${n(d.with_dates)} (${pct(d.moved, d.with_dates)}%)` + (d.median_months && d.moved ? `, by ${d.median_months} months in the middle case` : '')
}

const metro = (s: CompareSide) => (s.metro ? `${s.metro.name}, ${s.metro.line_short}: about ${kmText(s.metro.km)}` : 'None within reach yet')

/** The page's first sentences: a dated answer from the two columns, without saying which area is better. */
export function compareLead(c: AreaCompare): string {
  const [a, b] = c.sides
  const homes = (s: CompareSide) => (s.units_total === null ? '' : ` with ${n(s.units_total)} homes`)
  return `As of ${longDate(c.as_of)}, MahaRERA lists ${n(a.projects)} projects in ${a.area.name}${homes(a)} and ${n(b.projects)} in `
    + `${b.area.name}${homes(b)}. The middles of the two areas are about ${kmText(c.apart_km)} apart.`
}

/** Questions buyers search about two areas, each answered from the page's own figures. */
export function compareQuestions(c: AreaCompare): { q: string; a: string }[] {
  const [a, b] = c.sides
  const out = [{ q: `How far is ${a.area.name} from ${b.area.name}?`,
    a: `About ${kmText(c.apart_km)} in a straight line between the middles of the two areas; the drive is longer and depends on the time of day.` }]
  if (a.projects !== b.projects) {
    const [more, less] = a.projects > b.projects ? [a, b] : [b, a]
    out.push({ q: `Which has more new projects, ${a.area.name} or ${b.area.name}?`,
      a: `As of ${longDate(c.as_of)}, MahaRERA lists ${n(more.projects)} projects in ${more.area.name} and ${n(less.projects)} in ${less.area.name}. `
        + `In ${c.as_of.slice(0, 4)} so far, ${n(more.registered_this_year)} and ${n(less.registered_this_year)} were registered.` })
  }
  const work = c.distances.find((r) => r.kind === 'work' && r.a_km !== r.b_km)
  if (work) {
    const [near, far] = work.a_km < work.b_km ? [[a, work.a_km], [b, work.b_km]] as const : [[b, work.b_km], [a, work.a_km]] as const
    out.push({ q: `Is ${a.area.name} or ${b.area.name} closer to ${work.name}?`,
      a: `${near[0].area.name}: about ${kmText(near[1])} from its middle, against about ${kmText(far[1])} from ${far[0].area.name}'s, in a straight line. `
        + 'Try the drive at 9:00 am and 6:30 pm on a weekday before you decide.' })
  }
  return out
}

function Row({ label, a, b }: { label: string; a: string; b: string }) {
  return (
    <tr className="border-t border-slate-200 align-top">
      <th scope="row" className="p-2 text-left font-medium text-slate-700 sm:p-3">{label}</th>
      <td className="p-2 text-slate-900 sm:p-3">{a}</td>
      <td className="p-2 text-slate-900 sm:p-3">{b}</td>
    </tr>
  )
}

export function PairLinks({ pairs, title }: { pairs: AreaPair[]; title: string }) {
  if (!pairs.length) return null
  return (
    <section className="mt-9" aria-label={title} data-testid="area-pairs">
      <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
      <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
        {pairs.map((p) => (
          <li key={p.slug}><Link href={comparePath(p.slug)} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]">{p.a.name} vs {p.b.name}</Link></li>
        ))}
      </ul>
    </section>
  )
}

export default function AreaCompareView({ c, guides }: { c: AreaCompare; guides: [Locality | undefined, Locality | undefined] }) {
  const [a, b] = c.sides
  const year = +c.as_of.slice(0, 4)
  const asOf = longDate(c.as_of)
  const kinds = [...new Set(c.distances.map((r) => r.kind_label))]
  return (
    <div data-testid="area-compare">
      <section className="mt-9" aria-labelledby="register-title">
        <h2 id="register-title" className="text-xl font-semibold text-slate-900">On MahaRERA&apos;s register</h2>
        <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full table-fixed text-sm">
            <caption className="sr-only">{a.area.name} and {b.area.name} on MahaRERA&apos;s public register, as of {asOf}</caption>
            <thead className="bg-slate-50"><tr>
              <th scope="col" className="w-[38%] p-2 text-left font-semibold text-slate-600 sm:p-3">As of {asOf}</th>
              <th scope="col" className="p-2 text-left font-semibold text-slate-900 sm:p-3">{a.area.name}</th>
              <th scope="col" className="p-2 text-left font-semibold text-slate-900 sm:p-3">{b.area.name}</th>
            </tr></thead>
            <tbody>
              <Row label="Projects on the register" a={n(a.projects)} b={n(b.projects)} />
              <Row label="Homes booked, as builders report them" a={booked(a)} b={booked(b)} />
              <Row label={`Registered in ${year} so far`} a={n(a.registered_this_year)} b={n(b.registered_this_year)} />
              <Row label={`Registered in ${year - 1}`} a={n(a.registered_last_year)} b={n(b.registered_last_year)} />
              <Row label={`Due to complete in ${year}`} a={n(a.completing_this_year)} b={n(b.completing_this_year)} />
              <Row label={`Due to complete in ${year + 1}`} a={n(a.completing_next_year)} b={n(b.completing_next_year)} />
              <Row label="Home projects being built whose builder moved the possession date 3+ months later" a={moved(a)} b={moved(b)} />
              <Row label="Nearest metro station with trains today" a={metro(a)} b={metro(b)} />
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          From {c.source}. A tower or phase registered on its own counts as a project. Moved dates leave out the 4 months MahaRERA
          added to most projects in August 2026. Metro distances are straight lines from the middle of each area.
        </p>
      </section>

      {c.distances.length > 0 && (
        <section className="mt-9" aria-labelledby="distances-title">
          <h2 id="distances-title" className="text-xl font-semibold text-slate-900">How far each is from the places buyers ask about</h2>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-sm">
              <caption className="sr-only">Straight-line distances from the middle of {a.area.name} and of {b.area.name}</caption>
              <thead className="bg-slate-50"><tr>
                <th scope="col" className="p-3 text-left font-semibold text-slate-600">Place</th>
                <th scope="col" className="p-3 text-right font-semibold text-slate-900">From {a.area.name}</th>
                <th scope="col" className="p-3 text-right font-semibold text-slate-900">From {b.area.name}</th>
              </tr></thead>
              {kinds.map((k) => (
                <tbody key={k}>
                  <tr className="border-t border-slate-200 bg-slate-50/60"><th scope="rowgroup" colSpan={3} className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">{k}</th></tr>
                  {c.distances.filter((r) => r.kind_label === k).map((r) => (
                    <tr key={r.key} className="border-t border-slate-200">
                      <th scope="row" className="p-2 text-left font-medium sm:p-3">
                        <a href={r.maps} target="_blank" rel="noopener noreferrer" className="text-[#0f2340] underline underline-offset-2">{r.name}<span className="sr-only"> (opens in a new tab)</span></a>
                      </th>
                      <td className={`p-2 text-right sm:p-3 ${r.a_km < r.b_km ? 'font-bold text-slate-900' : 'text-slate-700'}`}>{kmText(r.a_km)}</td>
                      <td className={`p-2 text-right sm:p-3 ${r.b_km < r.a_km ? 'font-bold text-slate-900' : 'text-slate-700'}`}>{kmText(r.b_km)}</td>
                    </tr>
                  ))}
                </tbody>
              ))}
            </table>
          </div>
          <p className="mt-2 text-sm text-slate-600">{c.note} The nearer of the two is in bold. {c.attribution}</p>
        </section>
      )}

      {guides[0] && guides[1] && (
        <section className="mt-9" aria-labelledby="suits-title">
          <h2 id="suits-title" className="text-xl font-semibold text-slate-900">Who each area suits</h2>
          <div className="mt-3 grid gap-4 sm:grid-cols-2">
            {guides.map((g) => g && (
              <div key={g.slug} className="rounded-xl border border-slate-200 p-4">
                <h3 className="font-semibold text-slate-900">{g.name}</h3>
                <p className="mt-1 text-sm font-semibold text-amber-700">{g.tagline}</p>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-relaxed text-slate-800">{g.suits.map((s) => <li key={s}>{s}</li>)}</ul>
                <p className="mt-3 text-sm"><Link href={`/localities/${g.slug}`} className="font-semibold text-[#0f2340] underline underline-offset-2">{g.name} area guide</Link></p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
