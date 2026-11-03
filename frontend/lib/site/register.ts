/**
 * Our own page for every MahaRERA project (docs/plan/project-pages.md): GET /api/v1/public/register/projects/{slug} and the list.
 * The facts are Avasetu's (the register); an agent's listing in the project lives on the agent's page and uses them.
 */
import { serverApiBase } from './api'
import { badStatus, failed, withRetry, type Got } from './retry'
import type { WebFacts } from './webfacts'
import type { ProjectProfile } from './profile'
import { formatPrice, readableName } from './format'

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
  /** finished (backend pages.is_old: the filed completion date passed over a year ago): no enquiry form, out of search, and
   *  same_area holds the projects still being built nearby, soonest possession first */
  finished?: boolean
  /** other projects in the area; price_from (rupees) and bhk ("2, 3 BHK") from their published prices, when there are any */
  same_area: { name: string; slug: string; completion_now: string | null; price_from?: number | null; bhk?: string | null }[]
  source: string
  details?: ProjectDetailsGrid
  buildings?: RegisterBuilding[]
  map?: { lat: number; lon: number } | null
  /** a street map drawn around the checked pin, for the hero when there is no picture (backend areastats/locmap.py) */
  location_picture?: { url: string; width: number; height: number } | null
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
  /** the rounded price idea under the exact prices (backend areastats/priceidea.py) */
  price_idea?: PriceIdea | null
  plans_3d?: Plans3D | null
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
  /** the area's median ₹ per sq ft from at least 3 other projects' published prices with a size (backend pages.project_page) */
  area_rate?: { place: string; per_sqft: number; projects: number } | null
  /** this project beside the other projects still being built in its area (backend pages.area_compare): each part null with
   *  fewer than 8 to compare with. No rate comparison: sites mix carpet and super built-up areas */
  area_compare?: AreaCompare | null
  /** homes booked between two MahaRERA reads 30-90 days apart; null without two reads or when none were booked */
  sales?: { booked: number; days: number; since: string } | null
  /** straight-line km from the checked map position to the work hubs people commute to, nearest first */
  commute?: { name: string; km: number }[]
  /** the only change to the filed completion date is MahaRERA's 2026 blanket extension: the builder moved nothing */
  extension_only?: boolean | null
  /** homes booked as we read them from MahaRERA over time, oldest first, one per day (backend pagefacts.booked_readings);
   *  empty with fewer than two days. MahaRERA itself shows only today's count. */
  booked_readings?: { on: string; booked: number }[] | null
  /** every change of the filed completion date we saw, oldest first; `blanket`: MahaRERA's 2026 extension, not the builder
   *  (backend pages.completion_moves) */
  completion_moves?: { seen_on: string | null; from: string; to: string; blanket: boolean }[] | null
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

export interface BuilderLogo { url: string; width: number | null; height: number | null; tone: 'light' | 'dark'; site: string | null }

export interface AreaCompare {
  place: string
  /** share of homes booked against the middle of the area's projects registered within a year of this one */
  booked: { pct: number; area_pct: number; projects: number } | null
  /** months the builder moved the filed date (net of MahaRERA's 2026 order) against how many of the area's projects moved theirs */
  moved: { months: number; area_moved: number; area_with_dates: number } | null
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
  /** the builder's logo from its own home page (backend areastats/logos.py); tone 'light' is drawn for a dark background */
  logo?: BuilderLogo | null
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
  const asked = askedPrices(p)
  out.push({ topic: 'price', q: `What is the price of ${shown}?`,
    a: price ? `A local agent quotes ${price} for ${shown}. Prices change often: confirm the price and what it includes before you book.`
      : asked ? `${asked.rows.map((r) => r.text).join('; ')}, as listed on ${asked.sites}${asked.on ? ` on ${longDay(asked.on)}` : ''}. `
        + 'Builders change prices often and add parking and other charges: ask for the current price sheet before you book.'
      : `No agent has quoted a price for ${shown} yet. Ask through the enquiry form on this page and a local agent will send you the current price.` })
  const d = p.details
  const where = p.area ? `${p.area.name}, Pune` : [p.place, p.taluka, 'Pune district'].filter(Boolean).join(', ')
  const change = completionChange(p)
  if (p.completion_now && change) {
    const ext = change.kind === 'moved' && change.extension
      ? ` MahaRERA added ${change.extension} months to most projects' dates in August 2026 (Order 66/2026).` : ''
    out.push({ topic: 'possession', q: `What is the possession date of ${shown}?`,
      a: (change.kind === 'extension' ? extensionSentence(p.completion_now, change.months)
        : `The completion date filed with MahaRERA is ${longDay(p.completion_now)}.`
          + (change.kind === 'moved' ? ` At registration it was ${longDay(change.from)}.` : '') + ext)
        + ' Ask the builder for the possession date in your agreement, in writing.' })
  }
  out.push({ topic: 'rera', q: `What is the MahaRERA number of ${shown}?`, a: `${shown} is registered with MahaRERA as ${p.regno}.` })
  if (d?.towers) {
    out.push({ topic: 'size', q: `How many towers and floors does ${shown} have?`,
      a: `MahaRERA lists ${d.towers} building${d.towers === 1 ? '' : 's'}` + (d.max_floors ? `, the tallest with ${d.max_floors} floors.` : '.') })
  }
  const units = d?.units_total ?? p.units_total
  if (units) {
    out.push({ topic: 'size', q: `How many flats are there in ${shown}?`,
      a: `MahaRERA lists ${units} units` + (d?.units_residential != null && d?.units_other ? ` (${d.units_residential} residential, ${d.units_other} other).` : '.') })
  }
  if (p.units_total) {
    out.push({ topic: 'booked', q: `How many homes in ${shown} are booked?`,
      a: p.units_booked != null ? `${p.units_booked} of ${p.units_total} homes were booked as per MahaRERA${p.details_read_at ? ` on ${longDay(p.details_read_at)}` : ''}.`
        : 'The builder has not reported bookings on MahaRERA.' })
  }
  if (p.promoter) {
    const b = p.builder
    out.push({ topic: 'builder', q: `Who is the builder of ${shown}?`,
      a: `The promoter registered with MahaRERA is ${p.promoter}.` + (b && b.count > 1 ? ` Our register has ${b.count} Pune projects by ${b.name}${b.record_ok ? `; ${b.moved_later} of ${b.with_dates} with both dates moved their completion date 3 months or more later` : ''}.` : '') })
  }
  out.push({ topic: 'location', q: `Where is ${shown}?`, a: `${shown} is in ${where}${p.pincode ? ` (pincode ${p.pincode})` : ''}.` })
  const near = nearby.filter((n) => n.name && n.km != null).slice(0, 3)
  if (near.length) {
    out.push({ topic: 'near', q: `What is near ${shown}?`,
      a: near.map((n) => `${n.name}${n.label ? ` (${n.label})` : ''}, ${n.km} km`).join('; ') + ' (OpenStreetMap, straight-line distance).' })
  }
  if (p.completion_passed) {
    out.push({ topic: 'oc', q: `Has the completion date of ${shown} passed?`, a: 'Yes. Ask the builder for the occupancy certificate (OC) before you book.' })
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

/** 3D drawings of a project's checked floor plans (backend areastats/plans3d.py); rooms as the plan prints them */
export interface Plans3D {
  items: { url: string; width: number | null; height: number | null; label: string; title: string | null; site: string | null;
    kind: string | null; rooms: { name: string; sqft: number | null; dims: string | null }[] }[]
}

/** A rounded asking band (backend areastats/priceidea.py): never a site's own figure */
export interface PriceBand { bhk: string; low: number; high: number; projects: number }

/** "Price idea": sizes only one site prices, rounded and checked against the area, and the area's usual band per size */
export interface PriceIdea {
  place: string | null
  read_at: string | null
  rows: { bhk: string; low: number; high: number }[]
  area: PriceBand[]
}

export interface ProjectPrices {
  read_at: string | null
  /** url only for the builder's own site: property sites are named, not linked */
  /** sqft: the size the lowest price is for, when the site's line states it (carpet or saleable: sites differ) */
  /** per_sqft: ₹ per sq ft of the lowest price when its sqft is known (rounded) */
  rows: { bhk: string; from_inr: number; to_inr: number | null; official: boolean; sqft?: number | null; per_sqft?: number | null;
    sources: { site: string; url: string | null }[] }[]
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
  /** for the home finder: each size's lowest published price, months the builder moved the filed date, the checked position */
  homes?: { bhk: string; from_inr: number }[]
  months_later?: number | null
  map?: { lat: number; lon: number } | null
  /** the card's picture: the builder's or the brochure's (never copied from another site, never an AI drawing) */
  photo?: string | null
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

/** The register page of a MahaRERA number (any tower of a project), when it has one: a listing of that project shows it. */
export async function getRegisterProjectByRegno(regno: string | null | undefined): Promise<RegisterProject | null> {
  const n = regnoKey(regno)
  if (!/^P[A-Z0-9]{6,20}$/.test(n)) return null
  const r = await get<{ slug: string }>('/api/v1/public/register/by-regno/' + encodeURIComponent(n))
  return r.ok && r.data?.slug ? getRegisterProject(r.data.slug).catch(() => null) : null
}

/** The project page an agent's listing of this MahaRERA number shows and names as its canonical page: the number's register page
 *  (a tower merged into its project resolves to the project's page) when that page is in search; null otherwise or when it
 *  cannot be read. The listing page and the sitemap both decide with this, so the sitemap never lists a page naming another. */
export async function projectPageOfListing(regno: string | null | undefined): Promise<string | null> {
  const r = await getRegisterProjectByRegno(regno)
  return r?.indexable ? r.slug : null
}

/** A MahaRERA number as the register keys it. */
export const regnoKey = (regno: string | null | undefined): string => (regno || '').trim().toUpperCase()

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
  spellings?: string[]   // other spellings people search ("Lohgaon" for Lohegaon), never another place's name
  projects: number
  indexable: number
  current?: number       // being built or finished within a year: the rest are older projects, listed at the bottom of the page
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
  return [r.promoter ? `by ${readableName(r.promoter)}` : null, r.completion_now ? `possession ${monthYear(r.completion_now)}` : null,
    r.units_total ? (r.units_booked != null ? `${r.units_booked}/${r.units_total} booked` : `${r.units_total} homes`) : null].filter(Boolean).join(' · ')
}

/** The area name a project page shows: our locality, else the Pune place it is filed under. */
export function areaName(p: RegisterProject): string | null {
  return p.area?.name ?? p.pune_place?.name ?? p.place ?? null
}

const BHK_ROW = /^(\d+(?:\.\d+)?)\s*BHK$/i

/** A price row's name as a buyer reads it: "2 BHK" stays; the sites' "All homes" (a price not given per size) is "Homes". */
export function priceRowLabel(bhk: string): string {
  return /^all homes$/i.test(bhk.trim()) ? 'Homes' : bhk
}

/** The asked prices we publish (backend areastats/prices.py) in words: per home size, the lowest price, the sites. Null when none.
 *  `bhks` names only the rows that are a BHK size ("3, 4 BHK"); an "All homes" or "Plot" row is not one, so `bhks` is "" when no
 *  row is (a page once read "All homes BHK from ₹1.99 Cr"). A row's `text` reads "2 BHK: ₹69 L to ₹80 L", or "Homes from ₹1.99 Cr". */
export function askedPrices(p: Pick<RegisterProject, 'prices'>): { rows: { bhk: string; range: string; text: string }[]; from: string; bhks: string; sites: string; on: string | null } | null {
  const rows = (p.prices?.rows ?? []).filter((r) => r.from_inr > 0)
  if (!rows.length) return null
  const lowest = Math.min(...rows.map((r) => r.from_inr))
  const sites = Array.from(new Set(rows.flatMap((r) => r.sources.map((s) => s.site)))).slice(0, 3)
  const sized = Array.from(new Set(rows.map((r) => BHK_ROW.exec(r.bhk.trim())?.[1]).filter(Boolean)))
  return {
    rows: rows.map((r) => {
      const range = formatPrice(r.from_inr) + (r.to_inr && r.to_inr !== r.from_inr ? ` to ${formatPrice(r.to_inr)}` : '')
      return { bhk: r.bhk, range, text: BHK_ROW.test(r.bhk.trim()) ? `${r.bhk}: ${range}` : `${priceRowLabel(r.bhk)} from ${range}` }
    }),
    from: formatPrice(lowest),
    bhks: sized.length ? sized.join(', ') + ' BHK' : '',
    sites: sites.join(' and '),
    on: p.prices?.read_at ?? null,
  }
}

/** Whole months from one filed date to another ("2030-10-31" to "2031-02-28" is 4: a month end stays a month end); null when the
 *  days do not line up, so a move of 4 months and 10 days is never taken for the 4-month extension. */
export function monthsApart(from: string | null | undefined, to: string | null | undefined): number | null {
  const a = /^(\d{4})-(\d{2})-(\d{2})/.exec(from || '')
  const b = /^(\d{4})-(\d{2})-(\d{2})/.exec(to || '')
  if (!a || !b) return null
  const [ya, ma, da] = [Number(a[1]), Number(a[2]), Number(a[3])]
  const [yb, mb, db] = [Number(b[1]), Number(b[2]), Number(b[3])]
  const lastDay = (y: number, m: number) => new Date(Date.UTC(y, m, 0)).getUTCDate()
  const aligned = da === db || (db === lastDay(yb, mb) && da >= db) || (da === lastDay(ya, ma) && db === lastDay(yb, mb))
  return aligned ? (yb - ya) * 12 + (mb - ma) : null
}

/** Whether the only change to a filed completion date is MahaRERA's August 2026 blanket extension. The backend says so
 *  (`extension_only`); a page read before it did falls back to the dates: they differ by exactly the extension's months. */
export function isExtensionOnly(at: string | null | undefined, now: string | null | undefined, extensionMonths?: number | null,
  flag?: boolean | null): boolean {
  if (!at || !now || at === now) return false
  if (flag != null) return flag
  return !!extensionMonths && monthsApart(at, now) === extensionMonths
}

/** "The completion date filed with MahaRERA is 28 Feb 2031; MahaRERA's August 2026 order added 4 months to it (the builder has not
 *  moved it)." The extension is the regulator's, for most projects at once, so it is never worded as the builder moving the date. */
export function extensionSentence(now: string, months: number | null): string {
  return `The completion date filed with MahaRERA is ${longDay(now)}; MahaRERA's August 2026 order `
    + (months ? `added ${months} month${months === 1 ? '' : 's'} to it` : 'extended it') + ' (the builder has not moved it).'
}

/** How the filed completion date changed since registration: the 'same', only MahaRERA's 2026 'extension', or 'moved' by the
 *  builder (`extension`: the blanket extension's months inside that move). Null without a filed date; 'unknown' without the first. */
export type CompletionChange = { kind: 'unknown' } | { kind: 'same' } | { kind: 'extension'; from: string; months: number | null }
  | { kind: 'moved'; from: string; extension: number | null }

export function completionChange(p: Pick<RegisterProject, 'completion_now' | 'completion_at_registration' | 'details' | 'extension_only'>): CompletionChange | null {
  const now = p.completion_now
  const at = p.completion_at_registration
  if (!now) return null
  if (!at) return { kind: 'unknown' }
  if (at === now) return { kind: 'same' }
  const ext = p.details?.extension_months || null
  if (isExtensionOnly(at, now, ext, p.extension_only)) return { kind: 'extension', from: at, months: ext ?? monthsApart(at, now) }
  return { kind: 'moved', from: at, extension: ext }
}

/** The page heading's name: the one buyers know, with the phase when MahaRERA's name carries one and that name does not ("Park
 *  Eden" filed as "PARK EDEN PHASE I" is "Park Eden Phase I"), so two phases' pages do not read as one project. */
export function headingName(p: { name: string; marketed_name?: string | null; search_name?: string | null }): string {
  const shown = displayName(p)
  const m = /\b(?:phase|ph\.?)[\s-]*([ivx]+|\d+[a-z]?)\b/i.exec(p.name)
  if (!m || /\b(?:phase|ph\.?)(?:\b|\s|\d)/i.test(shown)) return shown
  return `${shown} Phase ${/^[ivx]+$/i.test(m[1]) ? m[1].toUpperCase() : m[1]}`
}

/** The agent's offer as kept on the property's fact sheet (propertyfacts public view): what campaign posts quote. */
export interface Offer {
  transaction?: string | null
  property_type?: string | null
  price_inr?: number | null
  plot_sqft?: number | null
  carpet_sqft?: number | null
  bhk?: number | null
  source?: string | null
  read_at?: string | null
  /** the live listing's price sheet: every home type with its size and price (a project listed with several) */
  homes?: { bhk: number; label: string; carpet_sqft?: number | null; price_inr?: number | null }[] | null
  payment_plan?: string | null
  /** the agent who lists it: the page names them, never with their number (owner 2026-10-31: enquiries come through us) */
  agent?: { slug: string; name: string; listing_id: string } | null
  /** the listing's photos (our /uploads copies), shown before the builder's */
  photos?: { url: string; width?: number | null; height?: number | null }[] | null
  /** the agent's sample-flat videos, played from their own website (only https .mp4 on it; propertyfacts listing_videos) */
  videos?: { url: string; label: string }[] | null
}

/** "2, 3 & 4 BHK" from a price sheet's home labels; "" when none is a BHK. */
export function bhkRange(homes: { label: string }[]): string {
  const nums = Array.from(new Set(homes.map((h) => h.label.replace(' BHK', '')).filter((x) => /^[\d.]+$/.test(x))))
  if (!nums.length) return ''
  return (nums.length > 1 ? `${nums.slice(0, -1).join(', ')} & ${nums[nums.length - 1]}` : nums[0]) + ' BHK'
}

/** The page's price when an agent's live sheet has one: the sheet is what the agent sells at today, so the portal prices are not
 *  shown beside it (a design review 2026-10-25 found ₹1.29 Cr in the hero and ₹1.2 Cr in the offer on one page). `from` is the
 *  offer's headline price, the one its all-in cost is worked out on. A rent is not a sale price: null, and the page keeps the portals'. */
export function offerPrice(o: Offer | null | undefined): { from: string; bhks: string; inr: number } | null {
  if (!o?.price_inr || o.price_inr <= 0 || o.transaction === 'rent') return null
  const sheet = o.homes && o.homes.length > 1 ? o.homes : null
  const bhks = sheet ? bhkRange(sheet) : o.bhk ? `${o.bhk} BHK` : /plot/i.test(o.property_type || '') ? 'Plot' : ''
  return { from: formatPrice(o.price_inr), bhks, inr: o.price_inr }
}

// The search title and description (registerTitle, registerDescription) live in projectSeo.ts with the page's structured data.
// No re-export here: projectSeo reads this module, and the cycle breaks the tests that mock it with requireActual.

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

/** The area page a search names ("kharadi", "2 bhk kharadi", "top projects wagholi"): shown above the projects. */
export interface PlaceMatch { path: string; label: string; place: string }

/** GET /api/v1/public/search/place: the area page the search names, or null (also on any failure). */
export async function searchPlace(q: string, signal?: AbortSignal): Promise<PlaceMatch | null> {
  const t = q.trim()
  if (t.length < 3) return null
  const server = typeof window === 'undefined'
  const base = server ? serverApiBase() : (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || '').replace(/\/+$/, '')
  try {
    const res = await fetch(`${base}/api/v1/public/search/place?q=${encodeURIComponent(t.slice(0, 80))}`,
      { headers: { Accept: 'application/json' }, signal, ...(server ? { next: { revalidate: 300 } } : {}) })
    if (!res.ok) return null
    const data = await res.json()
    return data && typeof data.path === 'string' && data.path.startsWith('/projects/area/') ? (data as PlaceMatch) : null
  } catch {
    return null
  }
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
