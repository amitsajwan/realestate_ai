'use client'
import React, { useMemo, useState } from 'react'
import { LinkOut, StatusPill } from '@/components/app/list'
import type { PillTone } from '@/components/app/list'
import { ErrorBox, Spinner } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { errorMessage } from '@/lib/app/client'
import { getAudit } from '@/lib/app/insights'
import type { AuditRow, AuditView } from '@/lib/app/insights'
import { useAsync } from '@/lib/app/useAsync'

// SEO → Audit (docs/plan/publishing-blueprint.md): every page Google knows of ours, one bucket and one action each, worked in
// the order of the buckets: protect what earns, then what is closest to earning. Read-only: nothing here changes a page.
const SITE = process.env.NEXT_PUBLIC_SITE_URL || 'https://avasetu.in'
const card = 'list-none rounded-2xl bg-white p-3'
const btn = 'min-h-[44px] rounded-xl border border-gray-300 px-3 text-sm font-semibold text-[#0f2340] active:bg-gray-100 disabled:text-gray-400'
const STEP = 50
const TONE: Record<string, PillTone> = { low_ctr: 'action', earning: 'ok', near_page_one: 'action', seen_far: 'action', not_indexed: 'bad' }
const COLUMNS: (keyof AuditRow)[] = ['path', 'kind', 'bucket', 'clicks', 'impressions', 'ctr', 'position', 'impressions_before',
  'trend', 'index_state', 'in_sitemap', 'top_search', 'top_search_impressions', 'action']

/** The rows as CSV, for a spreadsheet: every value quoted so a comma in a search or an action stays in its cell. */
export function auditCsv(rows: AuditRow[]): string {
  const cell = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`
  return [COLUMNS.join(','), ...rows.map((r) => COLUMNS.map((c) => cell(r[c])).join(','))].join('\n')
}

function download(rows: AuditRow[], at: string | null) {
  const url = URL.createObjectURL(new Blob([auditCsv(rows)], { type: 'text/csv' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `avasetu-page-audit-${(at ?? new Date().toISOString()).slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function Row({ r, label }: { r: AuditRow; label: string }) {
  const numbers = [`${r.clicks} clicks`, `${r.impressions} impressions`, r.position != null ? `position ${r.position.toFixed(1)}` : null,
    r.trend && r.trend !== 'steady' ? (r.trend === 'new' ? 'new' : `${r.trend} (${r.impressions_before} before)`) : null].filter(Boolean)
  return (
    <li className={card}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="min-w-0 break-words font-semibold text-gray-900"><LinkOut href={SITE + r.path}>{r.path}</LinkOut></p>
        <StatusPill tone={TONE[r.bucket] ?? 'muted'}>{label}</StatusPill>
      </div>
      <p className="text-xs text-gray-600">{r.kind} · {numbers.join(' · ')}{r.index_state ? ` · ${r.index_state}` : ''}</p>
      {r.top_search && <p className="mt-1 text-sm text-gray-800">Found for "{r.top_search}" ({r.top_search_impressions})</p>}
      <p className="mt-1 text-sm text-gray-700">{r.action}</p>
    </li>
  )
}

function Report({ d, onFresh, busy }: { d: AuditView; onFresh: () => void; busy: boolean }) {
  const [bucket, setBucket] = useState<string>('')
  const [kind, setKind] = useState<string>('')
  const [shown, setShown] = useState(STEP)
  const label = useMemo(() => Object.fromEntries(d.buckets.map((b) => [b.key, b.label])), [d.buckets])
  const rows = d.rows.filter((r) => (!bucket || r.bucket === bucket) && (!kind || r.kind === kind))
  const kinds = Object.keys(d.by_kind)
  return (
    <>
      <div className={card}>
        <p className="font-semibold text-gray-900">Every page Google knows</p>
        <p className="text-sm text-gray-600">
          {d.pages} pages{d.at ? `, read ${timeAgo(d.at)}` : ''}. Search Console's last 28 days against the 28 before, and the daily
          index check. Work the groups top to bottom: protect what earns, then what is closest to earning.
        </p>
        {d.error && <p className="mt-1 text-sm text-red-700">{d.error}. Showing the last audit.</p>}
        <div className="mt-2 flex flex-wrap gap-2">
          <button type="button" className={btn} disabled={busy} onClick={onFresh}>{busy ? 'Reading Google…' : 'Read again now'}</button>
          <button type="button" className={btn} disabled={!rows.length} onClick={() => download(rows, d.at)}>Download CSV</button>
        </div>
      </div>

      <ul className="mt-3 flex flex-wrap gap-2 p-0" aria-label="Groups">
        {d.buckets.filter((b) => b.pages).map((b) => (
          <li key={b.key} className="list-none">
            <button type="button" aria-pressed={bucket === b.key} className={`${btn} ${bucket === b.key ? 'bg-[#0f2340] text-white' : 'bg-white'}`}
              onClick={() => { setBucket(bucket === b.key ? '' : b.key); setShown(STEP) }}>
              {b.label} {b.pages}
            </button>
          </li>
        ))}
      </ul>
      {kinds.length > 1 && (
        <label className="mt-2 block text-sm text-gray-700">
          Kind of page{' '}
          <select className="min-h-[44px] rounded-xl border border-gray-300 bg-white px-2" value={kind}
            onChange={(e) => { setKind(e.target.value); setShown(STEP) }}>
            <option value="">All</option>
            {kinds.map((k) => <option key={k} value={k}>{k} ({d.by_kind[k].clicks ?? 0} clicks)</option>)}
          </select>
        </label>
      )}

      {rows.length ? (
        <ul className="mt-3 space-y-2 p-0">{rows.slice(0, shown).map((r) => <Row key={r.path} r={r} label={label[r.bucket] ?? r.bucket} />)}</ul>
      ) : <p className="mt-3 rounded-2xl bg-white p-4 text-sm text-gray-600">No page in this group.</p>}
      {rows.length > shown && (
        <button type="button" className={`${btn} mt-3 w-full bg-white`} onClick={() => setShown(shown + STEP)}>
          Show more ({rows.length - shown} left)
        </button>
      )}
    </>
  )
}

export default function AuditTab() {
  const [fresh, setFresh] = useState<AuditView | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const q = useAsync(() => getAudit(), [])
  const readAgain = async () => {
    setBusy(true); setErr(null)
    try { setFresh(await getAudit(true)) } catch (e) { setErr(errorMessage(e)) } finally { setBusy(false) }
  }
  if (q.loading && !q.data) return <><Spinner /><p className="text-center text-sm text-gray-600">Reading Search Console, about half a minute the first time a day…</p></>
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const d = fresh ?? q.data!
  if (!d.configured) {
    return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">The audit needs the Search Console key (GSC_SA_KEY_B64) on the server.</p>
  }
  return (
    <>
      {err && <p className="mb-2 text-sm text-red-700">{err}</p>}
      <Report d={d} onFresh={readAgain} busy={busy} />
    </>
  )
}
