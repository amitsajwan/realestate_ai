/**
 * "Latest from <Area>" on an area page: our posts and news stories about that one area (contracts in docs/plan/seo.md).
 *   GET /api/v1/public/posts?limit=6&area=<key>  items carry `slug` (page /posts/<slug>) and `area` (an area key or null)
 *   GET /api/v1/public/news?limit=5&area=<key>   items carry `id` (page /news/<id>) and `areas` ([{ slug, name }])
 * Server-side, revalidated like the other public data in lib/site/api.ts. Until the S1/S2 helpers (fetchPosts(limit, area) in
 * lib/posts/data.ts, fetchNews(limit, area) in lib/news/data.ts) are merged this module calls the endpoints itself; switch to
 * them then. Whatever the backend does, only items that say they are about this area are shown: a backend that does not yet
 * filter by `area` (or does not yet send `area`/`slug`) gives an empty list, never another area's items. Anything unexpected
 * (outage, error status, malformed body) also gives an empty list, and the page leaves the block out.
 */
import { fixturesForced, serverApiBase } from '@/lib/site/api'

export interface AreaRef { key: string; slug: string }

export interface AreaPost {
  slug: string
  title: string
  excerpt: string
  kind: 'post' | 'showcase' | 'reel'
  published_at: string
}

export interface AreaNews {
  id: string
  headline: string
  summary: string
  source_name: string
  published_at: string
}

const POST_SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const NEWS_ID = /^[A-Za-z0-9][A-Za-z0-9_-]*$/
const str = (v: unknown): string => (typeof v === 'string' ? v.trim() : '')
const rows = (raw: unknown): Record<string, unknown>[] =>
  (Array.isArray(raw) ? raw : []).filter((r): r is Record<string, unknown> => !!r && typeof r === 'object' && !Array.isArray(r))

/** Posts about this area with a page of their own; rows without a valid `slug`, or not tagged with this area, are skipped. */
export function cleanAreaPosts(raw: unknown, area: AreaRef, limit = 6): AreaPost[] {
  const out: AreaPost[] = []
  for (const p of rows(raw)) {
    const slug = str(p.slug)
    const title = str(p.title)
    if (!POST_SLUG.test(slug) || !title || p.area !== area.key || out.some((x) => x.slug === slug)) continue
    out.push({
      slug, title, excerpt: str(p.excerpt),
      kind: p.kind === 'showcase' || p.kind === 'reel' ? p.kind : 'post',
      published_at: str(p.published_at),
    })
  }
  return out.slice(0, limit)
}

/** True when a news item's `areas` names this area (by slug, as the API sends it, or by key). */
function namesArea(areas: unknown, area: AreaRef): boolean {
  return (Array.isArray(areas) ? areas : []).some((a) => {
    if (typeof a === 'string') return a === area.key || a === area.slug
    const o = a as Record<string, unknown> | null
    return !!o && typeof o === 'object' && (o.slug === area.slug || o.key === area.key)
  })
}

/** News stories about this area; rows without a usable `id` or headline, or not about this area, are skipped. */
export function cleanAreaNews(raw: unknown, area: AreaRef, limit = 5): AreaNews[] {
  const out: AreaNews[] = []
  for (const n of rows(raw)) {
    const id = str(n.id)
    const headline = str(n.headline)
    if (!NEWS_ID.test(id) || !headline || !namesArea(n.areas, area) || out.some((x) => x.id === id)) continue
    out.push({ id, headline, summary: str(n.summary), source_name: str(n.source_name), published_at: str(n.published_at) })
  }
  return out.slice(0, limit)
}

async function getList(path: string): Promise<unknown> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    const res = await fetch(serverApiBase() + path, {
      headers: { Accept: 'application/json' },
      next: { revalidate: 30 },
      signal: ctrl.signal,
    })
    return res.ok ? await res.json() : null
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

export async function getAreaPosts(area: AreaRef, limit = 6): Promise<AreaPost[]> {
  if (fixturesForced()) return []
  return cleanAreaPosts(await getList(`/api/v1/public/posts?limit=${limit}&area=${encodeURIComponent(area.key)}`), area, limit)
}

export async function getAreaNews(area: AreaRef, limit = 5): Promise<AreaNews[]> {
  if (fixturesForced()) return []
  return cleanAreaNews(await getList(`/api/v1/public/news?limit=${limit}&area=${encodeURIComponent(area.key)}`), area, limit)
}

export const postPath = (slug: string): string => `/posts/${slug}`
export const newsPath = (id: string): string => `/news/${encodeURIComponent(id)}`

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** An ISO time as "4 Oct 2026" in India time; '' when missing or unreadable. Month names are written out here (ICU data
 *  differs between Node and browsers). */
export function feedDate(iso: string): string {
  const d = new Date(iso)
  if (!iso || Number.isNaN(d.getTime())) return ''
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'numeric', year: 'numeric', timeZone: 'Asia/Kolkata' })
    .formatToParts(d).map((x) => [x.type, x.value]))
  return `${Number(p.day)} ${MONTHS[Number(p.month) - 1]} ${p.year}`
}
