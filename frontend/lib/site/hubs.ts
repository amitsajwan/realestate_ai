/**
 * Pages that link project pages together (docs/plan/rank-loop.md R5, R6; backend areastats/hubs.py):
 * GET /api/v1/public/register/active?area=|place=   "Most active projects": one fact line each, never a score
 * GET /api/v1/public/register/near/{area}/{slug}    project pages near a neighbourhood guide
 * GET /api/v1/public/builders and /builders/{slug}  one page per builder from MahaRERA records
 * GET /api/v1/public/register/spotlight?area=      the hot projects banner on every public page (owner's picks, then hot ones)
 * GET /api/v1/public/register/map?area=            an area's most active projects on its street map (areastats/areamap.py)
 * Lists come back empty on any failure; a builder page is null on a 404 and throws on an outage (never a cached 404).
 */
import { serverApiBase } from './api'

export interface ActiveProject { slug: string; name: string; fact: string; source: string; km?: number }

/** One project on an area's map. x, y: where its checked position falls on the drawn map (0..1 of its width and height);
 *  stage is by dates (backend pages.stage); booked/total add up every phase sold under the name. */
export interface AreaMapItem {
  n: number; slug: string; name: string; builder: string | null; regnos: string[]
  lat: number; lon: number; x: number; y: number
  stage: 'new' | 'early' | 'mid' | 'advanced' | 'passed' | null; stage_label: string
  booked: number | null; total: number | null; completion: string | null; price_from: number | null
  photo: { url: string; alt: string; source: string } | null
}

export interface AreaMapData {
  area: string; area_slug: string; name: string; map: string; box: number[]; attribution: string
  items: AreaMapItem[]; left_out: number
}

export interface BuilderCard {
  slug: string; name: string; projects: number; indexable: boolean; page_updated: string | null
  /** a brand over several MahaRERA companies (backend areastats/brands.py) */
  brand?: boolean
  with_dates?: number; moved_later?: number; avg_months_later?: number | null; record_ok?: boolean
}

export interface BuilderProject {
  slug: string
  name: string
  legal_name: string
  regno: string
  area: string | null
  completion_now: string | null
  months_later: number | null
  units_total: number | null
  units_booked: number | null
  active: boolean
  fact: string
  source: string
}

export interface BuilderPage {
  slug: string
  name: string
  projects_count: number
  areas: string[]
  active: number
  units_total: number | null
  units_booked: number | null
  with_dates: number
  moved_later: number
  avg_months_later: number | null
  /** 5+ projects with both dates: the record is stated */
  record_ok: boolean
  /** months later that count as moved (net of MahaRERA's blanket extensions) */
  moved_min: number
  brand: boolean
  /** the MahaRERA promoters counted, most projects first */
  companies: { name: string; projects: number }[]
  indexable: boolean
  page_updated: string | null
  source: string
  projects: BuilderProject[]
}

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,15}$/

async function get<T>(path: string): Promise<{ ok: true; data: T } | { ok: false; notFound: boolean }> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    const res = await fetch(serverApiBase() + path, { headers: { Accept: 'application/json' }, next: { revalidate: 300 }, signal: ctrl.signal })
    if (res.status === 404) return { ok: false, notFound: true }
    if (!res.ok) return { ok: false, notFound: false }
    return { ok: true, data: (await res.json()) as T }
  } catch {
    return { ok: false, notFound: false }
  } finally {
    clearTimeout(timer)
  }
}

/** An area's map, or null when it has none (only areas with a drawn street map and checked pins) or on any failure. */
export async function getAreaMap(area: string): Promise<AreaMapData | null> {
  if (!SLUG.test(area.replace(/_/g, '-'))) return null
  const r = await get<AreaMapData>('/api/v1/public/register/map?area=' + encodeURIComponent(area))
  return r.ok && Array.isArray(r.data?.items) ? r.data : null
}

export async function getActive(where: { area?: string; place?: string }, limit = 8): Promise<ActiveProject[]> {
  const q = where.area ? 'area=' + encodeURIComponent(where.area) : where.place ? 'place=' + encodeURIComponent(where.place) : ''
  if (!q) return []
  const r = await get<ActiveProject[]>(`/api/v1/public/register/active?${q}&limit=${limit}`)
  return r.ok && Array.isArray(r.data) ? r.data : []
}

/** One entry of the hot projects banner (backend areastats/spotlight.py): the owner's note, else one sourced fact; never a score. */
export interface SpotlightProject {
  slug: string; name: string; area: string | null; area_slug: string | null; note: string | null; fact: string; source: string; picked: boolean
  /** the registrations the page stands for (its towers too) */
  regnos?: string[]
}

/** The banner for a page; on an area's pages (area slug) that area's projects come first. Empty on any failure: never breaks a page. */
export async function getSpotlight(area?: string | null): Promise<SpotlightProject[]> {
  const q = area && SLUG.test(area) ? '?area=' + area : ''
  const r = await get<SpotlightProject[]>('/api/v1/public/register/spotlight' + q)
  return r.ok && Array.isArray(r.data) ? r.data : []
}

/** Registration number -> shared page slug of every project an agent lists (the register page 301s there). Kept 5 minutes like
 *  the banner itself: lib/site/api's getCatalog keeps 30 s, and a page renders as often as its shortest-lived read. */
export async function getListedSlugs(): Promise<Map<string, string>> {
  return new Map([...(await getListed())].map(([regno, c]) => [regno, c.slug]))
}

/** The same, with the listing's lowest price: an area map's card quotes the agent's own "from" price for a listed project, as its
 *  page and the banner do (the register's lowest asked price can differ: Camelot ₹2.77 Cr vs the listing's ₹2.24 Cr). */
export interface ListedProject { slug: string; price_min: number | null }
export async function getListed(): Promise<Map<string, ListedProject>> {
  const r = await get<{ items: { slug: string; rera_no?: string | null; agents?: unknown[]; price_min?: number | null }[] }>('/api/v1/public/projects')
  const items = r.ok && Array.isArray(r.data?.items) ? r.data.items : []
  return new Map(items.filter((c) => c.agents?.length && c.rera_no)
    .map((c) => [c.rera_no as string, { slug: c.slug, price_min: typeof c.price_min === 'number' && c.price_min > 0 ? c.price_min : null }]))
}

export async function getNearGuide(areaSlug: string, slug: string): Promise<ActiveProject[]> {
  if (!SLUG.test(areaSlug) || !SLUG.test(slug)) return []
  const r = await get<ActiveProject[]>(`/api/v1/public/register/near/${areaSlug}/${slug}`)
  return r.ok && Array.isArray(r.data) ? r.data : []
}

export async function getBuilders(): Promise<BuilderCard[]> {
  const r = await get<BuilderCard[]>('/api/v1/public/builders')
  return r.ok && Array.isArray(r.data) ? r.data : []
}

/** A builder page; { redirect } when the address is a company whose projects are all counted under a brand now. */
export async function getBuilder(slug: string): Promise<BuilderPage | { redirect: string } | null> {
  if (!SLUG.test(slug)) return null
  const r = await get<BuilderPage | { redirect: string }>('/api/v1/public/builders/' + encodeURIComponent(slug))
  if (r.ok) return r.data
  if (r.notFound) return null
  throw new Error('Builder data is temporarily unavailable')
}

/** An upcoming project MahaRERA has not registered yet (backend areastats/upcoming.py): no prices; facts carry their source. */
export interface UpcomingProject {
  slug: string; name: string; builder: string; area: string; area_name: string; area_slug: string; address: string
  summary: string; note: string; registered: false; updated_at: string | null
  facts: { label: string; value: string; source: string; to_confirm: boolean }[]
  homes: { bhk: number; carpet_sqft: string; source: string; to_confirm: boolean }[]
  highlights: string[]; amenities: string[]
  nearby: { name: string; km: number | null; source: string }[]
  pictures: { url: string; caption: string; illustrative: boolean }[]
  sources: { name: string; url: string; read_on: string }[]
}

/** null when there is no such live upcoming project; throws on any other failure so the page shows its error, not a 404. */
export async function getUpcoming(slug: string): Promise<UpcomingProject | null> {
  if (!SLUG.test(slug)) return null
  const r = await get<UpcomingProject>('/api/v1/public/register/upcoming/' + slug)
  if (r.ok) return r.data
  if (r.notFound) return null
  throw new Error('upcoming project ' + slug + ' could not be read')
}
