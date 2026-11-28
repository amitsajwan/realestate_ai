/**
 * The words and structured data of the research pages (docs/plan/pune-intelligence.md C): a place's /schools, /commute and
 * /rent pages, the work hub pages, and the "Around <project>" blocks. Every sentence is built here from the numbers the
 * backend measured (lib/site/research.ts), never written by a model, and says where they come from and when they were read.
 */
import { fitDescription, fitTitle, groupIndian } from './format'
import { longDay, monthYear } from './register'
import type { Board, CommuteBlock, HubCard, HubPage, PlaceResearch, RentBlock, ResearchKind, ResearchPageRow, SchoolsBlock, Source } from './research'
import { HUBS_PATH, hubPath, researchPath } from './research'

/** Google shows about 65 characters of a title on a phone (seo-system.md section 5). */
export const RESEARCH_TITLE_MAX = 65

export const rupees = (n: number) => '₹' + groupIndian(n)
export const minutes = ([lo, hi]: [number, number]) => (lo === hi ? `${lo} min` : `${lo}-${hi} min`)
export const kmText = (x: number) => `${Number.isInteger(x) ? x : x.toFixed(1)} km`

const MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
/** "2026-11" -> "November 2026"; "Nov 2026" with `short`. */
export function monthLabel(ym: string, short = false): string {
  const m = /^(\d{4})-(\d{2})/.exec(ym || '')
  if (!m) return ''
  return short ? monthYear(`${m[1]}-${m[2]}-01`) : `${MONTHS_LONG[Number(m[2]) - 1]} ${m[1]}`
}

/** "CBSE, ICSE and State board": the boards with schools here, in a fixed order. ISC is CISCE's Class 12, so it reads as ICSE. */
const BOARD_ORDER: Board[] = ['CBSE', 'ICSE', 'State', 'IB', 'IGCSE']
export function boardsOf(b: SchoolsBlock): Board[] {
  const by = b.total_within_km?.by_board ?? {}
  const has = new Set<Board>((Object.keys(by) as Board[]).filter((k) => (by[k] ?? 0) > 0).map((k) => (k === 'ISC' ? 'ICSE' : k)))
  if (!has.size) for (const s of b.schools) has.add(s.board === 'ISC' ? 'ICSE' : s.board)
  return BOARD_ORDER.filter((x) => has.has(x))
}
export const boardLabel = (x: Board) => (x === 'State' ? 'State board' : x)
export function andList(xs: string[]): string {
  return xs.length <= 1 ? xs.join('') : `${xs.slice(0, -1).join(', ')} and ${xs[xs.length - 1]}`
}
function boardWords(boards: Board[]): string {
  // "CBSE, ICSE and State board schools": with State last, the word "board" once at the end
  return boards[boards.length - 1] === 'State' ? `${andList(boards)} board` : andList(boards.map(boardLabel))
}
const schoolCount = (b: SchoolsBlock) => b.total_within_km?.count || b.schools.length

/** "1, 2 and 3 BHK" from the rent rows. */
export function bhkWords(b: RentBlock): string {
  const sizes = b.rows.map((r) => r.bhk.replace(/\s*BHK$/i, '').trim()).filter(Boolean)
  return sizes.length ? `${andList(sizes)} BHK` : 'flat'
}
export const rentListings = (b: RentBlock) => b.rows.reduce((n, r) => n + (r.listings || 0), 0)

/** The words for where a measure starts: the project's own map pin, else the place's centre. */
export const measuredFrom = (pinned: boolean, placeName: string) => (pinned ? "from the project's pin" : `from the ${placeName} centre`)

// ---- the place sub-pages ----

export interface ResearchHead { h1: string; title: string; description: string; answer: string; crumb: string }

export function schoolsHead(place: string, b: SchoolsBlock): ResearchHead {
  const n = schoolCount(b)
  const boards = boardsOf(b)
  const within = b.total_within_km?.km
  const h1 = `Schools in ${place}, Pune: ${n} ${boards.length ? boardWords(boards) + ' ' : ''}school${n === 1 ? '' : 's'}`
  const title = fitTitle([h1, `Schools in ${place}, Pune: ${n} by board, with distances`, `Schools in ${place}, Pune: ${n} schools`, `Schools in ${place}, Pune`], RESEARCH_TITLE_MAX)
  const by = b.total_within_km?.by_board ?? {}
  const counts = boards.map((x) => {
    const c = x === 'ICSE' ? (by.ICSE ?? 0) + (by.ISC ?? 0) : (by[x] ?? 0)
    return c ? `${c} ${boardLabel(x)}` : ''
  }).filter(Boolean)
  const near = [...b.schools].sort((a, c) => a.km - c.km)[0]
  const answer = [
    `There ${n === 1 ? 'is' : 'are'} ${n} school${n === 1 ? '' : 's'}${within ? ` within ${kmText(within)}` : ''} of the ${place} centre${counts.length ? `: ${andList(counts)}` : ''}.`,
    near ? `The nearest is ${near.name} (${boardLabel(near.board)}${near.level ? `, ${near.level.toLowerCase()}` : ''}), ${kmText(near.km)} away.` : '',
    `From the boards' own lists of affiliated schools, read ${longDay(b.updated)}.`,
  ].filter(Boolean).join(' ')
  const description = fitDescription((has) => `${n} schools in ${place}, Pune${counts.length && has(1) ? ` (${andList(counts)})` : ''}: board, classes and distance from the ${place} centre${has(2) ? ", from the boards' official lists" : ''}. Updated ${longDay(b.updated)}.`)
  return { h1, title, description, answer, crumb: 'Schools' }
}

export function commuteHead(place: string, b: CommuteBlock, pinned = false): ResearchHead {
  const hubs = b.rows.map((r) => r.hub)
  const to = (k: number) => `Commute from ${place}: drive times to ${hubs.slice(0, k).join(', ')}`
  const h1 = hubs.length ? to(Math.min(3, hubs.length)) : `Commute from ${place}: drive times`
  const title = fitTitle([h1, ...(hubs.length > 1 ? [to(2)] : []), ...(hubs.length ? [to(1)] : []), `Commute from ${place}, Pune: drive times at 9 am and 6 pm`, `Commute from ${place}, Pune`], RESEARCH_TITLE_MAX)
  const from = measuredFrom(pinned, place)
  const lines = b.rows.slice(0, 3).map((r) => `${r.hub} is ${kmText(r.km)} by road: ${minutes(r.am)} at 9 am and ${minutes(r.pm)} back at 6 pm`)
  const answer = lines.length
    ? `Driving ${from} on a weekday, ${lines.join('; ')}. Google's typical traffic, measured ${longDay(b.updated)}.`
    : ''
  const description = fitDescription((has) => `Drive times from ${place}, Pune to ${andList(hubs.slice(0, has(1) ? 4 : 2))} at 9 am and 6 pm on a weekday${has(2) ? ", Google's typical traffic" : ''}. Measured ${longDay(b.updated)}.`)
  return { h1, title, description, answer, crumb: 'Commute' }
}

export function rentHead(place: string, b: RentBlock): ResearchHead {
  const month = monthLabel(b.month, true)
  const sizes = bhkWords(b)
  const h1 = `Rent in ${place}, Pune (${month}): ${sizes} asked rent`
  const title = fitTitle([h1, `Rent in ${place}, Pune (${month}): ${sizes}`, `Rent in ${place}, Pune (${month})`, `Rent in ${place}, Pune`], RESEARCH_TITLE_MAX)
  const lines = b.rows.map((r) => `a ${r.bhk} ${rupees(r.low)} to ${rupees(r.high)} a month (middle ${rupees(r.median)}, ${r.listings} listings)`)
  const answer = lines.length
    ? `Asked rent in ${place} in ${monthLabel(b.month)}: ${andList(lines)}. These are what owners ask on rental listings, not what tenants pay; from ${rentListings(b)} listings.`
    : ''
  const two = b.rows.find((r) => /^2\b/.test(r.bhk)) ?? b.rows[0]
  const description = fitDescription((has) => `Asked rent in ${place}, Pune for ${sizes} flats, ${monthLabel(b.month)}${two ? `: ${two.bhk} ${rupees(two.low)} to ${rupees(two.high)} a month` : ''}${has(1) ? `, from ${rentListings(b)} listings` : ''}${has(2) ? '. Range, middle and yield' : ''}.`)
  return { h1, title, description, answer, crumb: 'Rent' }
}

export function researchHead(kind: ResearchKind, place: string, r: PlaceResearch): ResearchHead | null {
  const b = r.blocks
  if (kind === 'schools') return b.schools?.schools?.length ? schoolsHead(place, b.schools) : null
  if (kind === 'commute') return b.commute?.rows?.length ? commuteHead(place, b.commute) : null
  return b.rent?.rows?.length ? rentHead(place, b.rent) : null
}

/** A sub-page is in search only when the backend says it has enough (`pages.<kind>`); otherwise it is up for visitors, noindex. */
export const researchIndexable = (kind: ResearchKind, r: PlaceResearch) => r.pages?.[kind] === true

// ---- structured data ----

const org = (siteUrl: string) => ({ '@type': 'Organization', name: 'Avasetu', url: siteUrl })
const placeLd = (place: string) => ({ '@type': 'Place', name: `${place}, Pune`, containedInPlace: { '@type': 'City', name: 'Pune' } })

/** Schools as an ItemList of School (an EducationalOrganization) with name and address: what the page lists, nothing more. */
export function schoolsJsonLd(siteUrl: string, path: string, h1: string, place: string, b: SchoolsBlock): Record<string, unknown> {
  return {
    '@context': 'https://schema.org', '@type': 'ItemList', name: h1, url: siteUrl + path, numberOfItems: b.schools.length,
    itemListElement: b.schools.map((s, i) => ({
      '@type': 'ListItem', position: i + 1,
      item: { '@type': 'School', name: s.name, address: s.address || `${place}, Pune`, ...(s.website ? { url: s.website } : {}) },
    })),
  }
}

/** Drive times as an Article dated by the measure: there is no richer type for a table of travel times. */
export function commuteJsonLd(siteUrl: string, path: string, head: ResearchHead, place: string, b: CommuteBlock): Record<string, unknown> {
  return {
    '@context': 'https://schema.org', '@type': 'Article', headline: head.h1.slice(0, 110), description: head.description,
    inLanguage: 'en-IN', mainEntityOfPage: siteUrl + path, dateModified: b.updated, about: placeLd(place),
    author: org(siteUrl), publisher: org(siteUrl), isAccessibleForFree: true,
  }
}

/** Asked rent as a Dataset: a table of measured numbers for one place and one month, which is what Google's Dataset data
 *  describes (it reads name, description, temporal and spatial coverage, the creator and the variables measured). */
export function rentJsonLd(siteUrl: string, path: string, head: ResearchHead, place: string, b: RentBlock): Record<string, unknown> {
  return {
    '@context': 'https://schema.org', '@type': 'Dataset', name: head.h1, description: head.answer || head.description,
    url: siteUrl + path, dateModified: b.updated, temporalCoverage: b.month, spatialCoverage: placeLd(place),
    creator: org(siteUrl), isAccessibleForFree: true,
    variableMeasured: ['Asked monthly rent, 25th percentile (INR)', 'Asked monthly rent, median (INR)', 'Asked monthly rent, 75th percentile (INR)', 'Listings counted'],
    ...(b.sources.length ? { isBasedOn: b.sources.filter((s) => s.url).map((s) => s.url) } : {}),
  }
}

/** A work hub as a Place in Pune, with the companies the page names as its tenants. */
export function hubJsonLd(siteUrl: string, h: HubPage, placeName: string): Record<string, unknown> {
  return {
    '@context': 'https://schema.org', '@type': 'Place', name: h.name, url: siteUrl + hubPath(h.slug), description: h.summary,
    containedInPlace: { '@type': 'Place', name: `${placeName}, Pune`, containedInPlace: { '@type': 'City', name: 'Pune' } },
  }
}

/** A hub page goes in search when the backend says so, else once it names three companies or has three places' drive times. */
export const hubIndexable = (h: HubPage) => h.page_ready ?? (h.companies.length >= 3 || h.commute_from.length >= 3)

export function hubHead(h: HubPage, placeName: string): { h1: string; title: string; description: string } {
  const h1 = `${h.name}, ${placeName}: companies, drive times and homes nearby`
  const title = fitTitle([`${h.name}, Pune: companies, drive times, homes nearby`, `${h.name}, Pune: companies and drive times`, `${h.name}, Pune`], RESEARCH_TITLE_MAX)
  const description = fitDescription((has) => `${h.name} in ${placeName}, Pune${h.companies.length ? `: ${h.companies.length} companies${has(2) ? ` including ${h.companies.slice(0, 2).join(' and ')}` : ''}` : ''}, drive times at 9 am and 6 pm${h.homes_nearby.length && has(1) ? `, ${h.homes_nearby.length} projects nearby` : ''}. Updated ${longDay(h.updated)}.`)
  return { h1, title, description }
}

// ---- sitemap ----

export interface ResearchSitemapEntry { group: string; path: string; date?: string }

/** The research pages for the sitemap: each place sub-page the backend lists as worth indexing, and the work hub pages. */
export function researchSitemap(pages: ResearchPageRow[], hubs: HubCard[]): ResearchSitemapEntry[] {
  const out: ResearchSitemapEntry[] = pages.map((r) => ({ group: 'area-' + r.place, path: researchPath(r.place, r.kind), date: r.updated }))
  const ready = hubs.filter((h) => h.ready !== false)
  if (ready.length) out.push({ group: 'core', path: HUBS_PATH }, ...ready.map((h) => ({ group: 'core', path: hubPath(h.slug), date: h.updated })))
  return out
}

// ---- small print ----

/** A block's sources, each named once, for its small print. */
export function uniqueSources(sources: Source[]): Source[] {
  const seen = new Set<string>()
  return sources.filter((s) => s.name && !seen.has(s.name) && seen.add(s.name))
}

// ---- nearby lists ----

/** Places of worship never go in a nearby list (owner 2026-11-28: no religion, caste or community on our pages). */
const WORSHIP = /\b(temple|mandir|mosque|masjid|dargah|church|chapel|cathedral|gurudwara|gurdwara|synagogue|monastery|vihar|place of worship|worship)\b/i
export function withoutPlacesOfWorship<T extends { label?: string; name?: string }>(items: T[]): T[] {
  // by the kind of place only: a hospital or school named after a saint is still a hospital or a school
  return items.filter((x) => !WORSHIP.test(x.label ?? ''))
}
