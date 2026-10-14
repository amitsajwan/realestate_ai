/**
 * Pages that link project pages together (docs/plan/rank-loop.md R5, R6; backend areastats/hubs.py):
 * GET /api/v1/public/register/active?area=|place=   "Most active projects": one fact line each, never a score
 * GET /api/v1/public/register/near/{area}/{slug}    project pages near a neighbourhood guide
 * GET /api/v1/public/builders and /builders/{slug}  one page per builder from MahaRERA records
 * Lists come back empty on any failure; a builder page is null on a 404 and throws on an outage (never a cached 404).
 */
import { serverApiBase } from './api'

export interface ActiveProject { slug: string; name: string; fact: string; source: string; km?: number }

export interface BuilderCard { slug: string; name: string; projects: number; indexable: boolean; page_updated: string | null }

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

export async function getActive(where: { area?: string; place?: string }, limit = 8): Promise<ActiveProject[]> {
  const q = where.area ? 'area=' + encodeURIComponent(where.area) : where.place ? 'place=' + encodeURIComponent(where.place) : ''
  if (!q) return []
  const r = await get<ActiveProject[]>(`/api/v1/public/register/active?${q}&limit=${limit}`)
  return r.ok && Array.isArray(r.data) ? r.data : []
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

export async function getBuilder(slug: string): Promise<BuilderPage | null> {
  if (!SLUG.test(slug)) return null
  const r = await get<BuilderPage>('/api/v1/public/builders/' + encodeURIComponent(slug))
  if (r.ok) return r.data
  if (r.notFound) return null
  throw new Error('Builder data is temporarily unavailable')
}
