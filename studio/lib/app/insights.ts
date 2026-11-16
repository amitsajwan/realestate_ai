/** Owner SEO screen (/studio/seo): GET/POST /api/v1/newsroom/insights/* (backend/app/modules/areastats/owner.py; docs/plan/insights-and-seo.md O1 O2 O6). */
import { API_BASE_URL } from '@shared/config/api'
import { ApiError, parseErrorBody } from './api'
import { getToken } from './session'

export interface HotReason { signal: string; evidence: string; source: string }

export interface HotItem {
  regno: string
  name: string
  area: string | null
  page: string | null
  hot_score: number
  hot: boolean
  why: HotReason[]
  marketed_by: string[]
  enriched_at: string | null
  next_refresh: string | null
  refresh_waiting: boolean
}

export interface HotList { scored_at: string | null; projects: number | null; hot: number | null; hot_min: number; items: HotItem[] }

export type FoundState = 'searching' | 'missing' | 'found' | 'added'

export interface FoundItem {
  regno: string
  state: FoundState
  name: string | null
  first_seen: string | null
  last_seen: string | null
  tried_names: string[]
  seen: Array<{ title: string; link: string; query: string }>
}

export interface FoundList { counts: Partial<Record<FoundState, number>>; items: FoundItem[] }

export interface Loop {
  name: string
  state: 'ok' | 'error' | 'stale' | 'off'
  every_s: number | null
  last_ok_at: string | null
  last_error_at: string | null
  last_error: string | null
}

export interface SystemView {
  loops: Loop[]
  register: string[]
  marks: Record<string, string | null>
  serper_credits: number | null
  serper_per_day: number
  serper_split?: { name: string; per_day: number }[]   // what makes up serper_per_day, e.g. rank checks and prices
}

async function call<T>(path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/newsroom/insights/${path}`,
      body === undefined ? { headers } : { method: 'POST', headers, body: JSON.stringify(body) })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your internet.')
  }
  const data = await res.json().catch(() => null)
  if (!res.ok) throw parseErrorBody(data, res.status)
  return data as T
}

export const getHot = () => call<HotList>('hot')
export const refreshPage = (regno: string) => call<{ queued: boolean }>(`hot/${encodeURIComponent(regno)}/refresh`, {})
export const getFound = () => call<FoundList>('found')
export const getSystem = () => call<SystemView>('system')

// ---- Rankings (docs/plan/rank-loop.md R9; backend app/modules/seo/report.py) -------------------------------------------------
/** Project pages alone in the daily Google index check (seo.coverage.project_pages): an area's row mixes them with list pages. */
export interface ProjectIndex { listed: number; inspected: number; indexed: number; missing_by_state: Record<string, number> }

/** What the project pages in search hold (pages.content_counts). `full`: prices, web facts, highlights, photos and plans. */
export interface PageContent { pages: number; prices: number; facts: number; highlights: number; photos: number; plans: number; full: number; median_text: number }

export interface WeekNumbers { at: string; clicks: number; impressions: number; page_one: number; near_page_one: number; targeted: number; page_one_listed?: number; week?: WeekCounts }
export interface WeekCounts {
  clicks: number; clicks_before: number; clicks_listed: number; clicks_listed_before: number
  impressions: number; impressions_before: number; impressions_listed: number; impressions_listed_before: number
}

export interface FixResult {
  fix: string
  tried: number
  measured: number
  median_gain: number | null
  improved_pct: number | null
  reverted: number
  clicks_before: number
  clicks_after: number
}

export interface PageNumbers { position: number | null; impressions: number; clicks: number }

export interface RankAction {
  path: string
  fix: string
  at: string | null
  phrase: string | null
  note: string | null
  before: PageNumbers | null
  after14: PageNumbers | null
  after28: PageNumbers | null
  gain: number | null
  reverted: boolean
  new: string | null
}

export interface RankTarget {
  path: string
  name: string
  phrase: string
  impressions: number | null
  position: number | null
  page_position: number | null
  clicks: number | null
  history: { at: string | null; position: number | null }[]
  page_fix_at: string | null
  page_fix: string | null
  checked_at: string | null
  our_rank: number | null
  above: string[]
}


/** source: 'search_console' (Search Console impressions) or 'searched' (our own Google search, where we are absent or below 20). */
export interface RankGap { phrase: string; impressions: number; position: number | null; rising: boolean; page: string | null; shown_pages: string[]; action: string; source?: 'search_console' | 'searched'; area?: string | null }

export interface BoardRow { query: string; kind: string | null; area?: string | null; page?: string | null; at: string | null; ours: number | null; magicbricks: number | null; acres99: number | null; housing: number | null }

/** One kind of search on the board (backend seo/scoreboard.counts): `ahead` is both showing and us higher. */
export interface BoardKind { searches: number; ours: number; magicbricks: number; both: number; ahead: number; only_us: number; only_mb: number }

export interface BoardWeek { at: string | null; searches: number; ours: number; magicbricks: number; above_mb: number; above_mb_when_shown: number; both?: number; buyer_only?: boolean }

/** A site in the same Google results (backend seo/scoreboard.leaders): how often it showed above us, or showed when we did not. */
export interface BoardLeader { site: string; searches: number; above_us: number; top3: number }

/** Our own line in the same results (backend seo/scoreboard.standing): `place` is among every site seen, by searches shown in. */
export interface BoardStanding { site: string; searches: number; shows: number; top3: number; first: number; place: number; sites: number }
export interface Scoreboard extends BoardWeek { next: BoardRow[]; won: BoardRow[]; history: BoardWeek[]; ahead_rows?: BoardRow[]; behind_rows?: BoardRow[]; by_kind?: Record<string, BoardKind>; leaders?: BoardLeader[]; area_leaders?: Record<string, BoardLeader[]>; us?: BoardStanding | null; area_us?: Record<string, BoardStanding> }

/** One project on several pages (backend seo/splits.py). state: the web proved it (it merges by itself), a number still waits its
 * daily search, or everything was searched and only the owner can say. `searches`: searches that showed these pages together. */
export interface SplitProject {
  name: string
  where: string
  ours: boolean
  why: string
  homes: number
  state: 'proved' | 'waiting' | 'no_proof'
  hint: string | null
  impressions: number
  searches: { phrase: string; impressions: number; position: number | null }[]
  members: { regno: string; name: string; slug: string; impressions: number; in_search: boolean }[]
}
export interface SplitDecided { decision: 'same' | 'apart'; name: string; regnos: string[] }
export interface SplitView { total: number; proved: number; waiting: number; no_proof: number; items: SplitProject[]; decided: SplitDecided[] }
/** A search showing several of our pages that needs no decision, and why (seo/splits.explain). */
export type CompetingKind = 'project_and_list' | 'lists' | 'different'
export interface CompetingSearch { phrase: string; impressions: number; position: number | null; kind: CompetingKind; pages: { path: string; kind: string; label: string }[] }

export interface Rankings {
  week: { now: WeekNumbers | null; week_ago: WeekNumbers | null }
  targets_at: string | null
  doctor: { at: string | null; treated: { path: string; fix: string; reason: string }[]; menu: string[]; results: FixResult[] }
  actions: RankAction[]
  targets: RankTarget[]
  conflicts: { at: string | null; total: number; items: CompetingSearch[] }
  gaps: { at: string | null; total: number; items: RankGap[] }
  scoreboard?: Scoreboard
  split?: SplitView
  request_indexing?: { url: string; state: string | null; why: string }[]
  coverage?: { at: string | null; by_sitemap: { sitemap: string; listed: number; inspected: number; indexed: number }[]; projects?: ProjectIndex | null; content?: PageContent }
  ai?: AiVisits
  page_check?: PageCheck
}

/** The daily check of finished pages against their sources (backend seo/review.py). */
export interface PageCheck {
  at: string | null
  read: number
  flagged: number
  model: number
  week: number
  week_flagged: number
  items: { slug: string; name: string | null; url: string | null; at: string; problems: { kind: string; detail: string; quote?: string; source?: string }[] }[]
}

/** AI search (backend seo/aivisits.py): AI fetchers that read our pages and visits from AI answers, by day. */
export interface AiVisits {
  days: number
  since: string
  agents: { group: 'answer' | 'referral' | 'search' | 'training'; agent: string; week: number; total: number; kinds: Record<string, number> }[]
  answer_pages: { path: string; count: number }[]
  referral_pages: { path: string; count: number }[]
  totals: Record<string, number>
}

export const getRankings = () => call<Rankings>('rankings')
export const revertPage = (path: string) => call<{ reverted: number }>('rankings/revert', { path })
export const decideSplit = (regnos: string[], decision: 'same' | 'apart' | 'undo') => call<{ decision: string }>('rankings/split', { regnos, decision })

// ---- Pages that grow from searches (docs/plan/area-intent-pages.md 11.7; backend app/modules/seo/grow.py) ------------------------
export type GrownStatus = 'candidate' | 'live' | 'held' | 'never'

export interface GrownGate { ok?: boolean; demand?: boolean; supply?: boolean; distinct?: boolean; overlap?: number; overlaps_with?: string | null; projects?: number }

export interface GrownPage {
  key: string
  path: string
  status: GrownStatus
  source: 'seed' | 'search'
  kind: string
  count: number | null
  phrases: string[]
  demand: { impressions?: number; sources?: string[] }
  gate: GrownGate
  created_at: string | null
  live_at: string | null
}

export interface WordCount { word: string; impressions: number; phrases: string[] }

export interface GrownPages {
  at: string | null
  enabled: boolean
  last: { made?: number; waiting?: number; attached?: number; autocomplete?: number; budget?: number }
  counts: Record<GrownStatus, number>
  live: GrownPage[]
  waiting: GrownPage[]
  never: GrownPage[]
  unknown: WordCount[]
  gaps: WordCount[]
  existing: { path: string; impressions: number; phrases: string[] }[]
  /** the prices round (backend areastats/pricing.py): per area, projects being sold and how many show a price */
  prices?: { at: string | null; searches: number; coverage: { place: string; selling: number; priced: number; none_found: number; waiting: number }[] }
}

export const getGrownPages = () => call<GrownPages>('pages')
export const setPageStatus = (key: string, status: 'live' | 'held' | 'never') => call<{ status: string }>('pages/status', { key, status })
