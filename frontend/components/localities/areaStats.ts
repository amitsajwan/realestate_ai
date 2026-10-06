/**
 * MahaRERA facts for an area page: GET /api/v1/public/areas/{slug}/stats (contract in docs/plan/pune-areas.md).
 * Server-side, revalidated like the other public data in lib/site/api.ts. Anything unexpected (outage, 404, 0 projects, a
 * malformed body) gives null and the page simply leaves the section out: it must never break or show an error.
 */
import { fixturesForced, serverApiBase } from '@/lib/site/api'

export interface AreaStatsProject {
  name: string
  regno: string
  promoter?: string | null
  completion?: string | null // filed completion date, YYYY-MM-DD
  updated?: string | null // MahaRERA "Last Modified", YYYY-MM-DD: listed or updated, never "registered"
  url?: string | null
  /** Our own project page (/projects/<slug>), linked before MahaRERA. */
  page?: string | null
}

export interface AreaStats {
  area: { key: string; name: string; slug: string; tier: string }
  as_of: string
  projects: number
  completing: Array<{ year: number; projects: number }>
  units_total: number | null
  units_booked: number | null
  recent: AreaStatsProject[]
  source: string
}

const DAY = /^\d{4}-\d{2}-\d{2}$/
const count = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v) && v >= 0

/** Keeps only what the page can show truthfully; null when there is nothing to show. */
export function cleanAreaStats(raw: unknown, slug: string): AreaStats | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const area = r.area as AreaStats['area'] | undefined
  if (!area || area.slug !== slug || !count(r.projects) || r.projects === 0 || typeof r.as_of !== 'string' || !DAY.test(r.as_of)) return null
  const completing = (Array.isArray(r.completing) ? r.completing : [])
    .filter((c): c is { year: number; projects: number } => !!c && count(c.year) && count(c.projects) && c.projects > 0)
    .sort((a, b) => a.year - b.year)
  const total = count(r.units_total) && r.units_total > 0 ? r.units_total : null
  const booked = count(r.units_booked) && total !== null && r.units_booked <= total ? r.units_booked : null
  const recent = (Array.isArray(r.recent) ? r.recent : [])
    .filter((p): p is AreaStatsProject => !!p && typeof p.name === 'string' && p.name.trim() !== '' && typeof p.regno === 'string')
    .slice(0, 5)
    .map((p) => ({ ...p, url: typeof p.url === 'string' && /^https:\/\/[a-z0-9.-]*maharera[a-z0-9.-]*\.gov\.in\//i.test(p.url) ? p.url : null,
      page: typeof p.page === 'string' && /^\/projects\/[a-z0-9-]+$/.test(p.page) ? p.page : null }))
  return {
    area, as_of: r.as_of, projects: r.projects, completing,
    units_total: booked === null ? null : total, units_booked: booked,
    recent, source: typeof r.source === 'string' && r.source ? r.source : 'MahaRERA public records',
  }
}

export async function getAreaStats(slug: string): Promise<AreaStats | null> {
  if (fixturesForced()) return null
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/areas/' + encodeURIComponent(slug) + '/stats', {
      headers: { Accept: 'application/json' },
      next: { revalidate: 30 },
      signal: ctrl.signal,
    })
    if (!res.ok) return null
    return cleanAreaStats(await res.json(), slug)
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

/** "2026-10-04" -> "4 October 2026" (no time zone surprises: the string is split, not parsed as a Date). */
export function longDate(day: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(day || '')
  if (!m || +m[2] < 1 || +m[2] > 12) return ''
  return `${+m[3]} ${MONTHS[+m[2] - 1]} ${m[1]}`
}
