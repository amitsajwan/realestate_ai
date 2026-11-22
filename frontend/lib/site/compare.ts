/**
 * Two neighbouring areas side by side ("Kharadi vs Wagholi"): GET /api/v1/public/areas/compare/<pair> and the list of pairs,
 * GET /api/v1/public/areas/compare (backend areastats/compare.py). Only areas near each other are paired, each pair has one
 * address, and every figure is one the areas' own guides show. Like the other public reads, anything unexpected gives null and
 * the page or the links leave themselves out: never an error.
 */
import { fixturesForced, serverApiBase } from '@/lib/site/api'

export interface PairArea { key: string; name: string; slug: string }
export interface AreaPair { slug: string; a: PairArea; b: PairArea; apart_km: number }

export interface CompareSide {
  area: PairArea
  as_of: string
  projects: number
  units_total: number | null
  units_booked: number | null
  registered_this_year: number
  registered_last_year: number
  completing_this_year: number
  completing_next_year: number
  metro: { name: string; line_short: string; km: number } | null
  /** home projects still being built with both filed dates, and how many the builder moved 3+ months later */
  dates: { with_dates: number; moved: number; median_months: number | null } | null
}

export interface DistanceRow { key: string; name: string; kind: string; kind_label: string; a_km: number; b_km: number; maps: string; source: string }

export interface AreaCompare {
  slug: string
  as_of: string
  apart_km: number
  sides: [CompareSide, CompareSide]
  distances: DistanceRow[]
  related: AreaPair[]
  note: string
  attribution: string
  source: string
}

export const PAIR_SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*-vs-[a-z0-9]+(?:-[a-z0-9]+)*$/
const DAY = /^\d{4}-\d{2}-\d{2}$/
const MAPS = /^https:\/\/www\.google\.com\/maps\/search\/\?api=1&query=-?\d+(\.\d+)?,-?\d+(\.\d+)?$/
const count = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v) && v >= 0
const km = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v) && v > 0
const text = (v: unknown): v is string => typeof v === 'string' && v.trim() !== ''

function area(v: unknown): PairArea | null {
  const x = v as Record<string, unknown> | null
  return x && text(x.key) && text(x.name) && text(x.slug) && /^[a-z0-9-]+$/.test(x.slug) ? { key: x.key, name: x.name, slug: x.slug } : null
}

function pair(v: unknown): AreaPair | null {
  const x = v as Record<string, unknown> | null
  const a = area(x?.a), b = area(x?.b)
  if (!x || !a || !b || !text(x.slug) || x.slug !== `${a.slug}-vs-${b.slug}` || !km(x.apart_km)) return null
  return { slug: x.slug, a, b, apart_km: x.apart_km }
}

export function cleanPairs(raw: unknown): AreaPair[] {
  return (Array.isArray(raw) ? raw : []).map(pair).filter((p): p is AreaPair => p !== null)
}

function side(v: unknown): CompareSide | null {
  const x = v as Record<string, unknown> | null
  const a = area(x?.area)
  if (!x || !a || !text(x.as_of) || !DAY.test(x.as_of) || !count(x.projects)) return null
  const total = count(x.units_total) && x.units_total > 0 ? x.units_total : null
  const booked = total !== null && count(x.units_booked) && x.units_booked <= total ? x.units_booked : null
  const m = x.metro as Record<string, unknown> | null
  const d = x.dates as Record<string, unknown> | null
  const n = (k: string) => (count(x[k]) ? (x[k] as number) : 0)
  return {
    area: a, as_of: x.as_of, projects: x.projects,
    units_total: booked === null ? null : total, units_booked: booked,
    registered_this_year: n('registered_this_year'), registered_last_year: n('registered_last_year'),
    completing_this_year: n('completing_this_year'), completing_next_year: n('completing_next_year'),
    metro: m && text(m.name) && text(m.line_short) && km(m.km) ? { name: m.name, line_short: m.line_short, km: m.km } : null,
    dates: d && count(d.with_dates) && d.with_dates > 0 && count(d.moved) && d.moved <= d.with_dates
      ? { with_dates: d.with_dates, moved: d.moved, median_months: count(d.median_months) && d.median_months > 0 ? d.median_months : null }
      : null,
  }
}

/** Keeps only what the page can show truthfully; null when the answer is not the pair asked for or either side is unusable. */
export function cleanAreaCompare(raw: unknown, slug: string): AreaCompare | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const sides = (Array.isArray(r.sides) ? r.sides : []).map(side)
  const [a, b] = sides
  if (r.slug !== slug || sides.length !== 2 || !a || !b || `${a.area.slug}-vs-${b.area.slug}` !== slug || !km(r.apart_km)) return null
  const distances = (Array.isArray(r.distances) ? r.distances : []).flatMap((v): DistanceRow[] => {
    const x = v as Record<string, unknown> | null
    return x && text(x.key) && text(x.name) && text(x.kind) && km(x.a_km) && km(x.b_km) && text(x.maps) && MAPS.test(x.maps)
      ? [{ key: x.key, name: x.name, kind: x.kind, kind_label: text(x.kind_label) ? x.kind_label : x.kind, a_km: x.a_km, b_km: x.b_km,
          maps: x.maps, source: text(x.source) ? x.source : '' }]
      : []
  })
  return {
    slug, as_of: a.as_of > b.as_of ? a.as_of : b.as_of, apart_km: r.apart_km, sides: [a, b], distances,
    related: cleanPairs(r.related),
    note: text(r.note) ? r.note : 'Straight-line distances from the middle of each area, rounded; not travel times.',
    attribution: text(r.attribution) ? r.attribution : '', source: text(r.source) ? r.source : 'MahaRERA public records',
  }
}

async function read(path: string): Promise<Response | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    return await fetch(serverApiBase() + '/api/v1/public/areas/compare' + path, {
      headers: { Accept: 'application/json' }, next: { revalidate: 300 }, signal: ctrl.signal,
    })
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

/** The page's answer; `{ redirect }` when the address is the pair in the other order (the backend names the one to use). */
export async function getAreaCompare(slug: string): Promise<AreaCompare | { redirect: string } | null> {
  if (fixturesForced() || !PAIR_SLUG.test(slug)) return null
  const res = await read('/' + encodeURIComponent(slug))
  if (!res) return null
  try {
    const body = await res.json()
    if (res.ok) return cleanAreaCompare(body, slug)
    const to = body?.detail?.canonical
    return res.status === 404 && typeof to === 'string' && PAIR_SLUG.test(to) && to !== slug ? { redirect: to } : null
  } catch {
    return null
  }
}

/** Every pair we compare; [] when the API cannot be read. */
export async function getAreaPairs(): Promise<AreaPair[]> {
  if (fixturesForced()) return []
  const res = await read('')
  if (!res || !res.ok) return []
  try {
    return cleanPairs(await res.json())
  } catch {
    return []
  }
}

/** The pairs an area's guide links to: those with this area, nearest first. */
export function pairsWith(pairs: AreaPair[], slug: string): AreaPair[] {
  return pairs.filter((p) => p.a.slug === slug || p.b.slug === slug).sort((x, y) => x.apart_km - y.apart_km)
}

export const comparePath = (slug: string) => `/localities/compare/${slug}`
