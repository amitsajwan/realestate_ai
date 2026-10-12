/**
 * Neighbourhood articles the backend bot finds and writes from facts (backend/app/modules/communities):
 * GET /api/v1/public/communities?area=<key> and GET /api/v1/public/communities/{area}/{slug}. Only published, checked articles
 * come back. Lists hide themselves on any failure; one article is null only on a real 404, and an outage throws so the error
 * page (not a cached 404) shows.
 */
import { fixturesForced, serverApiBase } from '@/lib/site/api'

export interface CommunityCard {
  area: string
  area_name: string
  area_slug: string
  slug: string
  name: string
  title: string
  summary: string
  updated: string | null
}

export interface CommunityFacts {
  nearby: { kind: string; name: string; km: number }[]
  projects: { name: string; regno: string; promoter?: string | null; completion?: string | null; page?: string | null }[]
  area_projects: number
  as_of?: string | null
}

export interface Community extends CommunityCard {
  paragraphs: string[]
  facts: CommunityFacts
  published: string | null
  osm_url?: string | null
  sources: string[]
}

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,10}$/

export function cleanCard(raw: unknown): CommunityCard | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  for (const k of ['area', 'area_name', 'area_slug', 'slug', 'name', 'title']) if (typeof r[k] !== 'string' || !r[k]) return null
  if (!SLUG.test(r.slug as string) || !SLUG.test(r.area_slug as string)) return null
  return {
    area: r.area as string, area_name: r.area_name as string, area_slug: r.area_slug as string, slug: r.slug as string,
    name: r.name as string, title: r.title as string, summary: typeof r.summary === 'string' ? r.summary : '',
    updated: typeof r.updated === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(r.updated) ? r.updated : null,
  }
}

export async function getCommunities(area?: string): Promise<CommunityCard[]> {
  if (fixturesForced()) return []
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/communities' + (area ? '?area=' + encodeURIComponent(area) : ''), {
      headers: { Accept: 'application/json' }, next: { revalidate: 300 }, signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) return []
    const body = await res.json()
    return (Array.isArray(body) ? body : []).map(cleanCard).filter((c): c is CommunityCard => c !== null)
  } catch {
    return []
  }
}

export async function getCommunity(area: string, slug: string): Promise<Community | null> {
  if (fixturesForced() || !SLUG.test(area) || !SLUG.test(slug)) return null
  const res = await fetch(serverApiBase() + `/api/v1/public/communities/${area}/${slug}`, {
    headers: { Accept: 'application/json' }, next: { revalidate: 300 }, signal: AbortSignal.timeout(5000),
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Neighbourhood article temporarily unavailable')
  const r = await res.json()
  const card = cleanCard(r)
  const paragraphs = Array.isArray(r?.paragraphs) ? r.paragraphs.filter((p: unknown): p is string => typeof p === 'string' && p.trim() !== '') : []
  if (!card || paragraphs.length === 0) return null
  const f = (r.facts || {}) as Partial<CommunityFacts>
  return {
    ...card, paragraphs,
    facts: {
      nearby: (Array.isArray(f.nearby) ? f.nearby : []).filter((n) => n && typeof n.name === 'string' && typeof n.km === 'number'),
      projects: (Array.isArray(f.projects) ? f.projects : []).filter((p) => p && typeof p.name === 'string')
        .map((p) => ({ ...p, page: typeof p.page === 'string' && /^\/projects\/[a-z0-9-]+$/.test(p.page) ? p.page : null })),
      area_projects: typeof f.area_projects === 'number' ? f.area_projects : 0,
      as_of: typeof f.as_of === 'string' ? f.as_of : null,
    },
    published: typeof r.published === 'string' ? r.published : null,
    osm_url: typeof r.osm_url === 'string' && r.osm_url.startsWith('https://www.openstreetmap.org/') ? r.osm_url : null,
    sources: Array.isArray(r.sources) ? r.sources.filter((s: unknown) => typeof s === 'string') : [],
  }
}
