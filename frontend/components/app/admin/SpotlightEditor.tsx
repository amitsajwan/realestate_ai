'use client'
import React, { useEffect, useState } from 'react'
import { adminApi } from '@/lib/app/admin'
import type { SpotlightConfig, SpotlightPick } from '@/lib/app/admin'
import { errorMessage } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import { useAsync } from '@/lib/app/useAsync'
import { LOCALITIES } from '@/lib/marketing/localities'
import { displayName, searchRegister, type RegisterSearchHit } from '@/lib/site/register'
import { Btn, ErrorBox, inputCls, Spinner } from '../ui'

const MAX_PICKS = 20
const NOTE_MAX = 60

/** Find a project page to pick: the public register search, as on /projects. */
function PickSearch({ taken, onPick }: { taken: string[]; onPick: (hit: RegisterSearchHit) => void }) {
  const [q, setQ] = useState('')
  const [hits, setHits] = useState<RegisterSearchHit[]>([])
  useEffect(() => {
    const ctrl = new AbortController()
    const t = setTimeout(() => searchRegister(q, 8, ctrl.signal).then(setHits), 250)
    return () => { clearTimeout(t); ctrl.abort() }
  }, [q])
  return (
    <div>
      <label htmlFor="spotlight-search" className="text-sm font-semibold text-gray-800">Add a project</label>
      <input id="spotlight-search" data-testid="spotlight-search" className={inputCls} value={q} onChange={(e) => setQ(e.target.value)}
        placeholder="Name, builder or MahaRERA number" autoComplete="off" />
      {q.trim().length >= 2 && (
        <ul className="mt-1 divide-y divide-gray-100 rounded-xl border border-gray-200 bg-white">
          {hits.filter((h) => !taken.includes(h.slug)).map((h) => (
            <li key={h.slug}>
              <button type="button" data-testid="spotlight-hit" onClick={() => { onPick(h); setQ('') }}
                className="flex min-h-[48px] w-full flex-col items-start px-3 py-2 text-left active:bg-gray-50">
                <span className="font-semibold text-gray-900">{displayName(h)}</span>
                <span className="text-xs text-gray-500">{[h.place_name, h.regno].filter(Boolean).join(' · ')}</span>
              </button>
            </li>
          ))}
          {!hits.length && <li className="px-3 py-2 text-sm text-gray-500">No project found</li>}
        </ul>
      )}
    </div>
  )
}

/** Studio > Admin > Hot projects banner: the strip of project links under the header of every public page. */
export function SpotlightEditor() {
  const { data, error, loading, reload } = useAsync(() => adminApi.spotlight(), [])
  const [auto, setAuto] = useState(true)
  const [items, setItems] = useState<SpotlightPick[]>([])
  const [names, setNames] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState<SpotlightConfig | null>(null)
  const [busy, setBusy] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    if (!data) return
    setAuto(data.auto)
    setItems(data.items)
    setSaved(data)
    setNames(Object.fromEntries(data.preview.map((p) => [p.slug, p.name])))
  }, [data])

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />

  const change = (i: number, patch: Partial<SpotlightPick>) => setItems(items.map((it, j) => (j === i ? { ...it, ...patch } : it)))
  const move = (i: number, by: number) => {
    const j = i + by
    if (j < 0 || j >= items.length) return
    const next = [...items];
    [next[i], next[j]] = [next[j], next[i]]
    setItems(next)
  }
  async function save() {
    setBusy(true)
    setSaveError(null)
    try {
      const out = await adminApi.setSpotlight({ auto, items })
      setSaved(out)
      setItems(out.items)
    } catch (e) {
      setSaveError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-3" data-testid="spotlight-editor">
      <p className="text-sm text-gray-600">
        A rolling strip of project links under the header of every buyer page. Your picks come first; a pick for an area shows only on
        that area&apos;s pages. Only projects with a live page that Google may list are shown.
      </p>
      <label className="flex min-h-[48px] items-center gap-3 rounded-2xl border border-gray-200 bg-white p-3">
        <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} data-testid="spotlight-auto" className="h-5 w-5" />
        <span className="text-sm"><b>Fill up with hot projects</b><br />
          <span className="text-gray-600">After your picks, up to 6 in all, by MahaRERA bookings, launches, news and searches</span></span>
      </label>

      <ul className="space-y-2">
        {items.map((it, i) => (
          <li key={it.slug} data-testid="spotlight-pick" className="space-y-2 rounded-2xl border border-gray-200 bg-white p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="min-w-0 font-semibold text-gray-900">
                {names[it.slug] ?? it.slug}<br /><a href={`/projects/${it.slug}`} target="_blank" rel="noopener noreferrer" className="text-xs font-normal text-gray-500 underline">/projects/{it.slug}</a>
              </p>
              <div className="flex shrink-0 gap-1">
                <button type="button" aria-label="Move up" onClick={() => move(i, -1)} className="h-11 w-11 rounded-lg border border-gray-200">↑</button>
                <button type="button" aria-label="Move down" onClick={() => move(i, 1)} className="h-11 w-11 rounded-lg border border-gray-200">↓</button>
                <button type="button" aria-label={`Remove ${names[it.slug] ?? it.slug}`} onClick={() => setItems(items.filter((_, j) => j !== i))}
                  className="h-11 w-11 rounded-lg border border-gray-200 text-red-700">✕</button>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <label className="text-xs font-semibold text-gray-700">Show on
                <select className={inputCls} value={it.area ?? ''} onChange={(e) => change(i, { area: e.target.value || null })}>
                  <option value="">Every page</option>
                  {LOCALITIES.map((l) => <option key={l.key} value={l.key}>{l.name} pages</option>)}
                </select>
              </label>
              <label className="text-xs font-semibold text-gray-700">Short note (optional)
                <input className={inputCls} value={it.note} maxLength={NOTE_MAX} placeholder="e.g. New tower registered"
                  onChange={(e) => change(i, { note: e.target.value })} />
              </label>
              <label className="text-xs font-semibold text-gray-700">Last day (optional)
                <input type="date" className={inputCls} value={it.until ?? ''} onChange={(e) => change(i, { until: e.target.value || null })} />
              </label>
            </div>
          </li>
        ))}
      </ul>

      {items.length < MAX_PICKS && (
        <PickSearch taken={items.map((it) => it.slug)} onPick={(h) => {
          setNames({ ...names, [h.slug]: displayName(h) })
          setItems([...items, { slug: h.slug, area: null, note: '', until: null }])
        }} />
      )}

      {saveError && <ErrorBox message={saveError} />}
      <Btn type="button" onClick={save} disabled={busy} data-testid="spotlight-save">{busy ? 'Saving...' : 'Save banner'}</Btn>

      {saved && (
        <div className="rounded-2xl bg-gray-50 p-3" data-testid="spotlight-preview">
          <p className="text-sm font-semibold text-gray-800">Shown now on pages with no area</p>
          {saved.preview.length ? (
            <ol className="mt-1 list-decimal space-y-1 pl-5 text-sm text-gray-700">
              {saved.preview.map((p) => <li key={p.slug}><b>{p.name}</b>{p.area ? ` · ${p.area}` : ''}: {p.note || `${p.fact} (${p.source})`}{p.picked ? '' : ' (hot)'}</li>)}
            </ol>
          ) : <p className="text-sm text-gray-600">Nothing: the banner is hidden.</p>}
          {saved.updated_at && <p className="mt-1 text-xs text-gray-500">Last changed {timeAgo(saved.updated_at)}</p>}
        </div>
      )}
    </div>
  )
}
