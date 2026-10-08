'use client'

import React, { useMemo, useState } from 'react'
import Link from 'next/link'
import CheckBadge from '@/components/site/CheckBadge'

export interface SearchItem {
  slug: string
  name: string
  regno: string
  promoter?: string | null
  area?: string | null
  completion_now?: string | null
  checked?: number | null
  checks_total?: number
  active?: boolean
}

/** Lowercase, letters and digits only: "P521-0001 2345" and "p52100012345" match the same project. */
const norm = (s: string | null | undefined) => (s || '').toLowerCase().replace(/[^a-z0-9]/g, '')

/** Search every project in our MahaRERA register by name, MahaRERA number or builder. Runs in the browser over the list the page sends. */
export default function ProjectSearch({ items, areaNames }: { items: SearchItem[]; areaNames: Record<string, string> }) {
  const [q, setQ] = useState('')
  const hits = useMemo(() => {
    const n = norm(q)
    if (n.length < 2) return []
    const words = q.toLowerCase().split(/\s+/).map(norm).filter(Boolean)
    const scored: { it: SearchItem; score: number }[] = []
    for (const it of items) {
      const reg = norm(it.regno), name = norm(it.name), hay = name + ' ' + norm(it.promoter) + ' ' + norm(areaNames[it.area || ''])
      let score = 0
      if (reg === n) score = 100
      else if (reg.includes(n)) score = 80
      else if (name.startsWith(n)) score = 60
      else if (name.includes(n)) score = 50
      else if (words.every((w) => hay.includes(w))) score = 30
      if (score) scored.push({ it, score })
    }
    return scored.sort((a, b) => b.score - a.score || a.it.name.localeCompare(b.it.name)).slice(0, 25).map((s) => s.it)
  }, [q, items, areaNames])

  return (
    <section aria-labelledby="search-title" className="mt-8 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <label id="search-title" htmlFor="project-search" className="block text-lg font-semibold text-slate-900">Find a project</label>
      <input
        id="project-search" type="search" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off"
        placeholder="Project name, builder or MahaRERA number (P521…)"
        className="mt-2 min-h-[48px] w-full rounded-xl border border-slate-300 px-4 text-base text-slate-900 placeholder:text-slate-500 focus:border-[#0f2340] focus:outline-none focus:ring-2 focus:ring-[#0f2340]/20"
      />
      {norm(q).length >= 2 && (
        <div aria-live="polite" className="mt-3">
          {hits.length === 0 ? (
            <p className="text-slate-700">No project matches &ldquo;{q}&rdquo; in our {items.length} MahaRERA projects.</p>
          ) : (
            <ul className="list-none divide-y divide-slate-100 p-0" data-testid="project-search-results">
              {hits.map((it) => (
                <li key={it.slug}>
                  <Link href={`/projects/${it.slug}`} className="flex min-h-[48px] flex-wrap items-baseline justify-between gap-x-3 py-2 hover:bg-slate-50">
                    <span className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-[#0f2340] underline-offset-2 hover:underline">{it.name}</span>
                      {it.active === false ? <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600 ring-1 ring-inset ring-slate-300">Finished</span>
                        : <CheckBadge checked={it.checked} total={it.checks_total} />}
                    </span>
                    <span className="text-sm text-slate-600">
                      {[it.promoter, areaNames[it.area || ''], it.regno].filter(Boolean).join(' · ')}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}
