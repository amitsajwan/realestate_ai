import React from 'react'
import Link from 'next/link'
import { getListedSlugs, getSpotlight, type SpotlightProject } from '@/lib/site/hubs'

/** The hot projects banner under the header of every public page (backend areastats/spotlight.py; picked in Studio > Admin).
 *  Server-rendered plain links, so Google reads them as internal links into the hottest project pages (that is how those pages
 *  get crawled first). At most 6 links, inside <aside> with no heading, so it adds no headings or body text to the page.
 *  Rolls with CSS only (app/globals.css): pauses on hover, stops for keyboard focus, stands still (scrolls sideways) for reduced motion.
 *  The second copy of the list only closes the loop: hidden from screen readers and the tab order. Hidden when empty. */
const PX_PER_CHAR = 7.5        // text-sm Poppins, on average
const GAP_PX = 24              // gap-6 between entries
const READ_PX_PER_S = 35       // slow enough to read a moving line on a phone (2026-10-22: 40 s a loop was far too fast)

/** Seconds for one loop: the row's width at a steady reading speed, so a longer strip rolls longer, never faster. */
export function rollSeconds(items: SpotlightProject[]): number {
  const chars = items.reduce((n, p) => n + p.name.length + (p.area?.length ?? 0) + (p.note || `${p.fact} (${p.source})`).length + 4, 0)
  return Math.max(20, Math.round((chars * PX_PER_CHAR + items.length * GAP_PX) / READ_PX_PER_S))
}

export function HotStripView({ items, areaName }: { items: SpotlightProject[]; areaName?: string | null }) {
  if (!items.length) return null
  const label = areaName && items[0].area === areaName ? `Hot in ${areaName}` : 'Hot in Pune'
  const row = (copy: boolean) => (
    <ul className="hot-strip-row flex shrink-0 list-none items-center gap-6 p-0 pr-6" aria-hidden={copy || undefined}>
      {items.map((p) => (
        <li key={p.slug} className="whitespace-nowrap">
          <Link href={`/projects/${p.slug}`} tabIndex={copy ? -1 : undefined} data-testid={copy ? undefined : 'hot-strip-link'}
            className="inline-flex min-h-[40px] items-center gap-1 text-sm text-white no-underline hover:underline focus-visible:underline">
            <span className="font-semibold">{p.name}</span>
            {p.area && p.area !== areaName && <span className="text-white/70">· {p.area}</span>}
            {' '}<span className="text-[#f5c75e]">{p.note || `${p.fact} (${p.source})`}</span>
          </Link>
        </li>
      ))}
    </ul>
  )
  return (
    <aside aria-label={label} data-print="hide" data-testid="hot-strip" className="hot-strip border-b border-[#1d3a63] bg-[#16305a] text-white">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-4">
        <span className="shrink-0 rounded bg-[#f0b440] px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-[#0f2340]">{label}</span>
        <div className="hot-strip-viewport min-w-0 flex-1 overflow-hidden">
          <div className="hot-strip-track flex w-max" style={{ '--hot-roll': `${rollSeconds(items)}s` } as React.CSSProperties}>
            {row(false)}{items.length > 1 && row(true)}
          </div>
        </div>
      </div>
    </aside>
  )
}

/** Fetches the banner for the page's area (slug) and leaves out the page's own project. A project an agent lists is linked at its
 *  shared page, which its register page 301s to (app/projects/[slug]): a link should never go through a redirect.
 *  Never throws: an empty strip is fine. */
export default async function HotStrip({ area, exclude }: { area?: string | null; exclude?: string | null }) {
  const spot = await getSpotlight(area)   // no retries: on an outage it is empty at once and the page does not wait
  if (!spot.length) return null
  const listed = await getListedSlugs()
  const seen = new Set<string>()
  const items = spot.map((p) => ({ ...p, slug: (p.regnos ?? []).map((r) => listed.get(r)).find(Boolean) ?? p.slug }))
    .filter((p) => p.slug !== exclude && !seen.has(p.slug) && seen.add(p.slug))
  const areaName = area ? items.find((p) => p.area_slug === area)?.area ?? null : null
  return <HotStripView items={items} areaName={areaName} />
}
