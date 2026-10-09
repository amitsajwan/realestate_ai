'use client'
import React, { useState } from 'react'
import { errorMessage } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import { radarApi, WATCH_KINDS } from '@/lib/app/radar'
import type { RadarSignal, RadarSource, RadarWatch, RadarWatchKind } from '@/lib/app/radar'
import { useAsync } from '@/lib/app/useAsync'
import { Btn, ErrorBox, Spinner } from '../ui'

const box = 'rounded-2xl border border-gray-200 bg-white p-4'
const field = 'rounded-xl border border-gray-300 bg-white p-2 text-sm text-gray-900 [color-scheme:light]'

/** Leads that need a second step after a reply was sent: they wrote back, clicked, or a gentle nudge is due. */
export function Followups() {
  const { data, error, loading, reload } = useAsync(() => radarApi.followups(), [])
  const [done, setDone] = useState<Set<string>>(new Set())
  if (loading) return <Spinner label="Loading…" />
  if (error) return <ErrorBox message={error} onRetry={reload} />
  const items = (data ?? []).filter((s) => !done.has(s.id))
  if (!items.length) return <p className="rounded-2xl border border-dashed border-gray-300 p-6 text-center text-gray-600">No follow-ups due.</p>
  return (
    <ul className="space-y-3">
      {items.map((s) => <FollowupCard key={s.id} s={s} onDone={() => setDone((d) => new Set(d).add(s.id))} />)}
    </ul>
  )
}

const STATE: Record<string, string> = {
  replied: 'They wrote back', clicked: 'They opened the link: hand to the agent', nudge: 'No answer in 2 days: one gentle nudge',
}

function FollowupCard({ s, onDone }: { s: RadarSignal; onDone: () => void }) {
  const f = s.followup!
  const [reply, setReply] = useState(f.draft ?? '')
  const [error, setError] = useState<string | null>(null)
  async function act(action: 'sent' | 'handed' | 'closed') {
    try {
      await radarApi.followupDone(s.id, action)
      onDone()
    } catch (e) {
      setError(errorMessage(e))
    }
  }
  async function copyAndOpen() {
    try { await navigator.clipboard.writeText(reply) } catch { /* the textarea can still be copied by hand */ }
    window.open(s.url, '_blank', 'noopener')
  }
  return (
    <li className={`${box} space-y-2`}>
      <p className="text-sm font-bold text-[#102340]">{STATE[f.state] ?? f.state}</p>
      <p className="text-sm text-gray-700">They first wrote: “{s.text}”</p>
      {f.their_reply && <p className="text-sm text-gray-900">Then: <b>“{f.their_reply}”</b></p>}
      {f.state !== 'clicked' && (
        <textarea value={reply} onChange={(e) => setReply(e.target.value)} rows={3} className={`w-full ${field}`} />
      )}
      {error && <ErrorBox message={error} />}
      <div className="flex flex-wrap gap-2">
        {f.state !== 'clicked' && <Btn block={false} onClick={copyAndOpen}>Copy & open</Btn>}
        {f.state !== 'clicked' && <Btn block={false} variant="secondary" onClick={() => act('sent')}>Mark sent</Btn>}
        {f.state === 'clicked' && <Btn block={false} onClick={() => act('handed')}>Handed to agent</Btn>}
        <Btn block={false} variant="secondary" onClick={() => act('closed')}>Close</Btn>
      </div>
    </li>
  )
}

const SRC: Record<RadarSource, string> = { youtube: 'YouTube', reddit: 'Reddit', rss: 'RSS feed', instagram: 'Instagram' }

/** Where the radar looks, best first (the bandit's estimate). Agent-proposed watches show why they were added. */
export function Watches() {
  const { data, error, loading, reload } = useAsync(() => radarApi.watches(), [])
  const [source, setSource] = useState<RadarSource>('youtube')
  const [kind, setKind] = useState<RadarWatchKind>('query')
  const [value, setValue] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const [filter, setFilter] = useState<RadarSource | 'all'>('all')

  async function add() {
    setErr(null)
    try {
      await radarApi.addWatch(source, kind, value.trim())
      setValue('')
      reload()
    } catch (e) {
      setErr(errorMessage(e))
    }
  }
  async function toggle(w: RadarWatch) {
    try {
      await radarApi.toggleWatch(w.id, !w.active)
      reload()
    } catch (e) {
      setErr(errorMessage(e))
    }
  }
  const rows = (data ?? []).filter((w) => filter === 'all' || w.source === filter)
  return (
    <div className="space-y-3">
      <div className={`${box} space-y-2`}>
        <p className="font-semibold text-[#102340]">Add a watch</p>
        <div className="flex flex-wrap gap-2">
          <select value={source} onChange={(e) => { const s = e.target.value as RadarSource; setSource(s); setKind(WATCH_KINDS[s][0]) }} className={field}>
            {(Object.keys(SRC) as RadarSource[]).map((s) => <option key={s} value={s}>{SRC[s]}</option>)}
          </select>
          <select value={kind} onChange={(e) => setKind(e.target.value as RadarWatchKind)} className={field}>
            {WATCH_KINDS[source].map((k) => <option key={k} value={k}>{k}</option>)}
          </select>
        </div>
        <input value={value} onChange={(e) => setValue(e.target.value)} className={`w-full ${field}`}
          placeholder={kind === 'video' ? 'YouTube video id' : kind === 'feed' ? 'RSS feed URL (e.g. a Google Alert)' : kind === 'hashtag' ? 'hashtag, no #' : kind === 'subreddit' ? 'subreddit name' : 'search words'} />
        {err && <ErrorBox message={err} />}
        <Btn block={false} disabled={value.trim().length < 2} onClick={add}>Add</Btn>
      </div>
      <div className="flex flex-wrap gap-2">
        {(['all', ...Object.keys(SRC)] as (RadarSource | 'all')[]).map((s) => (
          <button key={s} type="button" onClick={() => setFilter(s)}
            className={`rounded-full border px-3 py-1 text-sm ${filter === s ? 'border-[#102340] bg-[#102340] text-white' : 'border-gray-300 text-gray-700'}`}>
            {s === 'all' ? 'All' : SRC[s]}
          </button>
        ))}
      </div>
      {loading && <Spinner label="Loading…" />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-200 bg-white">
        {rows.map((w) => (
          <li key={w.id} className={`flex items-start justify-between gap-3 p-3 ${w.active ? '' : 'opacity-50'}`}>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-gray-900">{w.title || w.value}</p>
              <p className="text-xs text-gray-500">
                {SRC[w.source]} {w.kind}{w.area ? ` · ${w.area}` : ''} · {w.hits ?? 0} leads / {w.checks ?? 0} checks
                {w.origin === 'agent' ? ' · found by the agent' : ''}{w.retired ? ` · retired (${w.retired})` : ''}
              </p>
              {w.reason && <p className="text-xs text-gray-600">{w.reason}</p>}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-bold text-gray-700" title="Expected chance a check finds a lead">
                {Math.round(w.mean * 100)}%
              </span>
              <button type="button" onClick={() => toggle(w)} className="text-xs font-semibold text-[#102340] underline">
                {w.active ? 'Pause' : 'Resume'}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** What people asked about this week, per area, grouped by meaning. */
export function Demand() {
  const { data, error, loading, reload } = useAsync(() => radarApi.themes(), [])
  if (loading) return <Spinner label="Loading…" />
  if (error) return <ErrorBox message={error} onRetry={reload} />
  if (!data?.length) return <p className="rounded-2xl border border-dashed border-gray-300 p-6 text-center text-gray-600">Themes are built once a week from the questions found.</p>
  return (
    <ul className="space-y-3">
      {data.map((a) => {
        const w = a.weeks[0]
        return (
          <li key={a.area} className={box}>
            <p className="font-bold text-[#102340]">{a.name} <span className="font-normal text-gray-500">· {w.questions} questions, week {w.week}</span></p>
            <ul className="mt-2 space-y-2">
              {w.themes.map((t) => (
                <li key={t.theme} className="text-sm">
                  <b>{t.count}</b> asked about <b>{t.theme}</b>
                  {t.faq && <span className="block text-xs text-gray-600">Page should answer: {t.faq}</span>}
                  {t.examples[0] && <span className="block text-xs italic text-gray-500">“{t.examples[0]}”</span>}
                </li>
              ))}
            </ul>
          </li>
        )
      })}
    </ul>
  )
}

/** Is it working: the funnel, the queue's precision, model cost, the agent's last runs and the scorer's refits. */
export function Health() {
  const m = useAsync(() => radarApi.metrics(), [])
  const r = useAsync(() => radarApi.runs(), [])
  if (m.loading || r.loading) return <Spinner label="Loading…" />
  if (m.error) return <ErrorBox message={m.error} onRetry={m.reload} />
  const steps = ['found', 'filtered_out', 'duplicate', 'gated', 'noise', 'shown', 'sent', 'clicked', 'converted']
  return (
    <div className="space-y-3">
      <div className={`${box} grid grid-cols-3 gap-2 text-center`}>
        <Stat label="Precision@10" value={m.data?.precision_at_10 != null ? `${Math.round(m.data.precision_at_10 * 100)}%` : '–'} />
        <Stat label="AI calls per lead" value={m.data?.llm_per_shown != null ? String(m.data.llm_per_shown) : '–'} />
        <Stat label="AI calls today" value={String(m.data?.llm_today ?? 0)} />
      </div>
      <div className={`${box} overflow-x-auto`}>
        <p className="mb-2 font-semibold text-[#102340]">Funnel, last 30 days</p>
        <table className="w-full text-right text-xs">
          <thead><tr><th className="text-left">Source</th>{steps.map((s) => <th key={s} className="px-1 font-semibold">{s.replace('_', ' ')}</th>)}</tr></thead>
          <tbody>
            {Object.entries(m.data?.by_source ?? {}).map(([src, c]) => (
              <tr key={src} className="border-t border-gray-100"><td className="text-left">{src}</td>{steps.map((s) => <td key={s} className="px-1">{c[s] ?? 0}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
      {r.data && (
        <div className={`${box} space-y-2 text-sm`}>
          <p className="font-semibold text-[#102340]">Discovery agent</p>
          {r.data.discovery.length === 0 && <p className="text-gray-600">Not run yet (once a day).</p>}
          {r.data.discovery.slice(0, 2).map((d) => (
            <div key={d._id}>
              <p className="text-xs text-gray-500">{timeAgo(d.started_at)} · {d.proposed?.length ?? 0} new watches · {d.steps?.length ?? 0} steps</p>
              {d.summary && <p className="text-gray-800">{d.summary}</p>}
              <ul className="ml-4 list-disc text-xs text-gray-700">
                {(d.proposed ?? []).map((p) => <li key={p.value}>{p.source} {p.kind}: {p.value}{p.reason ? ` (${p.reason})` : ''}</li>)}
              </ul>
            </div>
          ))}
          <p className="pt-2 font-semibold text-[#102340]">Learning</p>
          {r.data.models.length === 0 && <p className="text-gray-600">Scorer refits weekly once 60 leads are marked.</p>}
          {r.data.models.slice(0, 3).map((x, i) => (
            <p key={i} className="text-xs text-gray-700">
              {x.kind === 'scorer' ? `Scorer refit ${timeAgo(x.at)}: ${x.active ? 'shipped' : 'kept old weights'}` : `Draft rules ${timeAgo(x.at)}: ${(x.rules ?? []).join(' · ')}`}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-lg font-extrabold text-[#102340]">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}
