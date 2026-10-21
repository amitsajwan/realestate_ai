/**
 * Area list pages that grow from searches (docs/plan/area-intent-pages.md; backend app/modules/seo/facets.py and grow.py):
 * GET /api/v1/public/facets                     live pages (sitemap, chips on place and project pages)
 * GET /api/v1/public/facets/{place}/{rest}      one page, or { redirect_to } for its one URL
 * A list comes back empty on any failure; a page is null on a 404 and throws on an outage (never a cached 404).
 */
import { serverApiBase } from './api'
import { badStatus, failed, withRetry, type Got } from './retry'

export type Intent = 'new-launches' | 'top' | 'ready-to-move' | 'all'

export interface FacetLink {
  key: string
  path: string
  place: string
  place_slug: string
  intent: Intent
  possession: number | null
  builder: string | null
  bhk?: number | null
  label: string
  count: number
  indexable: boolean
  page_updated: string | null
}

export interface FacetRow {
  rank: number
  slug: string
  name: string
  legal_name: string
  regno: string
  promoter: string | null
  builder_slug: string | null
  registered_on: string | null
  completion_now: string | null
  completion_at_registration: string | null
  units_total: number | null
  units_booked: number | null
  reason: string
  source: string
  price_from?: number | null
  price_to?: number | null
  price_source?: string | null
}

export interface FacetChange { at: string; text: string; slug: string; source: string }

export interface FacetPage {
  key: string
  path: string
  place: { key: string; slug: string; name: string }
  intent: Intent
  possession: number | null
  builder: string | null
  builder_name: string | null
  bhk?: number | null
  title: string
  h1: string
  answer: string
  rows: FacetRow[]
  count: number
  changes: FacetChange[]
  month: string | null
  page_updated: string | null
  indexable: boolean
  as_of: string
  source: string
}

const SEG = /^[a-z0-9]+(?:-[a-z0-9]+){0,15}$/

/** Retried as getJson in ./api (./retry). */
function get<T>(path: string): Promise<Got<T>> {
  return withRetry(() => getOnce<T>(path))
}

async function getOnce<T>(path: string): Promise<Got<T>> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 8000)
  try {
    const res = await fetch(serverApiBase() + path, { headers: { Accept: 'application/json' }, next: { revalidate: 300 }, signal: ctrl.signal })
    if (res.status === 404) return { ok: false, notFound: true }
    if (!res.ok) return badStatus(res.status)
    return { ok: true, data: (await res.json()) as T }
  } catch (e) {
    return failed(e)
  } finally {
    clearTimeout(timer)
  }
}

export interface SizePrice { bhk: number; projects: number; low: number; high: number; cheapest: { name: string; slug: string }; path: string }
export interface PlacePrices { place: string; as_of: string; sizes: SizePrice[] }

/** Flat prices by home size for a place page (published prices only); null on any failure: the page shows no prices then. */
export async function getPlacePrices(placeSlug: string): Promise<PlacePrices | null> {
  if (!SEG.test(placeSlug)) return null
  const r = await get<PlacePrices>(`/api/v1/public/place-prices/${placeSlug}`)
  return r.ok && r.data && Array.isArray(r.data.sizes) ? r.data : null
}

export async function getFacets(): Promise<FacetLink[]> {
  const r = await get<FacetLink[]>('/api/v1/public/facets')
  return r.ok && Array.isArray(r.data) ? r.data : []
}

export async function getFacet(place: string, segments: string[]): Promise<FacetPage | { redirect_to: string } | null> {
  if (!SEG.test(place) || !segments.length || segments.length > 4 || !segments.every((s) => SEG.test(s))) return null
  const r = await get<FacetPage | { redirect_to: string }>(`/api/v1/public/facets/${place}/${segments.join('/')}`)
  if (r.ok) return r.data
  if (r.notFound) return null
  throw new Error('This list is temporarily unavailable')
}

/** The other lists of the same place, for chips: the intents first, then possession years, then builders. */
export function siblings(all: FacetLink[], placeKey: string, except?: string): FacetLink[] {
  return all.filter((f) => f.place === placeKey && f.indexable && f.path !== except)
}

/** Questions and answers written by code from the page's own numbers; nothing a number on the page does not say. */
export function facetFaq(p: FacetPage): { q: string; a: string }[] {
  const out: { q: string; a: string }[] = []
  const place = p.place.name
  const names = p.rows.slice(0, 5).map((r) => r.name).join(', ')
  if (p.bhk) {
    out.push({ q: `Which new projects in ${place}, Pune have ${p.bhk} BHK flats?`, a: `${p.answer} Cheapest first: ${names}.` })
    out.push({ q: `What is the price of a ${p.bhk} BHK flat in ${place}?`,
      a: `On this list, from the price the builder's own site states or two property sites agree on, read in the last 45 days. ` +
         'Ask the builder for the full cost sheet: parking, stamp duty, registration and GST are usually extra.' })
  } else if (p.intent === 'new-launches') {
    out.push({ q: `Which are the new launch projects in ${place}, Pune?`, a: `${p.answer} The newest: ${names}.` })
    out.push({ q: `Are pre-launch offers in ${place} allowed?`,
      a: 'Under RERA a builder may not advertise, market, book or sell homes in a project before it is registered with MahaRERA. ' +
         'Every project on this list is registered; check the MahaRERA number on its page before you pay anything.' })
  } else if (p.intent === 'top') {
    out.push({ q: `Which are the top projects in ${place}, Pune?`, a: `${p.answer} In order: ${names}.` })
    out.push({ q: 'How is this list ranked?',
      a: 'By homes booked in the last 90 days as MahaRERA shows them, then by the share of homes booked. No builder pays to be on it or to move up.' })
  } else if (p.intent === 'ready-to-move') {
    out.push({ q: `Which projects in ${place}, Pune are ready to move?`, a: `${p.answer} The newest: ${names}.` })
    out.push({ q: 'Does a passed completion date mean I can move in?',
      a: 'Not on its own. The completion date is what the builder filed with MahaRERA. The occupancy certificate (OC) from the local authority is what says the building can be lived in: ask for it.' })
  } else {
    out.push({ q: `Which projects in ${place}, Pune${p.possession ? ` have possession in ${p.possession}` : ''}?`, a: `${p.answer} ${names}.` })
  }
  out.push({ q: 'Where do these numbers come from?',
    a: `MahaRERA's public records, read by Avasetu; this list was worked out on ${p.as_of}. Each project's page shows the date we read its record.` })
  return out
}

const CHIP_LABEL: Record<Intent, string> = { 'new-launches': 'New launches', top: 'Top projects', 'ready-to-move': 'Ready to move', all: 'All projects' }

/** The live size page (/projects/area/<place>/2-bhk) for an area, when it has enough projects to be in search. */
export function sizePage(all: FacetLink[], placeSlug: string, bhk: number): FacetLink | null {
  return all.find((f) => f.place_slug === placeSlug && f.bhk === bhk && f.intent === 'all' && !f.possession && !f.builder && f.indexable) ?? null
}

/** The agents' listing pages (filters.livePages) less the size pages that now answer at /projects/area/<place>/<n>-bhk: an old
 *  /2-bhk/<area> URL redirects there once that page is in search, so one page answers "2 bhk flats in <area>". */
export function withoutMovedSizePages<T extends { path: string }>(pages: T[], all: FacetLink[]): T[] {
  return pages.filter((p) => {
    const m = /^\/(\d)-bhk\/([a-z0-9-]+)$/.exec(p.path)
    return !m || !sizePage(all, m[2], Number(m[1]))
  })
}

/** Chips for a place: its live lists, the 2 BHK and budget pages that have enough projects (from agents' listings), all
 *  projects, and the area guide for the areas we cover. `filterPages` is filters.livePages(catalog). */
export function placeChips(
  place: { key: string; slug: string },
  all: FacetLink[],
  filterPages: { path: string; title: string; area: { slug: string }; count: number }[] = [],
  guide?: string | null,
): { path: string; label: string; count?: number | null }[] {
  const mine = siblings(all, place.key)
  const label = (f: FacetLink) => (f.builder ? `${f.label} by ${f.builder.split('-').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}` : f.intent !== 'all' && !f.possession && !f.bhk ? CHIP_LABEL[f.intent] : f.label)
  return [
    ...mine.map((f) => ({ path: f.path, label: label(f), count: f.count })),
    ...withoutMovedSizePages(filterPages, all).filter((p) => p.area.slug === place.slug).map((p) => ({ path: p.path, label: p.title.replace(/ in .*$/, ''), count: p.count })),
    { path: `/projects/area/${place.slug}`, label: 'All projects' },
    ...(guide ? [{ path: guide, label: 'Area guide' }] : []),
  ]
}
