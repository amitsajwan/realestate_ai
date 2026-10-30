/**
 * The home finder: one set of rules for finding a home among projects, used by an agent's own site (their listings) and by
 * Avasetu's /projects (the MahaRERA register). Owner 2026-10-30: "a common framework".
 *
 * Buyers decide area -> budget -> BHK -> when they can move in, so those are the four questions, asked as taps. A filter shows
 * only when it splits the list (no Plot chip while every home is a flat). Budget and BHK match the price sheet's own rows,
 * not the project's lowest price: "3 BHK under 1.5 Cr" finds a project whose 3 BHK fits, and the card names that home. The
 * MahaRERA facts only we hold are filters too: the filed date has not moved, most homes booked. Every choice lives in the
 * address, so an agent can send "2 BHK in Wagholi under 1 Cr" as a link.
 */

export type HomeType = 'apartment' | 'villa' | 'plot' | 'commercial'

export interface FinderHome {
  bhk: number | null
  sqft?: number | null
  price: number | null
}

export interface FinderItem {
  id: string
  href: string
  name: string
  builder?: string | null
  area: string | null
  type: HomeType | null
  homes: FinderHome[]
  /** the completion date filed with MahaRERA (else the agent's), YYYY-MM or YYYY-MM-DD */
  possession: string | null
  /** months the builder moved the filed date later, net of MahaRERA's 2026 extension; null: unknown */
  monthsLater: number | null
  booked: number | null
  total: number | null
  video: boolean
  image?: string | null
  map?: { lat: number; lon: number } | null
  /** an agent sells it (Avasetu's list): their name */
  listedBy?: string | null
  /** default order: lower first (the page's own ranking) */
  rank?: number
}

export const BUDGETS = [
  { key: 'under-75l', label: 'Under ₹75 L', min: 0, max: 7_500_000 },
  { key: '75l-1cr', label: '₹75 L – 1 Cr', min: 7_500_000, max: 10_000_000 },
  { key: '1-1.5cr', label: '₹1 – 1.5 Cr', min: 10_000_000, max: 15_000_000 },
  { key: '1.5-2.5cr', label: '₹1.5 – 2.5 Cr', min: 15_000_000, max: 25_000_000 },
  { key: 'above-2.5cr', label: '₹2.5 Cr +', min: 25_000_000, max: Infinity },
] as const

export const BHKS = [
  { key: '1', label: '1 BHK' }, { key: '2', label: '2 BHK' }, { key: '3', label: '3 BHK' }, { key: '4', label: '4+ BHK' },
] as const

export const MOVE_INS = [
  { key: 'by-2027', label: 'Ready or by 2027', to: '2027-12-31' },
  { key: '2028-29', label: '2028 – 29', from: '2028-01-01', to: '2029-12-31' },
  { key: '2030-later', label: '2030 or later', from: '2030-01-01' },
] as const

export const TYPES: { key: HomeType; label: string }[] = [
  { key: 'apartment', label: 'Flats' }, { key: 'villa', label: 'Villas & houses' }, { key: 'plot', label: 'Plots' },
  { key: 'commercial', label: 'Shops & offices' },
]

export const SORTS = [
  { key: 'match', label: 'Best match' }, { key: 'price', label: 'Price: low to high' },
  { key: 'soonest', label: 'Possession: soonest' }, { key: 'booked', label: 'Most booked' },
] as const

export type BudgetKey = (typeof BUDGETS)[number]['key']
export type MoveInKey = (typeof MOVE_INS)[number]['key']
export type SortKey = (typeof SORTS)[number]['key']

export interface FinderQuery {
  area?: string            // an area's slug
  budget?: BudgetKey
  bhk?: string             // '1'..'4' (4 = 4 and more)
  movein?: MoveInKey
  type?: HomeType
  held?: boolean           // the filed date has not moved
  fast?: boolean           // half or more of the homes booked
  video?: boolean
  sort?: SortKey
  view?: 'map'
  compare?: string[]
  more?: number            // how many results are shown (paging without JavaScript)
}

export const PAGE = 24
export const MAX_COMPARE = 3

const one = (v: string | string[] | undefined): string => (Array.isArray(v) ? v[0] : v ?? '').trim().toLowerCase()

export function areaSlug(name: string | null | undefined): string {
  return (name || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

/** The address's ?area=&budget=… as a query; anything unknown is dropped, so a stale or edited link still opens a page. */
export function parseQuery(sp: Record<string, string | string[] | undefined> | undefined | null): FinderQuery {
  const s = sp || {}
  const q: FinderQuery = {}
  const area = one(s.area)
  if (/^[a-z0-9-]{2,40}$/.test(area)) q.area = area
  const budget = one(s.budget)
  if (BUDGETS.some((b) => b.key === budget)) q.budget = budget as BudgetKey
  const bhk = one(s.bhk)
  if (BHKS.some((b) => b.key === bhk)) q.bhk = bhk
  const movein = one(s.movein)
  if (MOVE_INS.some((m) => m.key === movein)) q.movein = movein as MoveInKey
  const type = one(s.type)
  if (TYPES.some((t) => t.key === type)) q.type = type as HomeType
  if (one(s.held) === '1') q.held = true
  if (one(s.fast) === '1') q.fast = true
  if (one(s.video) === '1') q.video = true
  const sort = one(s.sort)
  if (SORTS.some((x) => x.key === sort) && sort !== 'match') q.sort = sort as SortKey
  if (one(s.view) === 'map') q.view = 'map'
  const compare = one(s.compare).split(',').map((x) => x.trim()).filter((x) => /^[a-z0-9-]{1,64}$/.test(x))
  if (compare.length) q.compare = Array.from(new Set(compare)).slice(0, MAX_COMPARE)
  const more = parseInt(one(s.more), 10)
  if (more > PAGE && more <= 2000) q.more = more
  return q
}

/** The query as an address's search part ("?area=wagholi&bhk=2"), with `patch` applied; undefined/false removes a key. Paging
 *  restarts on any change but the compare list. */
export function toSearch(q: FinderQuery, patch: Partial<FinderQuery> = {}): string {
  const changed = Object.keys(patch).some((k) => k !== 'compare' && k !== 'more')
  const n: FinderQuery = { ...q, ...(changed ? { more: undefined } : {}), ...patch }
  const p = new URLSearchParams()
  if (n.area) p.set('area', n.area)
  if (n.budget) p.set('budget', n.budget)
  if (n.bhk) p.set('bhk', n.bhk)
  if (n.movein) p.set('movein', n.movein)
  if (n.type) p.set('type', n.type)
  if (n.held) p.set('held', '1')
  if (n.fast) p.set('fast', '1')
  if (n.video) p.set('video', '1')
  if (n.sort && n.sort !== 'match') p.set('sort', n.sort)
  if (n.view) p.set('view', n.view)
  if (n.compare?.length) p.set('compare', n.compare.join(','))
  if (n.more) p.set('more', String(n.more))
  const s = p.toString()
  return s ? '?' + s : '?'
}

/** Whether the buyer asked anything (paging, sort, view and the compare list are not questions). */
export function asked(q: FinderQuery): boolean {
  return !!(q.area || q.budget || q.bhk || q.movein || q.type || q.held || q.fast || q.video)
}

const bhkOk = (h: FinderHome, bhk?: string) =>
  !bhk || (h.bhk != null && (bhk === '4' ? h.bhk >= 4 : Math.floor(h.bhk) === Number(bhk)))
const budgetOk = (h: FinderHome, budget?: BudgetKey) => {
  if (!budget) return true
  const b = BUDGETS.find((x) => x.key === budget)!
  return h.price != null && h.price >= b.min && h.price < b.max
}

/** The item's homes that fit the BHK and budget asked, cheapest first. */
export function matchingHomes(item: FinderItem, q: Pick<FinderQuery, 'bhk' | 'budget'>): FinderHome[] {
  return item.homes.filter((h) => bhkOk(h, q.bhk) && budgetOk(h, q.budget))
    .sort((a, b) => (a.price ?? Infinity) - (b.price ?? Infinity))
}

const year = (d: string | null) => (d ? d.slice(0, 10) : null)
function moveInOk(item: FinderItem, key?: MoveInKey): boolean {
  if (!key) return true
  const m = MOVE_INS.find((x) => x.key === key)!
  const d = year(item.possession)
  if (!d) return false
  return (!('from' in m) || d >= m.from) && (!('to' in m) || d <= m.to)
}

export const bookedShare = (i: FinderItem): number | null => (i.booked != null && i.total ? i.booked / i.total : null)
const FAST = 0.5

type Dim = 'area' | 'budget' | 'bhk' | 'movein' | 'type' | 'held' | 'fast' | 'video'

function passes(i: FinderItem, q: FinderQuery): boolean {
  if (q.area && areaSlug(i.area) !== q.area) return false
  if (q.type && i.type !== q.type) return false
  if (!moveInOk(i, q.movein)) return false
  if (q.held && i.monthsLater !== 0) return false
  if (q.fast && !((bookedShare(i) ?? 0) >= FAST)) return false
  if (q.video && !i.video) return false
  if ((q.bhk || q.budget) && !matchingHomes(i, q).length) return false
  return true
}

/** The items that answer every question, in the order asked for. */
export function findHomes(items: FinderItem[], q: FinderQuery): FinderItem[] {
  return sortItems(items.filter((i) => passes(i, q)), q)
}

export function sortItems(items: FinderItem[], q: FinderQuery): FinderItem[] {
  const price = (i: FinderItem) => matchingHomes(i, q)[0]?.price ?? i.homes.find((h) => h.price != null)?.price ?? Infinity
  const by: Record<SortKey, (a: FinderItem, b: FinderItem) => number> = {
    match: (a, b) => (a.rank ?? 0) - (b.rank ?? 0),
    price: (a, b) => price(a) - price(b),
    soonest: (a, b) => (year(a.possession) ?? '9999').localeCompare(year(b.possession) ?? '9999'),
    booked: (a, b) => (bookedShare(b) ?? -1) - (bookedShare(a) ?? -1),
  }
  return [...items].sort((a, b) => by[q.sort ?? 'match'](a, b) || (a.rank ?? 0) - (b.rank ?? 0))
}

export interface Option { key: string; label: string; count: number; on: boolean }
export interface Facets {
  area: Option[]; budget: Option[]; bhk: Option[]; movein: Option[]; type: Option[]
  /** the MahaRERA and video switches, each only when some items have it and some do not */
  toggles: Option[]
}

/** Each question's choices with how many items each would give, counted with the other answers kept (a choice that gives
 *  nothing shows 0 and is not offered as a link). A question shows only when its choices split the whole list. */
export function facets(items: FinderItem[], q: FinderQuery): Facets {
  // the choice replaces this question's answer and keeps the others
  const count = (_dim: Dim, patch: Partial<FinderQuery>) => items.filter((i) => passes(i, { ...q, ...patch })).length
  const splits = (vals: (string | null)[]) => new Set(vals.filter(Boolean)).size > 1
  const areas = new Map<string, string>()
  for (const i of items) if (i.area) areas.set(areaSlug(i.area), i.area)
  const area = splits(items.map((i) => areaSlug(i.area) || null))
    ? [...areas].map(([key, label]) => ({ key, label, count: count('area', { area: key }), on: q.area === key }))
      .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
    : []
  const priced = items.filter((i) => i.homes.some((h) => h.price != null))
  const budget = priced.length > 1 ? BUDGETS.map((b) => ({ key: b.key, label: b.label, count: count('budget', { budget: b.key }), on: q.budget === b.key })) : []
  const bhks = items.flatMap((i) => i.homes.map((h) => (h.bhk == null ? null : String(Math.min(4, Math.floor(h.bhk))))))
  const bhk = splits(bhks) ? BHKS.map((b) => ({ key: b.key, label: b.label, count: count('bhk', { bhk: b.key }), on: q.bhk === b.key })) : []
  const dated = items.filter((i) => i.possession)
  const movein = dated.length > 1 ? MOVE_INS.map((m) => ({ key: m.key, label: m.label, count: count('movein', { movein: m.key }), on: q.movein === m.key })) : []
  const type = splits(items.map((i) => i.type)) ? TYPES.map((t) => ({ key: t.key, label: t.label, count: count('type', { type: t.key }), on: q.type === t.key }))
    .filter((t) => items.some((i) => i.type === t.key)) : []
  const toggle = (key: 'held' | 'fast' | 'video', label: string, has: (i: FinderItem) => boolean) => {
    const n = items.filter(has).length
    return n > 0 && n < items.length ? [{ key, label, count: count(key, { [key]: true }), on: !!q[key] }] : []
  }
  return {
    area, budget, bhk, movein, type,
    toggles: [
      ...toggle('held', 'Date not moved', (i) => i.monthsLater === 0),
      ...toggle('fast', 'Half or more booked', (i) => (bookedShare(i) ?? 0) >= FAST),
      ...toggle('video', 'Has a video', (i) => i.video),
    ],
  }
}

/** Items by area, biggest area first: the page with nothing asked. */
export function byArea(items: FinderItem[]): { area: string; slug: string; items: FinderItem[] }[] {
  const groups = new Map<string, FinderItem[]>()
  for (const i of items) {
    const a = i.area || 'Other'
    groups.set(a, [...(groups.get(a) ?? []), i])
  }
  return [...groups].map(([area, xs]) => ({ area, slug: areaSlug(area), items: sortItems(xs, {}) }))
    // biggest area first; between equals, the one holding the better-ranked project (agent-listed first on Avasetu's list)
    .sort((a, b) => b.items.length - a.items.length || (a.items[0].rank ?? 0) - (b.items[0].rank ?? 0) || a.area.localeCompare(b.area))
}

/** The question in words, for the empty state's enquiry and the page's heading: "3 BHK, ₹1 – 1.5 Cr, in Kharadi". */
export function describe(q: FinderQuery, areaName?: string | null): string {
  const parts = [
    q.type && q.type !== 'apartment' ? TYPES.find((t) => t.key === q.type)?.label : null,
    q.bhk ? BHKS.find((b) => b.key === q.bhk)?.label : null,
    q.budget ? BUDGETS.find((b) => b.key === q.budget)?.label : null,
    q.area ? `in ${areaName || q.area.replace(/-/g, ' ')}` : null,
    q.movein ? `possession ${MOVE_INS.find((m) => m.key === q.movein)?.label.toLowerCase()}` : null,
    q.held ? 'date not moved' : null, q.fast ? 'half or more booked' : null, q.video ? 'with a video' : null,
  ].filter(Boolean)
  return parts.join(', ')
}

/** "2 BHK" from a price row's label ("2 BHK", "2.5 BHK", "All homes", "Plot"). */
export function bhkOf(label: string | number | null | undefined): number | null {
  if (typeof label === 'number') return label
  const m = /(\d+(?:\.\d)?)\s*bhk/i.exec(label || '')
  return m ? Number(m[1]) : null
}
