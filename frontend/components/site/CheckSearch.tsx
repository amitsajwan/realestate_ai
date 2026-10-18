'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { displayName, searchRegister } from '@/lib/site/register'
import type { RegisterSearchHit } from '@/lib/site/register'
import { CHECK_STYLE, checkPill, checkState, forgetCheck, savedChecks } from '@/lib/site/check'
import type { SavedCheck } from '@/lib/site/check'

export function checkHref(it: { slug: string; regno: string }): string {
  return `/check/${it.slug}?r=${encodeURIComponent(it.regno)}`
}

/** One result: the name, what its possession date did, and who and where. The whole row is the tap target. */
export function CheckHitRow({ it }: { it: RegisterSearchHit }) {
  const s = checkState(it.completion_now, it.months_later)
  return (
    <li>
      <Link href={checkHref(it)} className="flex min-h-[56px] flex-col justify-center gap-1 px-1 py-3 no-underline hover:bg-slate-50">
        <span className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-[#0f2340]">{displayName(it)}</span>
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${CHECK_STYLE[s].pill}`}>{checkPill(s, it.months_later)}</span>
        </span>
        <span className="text-sm text-slate-600">{[it.promoter, it.place_name, it.regno].filter(Boolean).join(' · ')}</span>
      </Link>
    </li>
  )
}

/** Projects this viewer checked before, one tap away (kept in this browser only). */
function Saved() {
  const [items, setItems] = useState<SavedCheck[]>([])
  useEffect(() => setItems(savedChecks()), [])
  if (!items.length) return null
  return (
    <section aria-labelledby="saved-title" className="mt-6">
      <h2 id="saved-title" className="text-sm font-semibold uppercase tracking-wide text-slate-600">Checked before</h2>
      <ul className="mt-2 flex list-none flex-wrap gap-2 p-0">
        {items.map((c) => (
          <li key={c.regno} className="flex items-center rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200">
            <Link href={checkHref(c)} className="inline-flex min-h-[44px] items-center pl-4 pr-2 font-semibold text-[#0f2340] no-underline">{c.name}</Link>
            <button type="button" aria-label={`Remove ${c.name}`} onClick={() => { forgetCheck(c.regno); setItems(savedChecks()) }}
              className="inline-flex min-h-[44px] min-w-[40px] items-center justify-center rounded-full text-slate-500 hover:text-slate-900">×</button>
          </li>
        ))}
      </ul>
    </section>
  )
}

/**
 * The checker's search: name, builder or MahaRERA number; results as you type (GET /api/v1/public/register/search), each with what its
 * possession date did. Without JavaScript the box is a GET form to /check?q=, answered on the server (initialQ / initialHits).
 */
export default function CheckSearch({ initialQ = '', initialHits = [] }: { initialQ?: string; initialHits?: RegisterSearchHit[] }) {
  const [q, setQ] = useState(initialQ)
  const [hits, setHits] = useState<RegisterSearchHit[]>(initialHits)
  const [done, setDone] = useState(initialQ.trim().length >= 2)
  const input = useRef<HTMLInputElement>(null)

  useEffect(() => {   // typed before the page hydrated: pick it up
    const v = input.current?.value ?? ''
    if (v && v !== q) setQ(v)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const t = q.trim()
    if (t.length < 2) { setHits([]); setDone(false); return }
    if (t === initialQ.trim() && initialHits.length) return
    const ctrl = new AbortController()
    const timer = setTimeout(() => {
      searchRegister(t, 12, ctrl.signal).then((h) => { if (!ctrl.signal.aborted) { setHits(h); setDone(true) } })
    }, 250)
    return () => { clearTimeout(timer); ctrl.abort() }
  }, [q, initialQ, initialHits])

  return (
    <div>
      <form action="/check" method="get" role="search" onSubmit={(e) => e.preventDefault()}>
        <label htmlFor="check-search" className="sr-only">Project name, builder or MahaRERA number</label>
        <div className="flex gap-2">
          <input
            ref={input} id="check-search" name="q" type="search" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off"
            enterKeyHint="search" placeholder="Project name or MahaRERA no. (P52…)"
            className="min-h-[56px] w-full rounded-2xl border border-slate-300 bg-white px-4 text-lg text-slate-900 shadow-sm placeholder:text-slate-500 focus:border-[#0f2340] focus:outline-none focus:ring-2 focus:ring-[#0f2340]/20"
          />
          <button type="submit" className="min-h-[56px] rounded-2xl bg-amber-400 px-5 font-bold text-slate-900">Check</button>
        </div>
      </form>
      {q.trim().length >= 2 && done ? (
        <div aria-live="polite" className="mt-3 rounded-2xl border border-slate-200 bg-white px-3 shadow-sm">
          {hits.length === 0 ? (
            <p className="py-4 text-slate-700">
              No project matches &ldquo;{q}&rdquo; in our MahaRERA register for Pune district. Try another spelling, the builder&apos;s name,
              or the MahaRERA number printed on your agreement.
            </p>
          ) : (
            <ul className="list-none divide-y divide-slate-100 p-0" data-testid="check-results">
              {hits.map((it) => <CheckHitRow key={it.regno} it={it} />)}
            </ul>
          )}
        </div>
      ) : <Saved />}
    </div>
  )
}
