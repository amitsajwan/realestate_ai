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
  details?: ProjectDetailsGrid
  buildings?: RegisterBuilding[]
  map?: { lat: number; lon: number } | null
  builder?: BuilderRecord | null
  place?: string | null
  taluka?: string | null
  map_from?: string | null
  checks?: EnrichCheck[]
  text_checked?: boolean
  enriched_at?: string | null
}

/** One enrichment check behind the page (areastats.enrich): passed or not, when, and what was compared. */
export interface EnrichCheck {
  key: 'maharera_general' | 'buildings' | 'places' | 'text'
  label: string
  ok: boolean
  at: string | null
  note: string
}

export interface ProjectDetailsGrid {
  towers: number | null
  max_floors: number | null
  units_total: number | null
  units_residential: number | null
  units_other: number | null
  booked_pct: number | null
  registered_on: string | null
  completion_moved_months: number | null
}

export interface RegisterBuilding {
  name: string | null
  wing: string | null
  floors: number | null
  units_residential: number | null
  units_other: number | null
  units_total: number | null
}

export interface BuilderRecord {
  name: string
  count: number
  with_dates: number
  moved_later: number
  avg_months_later: number | null
  projects: { name: string; regno: string; slug: string | null; completion_now: string | null; months_later: number | null; this: boolean }[]
}

export interface Faq { q: string; a: string }

/** Questions and answers written by code from the page's facts only; a question with no fact behind it is left out. */
export function projectFaq(p: RegisterProject, nearby: { label?: string | null; name?: string | null; km?: number | null }[] = []): Faq[] {
  const out: Faq[] = []
  const d = p.details
  const where = p.area ? `${p.area.name}, Pune` : [p.place, p.taluka, 'Pune district'].filter(Boolean).join(', ')
  if (p.completion_now) {
    const moved = p.completion_at_registration && p.completion_at_registration !== p.completion_now
    out.push({ q: `What is the possession date of ${p.name}?`,
      a: `The completion date filed with MahaRERA is ${longDay(p.completion_now)}.` + (moved ? ` At registration it was ${longDay(p.completion_at_registration)}.` : '') +
        ' Ask the builder for the possession date in your agreement, in writing.' })
  }
  out.push({ q: `What is the MahaRERA number of ${p.name}?`, a: `${p.name} is registered with MahaRERA as ${p.regno}.` })
  if (d?.towers) {
    out.push({ q: `How many towers and floors does ${p.name} have?`,
      a: `MahaRERA lists ${d.towers} building${d.towers === 1 ? '' : 's'}` + (d.max_floors ? `, the tallest with ${d.max_floors} floors.` : '.') })
  }
  const units = d?.units_total ?? p.units_total
  if (units) {
    out.push({ q: `How many flats are there in ${p.name}?`,
      a: `MahaRERA lists ${units} units` + (d?.units_residential != null && d?.units_other ? ` (${d.units_residential} residential, ${d.units_other} other).` : '.') })
  }
  if (p.units_total) {
    out.push({ q: `How many homes in ${p.name} are booked?`,
      a: p.units_booked != null ? `${p.units_booked} of ${p.units_total} homes were booked as per MahaRERA${p.details_read_at ? ` on ${longDay(p.details_read_at)}` : ''}.`
        : 'The builder has not reported bookings on MahaRERA.' })
  }
  if (p.promoter) {
    const b = p.builder
    out.push({ q: `Who is the builder of ${p.name}?`,
      a: `The promoter registered with MahaRERA is ${p.promoter}.` + (b && b.count > 1 ? ` Our register has ${b.count} projects by this promoter${b.moved_later ? `; ${b.moved_later} moved their completion date later` : ''}.` : '') })
  }
  out.push({ q: `Where is ${p.name}?`, a: `${p.name} is in ${where}${p.pincode ? ` (pincode ${p.pincode})` : ''}.` })
  const near = nearby.filter((n) => n.name && n.km != null).slice(0, 3)
  if (near.length) {
    out.push({ q: `What is near ${p.name}?`,
      a: near.map((n) => `${n.name}${n.label ? ` (${n.label})` : ''}, ${n.km} km`).join('; ') + ' (OpenStreetMap, straight-line distance).' })
  }
  if (p.completion_passed) {
    out.push({ q: `Has the completion date of ${p.name} passed?`, a: 'Yes. Ask the builder for the occupancy certificate (OC) before you book.' })
  }
  return out.slice(0, 10)
}

export interface RegisterListItem {
  slug: string
  regno: string
  name: string
  area: string | null
  promoter?: string | null
  completion_now: string | null
  /** enrichment checks passed (null: our crawler has not reached it yet) out of checks_total */
  checked?: number | null
  checks_total?: number
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
export async function getRegisterProjects(area?: string, all = false): Promise<RegisterListItem[]> {
  const q = [area ? 'area=' + encodeURIComponent(area) : '', all ? 'all=true' : ''].filter(Boolean).join('&')
  const r = await get<RegisterListItem[]>('/api/v1/public/register/projects' + (q ? '?' + q : ''))
  return r.ok && Array.isArray(r.data) ? r.data : []
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** "2029-10-30" -> "30 Oct 2029"; anything else -> "". */
export function longDay(iso: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '')
  return m ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}` : ''
}
