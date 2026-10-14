import React from 'react'
import Link from 'next/link'
import type { ActiveProject } from '@/lib/site/hubs'

/** "Most active projects in <place>" / "Projects nearby" (docs/plan/rank-loop.md R5): links into project pages named the way people
 *  search for them, each with one fact and its source. Never a score or a "hot" badge. Hidden when the list is empty. */
export default function ActiveProjects({ title, items, className = 'mt-9' }: { title: string; items: ActiveProject[]; className?: string }) {
  if (!items.length) return null
  return (
    <section className={className} aria-labelledby="active-title" data-testid="active-projects">
      <h2 id="active-title" className="text-xl font-semibold text-slate-900">{title}</h2>
      <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
        {items.map((p) => (
          <li key={p.slug}>
            <Link href={`/projects/${p.slug}`} className="block h-full min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
              <span className="block font-semibold text-[#0f2340]">{p.name}{p.km != null ? <span className="font-normal text-slate-600"> · {p.km} km</span> : null}</span>
              <span className="block text-sm text-slate-600">{p.fact} ({p.source})</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
