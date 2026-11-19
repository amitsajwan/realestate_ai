/**
 * Demo data for the owner's screens that read the server directly (SEO, project pages, buyer radar, press, lead board), so demo
 * mode (`app_fixtures`) shows every screen instead of a server error, and they can be looked at and checked without a backend
 * (2026-11-19). Made-up projects and numbers in the shapes the server sends; nothing here is real. Changes live in memory only.
 */
import type { EnrichList, EnrichStatus } from './enrichment'
import type {
  AuditRow, AuditView, FoundList, GrownPages, HotList, Rankings, SystemView,
} from './insights'
import type { Board } from './leadBoard'
import type { PressPitch, PressStory, PressSummary } from './press'
import type { RadarDemand, RadarMetrics, RadarRuns, RadarSignal, RadarWatch } from './radar'

const ago = (hours: number) => new Date(Date.now() - hours * 3600_000).toISOString()
const days = (n: number) => ago(24 * n)

// ---- SEO (/api/v1/newsroom/insights/*) -------------------------------------------------------------------------------------

const PROJECTS = [
  { regno: 'P52100099001', name: 'Riverview Towers', area: 'kharadi', slug: 'riverview-towers-kharadi' },
  { regno: 'P52100099002', name: 'Green Meadows Phase 2', area: 'wagholi', slug: 'green-meadows-phase-2-wagholi' },
  { regno: 'P52100099003', name: 'Skyline Residency', area: 'upper_kharadi', slug: 'skyline-residency-upper-kharadi' },
  { regno: 'P52100099004', name: 'Lakeside Enclave', area: 'lohegaon', slug: 'lakeside-enclave-lohegaon' },
]

function rankings(): Rankings {
  const now = { at: days(1), clicks: 412, impressions: 18_640, page_one: 310, near_page_one: 96, targeted: 120, page_one_listed: 284,
    week: { clicks: 104, clicks_before: 92, clicks_listed: 88, clicks_listed_before: 80, impressions: 4_310, impressions_before: 4_020, impressions_listed: 3_900, impressions_listed_before: 3_610 } }
  const before = { at: days(8), clicks: 380, impressions: 17_200, page_one: 296, near_page_one: 101, targeted: 118 }
  return {
    week: { now, week_ago: before },
    targets_at: days(1),
    doctor: {
      at: ago(6), menu: ['title', 'faq', 'links', 'refresh'],
      treated: [{ path: '/projects/riverview-towers-kharadi', fix: 'faq', reason: 'just off page one for "riverview towers possession"' }],
      results: [
        { fix: 'faq', tried: 14, measured: 9, median_gain: 3, improved_pct: 67, reverted: 0, clicks_before: 12, clicks_after: 21 },
        { fix: 'title', tried: 11, measured: 7, median_gain: 1, improved_pct: 57, reverted: 1, clicks_before: 9, clicks_after: 11 },
        { fix: 'refresh', tried: 6, measured: 3, median_gain: null, improved_pct: null, reverted: 0, clicks_before: 2, clicks_after: 2 },
      ],
    },
    actions: PROJECTS.slice(0, 3).map((p, i) => ({
      path: `/projects/${p.slug}`, fix: ['faq', 'title', 'refresh'][i], at: days(3 + 6 * i), phrase: `${p.name.toLowerCase()} price`, note: null,
      before: { position: 14 - i, impressions: 120, clicks: 2 }, after14: { position: 9 - i, impressions: 160, clicks: 5 },
      after28: i === 2 ? { position: 9, impressions: 170, clicks: 6 } : null, gain: 5 - i, reverted: false, new: null,
    })),
    targets: PROJECTS.map((p, i) => ({
      path: `/projects/${p.slug}`, name: p.name, phrase: `${p.name.toLowerCase()} ${p.area.replace('_', ' ')}`, impressions: 340 - 60 * i,
      position: 6 + 3 * i, page_position: 7 + 3 * i, clicks: 14 - 3 * i, history: [{ at: days(14), position: 9 + 3 * i }, { at: days(1), position: 6 + 3 * i }],
      page_fix_at: i === 0 ? days(3) : null, page_fix: i === 0 ? 'faq' : null, checked_at: days(1), our_rank: i < 3 ? 4 + 2 * i : null,
      above: ['housing.com', 'magicbricks.com'].slice(0, i < 3 ? 1 + (i % 2) : 2),
    })),
    conflicts: { at: days(2), total: 1, items: [{ phrase: 'green meadows wagholi', impressions: 48, position: 8.4, kind: 'project_and_list',
      pages: [{ path: '/projects/area/wagholi', kind: 'area', label: 'Wagholi' }, { path: '/projects/green-meadows-phase-2-wagholi', kind: 'project', label: 'Green Meadows Phase 2' }] }] },
    gaps: { at: days(3), total: 2, items: [
      { phrase: 'ready to move flats in lohegaon', impressions: 90, position: 27, rising: true, page: '/projects/area/lohegaon/ready-to-move', shown_pages: [], action: 'Our page exists: link it from the Lohegaon page', source: 'search_console', area: 'lohegaon' },
      { phrase: 'plots in wagholi', impressions: 40, position: null, rising: false, page: null, shown_pages: [], action: 'Plots: not on MahaRERA, kept on the data-gaps list', source: 'searched', area: 'wagholi' },
    ] },
    scoreboard: {
      at: days(2), searches: 240, ours: 96, magicbricks: 150, above_mb: 41, above_mb_when_shown: 22, both: 58, buyer_only: true,
      by_kind: { area: { searches: 90, ours: 30, magicbricks: 80, both: 26, ahead: 8, only_us: 4, only_mb: 54 }, project: { searches: 150, ours: 66, magicbricks: 70, both: 32, ahead: 14, only_us: 34, only_mb: 38 } },
      ahead_rows: [{ query: 'riverview towers kharadi', kind: 'project', page: '/projects/riverview-towers-kharadi', at: days(2), ours: 2, magicbricks: 5, acres99: 7, housing: 3 }],
      behind_rows: [{ query: '2 bhk flats in wagholi', kind: 'area', page: '/projects/area/wagholi/2-bhk', at: days(2), ours: 9, magicbricks: 2, acres99: 4, housing: 1 }],
      next: [{ query: 'new projects in lohegaon', kind: 'area', page: '/projects/area/lohegaon', at: days(2), ours: 6, magicbricks: 4, acres99: null, housing: 2 }],
      won: [],
      history: [{ at: days(9), searches: 230, ours: 88, magicbricks: 146, above_mb: 37, above_mb_when_shown: 19, both: 55, buyer_only: true }],
      leaders: [{ site: 'housing.com', searches: 210, above_us: 150, top3: 120 }, { site: 'magicbricks.com', searches: 150, above_us: 98, top3: 80 }, { site: '99acres.com', searches: 140, above_us: 90, top3: 60 }],
      area_leaders: { wagholi: [{ site: 'housing.com', searches: 40, above_us: 30, top3: 25 }] },
      us: { site: 'avasetu.in', searches: 240, shows: 96, top3: 31, first: 9, place: 6, sites: 180 },
      area_us: { wagholi: { site: 'avasetu.in', searches: 40, shows: 14, top3: 4, first: 1, place: 7, sites: 60 } },
    },
    split: { total: 1, proved: 0, waiting: 0, no_proof: 1, decided: [], items: [{
      name: 'Green Meadows', where: '412207', ours: false, why: 'tower label', homes: 180, state: 'no_proof', hint: null, impressions: 22,
      searches: [{ phrase: 'green meadows phase 2 wagholi', impressions: 12, position: 9.1 }],
      members: [{ regno: 'P52100099002', name: 'Green Meadows Phase 2', slug: 'green-meadows-phase-2-wagholi', impressions: 18, in_search: true },
        { regno: 'P52100099005', name: 'Green Meadows Phase 3', slug: 'green-meadows-phase-3-wagholi', impressions: 4, in_search: false }],
    }] },
    request_indexing: [{ url: 'https://avasetu.in/projects/area/lohegaon', state: 'Discovered - currently not indexed', why: 'an area page in our 8 areas' }],
    coverage: {
      at: days(1),
      by_sitemap: [
        { sitemap: 'area-lohegaon', listed: 40, inspected: 40, indexed: 14 },
        { sitemap: 'area-wagholi', listed: 76, inspected: 70, indexed: 41 },
        { sitemap: 'area-kharadi', listed: 66, inspected: 66, indexed: 47 },
        { sitemap: 'core', listed: 25, inspected: 25, indexed: 23 },
      ],
      projects: { listed: 600, inspected: 590, indexed: 361, missing_by_state: { 'Discovered - currently not indexed': 140, 'Crawled - currently not indexed': 89 } },
      content: { pages: 361, prices: 210, facts: 300, highlights: 280, photos: 120, plans: 90, full: 70, median_text: 1450 },
    },
    ai: {
      days: 28, since: days(28),
      agents: [
        { group: 'answer', agent: 'ChatGPT-User', week: 31, total: 120, kinds: {} },
        { group: 'referral', agent: 'chatgpt.com', week: 6, total: 19, kinds: {} },
        { group: 'search', agent: 'OAI-SearchBot', week: 210, total: 880, kinds: {} },
        { group: 'search', agent: 'Googlebot', week: 1_420, total: 5_600, kinds: {} },
      ],
      answer_pages: [{ path: '/projects/area/kharadi/top', count: 9 }, { path: '/projects/riverview-towers-kharadi', count: 6 }],
      referral_pages: [{ path: '/projects/area/upper-kharadi', count: 4 }],
      totals: { answer: 120, referral: 19 },
    },
    page_check: {
      at: ago(5), read: 20, flagged: 2, model: 12, week: 140, week_flagged: 9,
      items: [{ slug: 'lakeside-enclave-lohegaon', name: 'Lakeside Enclave', url: 'https://avasetu.in/projects/lakeside-enclave-lohegaon', at: ago(5),
        problems: [{ kind: 'thin', detail: 'under 60 words of its own text' }] }],
    },
  }
}

const HOT: HotList = {
  scored_at: ago(3), projects: 420, hot: 2, hot_min: 60,
  items: PROJECTS.slice(0, 3).map((p, i) => ({
    regno: p.regno, name: p.name, area: p.area, page: `https://avasetu.in/projects/${p.slug}`, hot_score: 82 - 15 * i, hot: i < 2,
    why: [{ signal: i === 0 ? 'bookings' : 'search', evidence: i === 0 ? '18 homes booked in 90 days' : 'searches up 40% in 28 days', source: i === 0 ? 'MahaRERA' : 'Search Console' }],
    marketed_by: ['example-broker.in'], enriched_at: days(4 + i), next_refresh: days(-(10 - i)), refresh_waiting: false,
  })),
}

const FOUND: FoundList = {
  counts: { searching: 1, found: 1 },
  items: [
    { regno: 'P52100099010', state: 'searching', name: null, first_seen: days(2), last_seen: days(1), tried_names: [], seen: [{ title: 'New launch in Kharadi', link: 'https://example.com/kharadi', query: 'new launch kharadi' }] },
    { regno: 'P52100099011', state: 'found', name: 'Hillcrest Heights', first_seen: days(6), last_seen: days(2), tried_names: ['Hillcrest'], seen: [] },
  ],
}

const SYSTEM: SystemView = {
  loops: [
    { name: 'seo', state: 'ok', every_s: 1800, last_ok_at: ago(0.3), last_error_at: null, last_error: null },
    { name: 'project_enrich', state: 'ok', every_s: 180, last_ok_at: ago(0.05), last_error_at: ago(30), last_error: 'builder site timed out' },
    { name: 'newsroom', state: 'off', every_s: 7200, last_ok_at: null, last_error_at: null, last_error: null },
  ],
  register: ['MahaRERA register read 2 hours ago: 14,210 projects', 'Next full read tomorrow'],
  marks: { register: ago(2), coverage: days(1) },
  serper_credits: 1_840, serper_per_day: 29,
  serper_split: [{ name: 'Rank checks', per_day: 25 }, { name: 'Prices', per_day: 4 }],
}

const GROWN: GrownPages = {
  at: days(2), enabled: true, last: { made: 1, waiting: 2, autocomplete: 40, budget: 10 },
  counts: { live: 2, held: 0, candidate: 1, never: 0 },
  live: [
    { key: 'kharadi:top', path: '/projects/area/kharadi/top', status: 'live', source: 'seed', kind: 'top', count: 12, phrases: ['top projects in kharadi'], demand: { impressions: 220, sources: ['search_console'] }, gate: { ok: true }, created_at: days(30), live_at: days(28) },
    { key: 'wagholi:2-bhk', path: '/projects/area/wagholi/2-bhk', status: 'live', source: 'search', kind: 'bhk', count: 9, phrases: ['2 bhk flats in wagholi'], demand: { impressions: 160, sources: ['search_console', 'autocomplete'] }, gate: { ok: true }, created_at: days(20), live_at: days(19) },
  ],
  waiting: [{ key: 'lohegaon:ready-to-move', path: '/projects/area/lohegaon/ready-to-move', status: 'candidate', source: 'search', kind: 'ready', count: 2, phrases: ['ready to move flats in lohegaon'], demand: { impressions: 90 }, gate: { demand: true, supply: false, projects: 2 }, created_at: days(5), live_at: null }],
  never: [], unknown: [{ word: 'duplex', impressions: 14, phrases: ['duplex in kharadi'] }], gaps: [{ word: 'rent', impressions: 60, phrases: ['flats for rent in wagholi'] }],
  existing: [],
  prices: { at: ago(1), searches: 4, coverage: [{ place: 'kharadi', selling: 30, priced: 21, none_found: 5, waiting: 4 }, { place: 'wagholi', selling: 44, priced: 26, none_found: 8, waiting: 10 }] },
}

function audit(): AuditView {
  const row = (path: string, kind: string, bucket: string, action: string, clicks: number, impressions: number, position: number | null,
    before: number, top: string, state = 'Submitted and indexed'): AuditRow => ({
    path, kind, bucket, action, clicks, impressions, ctr: impressions ? Math.round((1000 * clicks) / impressions) / 1000 : null, position,
    impressions_before: before, trend: !before ? (impressions ? 'new' : '') : impressions >= before * 1.3 ? 'rising' : impressions <= before * 0.7 ? 'falling' : 'steady',
    index_state: state, in_sitemap: true, top_search: top, top_search_impressions: Math.round(impressions * 0.4),
  })
  const rows = [
    row('/projects/area/kharadi/top', 'area', 'low_ctr', 'On page one but rarely chosen: a title and description that answer the top search', 1, 640, 6.2, 520, 'top projects in kharadi'),
    row('/projects/riverview-towers-kharadi', 'project', 'earning', "Earns clicks: keep it steady, change it only through the doctor's measured fix", 21, 380, 4.1, 300, 'riverview towers kharadi'),
    row('/localities/wagholi', 'locality', 'near_page_one', "Just off page one: the doctor's queue; add the fact the top search asks for", 0, 120, 12.4, 140, 'living in wagholi'),
    row('/projects/lakeside-enclave-lohegaon', 'project', 'seen_far', 'Shown for searches it does not answer well: compare the page with its top search', 0, 60, 34, 20, 'lakeside enclave price'),
    row('/builders/example-developers', 'builder', 'indexed_silent', 'Indexed, never shown: merge (301) into the page that earns for the same search, or give it a fact nobody else has', 0, 0, null, 0, ''),
    row('/projects/area/lohegaon', 'area', 'not_indexed', 'Discovered - currently not indexed: not read yet; Request indexing and link it from a page that earns', 0, 0, null, 0, '', 'Discovered - currently not indexed'),
  ]
  const BUCKETS: [string, string][] = [['low_ctr', 'Page one, rarely clicked'], ['earning', 'Earning clicks'], ['near_page_one', 'Just off page one'],
    ['seen_far', 'Seen, ranked far'], ['too_few', 'Shown a little'], ['outside_sitemap', 'Out of the sitemap'], ['indexed_silent', 'Indexed, never shown'],
    ['not_indexed', 'Not indexed'], ['unchecked', 'Not checked yet']]
  const byKind: Record<string, Record<string, number>> = {}
  for (const r of rows) {
    const k = (byKind[r.kind] ??= { clicks: 0, impressions: 0 })
    k.clicks += r.clicks; k.impressions += r.impressions; k[r.bucket] = (k[r.bucket] ?? 0) + 1
  }
  return { configured: true, at: ago(2), error: null, pages: rows.length,
    buckets: BUCKETS.map(([key, label]) => ({ key, label, pages: rows.filter((r) => r.bucket === key).length })), by_kind: byKind, rows }
}

/** What GET/POST /newsroom/insights/<path> answers in demo mode. */
export function insightsFixture(path: string, body?: unknown): unknown {
  const p = path.split('?')[0]
  if (p === 'rankings') return rankings()
  if (p === 'rankings/revert') return { reverted: 1 }
  if (p === 'rankings/split') return { decision: (body as { decision?: string })?.decision ?? 'same' }
  if (p === 'hot') return HOT
  if (p.startsWith('hot/')) return { queued: true }
  if (p === 'found') return FOUND
  if (p === 'system') return SYSTEM
  if (p === 'pages') return GROWN
  if (p === 'pages/status') return { status: (body as { status?: string })?.status ?? 'live' }
  if (p === 'audit') return { ...audit(), at: path.includes('fresh') ? new Date().toISOString() : ago(2) }
  return {}
}

// ---- Project pages (/api/v1/newsroom/project-enrichment) ---------------------------------------------------------------------

export function enrichmentFixture(status?: EnrichStatus): EnrichList {
  const items = PROJECTS.map((p, i) => ({
    regno: p.regno, name: p.name, area: p.area, page: `https://avasetu.in/projects/${p.slug}`,
    status: (['ok', 'partial', 'ok', 'failed'] as EnrichStatus[])[i], enriched_at: days(2 + i), score: ['9/10', '6/10', '8/10', null][i],
    failed: i === 3 ? ['prices', 'web facts'] : i === 1 ? ['plans'] : [], checks: { prices: i === 3 ? null : 'builder site', plans: i === 1 ? null : 'brochure' },
    error: i === 3 ? 'builder site timed out' : null, fails: i === 3 ? 1 : 0,
  }))
  const counts = { ok: 2, partial: 1, failed: 1, parked: 0, waiting: 0, finished: 0 } as Record<EnrichStatus, number>
  return { counts, items: status ? items.filter((x) => x.status === status) : items }
}

// ---- Buyer radar (/api/v1/radar) --------------------------------------------------------------------------------------------

const SIGNALS: RadarSignal[] = [
  { id: 'rs1', source: 'reddit', url: 'https://reddit.com/r/pune/example1', text: 'Looking for a 2 BHK in Wagholi under 70 lakh, ready by next year. Any projects worth a visit?',
    context: 'r/pune', author: 'buyer_example', posted_at: ago(5), status: 'new', area: 'wagholi', score: 0.86, why: ['asks for a home', 'budget and area named'],
    matches: [{ listing_id: 'l2', title: '2 BHK near Baner Road', locality: 'Wagholi', bhk: 2, price_inr: 6_800_000 }],
    draft: 'Green Meadows Phase 2 in Wagholi lists 2 BHK homes with possession filed for Dec 2027 on MahaRERA; worth a look within your budget.',
    link: 'https://avasetu.in/projects/area/wagholi/2-bhk', intent: { role: 'buyer', intent: 0.9, stage: 'comparing', area: 'wagholi', project: null, bhk: 2,
      budget_min_inr: null, budget_max_inr: 7_000_000, timeline: '12 months', language: 'en', question: 'which projects to visit', answered_already: false },
    project: null, draft_origin: 'writer' },
  { id: 'rs2', source: 'youtube', url: 'https://youtube.com/watch?v=example2', text: 'Is Riverview Towers delayed? My possession date keeps moving.',
    context: 'Kharadi project walkthrough', author: 'viewer_example', posted_at: ago(20), status: 'new', area: 'kharadi', score: 0.71, why: ['asks about a project'],
    matches: [], draft: 'MahaRERA shows the filed completion date for Riverview Towers moved once, by 4 months; the project page has every change.',
    link: 'https://avasetu.in/projects/riverview-towers-kharadi', intent: { role: 'buyer', intent: 0.7, stage: 'post_visit', area: 'kharadi', project: 'Riverview Towers',
      bhk: null, budget_min_inr: null, budget_max_inr: null, timeline: null, language: 'en', question: 'is it delayed', answered_already: false },
    project: { name: 'Riverview Towers', regno: 'P52100099001', path: '/projects/riverview-towers-kharadi', line: 'Possession filed Mar 2028, moved once' }, draft_origin: 'llm' },
]
const METRICS: RadarMetrics = { by_source: { reddit: { shown: 12, sent: 4 }, youtube: { shown: 8, sent: 2 } }, by_area: { wagholi: { shown: 9, sent: 3 }, kharadi: { shown: 11, sent: 3 } },
  precision_at_10: 0.6, llm_calls: 140, llm_per_shown: 7, llm_today: 12, searches_today: 18 }
const WATCHES: RadarWatch[] = [
  { id: 'w1', source: 'reddit', kind: 'subreddit', value: 'pune', area: null, title: 'r/pune', active: true, hits: 40, checks: 120, converted: 3, mean: 0.4, origin: 'owner', reason: null, retired: null },
  { id: 'w2', source: 'youtube', kind: 'query', value: 'kharadi flats review', area: 'kharadi', title: null, active: true, hits: 12, checks: 60, converted: 1, mean: 0.3, origin: 'discovery', reason: 'buyers ask under these videos', retired: null },
]
const THEMES: RadarDemand[] = [{ area: 'wagholi', name: 'Wagholi', weeks: [{ week: '2026-W47', questions: 9, themes: [{ theme: 'traffic on Nagar Road', count: 4, faq: 'How bad is the Nagar Road traffic at peak hours?', examples: ['traffic near Wagholi?'] }] }] }]
const RUNS: RadarRuns = { discovery: [], jobs: [{ _id: 'j1', at: ago(1), result: { found: 6 } }], models: [] }

export function radarFixture(path: string, method = 'GET'): unknown {
  const p = path.split('?')[0]
  if (method !== 'GET') return { ok: true }
  if (p === '/signals') return SIGNALS
  if (p === '/metrics') return METRICS
  if (p === '/followups') return []
  if (p === '/watches') return WATCHES
  if (p === '/themes') return THEMES
  if (p === '/runs') return RUNS
  return {}
}

// ---- Press (/api/v1/press) --------------------------------------------------------------------------------------------------

const STORY: PressStory = {
  month: '2026-11',
  headline_facts: [{ text: '14 East Pune projects moved their filed possession date this month', area: null, topic: 'possession', source: 'MahaRERA, read by Avasetu', as_of: days(1) }],
  facts: [
    { text: '14 East Pune projects moved their filed possession date this month', area: null, topic: 'possession', source: 'MahaRERA, read by Avasetu', as_of: days(1) },
    { text: 'Wagholi: 210 homes booked across registered projects in 30 days', area: 'wagholi', topic: 'bookings', source: 'MahaRERA, read by Avasetu', as_of: days(1) },
  ],
}
let pitches: PressPitch[] = [
  { id: 'pp1', month: '2026-11', journalist: { name: 'A. Reporter', outlet: 'Example Pune Daily', email: 'reporter@example.com', contact_page: null },
    article: { title: 'Pune housing sales rise in October', url: 'https://example.com/pune-housing', date: days(12) },
    email: 'reporter@example.com', subject: 'Data: 14 East Pune projects moved possession dates in November',
    body: 'Hello,\n\nWe read MahaRERA every month. In November, 14 East Pune projects moved their filed possession date. The full list with sources is on our tracker.\n\nAvasetu',
    origin: 'template', status: 'draft', replied: false, link_won_url: null },
]

export function pressFixture(path: string, method = 'GET', json?: unknown): unknown {
  const p = path.split('?')[0]
  if (p === '/story') return STORY
  if (p === '/pitches') return pitches
  if (p === '/summary') return { sent: pitches.filter((x) => x.status === 'sent').length, replied: pitches.filter((x) => x.replied).length, links_won: 0 } as PressSummary
  if (p === '/run') return { month: '2026-11', facts: STORY.facts.length, pitches: pitches.length, pruned: 0 }
  const m = p.match(/^\/pitches\/(.+)$/)
  if (m && method === 'PATCH') {
    pitches = pitches.map((x) => (x.id === decodeURIComponent(m[1]) ? { ...x, ...(json as Partial<PressPitch>) } : x))
    return pitches.find((x) => x.id === decodeURIComponent(m[1]))
  }
  return {}
}

// ---- Lead board (/api/v1/lead-board) -----------------------------------------------------------------------------------------

function board(owner: boolean): Board {
  return {
    owner, preview: false,
    demand: { days: 7, visitors: 640, enquiries: 11, new_leads: 3, areas: [{ area: 'Wagholi', readers: 210, enquiries: 4 }, { area: 'Kharadi', readers: 180, enquiries: 5 }] },
    items: [
      { ref: 'b1', project: 'Green Meadows Phase 2', areas: ['Wagholi'], bhk: '2 BHK', budget: '₹60–70 L', when: 'Within 3 months', paying: 'Home loan', wants: 'Near a school',
        came_from: 'Website', age: 'Came in 2 days ago', created_at: days(2), last_active_at: ago(6), temperature: 'hot', genuine: 'replied', signals: ['opened the price list'],
        activity: { pages: [{ label: 'Green Meadows Phase 2', minutes: 4 }, { label: 'Wagholi 2 BHK flats', minutes: 2 }], more_pages: 1, page_count: 3, projects_seen: 2, visits: 2, days: 2, read_min: 7, device: 'Phone', city: 'Pune', taps: ['WhatsApp'], enquiries: 1 },
        caution: null, asked: 1, mine: null, given: null, ...(owner ? { lead_id: 'c1', asks: [] } : {}) },
      { ref: 'b2', project: null, areas: ['Kharadi', 'Upper Kharadi'], bhk: '3 BHK', budget: '₹1.2–1.5 Cr', when: '6–12 months', paying: null, wants: null,
        came_from: 'Instagram', age: 'Came in 5 days ago', created_at: days(5), last_active_at: days(1), temperature: 'warm', genuine: 'number', signals: [],
        activity: { pages: [{ label: 'Kharadi top projects', minutes: 3 }], more_pages: 0, page_count: 1, projects_seen: 3, visits: 1, days: 1, read_min: 3, device: 'Computer', city: null, taps: [], enquiries: 1 },
        caution: null, asked: 0, mine: null, given: null, ...(owner ? { lead_id: 'c2', asks: [] } : {}) },
    ],
  }
}

export function boardFixture(path: string, method = 'GET', asOwner = true): unknown {
  const p = path.split('?')[0]
  if (p === '' && method === 'GET') return board(asOwner && !path.includes('as_agent'))
  if (p === '/agents') return { items: [{ agent_id: 'fx-a1', name: 'Rahul Sharma', first_name: 'Rahul', whatsapp: '919800000001', listings: 2, asked: 1 }] }
  if (p.endsWith('/ask') && method === 'POST') return { offer_kind: 'none', offer_value: null, offer: null, note: null, at: new Date().toISOString() }
  if (p.endsWith('/give')) return { ok: true, passed_to: 'Rahul Sharma' }
  return { ok: true }
}
