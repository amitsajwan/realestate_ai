'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import type { UpcomingBrief } from '@/lib/site/hubs'

/** The East Pune band as a small card in the corner, so the page keeps its place and nobody has to scroll to find it (owner
 *  2026-11-02). It slides in after a moment and shows one project at a time, each for a few seconds. It stops while a pointer or
 *  the keyboard is on it, stands still for reduced motion, and leaves while someone types so it never covers a form on a phone.
 *  × folds it to a small tab for a day. "Not yet MahaRERA registered" stays on every turn: see ComingSoonBand for why. */
export const TURN_MS = 5000
export const SHOW_AFTER_MS = 2500
export const FOLD_MS = 24 * 60 * 60 * 1000
const FOLD_KEY = 'coming-soon-folded-at'

function foldedRecently(now: number): boolean {
  try {
    const at = Number(window.localStorage.getItem(FOLD_KEY))
    return !!at && now - at < FOLD_MS
  } catch {
    return false
  }
}

function rememberFold(at: number | null) {
  try {
    if (at) window.localStorage.setItem(FOLD_KEY, String(at))
    else window.localStorage.removeItem(FOLD_KEY)
  } catch { /* private window: it folds for this page only */ }
}

export default function ComingSoonDock({ items, bottomBar = false }: { items: UpcomingBrief[]; bottomBar?: boolean }) {
  const [shown, setShown] = useState(false)
  const [folded, setFolded] = useState(false)
  const [at, setAt] = useState(0)
  const [paused, setPaused] = useState(false)
  const [typing, setTyping] = useState(false)
  const still = useRef(false)

  useEffect(() => {
    still.current = !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    setFolded(foldedRecently(Date.now()))
    const t = window.setTimeout(() => setShown(true), SHOW_AFTER_MS)
    return () => window.clearTimeout(t)
  }, [])

  useEffect(() => {
    if (!shown || folded || paused || still.current || items.length < 2) return
    const t = window.setInterval(() => setAt((i) => (i + 1) % items.length), TURN_MS)
    return () => window.clearInterval(t)
  }, [shown, folded, paused, items.length])

  useEffect(() => {
    const field = (e: Event) => (e.target as Element | null)?.matches?.('input, textarea, select') ?? false
    const on = (e: Event) => { if (field(e)) setTyping(true) }
    const off = (e: Event) => { if (field(e)) setTyping(false) }
    document.addEventListener('focusin', on)
    document.addEventListener('focusout', off)
    return () => { document.removeEventListener('focusin', on); document.removeEventListener('focusout', off) }
  }, [])

  if (!items.length || !shown || typing) return null
  const place = 'fixed left-3 z-30 sm:left-4 ' + (bottomBar ? 'bottom-[calc(5rem+env(safe-area-inset-bottom,0px))] md:bottom-6' : 'bottom-[calc(1rem+env(safe-area-inset-bottom,0px))] sm:bottom-6')

  if (folded) {
    return (
      <button type="button" onClick={() => { rememberFold(null); setFolded(false) }} data-print="hide" data-testid="coming-soon-tab"
        className={place + ' inline-flex min-h-[44px] items-center gap-2 rounded-full bg-[#0f2340] px-4 text-sm font-semibold text-white shadow-lg'}>
        <span aria-hidden="true" className="h-2 w-2 rounded-full bg-amber-300" />
        {items.length} launching soon
      </button>
    )
  }

  const u = items[at % items.length]
  return (
    <aside aria-label="Launching soon in East Pune" data-print="hide" data-testid="coming-soon-dock"
      onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)} onFocus={() => setPaused(true)} onBlur={() => setPaused(false)}
      className={place + ' coming-soon-dock w-[calc(100vw-5.5rem)] max-w-[320px] overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/10 sm:w-80'}>
      <div className="flex h-8 items-center gap-2 bg-[#0f2340] pl-3 pr-1 text-white">
        <span aria-hidden="true" className="coming-soon-pulse h-2 w-2 shrink-0 rounded-full bg-amber-300" />
        <p className="min-w-0 flex-1 truncate text-xs font-semibold">Launching soon in East Pune</p>
        <button type="button" aria-label="Fold launching soon" onClick={() => { rememberFold(Date.now()); setFolded(true) }} data-testid="coming-soon-fold"
          className="inline-flex !min-h-0 !min-w-0 h-7 w-7 shrink-0 items-center justify-center rounded-full text-base leading-none text-white hover:bg-white/20">×</button>
      </div>
      <Link key={u.slug} href={`/projects/upcoming/${u.slug}#enquire`} data-testid="coming-soon-link" className="coming-soon-turn block px-3 pb-2 pt-2 text-[#0f2340] no-underline">
        <span className="flex min-h-9 items-center justify-between gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {u.logo ? <img src={u.logo} alt={`${u.builder} logo`} decoding="async" className="max-h-9 w-auto min-w-0 max-w-[120px] object-contain" />
            : <span className="min-w-0 truncate text-sm font-bold">{u.builder}</span>}
          <span className="shrink-0 rounded-lg bg-amber-300 px-3 py-1.5 text-sm font-semibold">Tell me first</span>
        </span>
        <span className="mt-1 block truncate text-sm font-semibold">{u.name}</span>
        <span className="block truncate text-xs text-slate-700">{u.area_name}{u.note ? ` · ${u.note}` : ''}</span>
        <span className="mt-1 hidden text-xs text-slate-600 sm:block">Price and any launch offer come out the day it registers.</span>
        <span className="mt-0.5 block text-[11px] font-medium text-amber-800">Not yet MahaRERA registered · No bookings taken</span>
      </Link>
    </aside>
  )
}
