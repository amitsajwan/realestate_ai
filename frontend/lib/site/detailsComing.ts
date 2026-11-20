import { LOCALITIES } from '@/lib/marketing/localities'
import type { RegisterListItem, RegisterProject } from './register'

/** Projects in our areas whose pages are not in search yet (thin: MahaRERA's record and little of their own, or waiting their turn,
 *  areastats/entry.py). The lists show only pages in search, so before this a buyer never found them (owner 2026-11-19: "instead of
 *  not showing thin projects ... a common page: our team is working on these new projects, this is what we have now"). They are
 *  shown on one page, /projects/details-coming, instead of hidden; that page stays out of search like each of their own pages. */

export const DETAILS_COMING_PATH = '/projects/details-coming'

export interface DetailsComingGroup { area: string; key: string; items: RegisterListItem[] }

/** Our areas' projects still being built whose page is not in search, by area in the site's area order, newest record first. An
 *  agent's live offer makes a page listed already (`offered`), and a sold-out project has nothing left to book. */
export function detailsComing(all: RegisterListItem[], offered: Set<string> = new Set()): DetailsComingGroup[] {
  const waiting = all.filter((r) => r.area && !r.indexable && r.active !== false && !r.sold_out && !offered.has(r.regno.toUpperCase()))
  return LOCALITIES.map((l) => ({
    area: l.name, key: l.key,
    items: waiting.filter((r) => r.area === l.key).sort((a, b) => (b.listed_or_updated ?? '').localeCompare(a.listed_or_updated ?? '')),
  })).filter((g) => g.items.length > 0)
}

/** What a project page does not hold yet, in the words its note says ("prices", "the builder's pictures", "floor plans"). Empty
 *  when it holds all three: such a page is only waiting its turn for search, and has nothing to apologise for. */
export function missingDetails(p: Pick<RegisterProject, 'prices' | 'profile'>): string[] {
  const own = (pics: { source?: string | null }[] | undefined) => (pics ?? []).some((x) => (x.source ?? 'builder') === 'builder' || x.source === 'brochure')
  return [
    (p.prices?.rows ?? []).length ? null : 'prices',
    own(p.profile?.photos) ? null : "the builder's pictures",
    (p.profile?.plans ?? []).length ? null : 'floor plans',
  ].filter((x): x is string => !!x)
}

/** "prices, the builder's pictures and floor plans" */
export function sayList(xs: string[]): string {
  return xs.length < 2 ? (xs[0] ?? '') : `${xs.slice(0, -1).join(', ')} and ${xs[xs.length - 1]}`
}

export interface ElsewhereComing { key: string; name: string; count: number }

/** The same projects outside our areas (about 4,400 on 2026-11-19, far too many for one page), counted per Pune place, most first:
 *  each place's own page (/projects/area/<place>) already lists every project still being built there, these included. */
export function elsewhereComing(all: RegisterListItem[]): ElsewhereComing[] {
  const by = new Map<string, ElsewhereComing>()
  for (const r of all) {
    if (r.area || !r.place || r.indexable || r.active === false || r.sold_out) continue
    const got = by.get(r.place) ?? { key: r.place, name: r.place_name || r.place, count: 0 }
    got.count += 1
    by.set(r.place, got)
  }
  return [...by.values()].sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
}
