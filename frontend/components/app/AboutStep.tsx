'use client'
import React, { useState } from 'react'
import { AMENITY_CHIPS, FAQ_PRESETS, MAX_FAQ_UI, MAX_HIGHLIGHTS, MAX_TEXT, NEARBY_CHIPS, aboutProblem, compactAbout, textProblem } from '@/lib/app/about'
import { api, errorMessage } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import type { About, AboutNearby, AboutSource, AboutSuggestion } from '@/lib/app/types'
import { Btn, ErrorBox, inputCls } from './ui'

type FieldKey = 'water' | 'power_backup' | 'maintenance' | 'parking' | 'society'
const FIELDS: Array<{ key: FieldKey; label: Parameters<typeof t>[0]; placeholder: string }> = [
  { key: 'water', label: 'aboutWater', placeholder: '24x7 water supply' },
  { key: 'power_backup', label: 'aboutPower', placeholder: 'Full power backup' },
  { key: 'maintenance', label: 'aboutMaintenance', placeholder: '₹3,000 per month' },
  { key: 'parking', label: 'aboutParking', placeholder: '1 covered parking' },
  { key: 'society', label: 'aboutSociety', placeholder: 'Gated society' },
]

export interface AboutStepProps {
  value: About
  onChange: (a: About) => void
  /** What the suggestion call reads: the listing so far. */
  context: { locality?: string; project_name?: string; bhk?: number; description: string }
  onDone: () => void
  onSkip: () => void
}

function SourceTag({ source }: { source: AboutSource }) {
  return (
    <span
      data-source={source}
      className={`ml-2 inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold ${source === 'area_guide' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'}`}
    >
      {source === 'area_guide' ? t('aboutFromGuide') : t('aboutFromYou')}
    </span>
  )
}

function Chip({ label, on, onClick }: { label: string; on: boolean; onClick: () => void }) {
  return (
    <button type="button" aria-pressed={on} onClick={onClick}
      className={`min-h-[44px] rounded-full border px-4 text-sm font-semibold ${on ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-gray-700'}`}>
      {label}
    </button>
  )
}

const toggle = (list: string[], v: string) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v])
const sameNearby = (a: AboutNearby, b: AboutNearby) => a.type === b.type && a.name.toLowerCase() === b.name.toLowerCase()

export function AboutStep({ value, onChange, context, onDone, onSkip }: AboutStepProps) {
  const [sugg, setSugg] = useState<AboutSuggestion | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hl, setHl] = useState('')
  const set = (patch: About) => onChange({ ...value, ...patch })
  const amenities = value.amenities ?? []
  const nearby = value.nearby ?? []
  const highlights = value.highlights ?? []
  const connectivity = value.connectivity ?? []
  const faq = value.faq ?? []

  async function suggest() {
    setBusy(true)
    setError(null)
    try {
      const s = await api.suggestAbout({ ...context, description: context.description })
      setSugg(s)
      if (s.project_name && !value.project_name) set({ project_name: s.project_name })
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  // ---- keep / remove for suggestions ----
  type Row = { key: string; text: string; source: AboutSource; kept: boolean; toggle: () => void }
  const rows: Row[] = []
  if (sugg) {
    for (const h of sugg.highlights) rows.push({ key: `h:${h.text}`, text: h.text, source: h.source, kept: highlights.includes(h.text),
      toggle: () => set({ highlights: highlights.includes(h.text) ? highlights.filter((x) => x !== h.text) : [...highlights, h.text].slice(0, MAX_HIGHLIGHTS) }) })
    for (const a of sugg.amenities) rows.push({ key: `a:${a.text}`, text: a.text, source: a.source, kept: amenities.includes(a.text), toggle: () => set({ amenities: toggle(amenities, a.text) }) })
    for (const n of sugg.nearby) {
      const item: AboutNearby = { type: n.type, name: n.name, ...(typeof n.minutes === 'number' ? { minutes: n.minutes } : {}) }
      const kept = nearby.some((x) => sameNearby(x, item))
      rows.push({ key: `n:${n.name}`, text: n.name, source: n.source, kept, toggle: () => set({ nearby: kept ? nearby.filter((x) => !sameNearby(x, item)) : [...nearby, item] }) })
    }
    for (const c of sugg.connectivity) rows.push({ key: `c:${c.text}`, text: c.text, source: c.source, kept: connectivity.includes(c.text), toggle: () => set({ connectivity: toggle(connectivity, c.text) }) })
    for (const f of FIELDS) {
      const s = sugg.fields[f.key]
      if (s) rows.push({ key: `f:${f.key}`, text: `${t(f.label)}: ${s.text}`, source: s.source, kept: value[f.key] === s.text, toggle: () => set({ [f.key]: value[f.key] === s.text ? undefined : s.text }) })
    }
  }
  function keepAll() {
    const next: About = { ...value }
    const add = (cur: string[], v: string) => (cur.includes(v) ? cur : [...cur, v])
    for (const h of sugg?.highlights ?? []) next.highlights = add(next.highlights ?? [], h.text).slice(0, MAX_HIGHLIGHTS)
    for (const a of sugg?.amenities ?? []) next.amenities = add(next.amenities ?? [], a.text)
    for (const c of sugg?.connectivity ?? []) next.connectivity = add(next.connectivity ?? [], c.text)
    for (const n of sugg?.nearby ?? []) {
      const item: AboutNearby = { type: n.type, name: n.name, ...(typeof n.minutes === 'number' ? { minutes: n.minutes } : {}) }
      if (!(next.nearby ?? []).some((x) => sameNearby(x, item))) next.nearby = [...(next.nearby ?? []), item]
    }
    for (const f of FIELDS) { const s = sugg?.fields[f.key]; if (s && !next[f.key]) next[f.key] = s.text }
    onChange(next)
  }

  const problem = aboutProblem(value)
  const addHighlight = () => {
    const v = hl.trim()
    if (!v || highlights.length >= MAX_HIGHLIGHTS || textProblem(v)) return
    set({ highlights: [...highlights, v] })
    setHl('')
  }
  const setFaq = (i: number, patch: Partial<{ q: string; a: string }>) => {
    const next = [...faq]
    while (next.length <= i) next.push({ q: FAQ_PRESETS[next.length] ?? '', a: '' })
    next[i] = { ...next[i], ...patch }
    set({ faq: next })
  }
  const faqRows = Array.from({ length: MAX_FAQ_UI }, (_, i) => faq[i] ?? { q: FAQ_PRESETS[i] ?? '', a: '' })

  return (
    <div className="space-y-5" data-testid="about-step">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold">{t('aboutTitle')}</h1>
        <p className="text-sm text-gray-600">{t('aboutHelp')}</p>
      </div>

      <section className="space-y-3 rounded-2xl border border-blue-200 bg-blue-50 p-3">
        <Btn variant="secondary" onClick={suggest} disabled={busy}>{busy ? t('aboutSuggesting') : t('aboutSuggest')}</Btn>
        {error && <ErrorBox message={error} />}
        {sugg && rows.length === 0 && <p className="text-sm text-gray-700">{t('aboutSuggestNone')}</p>}
        {rows.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm text-gray-700">{t('aboutSuggestHint')}</p>
            <ul className="space-y-2" aria-label="Suggestions">
              {rows.map((r) => (
                <li key={r.key} className="flex items-center justify-between gap-2 rounded-xl bg-white p-3">
                  <span className="min-w-0 flex-1 text-sm">{r.text}<SourceTag source={r.source} /></span>
                  <button type="button" onClick={r.toggle} aria-label={`${r.kept ? t('aboutRemove') : t('aboutKeep')}: ${r.text}`}
                    className={`min-h-[44px] min-w-[76px] rounded-xl border px-3 text-sm font-semibold ${r.kept ? 'border-gray-300 bg-white text-gray-700' : 'border-blue-600 bg-blue-600 text-white'}`}>
                    {r.kept ? t('aboutRemove') : t('aboutKeep')}
                  </button>
                </li>
              ))}
            </ul>
            <button type="button" onClick={keepAll} className="min-h-[44px] text-sm font-semibold text-blue-700 underline">{t('aboutKeepAll')}</button>
          </div>
        )}
      </section>

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-gray-700">{t('aboutAmenities')}</legend>
        <div className="flex flex-wrap gap-2">
          {Array.from(new Set([...AMENITY_CHIPS, ...amenities])).map((a) => <Chip key={a} label={a} on={amenities.includes(a)} onClick={() => set({ amenities: toggle(amenities, a) })} />)}
        </div>
      </fieldset>

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-gray-700">{t('aboutNearby')}</legend>
        <div className="flex flex-wrap gap-2">
          {NEARBY_CHIPS.map((c) => {
            const item = { type: c.type, name: c.label }
            const on = nearby.some((x) => sameNearby(x, item))
            return <Chip key={c.label} label={c.label} on={on} onClick={() => set({ nearby: on ? nearby.filter((x) => !sameNearby(x, item)) : [...nearby, item] })} />
          })}
          {nearby.filter((n) => !NEARBY_CHIPS.some((c) => c.label === n.name)).map((n) => (
            <Chip key={n.name} label={n.name} on onClick={() => set({ nearby: nearby.filter((x) => x !== n) })} />
          ))}
        </div>
      </fieldset>

      <div>
        <label htmlFor="about-project" className="mb-1 block text-sm font-medium text-gray-700">{t('aboutProject')}</label>
        <input id="about-project" className={inputCls} maxLength={MAX_TEXT} value={value.project_name ?? ''} onChange={(e) => set({ project_name: e.target.value })} />
      </div>

      <div className="grid grid-cols-1 gap-3">
        {FIELDS.map((f) => (
          <div key={f.key}>
            <label htmlFor={`about-${f.key}`} className="mb-1 block text-sm font-medium text-gray-700">{t(f.label)}</label>
            <input id={`about-${f.key}`} className={inputCls} maxLength={MAX_TEXT} placeholder={f.placeholder} value={value[f.key] ?? ''} onChange={(e) => set({ [f.key]: e.target.value })} />
          </div>
        ))}
      </div>

      {(highlights.length > 0 || connectivity.length > 0) && (
        <div className="space-y-2">
          {highlights.length > 0 && (
            <fieldset>
              <legend className="mb-2 text-sm font-medium text-gray-700">{t('aboutHighlights')}</legend>
              <div className="flex flex-wrap gap-2">
                {highlights.map((h) => <Chip key={h} label={h} on onClick={() => set({ highlights: highlights.filter((x) => x !== h) })} />)}
              </div>
            </fieldset>
          )}
          {connectivity.length > 0 && (
            <fieldset>
              <legend className="mb-2 text-sm font-medium text-gray-700">{t('aboutConnectivity')}</legend>
              <ul className="space-y-2">
                {connectivity.map((c) => (
                  <li key={c} className="flex items-start justify-between gap-2 rounded-xl bg-gray-50 p-3 text-sm">
                    <span className="min-w-0 flex-1">{c}</span>
                    <button type="button" aria-label={`${t('aboutRemove')}: ${c}`} onClick={() => set({ connectivity: connectivity.filter((x) => x !== c) })} className="min-h-[44px] min-w-[44px] font-semibold text-gray-600">✕</button>
                  </li>
                ))}
              </ul>
            </fieldset>
          )}
        </div>
      )}

      <div>
        <label htmlFor="about-hl" className="mb-1 block text-sm font-medium text-gray-700">{t('aboutHighlightAdd')}</label>
        <div className="flex gap-2">
          <input id="about-hl" className={inputCls} maxLength={80} placeholder="East facing, corner flat" value={hl} onChange={(e) => setHl(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addHighlight() } }} disabled={highlights.length >= MAX_HIGHLIGHTS} />
          <button type="button" onClick={addHighlight} disabled={!hl.trim() || highlights.length >= MAX_HIGHLIGHTS} className="min-h-[52px] rounded-xl border border-gray-300 px-4 font-semibold disabled:opacity-40">{t('aboutAdd')}</button>
        </div>
      </div>

      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-gray-800">{t('aboutFaqTitle')}</legend>
        {faqRows.map((f, i) => (
          <div key={i} className="space-y-2 rounded-xl border border-gray-200 p-3">
            <input aria-label={`Question ${i + 1}`} className={inputCls} maxLength={MAX_TEXT} value={f.q} onChange={(e) => setFaq(i, { q: e.target.value })} />
            <input aria-label={`${t('aboutFaqAnswer')} ${i + 1}`} className={inputCls} maxLength={MAX_TEXT} placeholder={t('aboutFaqAnswer')} value={f.a} onChange={(e) => setFaq(i, { a: e.target.value })} />
          </div>
        ))}
      </fieldset>

      <p className="text-xs text-gray-500">{t('aboutNoContact')}</p>
      {problem && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-700">{problem}</p>}

      <div className="sticky bottom-0 -mx-4 space-y-2 border-t border-gray-200 bg-white p-4" style={{ paddingBottom: 'calc(1rem + env(safe-area-inset-bottom, 0px))' }}>
        <Btn onClick={() => { onChange(compactAbout(value) ?? {}); onDone() }} disabled={!!problem}>{t('aboutContinue')}</Btn>
        <Btn variant="ghost" onClick={onSkip}>{t('aboutSkip')}</Btn>
      </div>
    </div>
  )
}
