/**
 * The East Pune home plan (docs/plan/home-plan.md): six answers about a family become a short list of projects, each with the
 * facts that put it there and what to check before booking.
 *
 * East Pune only for now (owner 2026-10-31: "we have only projects we know much and sell in East Pune"). A buyer who works
 * elsewhere is not pushed east: they get the finder for their side of the city and a note that we cover it later.
 *
 * Code picks and code writes. Every reason is a stored fact (MahaRERA's record, a published asking price, a straight-line
 * distance) put into a fixed sentence; nothing is estimated and no model is asked. A partner agent's project is labelled with
 * whose it is but never scored up: the list is ranked on the facts alone. The answers live in the address like the finder's,
 * so the plan re-reads today's facts every time it is opened.
 */
import {
  BHKS, BUDGETS, MOVE_INS, bookedShare, matchingHomes, type BudgetKey, type FinderHome, type FinderItem, type MoveInKey,
} from './finder'
import { formatPrice } from './format'
import { monthYear } from './register'

/** Where the buyer works. The positions mirror backend/app/core/work_hubs.py (backend/tests/modules/areastats/test_home_plan_hubs.py
 *  keeps them equal); `east: false` hubs get the finder, not a plan. */
export const WORK = [
  { key: 'kharadi', label: 'Kharadi (EON IT Park, WTC)', hub: 'EON IT Park, Kharadi', lat: 18.5532, lon: 73.9497, east: true },
  { key: 'magarpatta', label: 'Magarpatta, Hadapsar', hub: 'Magarpatta City', lat: 18.5155, lon: 73.9280, east: true },
  { key: 'airport', label: 'Viman Nagar, Airport', hub: 'Pune Airport (Lohegaon)', lat: 18.5797, lon: 73.9089, east: true },
  { key: 'home', label: 'Work from home', east: true },
  { key: 'west', label: 'Hinjawadi, Baner, Wakad', area: 'hinjawadi', east: false },
  { key: 'elsewhere', label: 'Elsewhere in Pune', east: false },
] as const

export const KIDS = [
  { key: 'none', label: 'No children' },
  { key: 'young', label: 'Under 5' },
  { key: 'school', label: 'School-going' },
  { key: 'grown', label: 'College or older' },
] as const

export const ELDERS = [
  { key: '1', label: 'Yes' },
  { key: '0', label: 'No' },
] as const

export type WorkKey = (typeof WORK)[number]['key']
export type KidsKey = (typeof KIDS)[number]['key']

export interface PlanAnswers {
  work?: WorkKey
  budget?: BudgetKey
  bhk?: string
  /** unset: any possession date */
  movein?: MoveInKey
  kids?: KidsKey
  elders?: boolean
}

/** Past this a hub is nobody's daily commute (the project page's own cut-off, areastats/pagefacts.py COMMUTE_KM). */
export const COMMUTE_KM = 25
export const MAX_PICKS = 5
/** Fewer priced fits than this and projects with no published price for the size are added, marked as such. */
export const MIN_PICKS = 3

const one = (v: string | string[] | undefined): string => (Array.isArray(v) ? v[0] : v ?? '').trim().toLowerCase()

/** The address's answers; anything unknown is dropped, so an edited link still opens a page. */
export function parsePlan(sp: Record<string, string | string[] | undefined> | undefined | null): PlanAnswers {
  const s = sp || {}
  const a: PlanAnswers = {}
  const work = one(s.work)
  if (WORK.some((w) => w.key === work)) a.work = work as WorkKey
  const budget = one(s.budget)
  if (BUDGETS.some((b) => b.key === budget)) a.budget = budget as BudgetKey
  const bhk = one(s.bhk)
  if (BHKS.some((b) => b.key === bhk)) a.bhk = bhk
  const movein = one(s.movein)
  if (MOVE_INS.some((m) => m.key === movein)) a.movein = movein as MoveInKey
  const kids = one(s.kids)
  if (KIDS.some((k) => k.key === kids)) a.kids = kids as KidsKey
  const elders = one(s.elders)
  if (elders === '1' || elders === '0') a.elders = elders === '1'
  return a
}

export function toPlanSearch(a: PlanAnswers): string {
  const p = new URLSearchParams()
  if (a.work) p.set('work', a.work)
  if (a.budget) p.set('budget', a.budget)
  if (a.bhk) p.set('bhk', a.bhk)
  if (a.movein) p.set('movein', a.movein)
  if (a.kids) p.set('kids', a.kids)
  if (a.elders != null) p.set('elders', a.elders ? '1' : '0')
  const s = p.toString()
  return s ? '?' + s : ''
}

/** Work, budget and BHK are needed for a plan; the rest only change the order and the checklist. */
export function complete(a: PlanAnswers): boolean {
  return !!(a.work && a.budget && a.bhk)
}

export const workOf = (a: PlanAnswers) => WORK.find((w) => w.key === a.work)
export const isEast = (a: PlanAnswers) => workOf(a)?.east === true

/** The finder for a buyer we do not plan for (works outside East Pune): their side of the city, with their budget and BHK. */
export function finderLink(a: PlanAnswers): string {
  const w = workOf(a)
  const p = new URLSearchParams()
  if (w && 'area' in w) p.set('area', w.area)
  if (a.budget) p.set('budget', a.budget)
  if (a.bhk) p.set('bhk', a.bhk)
  if (a.movein) p.set('movein', a.movein)
  const s = p.toString()
  return '/projects' + (s ? '?' + s : '')
}

function kmBetween(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const r = (d: number) => (d * Math.PI) / 180
  const a = Math.sin(r(lat2 - lat1) / 2) ** 2 + Math.cos(r(lat1)) * Math.cos(r(lat2)) * Math.sin(r(lon2 - lon1) / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(a))
}

/** Whole months from `today` to a filed date ("2027-06" or "2027-06-30"); negative once it has passed. */
export function monthsUntil(today: string, date: string | null): number | null {
  const a = /^(\d{4})-(\d{2})/.exec(today)
  const b = /^(\d{4})-(\d{2})/.exec(date || '')
  if (!a || !b) return null
  return (Number(b[1]) - Number(a[1])) * 12 + (Number(b[2]) - Number(a[2]))
}

const bhkFits = (h: FinderHome, bhk: string) => h.bhk != null && (bhk === '4' ? h.bhk >= 4 : Math.floor(h.bhk) === Number(bhk))
const bhkLabel = (bhk: string) => BHKS.find((b) => b.key === bhk)?.label ?? `${bhk} BHK`

export interface PlanPick {
  item: FinderItem
  /** the cheapest home that fits the BHK and budget; null: no price published for that size (an unconfirmed pick) */
  home: FinderHome | null
  km: number | null
  score: number
  /** why it is on the list: facts, each in one sentence */
  reasons: string[]
  /** what the buyer should know or ask before booking */
  watch: string[]
}

/** Whether the project can be on the list at all, and if so whether a priced home confirms it fits. */
function fit(item: FinderItem, a: PlanAnswers): { home: FinderHome | null } | null {
  const bhk = a.bhk!
  const homes = matchingHomes(item, { bhk, budget: a.budget })
  if (homes.length) return { home: homes[0] }
  // a published price for this size that is outside the budget, or only other sizes on the sheet: it does not fit
  if (item.homes.some((h) => bhkFits(h, bhk) && h.price != null)) return null
  if (item.homes.length && item.homes.every((h) => h.bhk != null) && !item.homes.some((h) => bhkFits(h, bhk))) return null
  // sizes not published, and the lowest price already above the budget: it does not fit either
  const budget = BUDGETS.find((b) => b.key === a.budget)
  const lowest = Math.min(...item.homes.map((h) => h.price ?? Infinity))
  if (budget && lowest !== Infinity && lowest >= budget.max) return null
  return { home: null }
}

function inMoveIn(item: FinderItem, key?: MoveInKey): boolean {
  if (!key) return true
  const m = MOVE_INS.find((x) => x.key === key)!
  const d = item.possession ? item.possession.slice(0, 10) : null
  if (!d) return false
  return (!('from' in m) || d >= m.from) && (!('to' in m) || d <= m.to)
}

/**
 * The plan's projects, best first. `items` are East Pune projects still being sold (the page filters by place zone); `today`
 * is YYYY-MM-DD. Points, all from stored facts:
 *   commute (a hub, a checked position): up to 30, by straight-line km
 *   the MahaRERA completion date never moved: 20 (unknown: 5)
 *   homes booked: up to 15 (buyers have already committed here)
 *   possession soon: up to 20 when parents live with them, young children or a move-in by 2027; up to 10 otherwise
 * Priced fits come before unconfirmed ones; ties go by name, never by who lists it (the finder's rank puts agent-listed first).
 */
export function planHomes(items: FinderItem[], a: PlanAnswers, today: string): PlanPick[] {
  if (!complete(a) || !isEast(a)) return []
  const w = workOf(a)!
  const hub = 'lat' in w ? w : null
  const soonMatters = !!a.elders || a.kids === 'young' || a.movein === 'by-2027'
  const confirmed: PlanPick[] = []
  const unconfirmed: PlanPick[] = []
  for (const item of items) {
    const f = fit(item, a)
    if (!f || !inMoveIn(item, a.movein)) continue
    const km = hub && item.map ? Math.round(kmBetween(item.map.lat, item.map.lon, hub.lat, hub.lon) * 10) / 10 : null
    if (km != null && km > COMMUTE_KM) continue
    const reasons: string[] = []
    const watch: string[] = []
    let score = 0
    if (f.home?.price != null) {
      reasons.push(`${bhkLabel(a.bhk!)} from ${formatPrice(f.home.price)}, the asking price published online`)
    } else {
      watch.push(`No ${bhkLabel(a.bhk!)} price published yet: ask our team for today's price`)
    }
    if (hub) {
      if (km == null) {
        watch.push("We have not checked this project's position yet, so there is no distance to your office")
      } else {
        score += km <= 5 ? 30 : km <= 10 ? 22 : km <= 15 ? 12 : km <= 20 ? 5 : 0
        reasons.push(`${km} km from ${hub.hub} in a straight line`)
        if (km > 15) watch.push(`${km} km from ${hub.hub}: check the drive at office hours before you decide`)
      }
    }
    const when = monthYear(item.possession)
    if (item.monthsLater === 0) {
      score += 20
      if (when) reasons.push(`Completion date filed on MahaRERA: ${when}, never moved`)
    } else if (item.monthsLater == null) {
      score += 5
      if (when) reasons.push(`Completion date filed on MahaRERA: ${when}`)
    } else if (when) {
      watch.push(`The builder has moved the MahaRERA completion date ${item.monthsLater} months later, to ${when}`)
    }
    const share = bookedShare(item)
    if (share != null) {
      const pct = Math.round(share * 100)
      score += share >= 0.7 ? 15 : share >= 0.5 ? 10 : share >= 0.3 ? 5 : 0
      if (share >= 0.3) reasons.push(`${item.booked} of ${item.total} homes booked on MahaRERA (${pct}%)`)
      else watch.push(`${pct}% of homes booked so far: an early project, so look at the builder's past deliveries`)
    }
    const months = monthsUntil(today, item.possession)
    if (months != null) {
      if (months <= 0) watch.push('The filed completion date has passed: ask whether the occupancy certificate (OC) is issued')
      const top = soonMatters ? 20 : 10
      score += months <= 12 ? top : months <= 24 ? Math.round(top * 0.6) : months <= 36 ? Math.round(top * 0.25) : 0
      if (months > 0 && months <= 12) reasons.push('Due for completion within a year')
    }
    const pick = { item, home: f.home, km, score, reasons, watch }
    ;(f.home ? confirmed : unconfirmed).push(pick)
  }
  const order = (x: PlanPick, y: PlanPick) => y.score - x.score || x.item.name.localeCompare(y.item.name)
  const out = confirmed.sort(order).slice(0, MAX_PICKS)
  if (out.length < MIN_PICKS) out.push(...unconfirmed.sort(order).slice(0, MIN_PICKS - out.length))
  return out
}

/** What to check on the site visit, for this family. Always the paperwork; then what their answers make matter. */
export function checklist(a: PlanAnswers): string[] {
  const out = [
    'Match the MahaRERA number on the agreement with the project you visited',
    'Ask where the water comes from: the corporation line, a borewell or tankers',
  ]
  if (a.kids === 'school') out.push('Ask which schools run buses to the society, and time the school run in the morning')
  if (a.kids === 'young') out.push('Check that the play area and clubhouse are in the approved plan, not only the brochure')
  if (a.elders) out.push('Check the lifts have power backup, and how far the nearest hospital with an emergency ward is')
  if (a.movein === 'by-2027') out.push('For a ready home, ask to see the occupancy certificate (OC) before you pay a token')
  return out
}

/** The answers in words, for the plan's heading and the lead's message. */
export function describePlan(a: PlanAnswers): string {
  const kids = KIDS.find((k) => k.key === a.kids)
  return [
    workOf(a) ? `works: ${workOf(a)!.label}` : null,
    a.bhk ? bhkLabel(a.bhk) : null,
    a.budget ? BUDGETS.find((b) => b.key === a.budget)?.label : null,
    a.movein ? `move in: ${MOVE_INS.find((m) => m.key === a.movein)?.label}` : 'move in: any time',
    kids ? `children: ${kids.label.toLowerCase()}` : null,
    a.elders != null ? `parents living with them: ${a.elders ? 'yes' : 'no'}` : null,
  ].filter(Boolean).join('; ')
}

/** The enquiry that goes with a plan: the message the team reads in Studio, with the plan's link, and the stated BHK and budget. */
export function planInquiry(a: PlanAnswers, url: string): { message: string; bhk?: number; budget_min_inr?: number; budget_max_inr?: number | null } {
  const b = BUDGETS.find((x) => x.key === a.budget)
  return {
    message: `${isEast(a) ? 'East Pune home plan' : 'Home plan (outside East Pune)'}: ${describePlan(a)}. Plan: ${url}`.slice(0, 1000),
    ...(a.bhk ? { bhk: Number(a.bhk) } : {}),
    ...(b ? { budget_min_inr: b.min, budget_max_inr: b.max === Infinity ? null : b.max } : {}),
  }
}

export interface Nearby { label: string; name: string; km: number }

/** Which surroundings this family's answers make worth showing: schools for young or school-going children, hospitals for parents. */
export function nearbyWanted(a: PlanAnswers): string[] {
  return [...(a.kids === 'school' || a.kids === 'young' ? ['School'] : []), ...(a.elders ? ['Hospital'] : [])]
}

/** The nearest school (children under 5 or school-going) and hospital (parents at home) from a pick's stored surroundings
 *  (propertyfacts: OpenStreetMap, straight line from the project). Nothing when the family's answers do not ask for it. */
export function familyNearby(a: PlanAnswers, nearby: Nearby[] | null | undefined): string[] {
  const want = nearbyWanted(a)
  const out: string[] = []
  for (const label of want) {
    const best = (nearby ?? []).filter((n) => n.label === label && n.name && n.km != null).sort((x, y) => x.km - y.km)[0]
    if (best) out.push(`Nearest ${label.toLowerCase()}: ${best.name}, ${best.km} km in a straight line (OpenStreetMap)`)
  }
  return out
}

export const NEAR_KM = 10

export interface HubSummary {
  key: WorkKey
  hub: string
  /** East Pune projects being sold within NEAR_KM of the office, from a checked position */
  near: number
  /** of those, how many publish a price */
  priced: number
  /** the places most of them are in, most first (at most 3) */
  places: { name: string; count: number }[]
}

/** For each East Pune office: how many projects being sold are within NEAR_KM of it and where they are. The public page's
 *  dated facts, counted from the same items the plans pick from. */
export function hubSummaries(items: FinderItem[]): HubSummary[] {
  const out: HubSummary[] = []
  for (const w of WORK) {
    if (!('lat' in w)) continue
    const near = items.filter((i) => i.map && kmBetween(i.map.lat, i.map.lon, w.lat, w.lon) <= NEAR_KM)
    const byPlace = new Map<string, number>()
    for (const i of near) if (i.area) byPlace.set(i.area, (byPlace.get(i.area) ?? 0) + 1)
    out.push({
      key: w.key, hub: w.hub, near: near.length, priced: near.filter((i) => i.homes.some((h) => h.price != null)).length,
      places: [...byPlace].map(([name, count]) => ({ name, count })).sort((x, y) => y.count - x.count || x.name.localeCompare(y.name)).slice(0, 3),
    })
  }
  return out
}
