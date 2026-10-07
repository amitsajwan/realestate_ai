/** Typed client, types and fixtures for the Studio Content screen: the owner reviews the planned posts and approves them (backend/app/modules/calendar). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'
import { HASHTAG } from '@/lib/brand'

export type ContentKind = 'post' | 'showcase' | 'reel'
/** What a post is about (calendar.groups on the server): the Content screen's type filter. */
export type ContentType = 'listings' | 'news' | 'guides' | 'agents' | 'other'
export type ContentStatus = 'planned' | 'approved' | 'scheduled' | 'published' | 'failed' | 'skipped' | 'removed'

export interface ContentItem {
  id: string
  slug: string
  kind: ContentKind
  channel: 'instagram' | 'facebook_page'
  due_at: string
  status: ContentStatus
  week: number | null
  caption: string
  /** Paths served by the backend, e.g. /uploads/calendar/w1/x-1.jpg (Instagram carousels have several). */
  image_urls: string[]
  video_url: string | null
  error: string | null
  /** The post on Facebook or Instagram, once it is out. */
  permalink?: string | null
  published_at?: string | null
  /** The last thing that happened to it, in words ("post now by owner", "held: ..."). */
  note?: string | null
  /** A post already published on this channel with the same opening line: the publisher holds this one back. */
  duplicate_of?: { slug: string; published_at: string | null; permalink: string | null } | null
  /** What it is about; 'other' when the server does not say. */
  group: ContentType
  /** Where the row came from (campaign, library, agent_reels, ...), for the record. */
  source?: string | null
  /** The property campaign (one per listing, "Start marketing") this post belongs to. */
  campaign?: { id: string; title: string } | null
}

/** The Instagram and Facebook copies of one post (same slug), shown and handled as one card. */
export interface ContentGroup {
  key: string
  items: ContentItem[]
  /** The earliest time any copy goes out. */
  due_at: string
}

const KINDS: ContentKind[] = ['post', 'showcase', 'reel']
export const CONTENT_TYPES: ContentType[] = ['listings', 'news', 'guides', 'agents', 'other']

/** Tolerate loose rows (missing arrays, unknown kinds). */
export function normalizeItem(raw: unknown): ContentItem {
  const r = (raw ?? {}) as Record<string, unknown>
  const kind = KINDS.includes(r.kind as ContentKind) ? (r.kind as ContentKind) : 'post'
  const urls = Array.isArray(r.image_urls) ? r.image_urls.map(String) : []
  return {
    id: String(r.id ?? ''),
    slug: String(r.slug ?? ''),
    kind,
    channel: r.channel === 'facebook_page' ? 'facebook_page' : 'instagram',
    due_at: String(r.due_at ?? ''),
    status: (typeof r.status === 'string' ? r.status : 'planned') as ContentStatus,
    week: typeof r.week === 'number' ? r.week : null,
    caption: String(r.caption ?? ''),
    image_urls: urls,
    video_url: typeof r.video_url === 'string' ? r.video_url : null,
    error: typeof r.error === 'string' ? r.error : null,
    duplicate_of: dupOf(r.duplicate_of),
    permalink: typeof r.permalink === 'string' ? r.permalink : null,
    published_at: typeof r.published_at === 'string' ? r.published_at : null,
    note: typeof r.note === 'string' ? r.note : null,
    group: CONTENT_TYPES.includes(r.group as ContentType) ? (r.group as ContentType) : 'other',
    source: typeof r.source === 'string' ? r.source : null,
    campaign: campaignOf(r.campaign),
  }
}

function campaignOf(raw: unknown): ContentItem['campaign'] {
  if (!raw || typeof raw !== 'object') return null
  const c = raw as Record<string, unknown>
  if (typeof c.id !== 'string' || !c.id) return null
  return { id: c.id, title: typeof c.title === 'string' && c.title.trim() ? c.title.trim() : 'Property campaign' }
}

function dupOf(raw: unknown): ContentItem['duplicate_of'] {
  if (!raw || typeof raw !== 'object') return null
  const d = raw as Record<string, unknown>
  if (typeof d.slug !== 'string') return null
  return { slug: d.slug, published_at: typeof d.published_at === 'string' ? d.published_at : null, permalink: typeof d.permalink === 'string' ? d.permalink : null }
}

const ts = (iso: string) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`).getTime()

/** One group per slug (its Instagram and Facebook copies), in the order the server sent them; Instagram first inside a group. */
export function groupItems(items: ContentItem[]): ContentGroup[] {
  const groups = new Map<string, ContentItem[]>()
  for (const it of items) groups.set(it.slug || it.id, [...(groups.get(it.slug || it.id) ?? []), it])
  return [...groups.entries()]
    .map(([key, its]) => {
      const sorted = [...its].sort((a, b) => (a.channel === b.channel ? 0 : a.channel === 'instagram' ? -1 : 1))
      const due = sorted.map((i) => i.due_at).filter(Boolean).sort((a, b) => ts(a) - ts(b))[0] ?? ''
      return { key, items: sorted, due_at: due }
    })
}

/** The filter chip: "Listings", "Agents". */
export function typeLabel(t: ContentType | 'all'): string {
  return { all: 'All', listings: 'Listings', news: 'News', guides: 'Guides', agents: 'Agents', other: 'Other' }[t]
}

/** The small label on a card: what one post is. */
export function typeTag(t: ContentType): string {
  return { listings: 'Listing', news: 'News', guides: 'Guide', agents: 'Agent recruiting', other: 'Other' }[t]
}

/** Cards per type, in filter order. */
export function typeCounts(groups: ContentGroup[]): Record<ContentType, number> {
  const out = { listings: 0, news: 0, guides: 0, agents: 0, other: 0 } as Record<ContentType, number>
  for (const g of groups) out[g.items[0]?.group ?? 'other'] += 1
  return out
}

export function ofType(groups: ContentGroup[], t: ContentType | 'all'): ContentGroup[] {
  return t === 'all' ? groups : groups.filter((g) => (g.items[0]?.group ?? 'other') === t)
}

/** A row of the list: one post (its IG and FB copies), or every post of one property campaign folded into one card. */
export type ContentRow =
  | { type: 'post'; key: string; group: ContentGroup }
  | { type: 'campaign'; key: string; id: string; title: string; groups: ContentGroup[] }

/** Fold each campaign's posts into one row, where its first post was; a campaign with a single post stays a plain row. */
export function foldCampaigns(groups: ContentGroup[]): ContentRow[] {
  const by = new Map<string, ContentGroup[]>()
  for (const g of groups) {
    const c = g.items[0]?.campaign
    if (c) by.set(c.id, [...(by.get(c.id) ?? []), g])
  }
  const rows: ContentRow[] = []
  const done = new Set<string>()
  for (const g of groups) {
    const c = g.items[0]?.campaign
    const mine = c ? by.get(c.id) ?? [] : []
    if (!c || mine.length < 2) rows.push({ type: 'post', key: g.key, group: g })
    else if (!done.has(c.id)) {
      done.add(c.id)
      rows.push({ type: 'campaign', key: `campaign:${c.id}`, id: c.id, title: c.title, groups: mine })
    }
  }
  return rows
}

/** "in 2h 14m", "in 3 days", or null when the time has come. */
export function countdown(iso: string, now: number = Date.now()): string | null {
  const ms = ts(iso) - now
  if (isNaN(ms) || ms <= 0) return null
  const m = Math.ceil(ms / 60000)
  if (m < 60) return `in ${m} min`
  const h = Math.floor(m / 60)
  if (h < 48) return `in ${h}h ${m % 60}m`
  return `in ${Math.round(h / 24)} days`
}

export function channelLabel(c: ContentItem['channel']): string {
  return c === 'instagram' ? 'Instagram' : 'Facebook'
}

export function kindLabel(k: ContentKind): string {
  return k === 'showcase' ? 'Sample home' : k === 'reel' ? 'Reel' : 'Post'
}

export function statusLabel(s: ContentStatus): string {
  return s === 'planned' ? 'Needs your OK' : s === 'approved' || s === 'scheduled' ? 'Approved' : s[0].toUpperCase() + s.slice(1)
}

/** "Mon 12 Oct, 10:00 am" in India time, whatever the viewer's zone. Naive timestamps from the server are UTC. */
export function dueLabel(iso: string): string {
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  if (isNaN(d.getTime())) return ''
  const parts = new Intl.DateTimeFormat('en-IN', { weekday: 'short', day: '2-digit', month: 'short', hour: 'numeric', minute: '2-digit', hour12: true, timeZone: 'Asia/Kolkata' }).formatToParts(d)
  const get = (t: string) => parts.find((p) => p.type === t)?.value ?? ''
  return `${get('weekday')} ${get('day')} ${get('month')}, ${get('hour')}:${get('minute')} ${get('dayPeriod').toLowerCase()}`
}

/** Absolute URL for a backend-served path; data: and http(s) URLs pass through. */
export function mediaUrl(path: string, base: string = API_BASE_URL): string {
  if (/^(https?:|data:)/.test(path)) return path
  return `${base}${path.startsWith('/') ? '' : '/'}${path}`
}

export function friendlyContentError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'The content calendar is only for the owner.'
    if (e.status === 404) return 'This item is gone. Refresh to see the latest.'
    if (e.status === 409) return 'This item was already handled. Refresh to see the latest.'
    return e.detail
  }
  return e instanceof Error ? e.message : 'Something went wrong'
}

export interface ContentApi {
  getUpcoming(limit?: number): Promise<ContentItem[]>
  approve(id: string): Promise<void>
  skip(id: string): Promise<void>
  /** Approve if needed and publish at the next pass (a few minutes at most). */
  postNow(id: string): Promise<void>
  /** What finished lately: posted (with link), failed (with reason), removed. */
  getRecent(hours?: number): Promise<ContentItem[]>
  /** A failed post back in the queue, a few minutes after the last one on its channel. */
  retry(id: string): Promise<void>
  /** An approved post back to "To approve". */
  unapprove(id: string): Promise<void>
}

export function createContentApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): ContentApi {
  const base = opts.baseUrl ?? API_BASE_URL
  async function request<T>(path: string, method = 'GET'): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    const token = opts.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
    let res: Response
    try {
      res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1/calendar${path}`, { method, headers })
    } catch {
      throw new ApiError(0, 'Cannot reach the server. Check your internet.')
    }
    const text = await res.text()
    let data: unknown = null
    if (text) {
      try {
        data = JSON.parse(text)
      } catch {
        data = { detail: text.slice(0, 200) }
      }
    }
    if (!res.ok) throw parseErrorBody(data, res.status)
    return data as T
  }
  return {
    getUpcoming: async (limit = 200) => {
      const r = await request<unknown[]>(`/upcoming?limit=${limit}`)
      return (Array.isArray(r) ? r : []).map(normalizeItem)
    },
    approve: async (id) => {
      await request<unknown>(`/items/${encodeURIComponent(id)}/approve`, 'POST')
    },
    skip: async (id) => {
      await request<unknown>(`/items/${encodeURIComponent(id)}/skip`, 'POST')
    },
    postNow: async (id) => {
      await request<unknown>(`/items/${encodeURIComponent(id)}/post-now`, 'POST')
    },
    getRecent: async (hours = 72) => {
      const r = await request<unknown[]>(`/recent?hours=${hours}`)
      return (Array.isArray(r) ? r : []).map(normalizeItem)
    },
    retry: async (id) => {
      await request<unknown>(`/items/${encodeURIComponent(id)}/retry`, 'POST')
    },
    unapprove: async (id) => {
      await request<unknown>(`/items/${encodeURIComponent(id)}/unapprove`, 'POST')
    },
  }
}

// ---- fixtures (local/dev mode) ----

function card(bg: string, text: string): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="540" height="675"><rect width="540" height="675" fill="${bg}"/><text x="40" y="320" font-size="40" font-family="sans-serif" fill="#fff">${text}</text></svg>`
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}

const day = (n: number, hour: number) => new Date(Date.UTC(2026, 9, 12 + n, hour - 6, 30)).toISOString()

export const FIXTURE_ITEMS: ContentItem[] = [
  {
    id: 'fx-1',
    slug: 'water-and-power-questions',
    kind: 'post',
    channel: 'instagram',
    due_at: day(1, 19),
    status: 'planned',
    week: 1,
    caption: 'Ask these water and power questions before booking.\n\nWhere does the water come from? Save this for your next visit.\n\n' + HASHTAG + ' #HomeBuyingTips',
    image_urls: [card('#16213f', 'Cover'), card('#2a1c4a', '1. Where does the water come from?'), card('#2a1c4a', '2. How much storage?')],
    video_url: null,
    error: null,
    group: 'guides',
    source: 'library',
  },
  {
    id: 'fx-2',
    slug: 'kharadi-2bhk-ready',
    kind: 'showcase',
    channel: 'facebook_page',
    due_at: day(1, 10),
    status: 'planned',
    week: 1,
    caption: 'Sample listing. Illustrative home, not available for sale. 2 BHK in Kharadi, 780 sq ft carpet area.',
    image_urls: [card('#0e3b4a', 'Sample home')],
    video_url: null,
    error: null,
    group: 'other',
    source: 'home',
  },
  {
    id: 'fx-3',
    slug: 'reel-w1-tip',
    kind: 'reel',
    channel: 'instagram',
    due_at: day(4, 19),
    status: 'approved',
    week: 1,
    caption: 'Do the commute test three times. Save this.',
    image_urls: [],
    video_url: null,
    error: null,
    group: 'guides',
    source: 'reel',
  },
  ...campaignFixtures(),
  fx('fx-hd', 'hd-goyal-my-home', 'post', 'instagram', day(2, 19), 'planned', 'listings', 'agentprojects',
    '3 BHK at Goyal My Home, Wagholi. MahaRERA registered, possession Dec 2027.\n\nMessage us for the floor plan.', [card('#3a2a10', 'Goyal My Home')]),
  fx('fx-area', 'area-wagholi-20261013', 'reel', 'instagram', day(1, 8), 'planned', 'news', 'area_insight',
    'Wagholi in MahaRERA records: 142 projects, 38 due by 2027.', []),
  fx('fx-trend', 'flat-60-lakh-real-cost', 'reel', 'facebook_page', day(3, 20), 'planned', 'guides', 'trend_reels',
    'A ₹60 lakh flat really costs ₹66 lakh. Here is where the rest goes.', []),
  fx('fx-agent', 'agent-a1', 'reel', 'instagram', day(2, 8), 'planned', 'agents', 'agent_reels',
    'Pune agents: buyers ask the same five questions. Let your page answer them.', []),
]

function fx(id: string, slug: string, kind: ContentKind, channel: ContentItem['channel'], due_at: string, status: ContentStatus,
  group: ContentType, source: string, caption: string, image_urls: string[], campaign: ContentItem['campaign'] = null): ContentItem {
  return { id, slug, kind, channel, due_at, status, week: 1, caption, image_urls, video_url: null, error: null, group, source, campaign }
}

/** Gulmohar City: a property campaign from "Start marketing", three posts on both channels and a reel. */
function campaignFixtures(): ContentItem[] {
  const c = { id: 'fx-listing-gulmohar', title: 'Gulmohar City' }
  const angles: Array<[string, string]> = [
    ['price', 'Gulmohar City, Wagholi: 2 BHK from ₹62 lakh, all-inclusive.'],
    ['location', 'Gulmohar City is 12 minutes from EON IT Park, Kharadi.'],
    ['amenities', 'Gulmohar City: clubhouse, pool and a 1 acre garden.'],
  ]
  const out: ContentItem[] = []
  angles.forEach(([angle, caption], n) => {
    for (const ch of ['instagram', 'facebook_page'] as const) {
      out.push(fx(`fx-gc-${angle}-${ch === 'instagram' ? 'ig' : 'fb'}`, `campaign-${c.id}-${angle}`, 'post', ch, day(5 + n, 19), 'planned',
        'listings', 'campaign', caption + '\n\nFull details and the MahaRERA record: link in bio.', [card('#0f2340', `Gulmohar · ${angle}`)], c))
    }
  })
  out.push(fx('fx-gc-reel', `campaign-${c.id}-price-reel`, 'reel', 'instagram', day(8, 19), 'planned', 'listings', 'campaign',
    'Gulmohar City in 20 seconds.', [], c))
  return out
}

export function createFixtureContentApi(seed: ContentItem[] = FIXTURE_ITEMS): ContentApi {
  let items = seed.map((i) => ({ ...i }))
  const find = (id: string) => {
    const it = items.find((i) => i.id === id)
    if (!it) throw new ApiError(404, 'Not found')
    return it
  }
  return {
    getUpcoming: async () => items.map((i) => ({ ...i })),
    approve: async (id) => {
      const it = find(id)
      if (it.status !== 'planned') throw new ApiError(409, 'Already handled')
      it.status = 'approved'
    },
    skip: async (id) => {
      find(id)
      items = items.filter((i) => i.id !== id)
    },
    postNow: async (id) => {
      const it = find(id)
      if (!['planned', 'approved', 'scheduled'].includes(it.status)) throw new ApiError(409, 'Already handled')
      it.status = 'approved'
      it.due_at = new Date().toISOString()
    },
    getRecent: async () => [],
    retry: async (id) => {
      const it = find(id)
      it.status = 'approved'
    },
    unapprove: async (id) => {
      const it = find(id)
      it.status = 'planned'
    },
  }
}

const real = createContentApi({ getToken })
let fake: ContentApi | null = null
const impl = (): ContentApi => (isFixtureMode() ? (fake ??= createFixtureContentApi()) : real)

/** What the screen imports: the fixture API in fixture mode, else the real one. */
export const contentApi: ContentApi = {
  getUpcoming: (limit) => impl().getUpcoming(limit),
  approve: (id) => impl().approve(id),
  skip: (id) => impl().skip(id),
  postNow: (id) => impl().postNow(id),
  getRecent: (hours) => impl().getRecent(hours),
  retry: (id) => impl().retry(id),
  unapprove: (id) => impl().unapprove(id),
}
