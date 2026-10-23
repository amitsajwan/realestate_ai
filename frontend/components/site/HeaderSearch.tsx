'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { checkHref } from '@/components/site/CheckSearch'
import { CHECK_STYLE, checkPill, checkState, savedChecks } from '@/lib/site/check'
import type { SavedCheck } from '@/lib/site/check'
import { displayName } from '@/lib/site/register'
import type { RegisterSearchHit } from '@/lib/site/register'
import { useRegisterSearch } from '@/lib/site/useRegisterSearch'

const SHOWN = 8
const PHONE = '(max-width: 1023px)'   // below Tailwind's lg: the full-screen sheet; from lg up a panel under the trigger
const REGNO = /^p(r|c)?\d/i            // the visitor is typing a MahaRERA number: show it on each row

function Glass({ className }: { className: string }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className={className}>
      <circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" />
    </svg>
  )
}

/** One result: the row opens the project page; the block on its right opens the MahaRERA check card. Two big, separate targets. */
function Row({ it, q, onPick }: { it: RegisterSearchHit; q: string; onPick: () => void }) {
  const name = displayName(it)
  const s = checkState(it.completion_now, it.months_later)
  return (
    <li className="flex items-stretch">
      <Link href={`/projects/${it.slug}`} onClick={onPick} data-testid="header-search-hit"
        className="flex min-h-[64px] min-w-0 flex-1 flex-col justify-center gap-1 px-4 py-2 no-underline hover:bg-slate-50 focus-visible:bg-slate-50">
        <span className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-[#0f2340]">{name}</span>
          {it.active === false
            ? <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600 ring-1 ring-inset ring-slate-300">Finished</span>
            : <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${CHECK_STYLE[s].pill}`}>{checkPill(s, it.months_later)}</span>}
        </span>
        <span className="truncate text-sm text-slate-600">{[it.promoter, it.place_name, REGNO.test(q.trim()) ? it.regno : null].filter(Boolean).join(' · ')}</span>
      </Link>
      <Link href={checkHref(it)} onClick={onPick} aria-label={`Check ${name} on MahaRERA`}
        className="flex w-[72px] flex-none flex-col items-center justify-center gap-0.5 border-l border-slate-100 text-xs font-semibold text-[#0f2340] no-underline hover:bg-amber-50 focus-visible:bg-amber-50">
        <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" />
        </svg>
        Check
      </Link>
    </li>
  )
}

/**
 * Project search from every buyer page's header (one search over the register, GET /api/v1/public/register/search). On a phone a
 * magnifier opens a full-screen sheet (a modal dialog: focus kept inside, the chat bubble hidden); from lg up a field-shaped button
 * opens a panel under it, and '/' opens it too. Results go to the project page, each with a 'Check' block for its MahaRERA card.
 * Without JavaScript the trigger is a link to the search on /projects, and Enter in the box submits to /projects?q= either way.
 * `askHref` is the header's Enquire link, offered when nothing matches.
 */
export default function HeaderSearch({ askHref }: { askHref: string }) {
  const [open, setOpen] = useState(false)
  const [modal, setModal] = useState(false)
  const [q, setQ] = useState('')
  const [saved, setSaved] = useState<SavedCheck[]>([])
  const { hits, done } = useRegisterSearch(open ? q : '', SHOWN + 1)
  const wrap = useRef<HTMLDivElement>(null)
  const panel = useRef<HTMLDivElement>(null)
  const input = useRef<HTMLInputElement>(null)
  const trigger = useRef<HTMLAnchorElement>(null)

  const show = () => {
    setModal(window.matchMedia(PHONE).matches)
    setSaved(savedChecks())
    setOpen(true)
  }
  const close = (refocus = true) => {
    setOpen(false)
    if (refocus) trigger.current?.focus()
  }

  useEffect(() => {   // '/' opens it on a laptop, unless the visitor is typing somewhere
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== '/' || open || e.metaKey || e.ctrlKey || e.altKey || window.matchMedia(PHONE).matches) return
      const el = e.target as HTMLElement | null
      if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) return
      e.preventDefault()
      show()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  useEffect(() => {
    if (!open) return
    input.current?.focus()
    const root = document.documentElement
    if (modal) { root.dataset.search = 'open'; document.body.style.overflow = 'hidden' }
    const onDown = (e: MouseEvent) => { if (!modal && wrap.current && !wrap.current.contains(e.target as Node)) close(false) }
    document.addEventListener('mousedown', onDown)
    return () => {
      document.removeEventListener('mousedown', onDown)
      delete root.dataset.search
      document.body.style.overflow = ''
    }
  }, [open, modal])

  const onPanelKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') { e.stopPropagation(); close(); return }
    const links = Array.from(panel.current?.querySelectorAll<HTMLElement>('a[href], button, input') ?? [])
    if (e.key === 'ArrowDown' && e.target === input.current) {
      const first = panel.current?.querySelector<HTMLElement>('[data-testid="header-search-hit"]')
      if (first) { e.preventDefault(); first.focus() }
      return
    }
    if (e.key === 'Tab' && modal && links.length) {   // the phone sheet is modal: Tab goes round inside it
      const [first, last] = [links[0], links[links.length - 1]]
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
    }
  }

  const t = q.trim()
  const picked = () => close(false)
  return (
    <div ref={wrap} className="relative">
      <a ref={trigger} href="/projects#project-search" aria-label="Search projects" aria-expanded={open} data-testid="header-search"
        onClick={(e) => { e.preventDefault(); if (open) close(false); else show() }}
        className="flex min-h-[44px] min-w-[44px] items-center justify-center gap-2 rounded-lg text-white no-underline hover:text-white lg:w-[220px] lg:justify-start lg:bg-white/10 lg:px-3 lg:ring-1 lg:ring-inset lg:ring-white/20 lg:hover:bg-white/15">
        <Glass className="h-5 w-5 flex-none lg:h-4 lg:w-4 lg:text-white/80" />
        <span className="hidden flex-1 text-left text-sm text-white/80 lg:inline">Search projects</span>
        <kbd aria-hidden="true" className="hidden rounded border border-white/30 px-1.5 font-sans text-xs text-white/70 lg:inline">/</kbd>
      </a>
      {open && (
        <div ref={panel} role="dialog" aria-modal={modal || undefined} aria-label="Search projects" onKeyDown={onPanelKey} data-testid="header-search-panel"
          className="fixed inset-0 z-50 flex flex-col bg-white text-slate-900 lg:absolute lg:inset-auto lg:left-0 lg:top-full lg:mt-2 lg:max-h-[70vh] lg:w-[480px] lg:rounded-2xl lg:shadow-2xl lg:ring-1 lg:ring-slate-200">
          <form action="/projects" method="get" role="search" className="flex flex-none items-center gap-2 border-b border-slate-200 p-3">
            <label htmlFor="header-search-q" className="sr-only">Project name, builder or MahaRERA number</label>
            <div className="relative flex-1">
              <Glass className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
              <input ref={input} id="header-search-q" name="q" type="search" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off"
                enterKeyHint="search" placeholder="Project, builder or MahaRERA no."
                className="min-h-[48px] w-full rounded-xl border border-slate-300 pl-10 pr-3 text-base text-slate-900 placeholder:text-slate-500 focus:border-[#0f2340] focus:outline-none focus:ring-2 focus:ring-[#0f2340]/20" />
            </div>
            <button type="button" onClick={() => close()} className="min-h-[48px] rounded-xl px-2 font-semibold text-[#0f2340] lg:hidden">Cancel</button>
          </form>
          <div className="min-h-0 flex-1 overflow-y-auto">
            <p aria-live="polite" className="sr-only">{t.length >= 2 && done ? (hits.length ? `${Math.min(hits.length, SHOWN)} projects found` : 'No project found') : ''}</p>
            {t.length < 2 ? (
              saved.length ? (
                <section aria-labelledby="header-search-saved" className="p-4">
                  <h2 id="header-search-saved" className="text-sm font-semibold uppercase tracking-wide text-slate-600">Checked before</h2>
                  <ul className="mt-2 flex list-none flex-wrap gap-2 p-0">
                    {saved.map((c) => (
                      <li key={c.regno}><Link href={checkHref(c)} onClick={picked}
                        className="inline-flex min-h-[44px] items-center rounded-full bg-slate-100 px-4 font-semibold text-[#0f2340] no-underline ring-1 ring-inset ring-slate-200 hover:bg-slate-200">{c.name}</Link></li>
                    ))}
                  </ul>
                </section>
              ) : <p className="p-4 text-slate-600">Type a project name, the builder, or the MahaRERA number on your agreement.</p>
            ) : !done ? null : hits.length === 0 ? (
              <div className="p-4 text-slate-700">
                <p>We couldn&apos;t find &ldquo;{t}&rdquo; in Pune&apos;s MahaRERA list. Try the builder&apos;s name, or the MahaRERA number on
                  your agreement (it starts with P52 or PR).</p>
                <a href={askHref} onClick={picked} className="mt-3 inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">Can&apos;t find it? Ask us</a>
              </div>
            ) : (
              <ul className="m-0 list-none divide-y divide-slate-100 p-0" data-testid="header-search-results">
                {hits.slice(0, SHOWN).map((it) => <Row key={it.regno} it={it} q={q} onPick={picked} />)}
                {hits.length > SHOWN && (
                  <li><Link href={`/projects?q=${encodeURIComponent(t)}`} onClick={picked}
                    className="flex min-h-[48px] items-center px-4 font-semibold text-[#0f2340] underline underline-offset-2">See all results for &ldquo;{t}&rdquo;</Link></li>
                )}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
