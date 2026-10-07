import React from 'react'
import Link from 'next/link'
import { agentPath } from '@/lib/site/slug'
import { bhkRange, formatDay, priceRange } from '@/lib/site/projects'
import type { PublicProject } from '@/lib/site/types'

/** A builder project on the agent's site. No photo: we show only images we have the right to use, so the card is typographic.
 *  `href` overrides the link (Avasetu's shared /projects pages link to themselves, not to one agent's site). */
export default function ProjectCard({ agentSlug, p, href }: { agentSlug?: string; p: PublicProject; href?: string }) {
  const done = formatDay(p.rera?.completion_now)
  return (
    <Link href={href ?? agentPath(agentSlug ?? '', 'projects/' + p.slug)} data-testid="project-card"
      className="flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white text-slate-900 no-underline shadow-sm transition hover:border-[var(--site-primary)] hover:shadow-md">
      <div className="bg-[var(--site-primary)] px-4 pb-4 pt-3 text-[var(--site-on-primary)]">
        <p className="text-xs font-bold uppercase tracking-wide text-[var(--site-accent)]">{p.locality}</p>
        <h3 className="mt-1 text-lg font-bold leading-snug">{p.name}</h3>
        <p className="text-sm opacity-90">by {p.builder}</p>
      </div>
      <div className="flex flex-1 flex-col gap-2 px-4 py-3">
        <p className="text-xl font-extrabold text-[var(--site-primary)]">{priceRange(p)}</p>
        <p className="text-sm text-slate-700">{bhkRange(p.bhk_options)}</p>
        {p.positioning && <p className="text-sm text-slate-600">{p.positioning}</p>}
        <dl className="mt-auto grid grid-cols-2 gap-2 border-t border-slate-100 pt-3 text-sm">
          <div>
            <dt className="text-xs text-slate-500">MahaRERA date</dt>
            <dd className="font-semibold">{done || 'Being checked'}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Homes booked</dt>
            <dd className="font-semibold">{p.booked_pct != null ? p.booked_pct + '%' : '—'}</dd>
          </div>
        </dl>
      </div>
    </Link>
  )
}
