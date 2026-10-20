/**
 * Our own page for every MahaRERA project (docs/plan/project-pages.md): GET /api/v1/public/register/projects/{slug} and the list.
 * The facts are Avasetu's (the register); an agent's listing in the project lives on the agent's page and uses them.
 */
import { serverApiBase } from './api'
import { badStatus, failed, withRetry, type Got } from './retry'
import type { WebFacts } from './webfacts'
import type { ProjectProfile } from './profile'

export interface RegisterProject {
  slug: string
  /** MahaRERA's legal name ("Geras World of Joy M") */
  name: string
  /** the name buyers search for ("Gera World of Joy"); absent until the backend sends it */
  marketed_name?: string | null
  /** other names the project is known by */
  aliases?: string[]
  /** newest date this page's facts changed (our crawler or MahaRERA); null when unknown */
  page_updated?: string | null
  /** the promoter's other projects in our register */
  same_promoter?: { name: string; marketed_name?: string | null; search_name?: string | null; slug: string; completion_now: string | null }[]
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
  /** the Pune place the register groups it under (app/core/pune_places.py): every Pune district project has one */
  pune_place?: { key: string; name: string | null } | null
  map_from?: string | null
  checks?: EnrichCheck[]
  text_checked?: boolean
  enriched_at?: string | null
  /** the marketed project this registration is one tower of, when that project is live on our pages (agentprojects.groups) */
  group?: { name: string; tower: string; towers: number; path: string } | null
  /** what the builder's site and the sites ranking for the project say, checked (backend areastats/webfacts.py) */
  web_facts?: WebFacts | null
  /** highlights, the builder's pictures and floor plans while the project is being built (backend areastats/profile.py) */
  profile?: ProjectProfile | null
  /** asked prices per home size, from the builder's site or two sites that agree (backend areastats/prices.py) */
  prices?: ProjectPrices | null
  /** 'Check before you book': weak points worked out by code from MahaRERA and checked web facts (backend areastats/cautions.py) */
  cautions?: { key: string; text: string; source: 'rera' | 'web' }[]
  stage?: Stage | null
  sold_out?: boolean
  /** how people search for the project (backend seo/targets.py, docs/plan/rank-loop.md R1): leads the title and H1 */
  search_name?: string | null
  /** Google's "People also ask" questions about it, answered from our facts (backend seo/questions.py, R4) */
  faq?: { q: string; a: string; source: string; topic?: string }[]
  /** a search description from the facts: the page doctor's (R3) when it wrote one, else the page writer's one-line summary */
  search_description?: string | null
  /** the page writer's sections under the paragraph (backend areastats/enrich.py SECTIONS), checked with it */
  sections?: { heading: string; text: string }[]
  /** every MahaRERA registration of the project (towers, phases) when this page stands for several (R0) */
  towers?: RegisterTower[]
  /** the nearest neighbourhood guide (R5) */
  near_guide?: { name: string; path: string; km: number } | null
  /** the builder's page: /builders/<slug> (R6) */
  builder_slug?: string | null
}

/** One registration of a project that MahaRERA holds tower by tower or phase by phase. */
export interface RegisterTower {
  regno: string
  name: string
  completion_now: string | null
  completion_at_registration: string | null
  units_total: number | null
  units_booked: number | null
  registered_on: string | null
  maharera_url: string | null
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
  extension_months?: number
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
  /** the brand's name (backend areastats/brands.py), else the MahaRERA promoter's */
  name: string
  slug?: string
  count: number
  /** enough projects with both dates (5+) to state the record */
  record_ok?: boolean
  with_dates: number
  moved_later: number
  avg_months_later: number | null
  projects: { name: string; regno: string; slug: string | null; completion_now: string | null; months_later: number | null; this: boolean }[]
}

export interface Faq { q: string; a: string }

/** Questions and answers written by code from the page's facts only; a question with no fact behind it is left out. The questions
 *  people really ask Google (p.faq, from the backend) take the place of our own question on the same topic. */
export function projectFaq(p: RegisterProject, nearby: { label?: string | null; name?: string | null; km?: number | null }[] = [],
  price?: string | null): Faq[] {
  const asked = (p.faq ?? []).filter((f) => f.q && f.a)
  if (!asked.length) return ownFaq(p, nearby, price).map(({ q, a }) => ({ q, a }))
  const topics = new Set(asked.map((f) => f.topic))
  const own = ownFaq(p, nearby, price).filter((f) => !topics.has(f.topic))
  return [...own.slice(0, 1), ...asked.map((f) => ({ q: f.q, a: f.a })), ...own.slice(1).map(({ q, a }) => ({ q, a }))].slice(0, 12)
}

function ownFaq(p: RegisterProject, nearby: { label?: string | null; name?: string | null; km?: number | null }[] = [],
  price?: string | null): (Faq & { topic: string })[] {
  const out: (Faq & { topic: string })[] = []
  const shown = displayName(p)
  out.push({ topic: 'price', q: `What is the price of ${shown}?`,
    a: price ? `A local agent quotes ${price} for ${shown}. Prices change often: confirm the price and what it includes before you book.`
      : `No agent has quoted a price for ${shown} yet. Ask through the enquiry form on this page and a local agent will send you the current price.` })
  const d = p.details
  const where = p.area ? `${p.area.name}, Pune` : [p.place, p.taluka, 'Pune district'].filter(Boolean).join(', ')
  if (p.completion_now) {
    const moved = p.completion_at_registration && p.completion_at_registration !== p.completion_now
    const ext = moved && d?.extension_months ? ` MahaRERA added ${d.extension_months} months to most projects' dates in August 2026 (Order 66/2026).` : ''
    out.push({ topic: 'possession', q: `What is the possession date of ${p.name}?`,
      a: `The completion date filed with MahaRERA is ${longDay(p.completion_now)}.` + (moved ? ` At registration it was ${longDay(p.completion_at_registration)}.` : '') + ext +
        ' Ask the builder for the possession date in your agreement, in writing.' })
  }
  out.push({ topic: 'rera', q: `What is the MahaRERA number of ${p.name}?`, a: `${p.name} is registered with MahaRERA as ${p.regno}.` })
  if (d?.towers) {
    out.push({ topic: 'size', q: `How many towers and floors does ${p.name} have?`,
      a: `MahaRERA lists ${d.towers} building${d.towers === 1 ? '' : 's'}` + (d.max_floors ? `, the tallest with ${d.max_floors} floors.` : '.') })
  }
  const units = d?.units_total ?? p.units_total
  if (units) {
    out.push({ topic: 'size', q: `How many flats are there in ${p.name}?`,
      a: `MahaRERA lists ${units} units` + (d?.units_residential != null && d?.units_other ? ` (${d.units_residential} residential, ${d.units_other} other).` : '.') })
  }
  if (p.units_total) {
    out.push({ topic: 'booked', q: `How many homes in ${p.name} are booked?`,
      a: p.units_booked != null ? `${p.units_booked} of ${p.units_total} homes were booked as per MahaRERA${p.details_read_at ? ` on ${longDay(p.details_read_at)}` : ''}.`
        : 'The builder has not reported bookings on MahaRERA.' })
  }
  if (p.promoter) {
    const b = p.builder
    out.push({ topic: 'builder', q: `Who is the builder of ${p.name}?`,
      a: `The promoter registered with MahaRERA is ${p.promoter}.` + (b && b.count > 1 ? ` Our register has ${b.count} Pune projects by ${b.name}${b.record_ok ? `; ${b.moved_later} of ${b.with_dates} with both dates moved their completion date 3 months or more later` : ''}.` : '') })
  }
  out.push({ topic: 'location', q: `Where is ${p.name}?`, a: `${p.name} is in ${where}${p.pincode ? ` (pincode ${p.pincode})` : ''}.` })
  const near = nearby.filter((n) => n.name && n.km != null).slice(0, 3)
  if (near.length) {
    out.push({ topic: 'near', q: `What is near ${p.name}?`,
      a: near.map((n) => `${n.name}${n.label ? ` (${n.label})` : ''}, ${n.km} km`).join('; ') + ' (OpenStreetMap, straight-line distance).' })
  }
  if (p.completion_passed) {
    out.push({ topic: 'oc', q: `Has the completion date of ${p.name} passed?`, a: 'Yes. Ask the builder for the occupancy certificate (OC) before you book.' })
  }
  return out.slice(0, 11)
}

/** How far a project is through the time from MahaRERA registration to its filed completion date (backend areastats/pages.stage):
 *  by dates, not a site check (MahaRERA's progress reports need its login). */
export type Stage = 'new' | 'early' | 'mid' | 'advanced' | 'passed'
export const STAGES: Stage[] = ['new', 'early', 'mid', 'advanced', 'passed']
export const STAGE_LABEL: Record<Stage, string> = { new: 'New launch', early: 'Early stage', mid: 'Mid stage', advanced: 'Near completion',
  passed: 'Completion date passed' }
export const STAGE_NOTE = 'Stage by dates: how much of the time between MahaRERA registration and the completion date the builder filed has gone. '
  + 'Not a site check: MahaRERA’s construction progress reports are behind its login.'

export interface ProjectPrices {
  read_at: string | null
  /** url only for the builder's own site: property sites are named, not linked */
  rows: { bhk: string; from_inr: number; to_inr: number | null; official: boolean; sources: { site: string; url: string | null }[] }[]
}

export interface RegisterListItem {
  slug: string
  regno: string
  name: string
  marketed_name?: string | null
  search_name?: string | null
  aliases?: string[]
  units_total?: number | null
  units_booked?: number | null
  area: string | null
  promoter?: string | null
  completion_now: string | null
  /** enrichment checks passed (null: our crawler has not reached it yet) out of checks_total */
  checked?: number | null
  checks_total?: number
  /** false: finished more than a year ago; the page stays, the lists leave it out */
  active?: boolean
  listed_or_updated: string | null
  /** how far through its filed build time, by dates (backend pages.stage) */
  stage?: Stage | null
  /** every home booked on MahaRERA */
  sold_out?: boolean
  /** the lowest asked price we publish for it (backend areastats/prices.py), in rupees */
  price_from?: number | null
  /** the Pune place (key) and its name: every Pune district project has one */
  place?: string | null
  place_name?: string | null
  /** our own last change to the page (details read, enrichment, page text): the sitemap lastmod; never MahaRERA dates */
  page_updated?: string | null
  indexable: boolean
}

/** Retried as getJson in ./api (./retry): a deploy's restart gives a slow page, not a 5xx. */
async function get<T>(path: string, ms = 5000): Promise<Got<T>> {
  return withRetry(() => getOnce<T>(path, ms))
}

async function getOnce<T>(path: string, ms: number): Promise<Got<T>> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), ms)
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

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,15}$/

/** The project page data; null for an unknown slug. An outage throws, so it is never shown (or cached) as a 404. */
export async function getRegisterProject(slug: string): Promise<RegisterProject | null> {
  if (!SLUG.test(slug)) return null
  const r = await get<RegisterProject>('/api/v1/public/register/projects/' + encodeURIComponent(slug))
  if (r.ok) return r.data
  if (r.notFound) return null
  throw new Error('Project data is temporarily unavailable')
}

/** Lists kept in this process for 5 minutes: the whole register is ~7.5 MB, over the 2 MB Next.js data cache limit, so without
 *  this /projects (rendered per request for ?q=), the homepage and the sitemap each fetched it again on every render (~8 s).
 *  Concurrent renders share one fetch; a failed fetch is not kept. */
const LIST_TTL_MS = 5 * 60 * 1000
const lists = new Map<string, { at: number; data: Promise<RegisterListItem[] | null> }>()

/** Indexable project pages (for the sitemap), optionally one area's. An outage gives an empty list. */
export async function getRegisterProjects(area?: string, all = false, place?: string): Promise<RegisterListItem[]> {
  const q = [area ? 'area=' + encodeURIComponent(area) : '', all ? 'all=true' : '', place ? 'place=' + encodeURIComponent(place) : '',
    'limit=20000'].filter(Boolean).join('&')
  const hit = lists.get(q)
  if (hit && Date.now() - hit.at < LIST_TTL_MS) {
    const data = await hit.data
    if (data) return data
  }
  // the whole register (11,000+ projects) takes several seconds: a 5 s cut left the sitemap without project pages
  const data = get<RegisterListItem[]>('/api/v1/public/register/projects?' + q, 30000)
    .then((r) => (r.ok && Array.isArray(r.data) ? r.data : null))
  lists.set(q, { at: Date.now(), data })
  const got = await data
  if (!got && lists.get(q)?.data === data) lists.delete(q)
  return got ?? []
}

/** A Pune place with projects in the register: GET /api/v1/public/register/places, in zone order. */
export interface RegisterPlace {
  key: string
  slug: string
  name: string
  zone: string
  projects: number
  indexable: number
}

export async function getRegisterPlaces(): Promise<RegisterPlace[]> {
  const r = await get<RegisterPlace[]>('/api/v1/public/register/places')
  return r.ok && Array.isArray(r.data) ? r.data : []
}

export function placePath(slug: string): string {
  return `/projects/area/${slug}`
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** "2029-10-30" -> "30 Oct 2029"; anything else -> "". */
export function longDay(iso: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '')
  return m ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}` : ''
}

/** "2029-10-30" -> "Oct 2029"; anything else -> "". */
export function monthYear(iso: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})/.exec(iso || '')
  return m ? `${MONTHS[Number(m[2]) - 1]} ${m[1]}` : ''
}

/** The name buyers know the project by: how they search for it (search_name), else the marketed name, else MahaRERA's. */
export function displayName(p: { name: string; marketed_name?: string | null; search_name?: string | null }): string {
  return (p.search_name || '').trim() || (p.marketed_name || '').trim() || p.name
}

/** Other names worth showing ("Also known as"): aliases and the legal name, minus the ones already displayed. */
export function otherNames(p: { name: string; marketed_name?: string | null; aliases?: string[] | null }, shown: string[] = []): string[] {
  const seen = new Set([displayName(p), ...shown].map((x) => x.toLowerCase().trim()))
  const out: string[] = []
  for (const a of [...(p.aliases ?? []), p.name]) {
    const k = (a || '').toLowerCase().trim()
    if (k && !seen.has(k)) { seen.add(k); out.push(a.trim()) }
  }
  return out
}

/** The one-line summary under a project link: "by {builder} · possession {Mon YYYY} · {booked}/{total} booked". */
export function projectSummary(r: { promoter?: string | null; completion_now?: string | null; units_total?: number | null; units_booked?: number | null }): string {
  return [r.promoter ? `by ${r.promoter}` : null, r.completion_now ? `possession ${monthYear(r.completion_now)}` : null,
    r.units_total ? (r.units_booked != null ? `${r.units_booked}/${r.units_total} booked` : `${r.units_total} homes`) : null].filter(Boolean).join(' · ')
}

/** The area name a project page shows: our locality, else the Pune place it is filed under. */
export function areaName(p: RegisterProject): string | null {
  return p.area?.name ?? p.pune_place?.name ?? p.place ?? null
}

/** Search result title, aiming at 60 characters: "{Marketed} {Area}: Price, Possession {Mon YYYY}, MahaRERA", dropping parts for long names. */
export function registerTitle(p: RegisterProject): string {
  const shown = displayName(p)
  const area = areaName(p)
  const at = area && !shown.toLowerCase().includes(area.toLowerCase()) ? `${shown} ${area}` : shown
  const when = monthYear(p.completion_now)
  const options = when
    ? [`${at}: Price, Possession ${when}, MahaRERA`, `${at}: Possession ${when}, MahaRERA`, `${at}: Possession ${when}`, `${shown}: Possession ${when}`]
    : [`${at}: Price, Possession, MahaRERA`, `${at}: Price, MahaRERA`]
  return options.find((t) => t.length <= 60) ?? at
}

/** Search result description: "{Marketed} ({Legal}) by {Builder}, {Area}, Pune. Possession {Mon YYYY}, moved from X, b/t homes booked, MahaRERA {regno}." */
export function registerDescription(p: RegisterProject): string {
  if (p.search_description) return p.search_description
  const shown = displayName(p)
  const legal = shown.toLowerCase() !== p.name.toLowerCase() ? ` (${p.name})` : ''
  const area = areaName(p)
  const head = `${shown}${legal}${p.promoter ? ` by ${p.promoter}` : ''}${area ? `, ${area}` : ''}, Pune.`
  const from = p.completion_at_registration && p.completion_now && monthYear(p.completion_at_registration) !== monthYear(p.completion_now)
    && p.details?.completion_moved_months !== 0 ? `, moved from ${monthYear(p.completion_at_registration)}` : ''
  const parts = [p.completion_now ? `Possession ${monthYear(p.completion_now)}${from}` : null,
    p.units_total && p.units_booked != null ? `${p.units_booked}/${p.units_total} homes booked` : null, `MahaRERA ${p.regno}`]
  return `${head} ${parts.filter(Boolean).join(', ')}.`
}

/** One hit from GET /api/v1/public/register/search. */
export interface RegisterSearchHit {
  slug: string
  name: string
  marketed_name?: string | null
  regno: string
  promoter?: string | null
  area?: string | null
  place_name?: string | null
  completion_now?: string | null
  units_total?: number | null
  units_booked?: number | null
  checked?: number | null
  checks_total?: number
  active?: boolean
  /** months the possession date moved later since registration (0: not moved; null: unknown): the project check's pill */
  months_later?: number | null
}

/** Search the register by name (marketed, legal or alias), builder or MahaRERA number. Works in the browser (the public API base,
 *  as lib/config/api) and on the server; any failure gives an empty list. */
export async function searchRegister(q: string, limit = 20, signal?: AbortSignal): Promise<RegisterSearchHit[]> {
  const t = q.trim()
  if (t.length < 2) return []
  const server = typeof window === 'undefined'
  const base = server ? serverApiBase() : (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || '').replace(/\/+$/, '')
  try {
    const res = await fetch(`${base}/api/v1/public/register/search?q=${encodeURIComponent(t.slice(0, 80))}&limit=${limit}`,
      { headers: { Accept: 'application/json' }, signal, ...(server ? { next: { revalidate: 300 } } : {}) })
    if (!res.ok) return []
    const data = await res.json()
    return Array.isArray(data) ? (data as RegisterSearchHit[]) : []
  } catch {
    return []
  }
}
