'use client'
/**
 * The Studio list pattern (UX + UI review, 2026-10-06), built once and used by Content, Newsroom, Listings, Leads:
 * - TabBar: sticky, scrolling tabs with counts (urgent = gold, error = red), the tab kept in the address (?tab=...);
 * - StatusPill: one wording and colour map for every Studio object (dot + word, never colour alone);
 * - ConfirmSheet: a bottom sheet for anything that cannot be undone (publishing);
 * - useUndo + UndoBar: "Skipped. Undo" for 8 s before the action reaches the server;
 * - LinkOut: "Instagram ↗" links to live posts.
 * Uses [display:flex] where a responsive variant could be overridden by styles/components.css.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react'

export const NAVY = '#0f2340'
export const GOLD = '#f0b440'

// ---- tabs ----------------------------------------------------------------------------------------------------------------
export interface TabDef {
  key: string
  label: string
  count?: number
  /** urgent: gold badge (needs you); error: red badge; normal: gray */
  tone?: 'normal' | 'urgent' | 'error'
  /** hide the tab when its count is 0 (e.g. Problems) */
  hideWhenEmpty?: boolean
}

export function TabBar({ tabs, value, onChange, label }: { tabs: TabDef[]; value: string; onChange: (key: string) => void; label: string }) {
  const shown = tabs.filter((t) => !(t.hideWhenEmpty && !t.count))
  return (
    <div role="tablist" aria-label={label}
      className="sticky top-0 z-10 -mx-4 mb-3 gap-1 overflow-x-auto border-b border-gray-200 bg-gray-50/95 px-2 backdrop-blur [display:flex] [scrollbar-width:none]">
      {shown.map((t) => {
        const on = t.key === value
        const badge = t.count == null ? null : (
          <span className={`min-w-[22px] rounded-full px-1.5 text-center text-xs font-bold tabular-nums leading-[22px] ${
            t.count && t.tone === 'urgent' ? 'bg-[#f0b440] text-[#0f2340]' : t.count && t.tone === 'error' ? 'bg-red-600 text-white' : 'bg-gray-200 text-gray-700'}`}>
            {t.count}
          </span>
        )
        return (
          <button key={t.key} type="button" role="tab" aria-selected={on} onClick={() => onChange(t.key)}
            className={`relative inline-flex min-h-[48px] flex-none items-center gap-1.5 whitespace-nowrap px-3 text-sm font-semibold ${
              on ? 'text-[#0f2340] after:absolute after:inset-x-2 after:bottom-0 after:h-[3px] after:rounded-full after:bg-[#0f2340]' : 'text-gray-600 active:bg-gray-100'}`}>
            {t.label}{badge}
          </button>
        )
      })}
    </div>
  )
}

/** The open tab, kept in the address (?tab=) so links, Back and refresh land on it. `fallback` is used when there is none. */
export function useUrlTab(param: string, fallback: string, allowed: string[]): [string, (k: string) => void] {
  const read = () => {
    if (typeof window === 'undefined') return null
    const v = new URLSearchParams(window.location.search).get(param)
    return v && allowed.includes(v) ? v : null
  }
  const [chosen, setChosen] = useState<string | null>(read)
  const set = useCallback((k: string) => {
    setChosen(k)
    if (typeof window !== 'undefined') {
      const u = new URL(window.location.href)
      u.searchParams.set(param, k)
      window.history.replaceState(window.history.state, '', u.toString())
    }
  }, [param])
  return [chosen && allowed.includes(chosen) ? chosen : fallback, set]
}

// ---- status --------------------------------------------------------------------------------------------------------------
export type PillTone = 'action' | 'info' | 'ok' | 'muted' | 'done' | 'bad'
const PILL: Record<PillTone, string> = {
  action: 'bg-[#f0b440] text-[#0f2340]', info: 'bg-blue-50 text-blue-800', ok: 'bg-green-50 text-green-800',
  muted: 'bg-gray-100 text-gray-700', done: 'bg-[#e7ebf2] text-[#0f2340]', bad: 'bg-red-50 text-red-700',
}

export function StatusPill({ tone, children }: { tone: PillTone; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold before:h-1.5 before:w-1.5 before:rounded-full before:bg-current ${PILL[tone]}`}>
      {children}
    </span>
  )
}

export function LinkOut({ href, children, label }: { href: string; children: React.ReactNode; label?: string }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer"
      className="inline-flex min-h-[44px] items-center gap-1 text-sm font-semibold text-[#0f2340] underline decoration-[#f0b440] decoration-2 underline-offset-4">
      {children} <span aria-hidden>↗</span><span className="sr-only"> {label ?? ''} (opens in a new tab)</span>
    </a>
  )
}

// ---- confirm sheet -------------------------------------------------------------------------------------------------------
export function ConfirmSheet({ title, children, confirmLabel, onConfirm, onCancel, busy }: {
  title: string; children?: React.ReactNode; confirmLabel: string; onConfirm: () => void; onCancel: () => void; busy?: boolean
}) {
  return (
    <div className="fixed inset-0 z-[60] items-end bg-black/50 [display:flex]" role="dialog" aria-modal="true" aria-label={title}>
      <div className="mx-auto max-h-[92vh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-white p-5" style={{ paddingBottom: 'calc(1.25rem + env(safe-area-inset-bottom, 0px))' }}>
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        {children && <div className="mt-2 space-y-2 text-sm text-gray-700">{children}</div>}
        <div className="mt-4 space-y-2">
          <button type="button" disabled={busy} onClick={onConfirm}
            className="min-h-[52px] w-full rounded-xl bg-[#0f2340] px-5 text-base font-semibold text-white disabled:bg-gray-300">{confirmLabel}</button>
          <button type="button" onClick={onCancel} className="min-h-[48px] w-full rounded-xl text-base font-semibold text-gray-700 active:bg-gray-100">Cancel</button>
        </div>
      </div>
    </div>
  )
}

// ---- undo ----------------------------------------------------------------------------------------------------------------
export interface Pending { id: string; message: string }

/** Run `act` after `ms` unless undone. Returns [pending, schedule, undo]. Leaving the page runs what is pending at once. */
export function useUndo(ms = 8000): [Pending | null, (id: string, message: string, act: () => Promise<void>) => void, () => void] {
  const [pending, setPending] = useState<Pending | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const action = useRef<(() => Promise<void>) | null>(null)
  const flush = useCallback(() => {
    if (timer.current) clearTimeout(timer.current)
    const a = action.current
    action.current = null
    timer.current = null
    setPending(null)
    if (a) void a()
  }, [])
  const schedule = useCallback((id: string, message: string, act: () => Promise<void>) => {
    if (action.current) flush()   // one at a time: the previous one goes through
    action.current = act
    setPending({ id, message })
    timer.current = setTimeout(flush, ms)
  }, [flush, ms])
  const undo = useCallback(() => {
    if (timer.current) clearTimeout(timer.current)
    action.current = null
    timer.current = null
    setPending(null)
  }, [])
  useEffect(() => () => { if (action.current) void action.current() }, [])
  return [pending, schedule, undo]
}

export function UndoBar({ pending, onUndo }: { pending: Pending | null; onUndo: () => void }) {
  if (!pending) return null
  return (
    <div role="status" className="fixed inset-x-0 z-50 px-4" style={{ bottom: 'calc(76px + env(safe-area-inset-bottom, 0px))' }}>
      <div className="mx-auto max-w-md items-center justify-between gap-3 rounded-2xl bg-gray-900 px-4 py-2 text-sm text-white shadow-lg [display:flex]">
        <span>{pending.message}</span>
        <button type="button" onClick={onUndo} className="min-h-[44px] px-2 font-bold text-[#f0b440]">Undo</button>
      </div>
    </div>
  )
}
