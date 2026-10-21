'use client'
import React, { useState } from 'react'
import { LinkOut, StatusPill } from '@/components/app/list'
import { ErrorBox, Spinner } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { errorMessage } from '@/lib/app/client'
import { getRankings, revertPage } from '@/lib/app/insights'
import type { BoardRow, RankAction, RankTarget, Scoreboard, WeekNumbers } from '@/lib/app/insights'
import { useAsync } from '@/lib/app/useAsync'

// Insights → Rankings (docs/plan/rank-loop.md R9): the rank loop's numbers, fixes and results, read-only except "Undo".
const SITE = process.env.NEXT_PUBLIC_SITE_URL || 'https://avasetu.in'
const FIX_LABEL: Record<string, string> = { title: 'Title from search', faq: 'Buyer questions', links: 'Link slot', refresh: 'Refresh facts',
  description: 'Search description' }
const WEEK_ROWS: [keyof WeekNumbers, string][] = [['clicks', 'Clicks (28 days)'], ['impressions', 'Impressions (28 days)'],
  ['page_one', 'Pages on page one'], ['near_page_one', 'Pages near page one'], ['targeted', 'Pages with a target search']]
const card = 'list-none rounded-2xl bg-white p-3'
const btn = 'min-h-[44px] rounded-xl border border-gray-300 px-3 text-sm font-semibold text-[#0f2340] active:bg-gray-100 disabled:text-gray-400'
const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '')
const pos = (p: number | null | undefined) => (p == null ? '-' : `#${Math.round(p * 10) / 10}`)

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">{children}</p>
}

/** Google position over the last readings: lower on the chart is better (position 1 at the top). */
function Trend({ t }: { t: RankTarget }) {
  const pts = t.history.filter((h) => h.position != null).map((h) => h.position as number)
  if (pts.length < 2) return null
  const max = Math.max(...pts, 10)
  const w = 120
  const h = 28
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${((i / (pts.length - 1)) * w).toFixed(1)},${((p / max) * h).toFixed(1)}`).join(' ')
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`position from ${pos(pts[0])} to ${pos(pts[pts.length - 1])}`}>
      <path d={d} fill="none" stroke="#0f2340" strokeWidth="1.5" />
    </svg>
  )
}

function ActionRow({ a, onDone }: { a: RankAction; onDone: () => void }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const undo = async () => {
    setBusy(true); setErr(null)
    try { await revertPage(a.path); onDone() } catch (e) { setErr(errorMessage(e)) } finally { setBusy(false) }
  }
  const after = a.after28 ?? a.after14
  return (
    <li className={card}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="min-w-0 break-words font-semibold text-gray-900">{FIX_LABEL[a.fix] ?? a.fix} · <span className="font-normal">{a.path}</span></p>
        {a.gain != null && <StatusPill tone={a.gain > 0 ? 'ok' : a.gain < 0 ? 'bad' : 'muted'}>{a.gain > 0 ? '+' : ''}{a.gain} positions</StatusPill>}
      </div>
      <p className="text-xs text-gray-600">
        {day(a.at)}{a.phrase ? ` · "${a.phrase}"` : ''} · before {pos(a.before?.position)}, {a.before?.clicks ?? 0} clicks
        {after ? ` · after ${a.after28 ? 28 : 14} days ${pos(after.position)}, ${after.clicks} clicks` : ' · not measured yet'}
        {a.reverted ? ' · undone' : ''}
      </p>
      {a.new && <p className="mt-1 text-sm text-gray-800">Now: {a.new}</p>}
      {a.note && <p className="text-xs text-gray-500">{a.note}</p>}
      {(a.fix === 'title' || a.fix === 'description') && !a.reverted && (
        <button type="button" className={`${btn} mt-2`} disabled={busy} onClick={undo}>{busy ? 'Undoing…' : 'Undo on this page'}</button>
      )}
      {err && <p className="mt-1 text-sm text-red-700">{err}</p>}
    </li>
  )
}

const place = (p: number | null) => (p == null ? 'not top 10' : `#${p}`)

function BoardLine({ r }: { r: BoardRow }) {
  return (
    <li className="text-xs text-gray-700">&quot;{r.query}&quot;: us {place(r.ours)}, MagicBricks {place(r.magicbricks)}, 99acres {place(r.acres99)}, Housing {place(r.housing)}</li>
  )
}

/** docs/plan/index-everything.md I6: our Google place against the big portals, from the searches we already run. */
function Board({ b }: { b: Scoreboard }) {
  const prev = b.history.length > 1 ? b.history[b.history.length - 2] : null
  const diff = prev ? b.above_mb - prev.above_mb : null
  return (
    <div className={card}>
      <p className="font-semibold text-gray-900">Above MagicBricks</p>
      <p className="text-xs text-gray-600">Google searches we ran in the last 28 days{b.at ? `, counted ${timeAgo(b.at)}` : ''} (weekly).</p>
      <p className="mt-1 text-lg font-semibold text-gray-900">{b.above_mb} of {b.searches}
        {diff != null && <span className={`ml-1 text-xs ${diff >= 0 ? 'text-green-700' : 'text-red-700'}`}>{diff >= 0 ? '+' : ''}{diff}</span>}
      </p>
      <p className="text-xs text-gray-600">We show in {b.ours}; MagicBricks shows in {b.magicbricks}, and we are above them in {b.above_mb_when_shown} of those.</p>
      {b.next.length > 0 && (<>
        <p className="mt-2 text-sm font-semibold text-gray-900">Win next (MagicBricks just above us)</p>
        <ul className="space-y-1 p-0">{b.next.slice(0, 10).map((r) => <BoardLine key={r.query} r={r} />)}</ul>
      </>)}
    </div>
  )
}

export default function RankingsTab() {
  const q = useAsync(() => getRankings(), [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const d = q.data!
  const now = d.week.now
  const ago = d.week.week_ago
  return (
    <>
      <div className={card}>
        <p className="font-semibold text-gray-900">This week</p>
        {!now ? <p className="text-sm text-gray-600">No numbers yet: they start the day after Search Console is read.</p> : (
          <dl className="mt-1 grid grid-cols-2 gap-2 sm:grid-cols-5">
            {WEEK_ROWS.map(([k, label]) => {
              const v = Number(now[k])
              const diff = ago ? v - Number(ago[k]) : null
              return (
                <div key={k}>
                  <dt className="text-xs text-gray-600">{label}</dt>
                  <dd className="text-lg font-semibold text-gray-900">{v.toLocaleString('en-IN')}
                    {diff != null && <span className={`ml-1 text-xs ${diff >= 0 ? 'text-green-700' : 'text-red-700'}`}>{diff >= 0 ? '+' : ''}{diff}</span>}
                  </dd>
                </div>
              )
            })}
          </dl>
        )}
      </div>

      {d.scoreboard?.at && <Board b={d.scoreboard} />}

      <div className={card}>
        <p className="font-semibold text-gray-900">What works (page doctor)</p>
        <p className="text-xs text-gray-600">
          Positions gained 14 or 28 days after each fix. A fix with fewer than 5 results is tried first.
          {d.doctor.at ? ` Last round ${timeAgo(d.doctor.at)}.` : ''}
        </p>
        {d.doctor.results.length === 0 ? <p className="mt-1 text-sm text-gray-600">No fixes yet.</p> : (
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-gray-600"><tr><th className="py-1">Fix</th><th>Tried</th><th>Measured</th><th>Median gain</th><th>Improved</th></tr></thead>
              <tbody>
                {d.doctor.results.map((r) => (
                  <tr key={r.fix} className="border-t border-gray-100">
                    <td className="py-1">{FIX_LABEL[r.fix] ?? r.fix}</td><td>{r.tried}</td><td>{r.measured}</td>
                    <td>{r.median_gain == null ? '-' : `${r.median_gain > 0 ? '+' : ''}${r.median_gain}`}</td>
                    <td>{r.improved_pct == null ? '-' : `${r.improved_pct}%`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {d.doctor.treated.length > 0 && (
          <ul className="mt-2 space-y-1 p-0 text-xs text-gray-700">
            {d.doctor.treated.map((t) => <li key={t.path} className="list-none break-words">{FIX_LABEL[t.fix] ?? t.fix}: {t.path} ({t.reason})</li>)}
          </ul>
        )}
      </div>

      <p className="px-1 pt-2 text-sm font-semibold text-gray-900">Target searches ({d.targets.length})</p>
      {d.targets.length === 0 ? <Empty>No page has a target search yet (it needs Search Console data).</Empty> : (
        <ul className="space-y-2 p-0">
          {d.targets.map((t) => (
            <li key={t.path} className={card}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-gray-900">{t.name}</p>
                <Trend t={t} />
              </div>
              <p className="text-sm text-gray-700">&quot;{t.phrase}&quot; · {t.impressions ?? 0} impressions · {pos(t.position)} for it · page {pos(t.page_position)}, {t.clicks ?? 0} clicks</p>
              {t.checked_at && (
                <p className="text-xs text-gray-600">
                  Google {day(t.checked_at)}: {t.our_rank ? `we are #${t.our_rank}` : 'we are not in the top 10'}{t.above.length ? `; above us: ${t.above.join(', ')}` : ''}
                </p>
              )}
              {t.page_fix && <p className="text-xs text-gray-600">Last fix: {FIX_LABEL[t.page_fix] ?? t.page_fix}, {day(t.page_fix_at)}</p>}
              <LinkOut href={SITE + t.path} label={t.name}>Open page</LinkOut>
            </li>
          ))}
        </ul>
      )}

      <p className="px-1 pt-2 text-sm font-semibold text-gray-900">Latest fixes</p>
      {d.actions.length === 0 ? <Empty>No fixes yet.</Empty> : (
        <ul className="space-y-2 p-0">{d.actions.map((a, i) => <ActionRow key={`${a.path}-${a.fix}-${i}`} a={a} onDone={q.reload} />)}</ul>
      )}

      <p className="px-1 pt-2 text-sm font-semibold text-gray-900">Our pages competing for one search ({d.conflicts.total})</p>
      {d.conflicts.items.length === 0 ? <Empty>None found.</Empty> : (
        <ul className="space-y-2 p-0">
          {d.conflicts.items.map((c) => (
            <li key={c.phrase} className={card}>
              <p className="font-semibold text-gray-900">&quot;{c.phrase}&quot; · {c.impressions} impressions · {pos(c.position)}</p>
              <p className="break-words text-xs text-gray-700">{c.pages.join(' · ')}</p>
            </li>
          ))}
        </ul>
      )}

      <p className="px-1 pt-2 text-sm font-semibold text-gray-900">Searches with no page in the top 20 ({d.gaps.total})</p>
      {d.gaps.items.length === 0 ? <Empty>None yet (checked weekly).</Empty> : (
        <ul className="space-y-2 p-0">
          {d.gaps.items.map((g) => (
            <li key={g.phrase} className={card}>
              <p className="font-semibold text-gray-900">&quot;{g.phrase}&quot; · {g.impressions} impressions · {pos(g.position)}{g.rising ? ' · rising' : ''}</p>
              <div className="text-xs text-gray-700">{g.page ? <>Our page for it: <LinkOut href={SITE + g.page}>{g.page}</LinkOut></> : g.action}</div>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
