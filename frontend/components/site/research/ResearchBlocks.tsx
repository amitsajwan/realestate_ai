import React from 'react'
import Link from 'next/link'
import { trackerPath } from '@/lib/news/trackers'
import { longDay, monthYear } from '@/lib/site/register'
import { hubPath } from '@/lib/site/research'
import type { BeingBuiltBlock, ChangeLine, CommuteBlock, JobsBlock, RentBlock, SchoolsBlock, Source } from '@/lib/site/research'
import { boardLabel, boardsOf, kmText, minutes, monthLabel, rentListings, rupees, uniqueSources } from '@/lib/site/researchPages'

// The research blocks (docs/plan/pune-intelligence.md C), drawn the same on a project page's "Around <name>" and on a place's
// /schools, /commute and /rent pages. Each one draws nothing when its block is absent or empty, and each says its sources and
// the day it was measured in small print. Server-rendered: these are facts for search, no client code.

const H3 = 'text-base font-semibold text-slate-900'
const LINK = 'inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2'
const TH = 'px-3 py-2 font-semibold'

/** "Sources: CBSE SARAS, CISCE · measured 20 Nov 2026" */
export function SmallPrint({ sources, updated, note, testId }: { sources: Source[]; updated: string; note?: React.ReactNode; testId?: string }) {
  const list = uniqueSources(sources)
  return (
    <p className="mt-2 text-xs text-slate-500" data-testid={testId}>
      {note && <>{note} </>}
      {list.length > 0 && <>Source{list.length === 1 ? '' : 's'}:{' '}
        {list.map((s, i) => (
          <React.Fragment key={s.name}>
            {i > 0 && ', '}
            {s.url ? <a href={s.url} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">{s.name}</a> : s.name}
          </React.Fragment>
        ))}
        {' · '}</>}
      {updated && <>measured {longDay(updated)}</>}
    </p>
  )
}

function Head({ id, title, more }: { id: string; title: string; more?: { href: string; label: string } | null }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4">
      <h3 id={id} className={H3}>{title}</h3>
      {more && <Link href={more.href} className={LINK}>{more.label}</Link>}
    </div>
  )
}

type More = { href: string; label: string } | null

export function CommuteTable({ b, from, more = null, heading = 'Commute', level = 3 }: { b?: CommuteBlock; from: string; more?: More; heading?: string; level?: 2 | 3 }) {
  if (!b?.rows?.length) return null
  return (
    <section aria-labelledby={level === 3 ? 'commute-title' : undefined} data-testid="research-commute">
      {level === 3 ? <Head id="commute-title" title={heading} more={more} /> : null}
      <div className="mt-2 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[420px] text-left text-sm">
          <thead><tr className="text-xs text-slate-500"><th className={TH}>To</th><th className={TH}>By road</th><th className={TH}>9 am</th><th className={TH}>6 pm, back</th></tr></thead>
          <tbody>
            {b.rows.map((r) => (
              <tr key={r.hub} className="border-t border-slate-200">
                <th scope="row" className="px-3 py-2 font-semibold text-slate-900">
                  {r.hub_slug ? <Link href={hubPath(r.hub_slug)} className="text-[#0f2340] underline underline-offset-2">{r.hub}</Link> : r.hub}
                </th>
                <td className="px-3 py-2 text-slate-800">{kmText(r.km)}</td>
                <td className="px-3 py-2 text-slate-800">{minutes(r.am)}</td>
                <td className="px-3 py-2 text-slate-800">{minutes(r.pm)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <SmallPrint sources={b.sources} updated={b.updated} note={`Driving ${from} on a weekday, Google's typical traffic.`} testId="commute-print" />
    </section>
  )
}

export function ChangesList({ changes, heading = "What's changing nearby" }: { changes?: ChangeLine[]; heading?: string }) {
  if (!changes?.length) return null
  return (
    <section aria-labelledby="changes-near-title" data-testid="research-changes">
      <Head id="changes-near-title" title={heading} />
      <ul className="mt-2 list-none space-y-2 p-0">
        {changes.map((c) => (
          <li key={c.slug} className="rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <Link href={trackerPath(c.slug)} className="font-semibold text-[#0f2340] underline underline-offset-2">{c.name}</Link>
            <span className="block text-slate-800">{c.status}</span>
            {c.date && <span className="block text-xs text-slate-500">Status of {longDay(c.date)}</span>}
          </li>
        ))}
      </ul>
    </section>
  )
}

export function BeingBuilt({ b }: { b?: BeingBuiltBlock }) {
  if (!b || !b.projects) return null
  const due = b.due_from && b.due_to ? (b.due_from === b.due_to ? `, due ${b.due_from}` : `, due ${b.due_from} to ${b.due_to}`) : ''
  return (
    <section aria-labelledby="being-built-title" data-testid="research-being-built">
      <Head id="being-built-title" title="Being built around it" />
      <p className="mt-1 text-slate-800">
        {b.projects.toLocaleString('en-IN')} project{b.projects === 1 ? '' : 's'} with {b.homes.toLocaleString('en-IN')} homes being built within {kmText(b.within_km)}{due}.
      </p>
      {b.biggest.length > 0 && (
        <ul className="mt-2 grid list-none gap-2 p-0 sm:grid-cols-2">
          {b.biggest.map((x) => (
            <li key={x.slug}>
              <Link href={`/projects/${x.slug}`} className="block min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
                <span className="block font-semibold text-[#0f2340]">{x.name}</span>
                <span className="text-sm text-slate-600">{x.homes.toLocaleString('en-IN')} homes{x.due ? ` · due ${/^\d{4}-\d{2}/.test(x.due) ? monthYear(x.due) : x.due}` : ''}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <SmallPrint sources={b.sources} updated={b.updated} note="From MahaRERA's register." />
    </section>
  )
}

export function SchoolsList({ b, from, limit = 8, more = null, level = 3, addresses = false }: { b?: SchoolsBlock; from: string; limit?: number; more?: More; level?: 2 | 3; addresses?: boolean }) {
  if (!b?.schools?.length) return null
  const t = b.total_within_km
  const schools = [...b.schools].sort((a, c) => a.km - c.km).slice(0, limit)
  const by = t?.by_board ?? {}
  const counts = boardsOf(b).map((x) => {
    const c = x === 'ICSE' ? (by.ICSE ?? 0) + (by.ISC ?? 0) : (by[x] ?? 0)
    return c ? `${c} ${boardLabel(x)}` : ''
  }).filter(Boolean)
  return (
    <section aria-labelledby={level === 3 ? 'schools-title' : undefined} data-testid="research-schools">
      {level === 3 ? <Head id="schools-title" title="Schools" more={more} /> : null}
      {t?.count ? <p className="mt-1 text-slate-800">{t.count} school{t.count === 1 ? '' : 's'} within {kmText(t.km)}{counts.length ? `: ${counts.join(', ')}` : ''}.</p> : null}
      <ul className="mt-2 list-none space-y-2 p-0">
        {schools.map((s) => (
          <li key={s.name + s.km} className="flex items-baseline justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <span className="min-w-0">
              <span className="block font-semibold text-slate-900">{s.website ? <a href={s.website} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">{s.name}</a> : s.name}</span>
              <span className="mt-0.5 flex flex-wrap items-center gap-x-2 text-slate-600">
                <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-slate-800 ring-1 ring-inset ring-slate-300" data-testid="board">{boardLabel(s.board)}</span>
                {s.level && <span>{s.level}</span>}
                {s.address && addresses && <span className="block w-full text-xs">{s.address}</span>}
              </span>
            </span>
            <span className="whitespace-nowrap font-semibold text-slate-900">{kmText(s.km)}</span>
          </li>
        ))}
      </ul>
      <SmallPrint sources={b.sources} updated={b.updated} note={`Straight-line distance ${from}. No fees or ratings: they are rarely published reliably.`} testId="schools-print" />
    </section>
  )
}

export function RentTable({ b, more = null, level = 3 }: { b?: RentBlock; more?: More; level?: 2 | 3 }) {
  if (!b?.rows?.length) return null
  const yields = b.rows.some((r) => r.yield_pct != null)
  const label = `Asked rent, from ${rentListings(b)} listings${b.within_km ? ` within ${kmText(b.within_km)}` : ''}, ${monthLabel(b.month, true)}`
  return (
    <section aria-labelledby={level === 3 ? 'rent-title' : undefined} data-testid="research-rent">
      {level === 3 ? <Head id="rent-title" title="Asked rent" more={more} /> : null}
      <p className="mt-1 text-sm text-slate-600" data-testid="rent-label">{label}</p>
      <div className="mt-2 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[420px] text-left text-sm">
          <thead><tr className="text-xs text-slate-500"><th className={TH}>Size</th><th className={TH}>A month</th><th className={TH}>Middle</th><th className={TH}>Listings</th>{yields && <th className={TH}>Yield</th>}</tr></thead>
          <tbody>
            {b.rows.map((r) => (
              <tr key={r.bhk} className="border-t border-slate-200">
                <th scope="row" className="px-3 py-2 font-semibold text-slate-900">{r.bhk}</th>
                <td className="px-3 py-2 text-slate-800">{rupees(r.low)} to {rupees(r.high)}</td>
                <td className="px-3 py-2 text-slate-800">{rupees(r.median)}</td>
                <td className="px-3 py-2 text-slate-800">{r.listings}</td>
                {yields && <td className="px-3 py-2 text-slate-800">{r.yield_pct != null ? `${r.yield_pct.toFixed(1)}%` : ''}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <SmallPrint sources={b.sources} updated={b.updated} testId="rent-print"
        note={`What owners ask on listings, not what tenants pay; the middle half of asks.${yields ? " Yield: a year's middle rent over the middle asking price for that size." : ''}`} />
    </section>
  )
}

export function WorkNearby({ b }: { b?: JobsBlock }) {
  if (!b?.hubs?.length) return null
  return (
    <section aria-labelledby="work-title" data-testid="research-jobs">
      <Head id="work-title" title="Work nearby" />
      <ul className="mt-2 grid list-none gap-2 p-0 sm:grid-cols-2">
        {b.hubs.map((h) => {
          const extra = (h.companies_count ?? h.companies.length) - Math.min(5, h.companies.length)
          return (
            <li key={h.hub} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
              <span className="flex items-baseline justify-between gap-3">
                {h.hub_slug ? <Link href={hubPath(h.hub_slug)} className="font-semibold text-[#0f2340] underline underline-offset-2">{h.hub}</Link>
                  : <span className="font-semibold text-slate-900">{h.hub}</span>}
                <span className="whitespace-nowrap font-semibold text-slate-900">{kmText(h.km)}</span>
              </span>
              {h.companies.length > 0 && <span className="mt-1 block text-slate-700">{h.companies.slice(0, 5).join(', ')}{extra > 0 ? ` and ${extra} more` : ''}</span>}
            </li>
          )
        })}
      </ul>
      <SmallPrint sources={b.sources} updated={b.updated} note="Companies from each hub's own tenant list; straight-line distance." />
    </section>
  )
}
