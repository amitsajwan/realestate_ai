'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { LinkOut, StatusPill, TabBar, useUrlTab } from '@/components/app/list'
import type { PillTone } from '@/components/app/list'
import { ErrorBox, PageTitle, Spinner, inputCls } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { errorMessage } from '@/lib/app/client'
import { getFound, getHot, getSystem, ignoreFound, refreshPage, searchAs } from '@/lib/app/insights'
import type { FoundItem, FoundState, HotItem, Loop } from '@/lib/app/insights'
import { useAsync } from '@/lib/app/useAsync'
import PagesTab from './PagesTab'
import RankingsTab from './RankingsTab'

const TABS = ['hot', 'rankings', 'pages', 'found', 'system']
const TAB_LABEL: Record<string, string> = { hot: 'Hot projects', rankings: 'Rankings', pages: 'Pages', found: 'Found on Google', system: 'System' }
const SIGNAL: Record<string, string> = { launch: 'New', bookings: 'Bookings', news: 'News', search: 'Search Console', google: 'Google', youtube: 'YouTube' }
const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '')
const card = 'list-none rounded-2xl bg-white p-3'
const btn = 'min-h-[44px] rounded-xl border border-gray-300 px-3 text-sm font-semibold text-[#0f2340] active:bg-gray-100 disabled:text-gray-400'

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">{children}</p>
}

// ---- O1 hot projects -----------------------------------------------------------------------------------------------------
function HotRow({ item, onDone }: { item: HotItem; onDone: () => void }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const refresh = async () => {
    setBusy(true); setErr(null)
    try { await refreshPage(item.regno); onDone() } catch (e) { setErr(errorMessage(e)) } finally { setBusy(false) }
  }
  return (
    <li className={card}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-gray-900">{item.name}</p>
          <p className="text-xs text-gray-600">{[item.regno, item.area].filter(Boolean).join(' · ')}</p>
        </div>
        <StatusPill tone={item.hot ? 'action' : 'muted'}>{item.hot_score}</StatusPill>
      </div>
      <ul className="mt-2 space-y-1 p-0 text-xs text-gray-700">
        {item.why.map((w) => (
          <li key={w.signal} className="list-none"><span className="font-semibold">{SIGNAL[w.signal] ?? w.signal}:</span> {w.evidence} <span className="text-gray-500">({w.source})</span></li>
        ))}
      </ul>
      {item.marketed_by.length > 0 && (
        <p className="mt-2 text-xs text-gray-600"><span className="font-semibold">{item.marketed_by.length} sites market it:</span> {item.marketed_by.join(', ')}</p>
      )}
      <p className="mt-2 text-xs text-gray-600">
        {item.enriched_at ? `Page refreshed ${timeAgo(item.enriched_at)}, next ${day(item.next_refresh)}` : 'Page not enriched yet'}
      </p>
      <div className="mt-1 flex flex-wrap items-center gap-3">
        {item.refresh_waiting ? <span className="text-sm text-gray-600">Refresh asked, waiting its turn</span> :
          <button type="button" className={btn} disabled={busy} onClick={refresh}>Refresh page now</button>}
        {item.page && <LinkOut href={item.page} label={item.name}>Open page</LinkOut>}
      </div>
      {err && <p className="mt-1 text-sm text-red-700">{err}</p>}
    </li>
  )
}

function HotTab() {
  const q = useAsync(() => getHot(), [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const d = q.data!
  return (
    <>
      <p className="text-xs text-gray-600">
        Scored once a day from MahaRERA bookings and launches, news, Search Console, Google results and YouTube.
        {d.scored_at ? ` Last scored ${timeAgo(d.scored_at)}: ${d.hot ?? 0} of ${d.projects ?? 0} projects at ${d.hot_min} or more.` : ' Not scored yet.'}
        {' '}Buyers never see the score; marketer sites are for you and agents only.
      </p>
      {!d.items.length ? <Empty>No project has a score yet.</Empty> :
        <ul className="space-y-2 p-0">{d.items.map((i) => <HotRow key={i.regno} item={i} onDone={q.reload} />)}</ul>}
    </>
  )
}

// ---- O2 found on Google --------------------------------------------------------------------------------------------------
const STATE: Record<FoundState, { label: string; tone: PillTone }> = {
  stuck: { label: 'Needs a name', tone: 'action' }, searching: { label: 'Searching', tone: 'info' },
  found: { label: 'Found, adding', tone: 'ok' }, added: { label: 'Added', tone: 'done' }, ignored: { label: 'Ignored', tone: 'muted' },
}
const ORDER: FoundState[] = ['stuck', 'searching', 'found', 'added', 'ignored']

function FoundRow({ item, onDone }: { item: FoundItem; onDone: () => void }) {
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true); setErr(null)
    try { await fn(); onDone() } catch (e) { setErr(errorMessage(e)) } finally { setBusy(false) }
  }
  const open = item.state === 'stuck' || item.state === 'searching'
  return (
    <li className={card}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-gray-900">{item.name || item.regno}</p>
          <p className="text-xs text-gray-600">{[item.name ? item.regno : null, item.last_seen ? `seen ${timeAgo(item.last_seen)}` : null].filter(Boolean).join(' · ')}</p>
        </div>
        <StatusPill tone={STATE[item.state].tone}>{STATE[item.state].label}</StatusPill>
      </div>
      <ul className="mt-2 space-y-1 p-0 text-xs text-gray-700">
        {item.seen.map((s) => (
          <li key={s.link || s.title} className="list-none break-words">
            {s.link ? <a href={s.link} target="_blank" rel="noopener noreferrer" className="underline">{s.title || s.link}</a> : s.title}
            {s.query && <span className="text-gray-500"> (search: {s.query})</span>}
          </li>
        ))}
      </ul>
      {item.tried_names.length > 0 && <p className="mt-2 text-xs text-gray-600"><span className="font-semibold">Searched MahaRERA for:</span> {item.tried_names.join(', ')}</p>}
      {open && (
        <form className="mt-2 flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); act(() => searchAs(item.regno, name)) }}>
          <input className={`${inputCls} min-w-0 flex-1`} value={name} onChange={(e) => setName(e.target.value)}
            placeholder="Name it is registered under" aria-label={`MahaRERA name for ${item.regno}`} />
          <button type="submit" className={btn} disabled={busy || name.trim().length < 5}>Search</button>
          <button type="button" className={btn} disabled={busy} onClick={() => act(() => ignoreFound(item.regno))}>Ignore</button>
        </form>
      )}
      {err && <p className="mt-1 text-sm text-red-700">{err}</p>}
    </li>
  )
}

function FoundTab() {
  const q = useAsync(() => getFound(), [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const items = [...q.data!.items].sort((a, b) => ORDER.indexOf(a.state) - ORDER.indexOf(b.state))
  return (
    <>
      <p className="text-xs text-gray-600">
        MahaRERA numbers printed on pages Google shows that our register does not have yet. One is looked up on MahaRERA by name every step and
        added only when the number matches exactly. When every name has been tried, give the name the builder registered.
      </p>
      {!items.length ? <Empty>Nothing found yet.</Empty> :
        <ul className="space-y-2 p-0">{items.map((i) => <FoundRow key={i.regno} item={i} onDone={q.reload} />)}</ul>}
    </>
  )
}

// ---- O6 system -----------------------------------------------------------------------------------------------------------
const LOOP_TONE: Record<Loop['state'], PillTone> = { ok: 'ok', error: 'bad', stale: 'bad', off: 'muted' }
const LOOP_LABEL: Record<Loop['state'], string> = { ok: 'OK', error: 'Failed', stale: 'Stopped', off: 'Off' }

function SystemTab() {
  const q = useAsync(() => getSystem(), [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const d = q.data!
  const order = { stale: 0, error: 1, ok: 2, off: 3 }
  const loops = [...d.loops].sort((a, b) => order[a.state] - order[b.state])
  const credits = d.serper_credits
  return (
    <>
      <div className={card}>
        <p className="font-semibold text-gray-900">Google searches (Serper)</p>
        <p className="text-sm text-gray-700">
          {credits == null ? 'Credits unknown (no key, or Serper did not answer).' :
            `${credits.toLocaleString('en-IN')} credits left, about ${Math.floor(credits / d.serper_per_day)} days at ${d.serper_per_day} searches a day.`}
        </p>
        <p className="text-xs text-gray-600">
          {d.marks.web_search ? `Last searched ${timeAgo(d.marks.web_search)}` : 'Not searched yet'}
          {' · '}{d.marks.hot_projects ? `hot scores ${timeAgo(d.marks.hot_projects)}` : 'hot scores not run yet'}
        </p>
      </div>
      <ul className="space-y-2 p-0">
        {loops.map((l) => (
          <li key={l.name} className={card}>
            <div className="flex items-center justify-between gap-2">
              <p className="font-semibold text-gray-900">{l.name.replace(/_/g, ' ')}</p>
              <StatusPill tone={LOOP_TONE[l.state]}>{LOOP_LABEL[l.state]}</StatusPill>
            </div>
            <p className="text-xs text-gray-600">
              {l.state === 'off' ? 'Switched off by its setting' : l.last_ok_at ? `Last good run ${timeAgo(l.last_ok_at)}` : 'No good run yet'}
              {l.last_error_at && l.state !== 'ok' ? ` · failed ${timeAgo(l.last_error_at)}` : ''}
            </p>
            {l.last_error && <p className="mt-1 break-words text-xs text-red-700">{l.last_error}</p>}
          </li>
        ))}
      </ul>
      <div className={card}>
        <p className="font-semibold text-gray-900">MahaRERA register</p>
        <ul className="mt-1 space-y-1 p-0 text-xs text-gray-700">
          {d.register.map((line) => <li key={line} className={`list-none ${line.startsWith('WARN') ? 'text-red-700' : ''}`}>{line}</li>)}
        </ul>
      </div>
    </>
  )
}

/** Studio → Newsroom → Insights: what we collect about projects and the system, for the owner (O1, O2, O6). */
export default function InsightsPage() {
  const [tab, setTab] = useUrlTab('tab', 'hot', TABS)
  return (
    <div className="space-y-3 pb-24">
      <PageTitle action={<Link href="/studio/newsroom" className="inline-flex min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline">Newsroom</Link>}>
        Insights
      </PageTitle>
      <TabBar label="Insights" value={tab} onChange={setTab} tabs={TABS.map((k) => ({ key: k, label: TAB_LABEL[k] }))} />
      {tab === 'hot' ? <HotTab /> : tab === 'rankings' ? <RankingsTab /> : tab === 'pages' ? <PagesTab /> : tab === 'found' ? <FoundTab /> : <SystemTab />}
    </div>
  )
}
