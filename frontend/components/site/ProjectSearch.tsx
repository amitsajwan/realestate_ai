'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import CheckBadge from '@/components/site/CheckBadge'
import { displayName, projectSummary, searchPlace, searchRegister } from '@/lib/site/register'
import type { PlaceMatch, RegisterSearchHit } from '@/lib/site/register'

/** The area page the search names ("2 bhk kharadi" opens Kharadi's 2 BHK list), above the projects. Shared with HeaderSearch. */
export function PlaceRow({ place, onPick, className = '' }: { place: PlaceMatch; onPick?: () => void; className?: string }) {
  return (
    <li>
      <Link href={place.path} onClick={onPick} data-testid="search-place"
        className={`flex min-h-[56px] items-center justify-between gap-3 py-2 no-underline hover:bg-amber-50 ${className}`}>
        <span className="flex flex-col">
          <span className="font-semibold text-[#0f2340] underline-offset-2 hover:underline">{place.label}</span>
          <span className="text-sm text-slate-600">Area page: every project there, checked against MahaRERA</span>
        </span>
        <span aria-hidden="true" className="text-xl text-[#0f2340]">&rsaquo;</span>
      </Link>
    </li>
  )
}

/** One result row: marketed name as the link, the summary line under it. Shared by the server-rendered (?q=) results. */
export function SearchHitRow({ it }: { it: RegisterSearchHit }) {
  const shown = displayName(it)
  return (
    <li>
      <Link href={`/projects/${it.slug}`} className="flex min-h-[48px] flex-col justify-center py-2 no-underline hover:bg-slate-50">
        <span className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-[#0f2340] underline-offset-2 hover:underline">{shown}</span>
          {it.active === false ? <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600 ring-1 ring-inset ring-slate-300">Finished</span>
            : <CheckBadge checked={it.checked} total={it.checks_total} compact />}
        </span>
        <span className="text-sm text-slate-600">
          {[projectSummary(it), it.place_name, shown !== it.name ? `MahaRERA: ${it.name}` : null, it.regno].filter(Boolean).join(' · ')}
        </span>
      </Link>
    </li>
  )
}

/**
 * Find a project by name (marketed, MahaRERA's or another known name), builder or MahaRERA number: the backend searches
 * (GET /api/v1/public/register/search), so the page never ships the whole register. Without JavaScript the box is a plain GET
 * form to /projects?q=, which the page answers on the server (initialQ / initialHits).
 */
/** One empty list for the default: a new [] on each render would re-run the search effect, which sets state, forever. */
const NO_HITS: RegisterSearchHit[] = []

/** `hero` sits the box on the home page's navy hero: no card around it, the label for screen readers only, results in a white panel. */
export default function ProjectSearch({ initialQ = '', initialHits = NO_HITS, initialPlace = null, hero = false }:
  { initialQ?: string; initialHits?: RegisterSearchHit[]; initialPlace?: PlaceMatch | null; hero?: boolean }) {
  const [q, setQ] = useState(initialQ)
  const [hits, setHits] = useState<RegisterSearchHit[]>(initialHits)
  const [place, setPlace] = useState<PlaceMatch | null>(initialPlace)
  const router = useRouter()
  const [done, setDone] = useState(initialQ.trim().length >= 2)
  const input = useRef<HTMLInputElement>(null)

  // a visitor may type before the page hydrates: pick up what is already in the box
  useEffect(() => {
    const v = input.current?.value ?? ''
    if (v && v !== q) setQ(v)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const t = q.trim()
    if (t.length < 2) { setHits([]); setPlace(null); setDone(false); return }
    if (t === initialQ.trim() && (initialHits.length || initialPlace)) return
    const ctrl = new AbortController()
    const timer = setTimeout(() => {
      Promise.all([searchRegister(t, 20, ctrl.signal), searchPlace(t, ctrl.signal)]).then(([h, p]) => {
        if (!ctrl.signal.aborted) { setHits(h); setPlace(p); setDone(true) }
      })
    }, 250)
    return () => { clearTimeout(timer); ctrl.abort() }
  }, [q, initialQ, initialHits, initialPlace])

  // Search (or Enter): an area the search names opens its page, one project opens that project; anything else goes on to
  // /projects?q=, the full results (the form's own submit, as without JavaScript). It used to do nothing (2026-10-29).
  const submit = (e: React.FormEvent) => {
    const t = q.trim()
    const go = place && done ? place.path : hits.length === 1 && done ? `/projects/${hits[0].slug}` : null
    if (go) { e.preventDefault(); router.push(go) }
    else if (t.length < 2) e.preventDefault()
  }

  return (
    <section aria-labelledby="search-title" className={hero ? 'mt-7 max-w-2xl' : 'mt-8 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5'}>
      <form action="/projects" method="get" role="search" onSubmit={submit}>
        <label id="search-title" htmlFor="project-search" className={hero ? 'sr-only' : 'block text-lg font-semibold text-slate-900'}>Find a project</label>
        <div className={hero ? 'flex gap-2' : 'mt-2 flex gap-2'}>
          <input
            ref={input} id="project-search" name="q" type="search" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off"
            placeholder="Area, project, builder or MahaRERA number"
            className={(hero ? 'min-h-[52px] border-transparent bg-white shadow-sm' : 'min-h-[48px] border-slate-300') + ' w-full rounded-xl border px-4 text-base text-slate-900 placeholder:text-slate-500 focus:border-[#0f2340] focus:outline-none focus:ring-2 focus:ring-[#0f2340]/20'}
          />
          <button type="submit" className={hero ? 'min-h-[52px] rounded-xl bg-[#f0b440] px-5 font-semibold text-[#0f2340] hover:bg-[#f5c75e]' : 'min-h-[48px] rounded-xl bg-[#0f2340] px-4 font-semibold text-white'}>Search</button>
        </div>
      </form>
      {q.trim().length >= 2 && done && (
        <div aria-live="polite" className={hero ? 'mt-2 rounded-xl bg-white px-4 py-2 text-slate-900 shadow-lg' : 'mt-3'}>
          {hits.length === 0 && !place ? (
            <p className="text-slate-700">No project matches &ldquo;{q}&rdquo; in our MahaRERA register.</p>
          ) : (
            <ul className="list-none divide-y divide-slate-100 p-0" data-testid="project-search-results">
              {place && <PlaceRow place={place} />}
              {hits.map((it) => <SearchHitRow key={it.slug} it={it} />)}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}
