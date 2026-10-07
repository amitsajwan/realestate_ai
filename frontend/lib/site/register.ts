/**
 * Our own page for every MahaRERA project (docs/plan/project-pages.md): GET /api/v1/public/register/projects/{slug} and the list.
 * The facts are Avasetu's (the register); an agent's listing in the project lives on the agent's page and uses them.
 */
import { serverApiBase } from './api'

export interface RegisterProject {
  slug: string
  name: string
  regno: string
  promoter: string | null
  pincode: string | null
  area: { key: string; slug: string; name: string } | null
  completion_now: string | null
  completion_at_registration: string | null
  units_total: number | null
  units_booked: number | null
  completion_passed?: boolean
  details_read_at: string | null
  listed_or_updated: string | null
  maharera_url: string | null
  paragraph: string
  indexable: boolean
  same_area: { name: string; slug: string; completion_now: string | null }[]
  source: string
}

export interface RegisterListItem {
  slug: string
  regno: string
  name: string
  area: string | null
  completion_now: string | null
  listed_or_updated: string | null
  indexable: boolean
}

type Got<T> = { ok: true; data: T } | { ok: false; notFound: boolean }

async function get<T>(path: string): Promise<Got<T>> {
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

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,15}$/

/** The project page data; null for an unknown slug. An outage throws, so it is never shown (or cached) as a 404. */
export async function getRegisterProject(slug: string): Promise<RegisterProject | null> {
  if (!SLUG.test(slug)) return null
  const r = await get<RegisterProject>('/api/v1/public/register/projects/' + encodeURIComponent(slug))
  if (r.ok) return r.data
  if (r.notFound) return null
  throw new Error('Project data is temporarily unavailable')
}

/** Indexable project pages (for the sitemap), optionally one area's. An outage gives an empty list. */
export async function getRegisterProjects(area?: string): Promise<RegisterListItem[]> {
  const r = await get<RegisterListItem[]>('/api/v1/public/register/projects' + (area ? '?area=' + encodeURIComponent(area) : ''))
  return r.ok && Array.isArray(r.data) ? r.data : []
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** "2029-10-30" -> "30 Oct 2029"; anything else -> "". */
export function longDay(iso: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '')
  return m ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}` : ''
}
