/** Listing reels: typed client for the agent (/listings/{id}/reel) and the owner concierge (/concierge/agents/{a}/listings/{l}/reel),
 *  a small fixture fake, and the share helpers used by the reel card. */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'
import { whatsappShareUrl } from './share'

export type ReelLang = 'en' | 'hi' | 'mr'
export type ReelStatus = 'queued' | 'rendering' | 'done' | 'failed'
export const REEL_LANGS: Array<{ code: ReelLang; label: string }> = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'mr', label: 'मराठी' },
]

export interface ReelPost {
  channel: 'instagram' | 'facebook_page'
  status: string
  permalink?: string | null
  error?: string | null
}
export interface ReelJob {
  id: string
  listing_id: string
  lang: ReelLang
  status: ReelStatus
  video_path: string | null
  video_url: string | null
  audio: 'voice+music' | 'music' | null
  note: string
  error: string
  sample: boolean
  created_at: string | null
  finished_at: string | null
  posts?: ReelPost[]
}
export type ReelJobs = Partial<Record<ReelLang, ReelJob>>

/** What the reel card needs; the agent and the owner (on the agent's behalf) each get one. */
export interface ReelSource {
  make(lang: ReelLang, again?: boolean): Promise<ReelJob>
  latest(): Promise<ReelJobs>
}

export interface ReelsApi {
  forListing(listingId: string): ReelSource
  forAgentListing(agentId: string, listingId: string): ReelSource
  postReel(agentId: string, listingId: string, lang: ReelLang, channels?: Array<'instagram' | 'facebook_page'>): Promise<ReelPost[]>
}

export const POLL_MS = 5000
export const isActive = (j: ReelJob | null | undefined) => !!j && (j.status === 'queued' || j.status === 'rendering')

/** Absolute URL of the mp4 the browser (and WhatsApp) can open: the API host serves /uploads. */
export function reelVideoUrl(job: Pick<ReelJob, 'video_path' | 'video_url'>, base: string = API_BASE_URL): string {
  const p = job.video_path || job.video_url || ''
  if (/^https?:/.test(p)) return p
  return `${base.replace(/\/+$/, '')}${p.startsWith('/') ? '' : '/'}${p}`
}

/** 'Share on WhatsApp': a short caption and the video link (WhatsApp shows a preview and plays it). */
export function whatsappReelUrl(videoUrl: string, caption: string): string {
  return whatsappShareUrl(`${caption.trim()}\n${videoUrl}`.trim())
}

export function reelFilename(job: Pick<ReelJob, 'listing_id' | 'lang'>): string {
  return `reel-${job.listing_id}-${job.lang}.mp4`
}

export function friendlyReelError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 429) return e.detail || 'You have made the most reels for today. Try again tomorrow.'
    if (e.status === 404) return 'This listing was not found. Go back and refresh.'
    return e.detail
  }
  return e instanceof Error ? e.message : 'Something went wrong'
}

export function createReelsApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): ReelsApi {
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
      res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1${path}`, { method: init.method ?? 'GET', headers, body })
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
  const source = (path: string): ReelSource => ({
    make: async (lang, again = false) => (await request<{ job: ReelJob }>(path, { method: 'POST', json: again ? { lang, again } : { lang } })).job,
    latest: async () => (await request<{ jobs: ReelJobs }>(path)).jobs ?? {},
  })
  const enc = encodeURIComponent
  return {
    forListing: (lid) => source(`/listings/${enc(lid)}/reel`),
    forAgentListing: (aid, lid) => source(`/concierge/agents/${enc(aid)}/listings/${enc(lid)}/reel`),
    postReel: async (aid, lid, lang, channels) =>
      (await request<{ publications: ReelPost[] }>(`/concierge/agents/${enc(aid)}/listings/${enc(lid)}/reel/post`, {
        method: 'POST', json: channels ? { lang, channels } : { lang },
      })).publications ?? [],
  }
}

/** Local/dev fake: a reel goes queued -> rendering -> done over three polls. */
export function createFixtureReelsApi(): ReelsApi {
  const jobs = new Map<string, ReelJob>()
  const polls = new Map<string, number>()
  const key = (lid: string, lang: string) => `${lid}:${lang}`
  const advance = (j: ReelJob) => {
    const n = (polls.get(j.id) ?? 0) + 1
    polls.set(j.id, n)
    if (j.status === 'queued' && n >= 1) j.status = 'rendering'
    else if (j.status === 'rendering' && n >= 3) {
      j.status = 'done'
      j.video_path = `/uploads/reels/listing-${j.listing_id}-${j.lang}-fixture.mp4`
      j.video_url = j.video_path
      j.audio = 'music'
      j.note = 'Made without a voiceover (test mode). Music only.'
      j.finished_at = new Date().toISOString()
    }
  }
  const source = (lid: string): ReelSource => ({
    make: async (lang, again = false) => {
      const cur = jobs.get(key(lid, lang))
      if (cur && (isActive(cur) || (cur.status === 'done' && !again))) return { ...cur }
      const j: ReelJob = {
        id: `fx-reel-${jobs.size + 1}`, listing_id: lid, lang, status: 'queued', video_path: null, video_url: null, audio: null,
        note: '', error: '', sample: false, created_at: new Date().toISOString(), finished_at: null, posts: [],
      }
      jobs.set(key(lid, lang), j)
      return { ...j }
    },
    latest: async () => {
      const out: ReelJobs = {}
      for (const { code } of REEL_LANGS) {
        const j = jobs.get(key(lid, code))
        if (j) {
          advance(j)
          out[code] = { ...j }
        }
      }
      return out
    },
  })
  return {
    forListing: source,
    forAgentListing: (_aid, lid) => source(lid),
    postReel: async (_aid, lid, lang, channels = ['instagram', 'facebook_page']) => {
      const j = jobs.get(key(lid, lang))
      if (!j || j.status !== 'done') throw new ApiError(409, 'Make the reel first, then post it')
      return channels.map((channel) => ({ channel, status: 'dry_run', permalink: null, error: null }))
    },
  }
}

const real = createReelsApi({ getToken })
let fake: ReelsApi | null = null
/** The API all screens use: the fixture fake in fixture mode, else the server. */
export const reelsApi: ReelsApi = {
  forListing: (lid) => (isFixtureMode() ? (fake ??= createFixtureReelsApi()) : real).forListing(lid),
  forAgentListing: (aid, lid) => (isFixtureMode() ? (fake ??= createFixtureReelsApi()) : real).forAgentListing(aid, lid),
  postReel: (...args) => (isFixtureMode() ? (fake ??= createFixtureReelsApi()) : real).postReel(...args),
}
