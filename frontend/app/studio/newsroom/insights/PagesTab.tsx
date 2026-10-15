'use client'
import React, { useState } from 'react'
import { LinkOut, StatusPill } from '@/components/app/list'
import { ErrorBox, Spinner } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { errorMessage } from '@/lib/app/client'
import { getGrownPages, setPageStatus } from '@/lib/app/insights'
import type { GrownPage, WordCount } from '@/lib/app/insights'
import { useAsync } from '@/lib/app/useAsync'

// Insights → Pages (docs/plan/area-intent-pages.md 11.7): the area list pages the site grew from searches, the ones waiting and
// why, and the words it could not use. Everything runs without a person; Hold and Never are the owner's undo.
const SITE = process.env.NEXT_PUBLIC_SITE_URL || 'https://avasetu.in'
const card = 'list-none rounded-2xl bg-white p-3'
const btn = 'min-h-[44px] rounded-xl border border-gray-300 px-3 text-sm font-semibold text-[#0f2340] active:bg-gray-100 disabled:text-gray-400'
const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '')

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">{children}</p>
}

/** Why a page is waiting, in words: the first rule it fails. */
function why(p: GrownPage): string {
  const g = p.gate
  if (!g.demand) return 'not searched enough yet'
  if (!g.supply) return `only ${g.projects ?? 0} matching project${g.projects === 1 ? '' : 's'} (needs 3)`
  if (!g.distinct) return `${Math.round((g.overlap ?? 0) * 100)}% the same projects as ${g.overlaps_with ?? 'another page'}`
  return "over this week's budget: next round"
}

function PageRow({ p, onDone }: { p: GrownPage; onDone: () => void }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const act = async (to: 'live' | 'held' | 'never') => {
    setBusy(true); setErr(null)
    try { await setPageStatus(p.key, to); onDone() } catch (e) { setErr(errorMessage(e)) } finally { setBusy(false) }
  }
  const searches = p.demand.impressions ? `${p.demand.impressions} impressions` : null
  const sources = (p.demand.sources ?? []).join(', ')
  return (
    <li className={card}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="min-w-0 break-words font-semibold text-gray-900">
          {p.status === 'candidate' ? p.path : <LinkOut href={SITE + p.path}>{p.path}</LinkOut>}
        </p>
        <StatusPill tone={p.status === 'live' ? 'ok' : p.status === 'held' ? 'bad' : 'muted'}>
          {p.status === 'live' ? 'Live' : p.status === 'held' ? 'Held' : p.status === 'never' ? 'Never' : 'Waiting'}
        </StatusPill>
      </div>
      <p className="text-xs text-gray-600">
        {p.source === 'seed' ? 'Seed list' : 'From searches'} · {p.count ?? 0} projects
        {searches ? ` · ${searches}` : ''}{sources ? ` · seen in ${sources}` : ''}
        {p.live_at ? ` · live since ${day(p.live_at)}` : p.created_at ? ` · first seen ${day(p.created_at)}` : ''}
      </p>
      {p.phrases.length > 0 && <p className="mt-1 text-sm text-gray-800">Searches: {p.phrases.map((x) => `"${x}"`).join(', ')}</p>}
      {p.status === 'candidate' && <p className="mt-1 text-sm text-gray-700">Waiting: {why(p)}</p>}
      <div className="mt-2 flex flex-wrap gap-2">
        {p.status === 'live' && <button type="button" className={btn} disabled={busy} onClick={() => act('held')}>Hold (hide from Google)</button>}
        {p.status === 'held' && <button type="button" className={btn} disabled={busy} onClick={() => act('live')}>Put back live</button>}
        {p.status !== 'never' && <button type="button" className={btn} disabled={busy} onClick={() => act('never')}>Never make this page</button>}
        {p.status === 'never' && <button type="button" className={btn} disabled={busy} onClick={() => act('live')}>Allow again</button>}
      </div>
      {err && <p className="mt-1 text-sm text-red-700">{err}</p>}
    </li>
  )
}

function Words({ title, note, items }: { title: string; note: string; items: WordCount[] }) {
  if (!items.length) return null
  return (
    <section className="mt-4">
      <h3 className="font-semibold text-gray-900">{title}</h3>
      <p className="text-xs text-gray-600">{note}</p>
      <ul className="mt-2 space-y-2 p-0">
        {items.slice(0, 20).map((w) => (
          <li key={w.word} className={card}>
            <p className="text-sm"><span className="font-semibold">{w.word}</span> · {w.impressions} impressions</p>
            <p className="text-xs text-gray-600">{w.phrases.map((x) => `"${x}"`).join(', ')}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function PagesTab() {
  const q = useAsync(() => getGrownPages(), [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const d = q.data!
  return (
    <>
      <div className={card}>
        <p className="font-semibold text-gray-900">Pages that grow from searches</p>
        <p className="text-sm text-gray-600">
          {d.at ? `Last round ${timeAgo(d.at)}: ${d.last.made ?? 0} made, ${d.last.waiting ?? 0} waiting, ${d.last.autocomplete ?? 0} Google suggestions read, budget ${d.last.budget ?? 0} a week.`
            : 'The first round runs within half an hour of the seo loop starting.'}
          {!d.enabled && ' New pages are switched off (SEO_GROW_ENABLED).'}
        </p>
        <p className="text-sm text-gray-600">Live {d.counts.live ?? 0} · held {d.counts.held ?? 0} · waiting {d.counts.candidate ?? 0} · never {d.counts.never ?? 0}</p>
      </div>

      <h2 className="mt-4 font-semibold text-gray-900">Live</h2>
      {d.live.length ? <ul className="mt-2 space-y-2 p-0">{d.live.map((p) => <PageRow key={p.key} p={p} onDone={q.reload} />)}</ul>
        : <Empty>No list page is live yet.</Empty>}

      <h2 className="mt-4 font-semibold text-gray-900">Waiting</h2>
      {d.waiting.length ? <ul className="mt-2 space-y-2 p-0">{d.waiting.map((p) => <PageRow key={p.key} p={p} onDone={q.reload} />)}</ul>
        : <Empty>Nothing people search for is waiting.</Empty>}

      <Words title="Words we cannot answer" note="Searches about things MahaRERA's records do not hold. They never become pages; a data source could change that." items={d.gaps} />
      <Words title="Words we do not know yet" note="Add one to backend/app/modules/seo/vocabulary.json and the next round uses it." items={d.unknown} />

      {d.never.length > 0 && (
        <>
          <h2 className="mt-4 font-semibold text-gray-900">Never</h2>
          <ul className="mt-2 space-y-2 p-0">{d.never.map((p) => <PageRow key={p.key} p={p} onDone={q.reload} />)}</ul>
        </>
      )}
    </>
  )
}
