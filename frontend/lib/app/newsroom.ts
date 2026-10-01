/** Typed client, types and fixtures for the Studio Newsroom review screen (docs/contracts/newsroom.md, HTTP API). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'
import { BRAND_NAME, DEFAULT_SITE_URL, HASHTAG } from '@/lib/brand'

export interface NewsroomFact {
  text: string
  quote: string
}
export interface NewsroomSource {
  name: string
  url: string | null
}
export interface NewsroomCheck {
  ok: boolean
  problems: string[]
}
/** A channel an approved item will be published to. */
export interface NewsroomChannel {
  id: 'facebook' | 'instagram'
  label: string
  post: string
}
/** The rendered social card (public image addresses): `fb` square, `ig` portrait, `slides` every Instagram slide (a digest has several). */
export interface NewsroomCard {
  fb: string
  ig: string | null
  slides: string[]
  variant: string | null
}
/** What the owner is about to publish: the card, the channels, and the exact final caption per channel with its check problems. */
export interface NewsroomPreview {
  card: NewsroomCard | null
  channels: NewsroomChannel[]
  captions: Record<string, string>
  captionProblems: Record<string, string[]>
  dryRun: boolean
}
export interface NewsroomItem extends NewsroomPreview {
  id: string
  title: string
  pillar: string
  areas: string[]
  draft: string
  facts: NewsroomFact[]
  check: NewsroomCheck
  sources: NewsroomSource[]
  age_days: number
}
export interface NewsroomStatus {
  enabled: boolean
  counts: Record<string, number>
  last_run_at: string | null
  last_error: string | null
}
export interface ApproveBody {
  text?: string
  when?: string
}
/** The approve answer is not frozen by the contract: tolerate anything. */
export type ApproveResult = Record<string, unknown>

/** A media address from the API: absolute, or a path on the API host (when PUBLIC_MEDIA_BASE_URL is not set). */
export function mediaUrl(u: unknown, base: string = API_BASE_URL): string | null {
  if (typeof u !== 'string' || !u) return null
  if (/^https?:\/\//.test(u)) return u
  return u.startsWith('/') ? base.replace(/\/+$/, '') + u : null
}

/** The preview part of a queue item (or of the preview endpoint's answer). Tolerates missing fields, so an older server still works. */
export function normalizePreview(raw: unknown): NewsroomPreview {
  const r = (raw ?? {}) as Record<string, unknown>
  const c = (r.card ?? null) as { fb?: unknown; ig?: unknown; slides?: unknown; variant?: unknown } | null
  const fb = mediaUrl(c?.fb)
  const ig = mediaUrl(c?.ig)
  const slides = (Array.isArray(c?.slides) ? (c!.slides as unknown[]) : []).map((x) => mediaUrl(x)).filter((x): x is string => !!x)
  const channels = (Array.isArray(r.channels) ? r.channels : []).flatMap((x): NewsroomChannel[] => {
    const o = x as { id?: string; label?: string; post?: string }
    return o && (o.id === 'facebook' || o.id === 'instagram')
      ? [{ id: o.id, label: o.label ?? (o.id === 'facebook' ? 'Facebook Page' : 'Instagram'), post: o.post ?? '' }]
      : []
  })
  const captions: Record<string, string> = {}
  for (const [k, v] of Object.entries((r.captions ?? {}) as Record<string, unknown>)) if (typeof v === 'string') captions[k] = v
  const captionProblems: Record<string, string[]> = {}
  for (const [k, v] of Object.entries((r.caption_problems ?? r.captionProblems ?? {}) as Record<string, unknown>)) {
    if (Array.isArray(v) && v.length) captionProblems[k] = v.map(String)
  }
  return {
    card: fb ? { fb, ig, slides: slides.length ? slides : ig ? [ig] : [], variant: typeof c?.variant === 'string' ? c.variant : null } : null,
    channels, captions, captionProblems, dryRun: r.dry_run === true || r.dryRun === true,
  }
}

/** Accept the contract shape but tolerate loose variants (draft as object, sources as strings or name only). */
export function normalizeItem(raw: unknown): NewsroomItem {
  const r = (raw ?? {}) as Record<string, unknown>
  const draft = r.draft
  const text = typeof draft === 'string' ? draft : ((draft as { text?: string } | null)?.text ?? '')
  const check = (r.check ?? {}) as { ok?: boolean; problems?: unknown }
  const problems = Array.isArray(check.problems) ? check.problems.map(String) : []
  const sources = (Array.isArray(r.sources) ? r.sources : []).map((s): NewsroomSource => {
    if (typeof s === 'string') return { name: s, url: /^https?:\/\//.test(s) ? s : null }
    const o = s as { name?: string; url?: string | null; link?: string | null }
    const url = o.url ?? o.link ?? null
    return { name: o.name ?? url ?? 'Source', url }
  })
  return {
    ...normalizePreview(r),
    id: String(r.id ?? ''),
    title: String(r.title ?? ''),
    pillar: String(r.pillar ?? ''),
    areas: Array.isArray(r.areas) ? r.areas.map(String) : [],
    draft: text,
    facts: (Array.isArray(r.facts) ? r.facts : []).map((f) => {
      const o = f as { text?: string; quote?: string }
      return { text: o.text ?? '', quote: o.quote ?? '' }
    }),
    check: { ok: check.ok === true && problems.length === 0, problems },
    sources,
    age_days: typeof r.age_days === 'number' ? r.age_days : 0,
  }
}

/** Pillar slugs (docs/NEWSROOM_PLAN.md) to short labels; unknown slugs are prettified. */
const PILLARS: Record<string, string> = {
  infrastructure: 'Infrastructure',
  new_supply: 'New supply',
  rules_money: 'Rules and money',
  locality_life: 'Locality life',
  education: 'Buyer education',
  digest: 'Weekly digest',
}
export function pillarLabel(p: string): string {
  if (PILLARS[p]) return PILLARS[p]
  const s = p.replace(/[_-]+/g, ' ').trim()
  return s ? s[0].toUpperCase() + s.slice(1) : 'News'
}

export function ageLabel(days: number): string {
  if (days < 1) return 'today'
  return days === 1 ? '1 day old' : `${Math.round(days)} days old`
}

/** `datetime-local` value (local time, no zone) to an ISO string; empty or invalid gives undefined (next slot). */
export function whenToIso(local: string): string | undefined {
  if (!local) return undefined
  const d = new Date(local)
  return isNaN(d.getTime()) ? undefined : d.toISOString()
}

export function friendlyNewsroomError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'The newsroom is only for the owner.'
    if (e.status === 404) return 'This item is no longer in the queue. Refresh to see the latest.'
    if (e.status === 409) return 'This item was already handled. Refresh to see the latest.'
    return e.detail
  }
  return e instanceof Error ? e.message : 'Something went wrong'
}

export interface NewsroomApi {
  getQueue(): Promise<NewsroomItem[]>
  getStatus(): Promise<NewsroomStatus>
  approve(id: string, body?: ApproveBody): Promise<ApproveResult>
  reject(id: string, reason?: string): Promise<void>
  /** The final captions (checked) for the draft, or for edited text, without saving anything. */
  preview(id: string, text?: string): Promise<NewsroomPreview>
}

export function createNewsroomApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): NewsroomApi {
  const base = opts.baseUrl ?? API_BASE_URL
  async function request<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    const token = opts.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
    let body: string | undefined
    if (init.json !== undefined) {
      headers['Content-Type'] = 'application/json'
      body = JSON.stringify(init.json)
    }
    let res: Response
    try {
      res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1/newsroom${path}`, { method: init.method ?? 'GET', headers, body })
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
    getQueue: async () => {
      const r = await request<unknown[]>('/queue')
      return (Array.isArray(r) ? r : []).map(normalizeItem)
    },
    getStatus: () => request<NewsroomStatus>('/status'),
    approve: (id, body = {}) => request<ApproveResult>(`/items/${encodeURIComponent(id)}/approve`, { method: 'POST', json: body }),
    reject: async (id, reason) => {
      await request<unknown>(`/items/${encodeURIComponent(id)}/reject`, { method: 'POST', json: reason ? { reason } : {} })
    },
    preview: async (id, text) => normalizePreview(await request<unknown>(`/items/${encodeURIComponent(id)}/preview`, { method: 'POST', json: text ? { text } : {} })),
  }
}

// ---- fixtures (local/dev mode) ----

export const FIXTURE_QUEUE: NewsroomItem[] = [
  {
    id: 'gn-metro-hinjewadi-1',
    title: 'Pune Metro Line 3 (Hinjewadi to Shivajinagar) crosses 90 percent of civil work',
    pillar: 'infrastructure',
    areas: ['Hinjewadi', 'Baner'],
    draft:
      'Metro Line 3 between Hinjewadi and Shivajinagar has crossed 90 percent of civil work, according to The Times of India. Stations at Baner and Balewadi are next in line for finishing work. Source: https://example.test/metro-line-3\n\nWhich station would make your daily commute easier?',
    facts: [
      { text: 'Civil work on Metro Line 3 is over 90 percent complete.', quote: 'Civil work on the Hinjewadi-Shivajinagar corridor has crossed 90 percent.' },
      { text: 'Finishing work is next at Baner and Balewadi stations.', quote: 'Finishing work at Baner and Balewadi stations will follow.' },
    ],
    check: { ok: true, problems: [] },
    sources: [{ name: 'Times of India', url: 'https://example.test/metro-line-3' }],
    age_days: 1,
    card: {
      fb: 'https://media.example.com/uploads/news/gn-metro-hinjewadi-1-fb.jpg',
      ig: 'https://media.example.com/uploads/news/gn-metro-hinjewadi-1-ig.jpg',
      slides: ['https://media.example.com/uploads/news/gn-metro-hinjewadi-1-ig.jpg'],
      variant: 'figure',
    },
    channels: [
      { id: 'facebook', label: 'Facebook Page', post: 'photo post with our link' },
      { id: 'instagram', label: 'Instagram', post: 'image post, link in bio' },
    ],
    captions: {
      facebook:
        `Metro Line 3 between Hinjewadi and Shivajinagar has crossed 90 percent of civil work.\n\nSource: Times of India, as of 29 Sep 2026.\n\nWhich station would make your daily commute easier?\n\nRead more: ${DEFAULT_SITE_URL}/news/gn-metro-hinjewadi-1\n\n#Pune ${HASHTAG} #PuneInfrastructure\n\n${BRAND_NAME} · ${DEFAULT_SITE_URL}`,
      instagram:
        'Metro Line 3 between Hinjewadi and Shivajinagar has crossed 90 percent of civil work.\n\nSource: Times of India, as of 29 Sep 2026.\n\nWhich station would make your daily commute easier?\n\nRead more: link in our bio.\n\n#Pune ' + HASHTAG + ' #PuneInfrastructure #PuneRealEstate\n\n' + BRAND_NAME + ' · link in our bio',
    },
    captionProblems: {},
    dryRun: true,
  },
  {
    id: 'mr-kharadi-2',
    title: 'New MahaRERA registration in Kharadi: 3 towers, possession 2029',
    pillar: 'new_supply',
    areas: ['Kharadi'],
    draft: 'A new project has been registered with MahaRERA in Kharadi with three towers. The registered possession date is December 2031, so buyers should plan for a long wait.',
    facts: [{ text: 'Project has three towers in Kharadi.', quote: 'The project comprises 3 towers at Kharadi.' }],
    check: {
      ok: false,
      problems: ['Date "December 2031" is not in the source text.', 'Draft contains a prediction ("buyers should plan for").', 'Draft does not end with a question.'],
    },
    sources: [{ name: 'MahaRERA', url: 'https://example.test/maharera/P52100012345' }],
    age_days: 3,
    card: null,
    channels: [{ id: 'facebook', label: 'Facebook Page', post: 'photo post with our link' }],
    captions: {},
    captionProblems: {},
    dryRun: false,
  },
]

export const FIXTURE_STATUS: NewsroomStatus = {
  enabled: true,
  counts: { pending_review: 2, approved: 0, scheduled: 1, published: 7, rejected: 4, dropped: 31 },
  last_run_at: new Date(Date.now() - 95 * 60_000).toISOString(),
  last_error: null,
}

export function createFixtureNewsroomApi(seed: NewsroomItem[] = FIXTURE_QUEUE, status: NewsroomStatus = FIXTURE_STATUS): NewsroomApi {
  let queue = seed.map((i) => ({ ...i }))
  const done = (id: string) => {
    if (!queue.some((i) => i.id === id)) throw new ApiError(404, 'Not found')
    queue = queue.filter((i) => i.id !== id)
  }
  return {
    getQueue: async () => queue.map((i) => ({ ...i })),
    getStatus: async () => ({ ...status, counts: { ...status.counts, pending_review: queue.length } }),
    approve: async (id) => {
      done(id)
      return {}
    },
    reject: async (id) => done(id),
    preview: async (id, text) => {
      const item = queue.find((i) => i.id === id)
      if (!item) throw new ApiError(404, 'Not found')
      if (!text) return { card: item.card, channels: item.channels, captions: item.captions, captionProblems: item.captionProblems, dryRun: item.dryRun }
      const captions = Object.fromEntries(Object.entries(item.captions).map(([k, v]) => [k, text.trim() + '\n\n' + v.split('\n\n').slice(-1)[0]]))
      return { card: item.card, channels: item.channels, captions, captionProblems: item.captionProblems, dryRun: item.dryRun }
    },
  }
}

const real = createNewsroomApi({ getToken })
let fake: NewsroomApi | null = null
const impl = (): NewsroomApi => (isFixtureMode() ? (fake ??= createFixtureNewsroomApi()) : real)

/** What the screen imports: the fixture API in fixture mode, else the real one. */
export const newsroomApi: NewsroomApi = {
  getQueue: () => impl().getQueue(),
  getStatus: () => impl().getStatus(),
  approve: (id, body) => impl().approve(id, body),
  reject: (id, reason) => impl().reject(id, reason),
  preview: (id, text) => impl().preview(id, text),
}
