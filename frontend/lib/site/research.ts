/**
 * Neighbourhood research (backend app/modules/neighbourhood, docs/plan/pune-intelligence.md): what is around a place and a
 * project, measured from data and refreshed by itself. Every block carries its sources and the day it was measured; a block
 * the backend has too little for is simply absent, so a page shows only what it has.
 * GET /api/v1/public/research/places/{place}    a place's research (place page, /schools, /commute, /rent)
 * GET /api/v1/public/research/projects/{slug}   "Around this project" on a project page
 * GET /api/v1/public/research/hubs              the work hubs with pages
 * GET /api/v1/public/research/hubs/{slug}       one work hub page (/work-hubs/<slug>)
 * GET /api/v1/public/research/pages             every place sub-page worth indexing, for the sitemap (one read, not one per place)
 * These types are the contract with backend/app/modules/neighbourhood/views.py and each researcher's `present`: change both.
 * A page read is { ok: true, data: null } on a 404 (no research yet) and { ok: false } on an outage, which is never kept in the
 * cache; a list read comes back empty on any failure.
 */
import { dontCacheThisRender } from './noCacheOnError'
import { serverApiBase } from './api'

export interface Source {
  name: string
  url?: string
  read_on: string // YYYY-MM-DD
}

/** Every block has these on top of its own fields. */
interface BlockBase {
  sources: Source[]
  updated: string // YYYY-MM-DD, when this block was measured
  page_ready?: boolean // enough here for a page of its own (/schools, /commute, /rent) to be indexed
}

/** Drive times from the place (or the project's pin) to a work hub, with typical traffic, in minutes. */
export interface CommuteRow {
  hub: string
  hub_slug?: string // when the hub has a page (/work-hubs/<slug>)
  km: number // road distance
  am: [number, number] // weekday 9 am, low-high minutes
  pm: [number, number] // weekday 6 pm, back
  pin_km?: number // on a project page with a pin: straight-line km from the project's own pin to this hub
}
export interface CommuteBlock extends BlockBase {
  rows: CommuteRow[]
  measured_from?: 'place' | 'pin' // drive times are measured from the place centre ("place"), never scaled to a pin
  place_name?: string
  from?: string // "the Kharadi centre"
}

export type Board = 'CBSE' | 'ICSE' | 'ISC' | 'State' | 'IB' | 'IGCSE'
export interface School {
  name: string
  board: Board
  affiliation?: string // the board's affiliation number
  level?: string // "Up to Class 10", "Up to Class 12"
  km: number // straight line from the place centre or the project's pin
  address?: string
  website?: string
}
export interface SchoolsBlock extends BlockBase {
  schools: School[]
  total_within_km: { km: number; count: number; by_board: Partial<Record<Board, number>> }
  all?: School[] // the /schools page's list: up to 40 within 5 km, nearest first
}

/** Asked rent from listings (never what was paid), by flat size, for one month. */
export interface RentRow {
  bhk: string // "1 BHK", "2 BHK", "3 BHK"
  low: number // rupees a month, 25th percentile
  median: number
  high: number // 75th percentile
  listings: number
  yield_pct?: number // a year's median rent over the median asking price for that size, when both are known
}
export interface RentBlock extends BlockBase {
  month: string // YYYY-MM
  rows: RentRow[]
  within_km?: number // on a project page: listings this close to the project
  listings_within_km?: number // how many listings with a position are within within_km of the project (10 or more)
}

/** Who lives and works around here, from facts we hold (never religion, caste or community). */
export interface ProfileBlock extends BlockBase {
  home_mix: Array<{ label: string; share: number }> // share of homes being built by size, 0-1
  finished_by_year: Array<{ year: number; homes: number }> // homes MahaRERA shows finished each year
  nearby: Array<{
    kind: 'it_park' | 'office' | 'college' | 'hospital' | 'government' | 'defence' | 'industrial' | 'market' | 'transport'
    name: string
    km: number
  }>
  lines: string[] // plain sentences built from the numbers above, e.g. "Most homes being built here are 2 BHK."
  measured_from?: 'place' | 'pin' // nearby km from the place centre or the project's pin
}

export interface BeingBuiltBlock extends BlockBase {
  within_km: number
  projects: number
  homes: number
  due_from: number // year
  due_to: number
  biggest: Array<{ slug: string; name: string; homes: number; due: string }> // due "YYYY-MM"
  measured_from?: 'place' | 'pin' // "place": filed under the place plus pinned ones within_km of its centre; "pin": pinned ones within_km of the project
  note?: string // says which of the two, in words
}

export interface JobsBlock extends BlockBase {
  hubs: Array<{ hub: string; hub_slug?: string; km: number; companies: string[]; companies_count?: number }>
}

/** A tracker (/news/track/<slug>) that touches the place: roads, metro, rules being built or changing. */
export interface ChangeLine {
  slug: string
  name: string
  status: string
  date: string // YYYY-MM-DD of the status
  stage?: string
}

export interface ResearchBlocks {
  commute?: CommuteBlock
  schools?: SchoolsBlock
  rent?: RentBlock
  profile?: ProfileBlock
  being_built?: BeingBuiltBlock
  jobs?: JobsBlock
}

export interface PlaceResearch {
  place: string
  place_name?: string
  blocks: ResearchBlocks
  changes: ChangeLine[]
  pages: { schools: boolean; commute: boolean; rent: boolean } // which sub-pages are worth indexing
}

export interface ProjectResearch {
  slug: string
  place: string
  place_name?: string
  pinned: boolean // measured from the project's own Google pin, else from the place centre
  blocks: ResearchBlocks
  changes: ChangeLine[]
}

export interface HubCard {
  slug: string
  name: string
  place: string
  kind: 'it_park' | 'business_district' | 'airport' | 'station' | 'industrial'
  ready?: boolean // its page is worth indexing: 3+ companies from its own list, or drive times from 3+ places; absent = ready
  updated?: string // YYYY-MM-DD of its last research (its sitemap date), "" before the first
}

export interface HubPage extends HubCard {
  summary: string
  companies: string[]
  companies_source?: Source
  commute_from: Array<{ place: string; name: string; am: [number, number]; pm: [number, number] }>
  homes_nearby: Array<{ slug: string; name: string; km: number; price_from?: number; possession?: string }>
  rent_nearby?: RentRow[]
  changes: ChangeLine[]
  sources: Source[]
  updated: string
  page_ready?: boolean // the same rule as HubCard.ready
}

/** GET /api/v1/public/research/pages: the place sub-pages worth indexing, for the sitemap. */
export interface ResearchPages {
  pages: Array<{ place: string; kind: 'schools' | 'commute' | 'rent'; updated: string }>
}

export type ResearchKind = 'schools' | 'commute' | 'rent'
export const RESEARCH_KINDS: ResearchKind[] = ['schools', 'commute', 'rent']

/** GET /public/research/pages -> { pages: ResearchPageRow[] }: one row per place sub-page whose `pages.<kind>` is true. */
export interface ResearchPageRow {
  place: string // place slug
  kind: ResearchKind
  updated?: string // YYYY-MM-DD the block was measured
}

// ---- reads ----

export type ResearchRead<T> = { ok: true; data: T | null } | { ok: false }

const SLUG = /^[a-z0-9-]{1,80}$/
const REVALIDATE = 3600   // research changes at most daily; an hour keeps a page in step without a read per visit

async function getJson(path: string): Promise<{ status: number; body: unknown } | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(`${serverApiBase()}/api/v1/public/research${path}`, {
      headers: { Accept: 'application/json' }, next: { revalidate: REVALIDATE }, signal: ctrl.signal,
    } as RequestInit)
    return { status: res.status, body: res.ok ? await res.json() : null }
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

/** `extra`: the read is one section of a page that stands without it (a project page's "Around", a place page's strip), so an
 *  outage leaves the section out and the page is still kept; a page made of the research is not kept on an outage. */
async function readOne<T>(path: string, extra: boolean): Promise<ResearchRead<T>> {
  const res = await getJson(path)
  if (res?.status === 404) return { ok: true, data: null }
  if (!res || res.status >= 400 || !res.body || typeof res.body !== 'object') {
    if (!extra) await dontCacheThisRender()
    return { ok: false }
  }
  return { ok: true, data: res.body as T }
}

export async function getPlaceResearch(place: string, extra = false): Promise<ResearchRead<PlaceResearch>> {
  if (!SLUG.test(place)) return { ok: true, data: null }
  const got = await readOne<PlaceResearch>(`/places/${place}`, extra)
  if (!got.ok || !got.data) return got
  const d = got.data
  const pages = d.pages ?? {}
  return { ok: true, data: { ...d, blocks: d.blocks ?? {}, changes: d.changes ?? [],
    pages: { schools: pages.schools === true, commute: pages.commute === true, rent: pages.rent === true } } }
}

/** Always an extra: a project page is never held back by its research. */
export async function getProjectResearch(slug: string): Promise<ResearchRead<ProjectResearch>> {
  if (!SLUG.test(slug)) return { ok: true, data: null }
  const got = await readOne<ProjectResearch>(`/projects/${slug}`, true)
  if (!got.ok || !got.data) return got
  return { ok: true, data: { ...got.data, blocks: got.data.blocks ?? {}, changes: got.data.changes ?? [] } }
}

export async function getHub(slug: string): Promise<ResearchRead<HubPage>> {
  if (!SLUG.test(slug)) return { ok: true, data: null }
  const got = await readOne<HubPage>(`/hubs/${slug}`, false)
  if (!got.ok || !got.data) return got
  const h = got.data
  return { ok: true, data: { ...h, companies: h.companies ?? [], commute_from: h.commute_from ?? [], homes_nearby: h.homes_nearby ?? [],
    changes: h.changes ?? [], sources: h.sources ?? [] } }
}

/** The work hubs with pages: the backend answers { hubs: [...] }; a hub marked not ready is left out. */
export async function getHubs(): Promise<HubCard[]> {
  const res = await getJson('/hubs')
  const body = res && res.status < 400 ? res.body : null
  const list = Array.isArray(body) ? body : (body as { hubs?: unknown } | null)?.hubs
  return Array.isArray(list) ? (list as HubCard[]).filter((h) => h && SLUG.test(h.slug) && h.ready !== false) : []
}

/** The place sub-pages worth indexing (GET /public/research/pages); empty until the backend has that route. */
export async function getResearchPages(): Promise<ResearchPageRow[]> {
  const res = await getJson('/pages')
  const body = res && res.status < 400 ? res.body : null
  const list = Array.isArray(body) ? body : (body as { pages?: unknown } | null)?.pages
  return Array.isArray(list)
    ? (list as ResearchPageRow[]).filter((r) => r && SLUG.test(r.place) && RESEARCH_KINDS.includes(r.kind))
    : []
}

export const researchPath = (place: string, kind: ResearchKind) => `/projects/area/${place}/${kind}`
export const hubPath = (slug: string) => `/work-hubs/${slug}`
export const HUBS_PATH = '/work-hubs'
