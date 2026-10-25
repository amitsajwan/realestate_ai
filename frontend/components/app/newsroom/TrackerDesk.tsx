'use client'
import React, { useState } from 'react'
import { Btn, Chip, ErrorBox, Spinner } from '@/components/app/ui'
import { StatusPill } from '@/components/app/list'
import { friendlyNewsroomError } from '@/lib/app/newsroom'
import { trackersApi, type DeskTracker } from '@/lib/app/trackers'
import { useAsync } from '@/lib/app/useAsync'

const KIND = { project: 'Project', rule: 'Rule', rate: 'Rate' } as const
const field = 'w-full rounded-xl border border-gray-300 bg-white p-3 text-base text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200'

/** Today in India, as the date input wants it. */
function today(): string {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'Asia/Kolkata' })
    .formatToParts(new Date()).map((x) => [x.type, x.value]))
  return `${p.year}-${p.month}-${p.day}`
}

/** One tracker on the desk: compact until opened, then the status, the new reports and the update form. */
export function TrackerRow({ t, open, onToggle, onChange }: { t: DeskTracker; open: boolean; onToggle: () => void; onChange: (t: DeskTracker) => void }) {
  const fresh = t.reports.filter((r) => r.new)
  const [editing, setEditing] = useState(false)
  const [status, setStatus] = useState(t.status)
  const [stage, setStage] = useState<number | null>(t.stage)
  const [date, setDate] = useState(today())
  const [sources, setSources] = useState('')
  const [showAll, setShowAll] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(fn: () => Promise<DeskTracker>) {
    setBusy(true)
    setError(null)
    try {
      onChange(await fn())
      setEditing(false)
    } catch (e) {
      setError(friendlyNewsroomError(e))
    } finally {
      setBusy(false)
    }
  }
  function startEdit() {
    setStatus(t.status)
    setStage(t.stage)
    setDate(fresh[0]?.date || today())
    setSources([...new Set(fresh.map((r) => r.source))].join(', '))
    setEditing(true)
  }
  const save = () => run(() => trackersApi().setStatus(t.slug, {
    status, date, stage: t.stages.length ? stage : null, sources: sources.split(',').map((s) => s.trim()).filter(Boolean),
  }))
  const list = showAll ? t.reports : fresh

  return (
    <li className={`list-none rounded-2xl border bg-white ${open ? 'border-[#0f2340]/20 shadow-sm' : 'border-gray-200'}`} data-testid="tracker-row">
      <button type="button" onClick={onToggle} aria-expanded={open} className="min-h-[72px] w-full items-center gap-3 rounded-2xl p-3 text-left active:bg-gray-50 [display:flex]">
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[15px] font-semibold text-gray-900">{t.name}</span>
          <span className="mt-1 flex-wrap items-center gap-1.5 text-xs text-gray-600 [display:flex]">
            <Chip tone="blue" className="!px-2 !py-0.5">{KIND[t.kind]}</Chip>
            {t.stage !== null && <span>{t.stages[t.stage]}</span>}
            <span>status {t.status_date}</span>
            {t.new_count > 0 ? <StatusPill tone="bad">{t.new_count} new report{t.new_count === 1 ? '' : 's'}</StatusPill> : <StatusPill tone="ok">Up to date</StatusPill>}
          </span>
        </span>
        <span aria-hidden className={`text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}>›</span>
      </button>

      {open && (
        <div className="space-y-3 px-4 pb-4">
          <div className="rounded-xl bg-[#0f2340] p-3 text-white">
            <p className="text-xs font-bold uppercase tracking-wide text-[#f6d58a]">Status on the site{t.stage !== null && ` · ${t.stages[t.stage]}`}</p>
            <p className="mt-1 text-sm leading-relaxed">{t.status}</p>
            <p className="mt-1 text-xs text-white/70">As of {t.status_date}{t.status_sources.length > 0 && ` · from ${t.status_sources.join(', ')}`}</p>
          </div>

          <div>
            <p className="text-sm font-semibold text-gray-800">{showAll ? `All reports (${t.reports.length})` : fresh.length ? 'New since the status was checked' : 'No new reports since the status was checked.'}</p>
            {list.length > 0 && (
              <ul className="mt-2 space-y-2 p-0">
                {list.map((r) => (
                  <li key={r.id} className={`list-none rounded-xl border p-3 text-sm ${r.hidden ? 'border-dashed border-gray-300 bg-gray-50 text-gray-500' : 'border-gray-200'}`}>
                    <p className="text-xs text-gray-500">{r.date} · {r.source}{r.hidden && ' · hidden from the site'}</p>
                    <a href={r.url} target="_blank" rel="noopener noreferrer" className="mt-0.5 block font-semibold text-blue-800 underline">{r.title}</a>
                    <button type="button" disabled={busy} onClick={() => run(() => trackersApi().hide(t.slug, r.id, !r.hidden))}
                      className="mt-1 min-h-[44px] text-xs font-semibold text-[#0f2340] underline disabled:opacity-50">
                      {r.hidden ? 'Show on the site again' : 'Not about this: hide it'}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {t.reports.length > fresh.length && (
              <button type="button" onClick={() => setShowAll((s) => !s)} className="min-h-[44px] text-sm font-semibold text-[#0f2340] underline">
                {showAll ? 'Show only the new ones' : `Show all ${t.reports.length} reports`}
              </button>
            )}
          </div>

          {editing ? (
            <div className="space-y-3 rounded-xl border border-gray-200 p-3">
              {t.stages.length > 0 && (
                <div>
                  <label htmlFor={`stage-${t.slug}`} className="mb-1 block text-sm font-medium text-gray-700">Stage</label>
                  <select id={`stage-${t.slug}`} value={stage ?? ''} onChange={(e) => setStage(e.target.value === '' ? null : Number(e.target.value))} className={field}>
                    <option value="">Not sure</option>
                    {t.stages.map((s, i) => <option key={s} value={i}>{s}</option>)}
                  </select>
                </div>
              )}
              <div>
                <label htmlFor={`status-${t.slug}`} className="mb-1 block text-sm font-medium text-gray-700">Status, in our words</label>
                <textarea id={`status-${t.slug}`} rows={4} value={status} onChange={(e) => setStatus(e.target.value)} className={field} />
                <p className="mt-1 text-xs text-gray-600">Say only what the reports say. Approved is not built, and built is not open.</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label htmlFor={`date-${t.slug}`} className="mb-1 block text-sm font-medium text-gray-700">True as of</label>
                  <input id={`date-${t.slug}`} type="date" value={date} max={today()} onChange={(e) => setDate(e.target.value)} className={`${field} min-h-[52px]`} />
                </div>
                <div>
                  <label htmlFor={`src-${t.slug}`} className="mb-1 block text-sm font-medium text-gray-700">From reports by</label>
                  <input id={`src-${t.slug}`} type="text" value={sources} onChange={(e) => setSources(e.target.value)} placeholder="Punekar News, Pune Mirror" className={`${field} min-h-[52px]`} />
                </div>
              </div>
              {error && <ErrorBox message={error} />}
              <Btn onClick={save} disabled={busy || (status.trim() === t.status && stage === t.stage)} className="!bg-blue-900 active:!bg-blue-950 disabled:!bg-blue-300">{busy ? 'Saving...' : 'Put this status on the site'}</Btn>
              <Btn variant="ghost" onClick={() => setEditing(false)} disabled={busy}>Cancel</Btn>
            </div>
          ) : (
            <div className="space-y-2">
              {error && <ErrorBox message={error} />}
              <Btn onClick={startEdit} disabled={busy} className="!bg-blue-900 active:!bg-blue-950">Update the status</Btn>
              {fresh.length > 0 && <Btn variant="secondary" onClick={() => run(() => trackersApi().checked(t.slug))} disabled={busy}>Read them: the status still holds</Btn>}
              <a href={`/news/track/${t.slug}`} target="_blank" rel="noopener noreferrer" className="flex min-h-[44px] items-center justify-center text-sm font-semibold text-[#0f2340] underline">Open the public page</a>
            </div>
          )}
        </div>
      )}
    </li>
  )
}

/** The Trackers tab: every tracker, the ones with new reports first. `onCount` tells the tab bar how many reports are new. */
export function TrackerDesk({ onCount }: { onCount?: (n: number) => void }) {
  const { data, error, loading, reload, setData } = useAsync(async () => {
    const rows = await trackersApi().list()
    onCount?.(rows.reduce((n, t) => n + t.new_count, 0))
    return rows
  }, [])
  const [openSlug, setOpenSlug] = useState<string | null>(null)
  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return null
  const replace = (t: DeskTracker) => setData((rows) => {
    const next = (rows ?? []).map((x) => (x.slug === t.slug ? t : x))
    onCount?.(next.reduce((n, x) => n + x.new_count, 0))
    return next
  })
  return (
    <>
      <p className="text-xs text-gray-600">
        One page per thing that keeps changing. Reports attach by themselves; the status line changes only when you write one here. Check the new reports, then update the status or mark it still true.
      </p>
      <ul className="space-y-2 p-0">
        {data.map((t) => (
          <TrackerRow key={t.slug} t={t} open={openSlug === t.slug} onToggle={() => setOpenSlug((o) => (o === t.slug ? null : t.slug))} onChange={replace} />
        ))}
      </ul>
    </>
  )
}
