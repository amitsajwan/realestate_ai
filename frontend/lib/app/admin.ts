/** Typed client, types and fixtures for the owner's Admin home (backend /admin). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { createFixtureConciergeApi } from './concierge'
import type { AgentSummary, CreatedAgent } from './concierge'
import { getToken } from './session'

export interface WindowCounts {
  leads: number
  leads_by_source: Record<string, number>
  chat_leads: number
  whatsapp_leads: number
  interest_taps: number
  comments_answered: number
  posts_published: { facebook_page: number; instagram: number }
  news_published: number
}
export interface InviteRequest {
  id: string
  name: string
  /** Masked by the server, like 90******17. */
  mobile: string
  city: string
  message: string
  created_at: string | null
  status: string
}
export type HealthStatus = 'ok' | 'warn' | 'bad'
export interface HealthRow {
  key: string
  label: string
  status: HealthStatus
  text: string
  fix: string
  last_run_at?: string | null
}
export type ControlFlag = 'posting_paused' | 'comments_paused' | 'news_paused'
export interface AdminControls {
  posting_paused: boolean
  comments_paused: boolean
  news_paused: boolean
  updated_at: string | null
  updated_by: string | null
}
export interface AdminOverview {
  generated_at: string
  counts: { today: WindowCounts; week: WindowCounts }
  waiting: { posts: number; news: number; invite_requests: number }
  invite_requests: InviteRequest[]
  agents: AgentSummary[]
  health: HealthRow[]
  controls: AdminControls
}
export type InvitedRequest = CreatedAgent & { request: InviteRequest }

export interface AdminApi {
  overview(): Promise<AdminOverview>
  setControls(changes: Partial<Record<ControlFlag, boolean>>): Promise<AdminControls>
  inviteRequests(): Promise<InviteRequest[]>
  invite(id: string): Promise<InvitedRequest>
  dismiss(id: string): Promise<InviteRequest>
}

/** What each pause switch does, in plain words (shown on the switch and in its confirmation). */
export const CONTROL_TEXT: Record<ControlFlag, { label: string; pause: string; resume: string }> = {
  posting_paused: {
    label: 'Pause posting',
    pause: 'Scheduled Facebook and Instagram posts stop until you resume. Nothing already posted is removed.',
    resume: 'Scheduled posts start going out again at their times.',
  },
  comments_paused: {
    label: 'Pause comment replies',
    pause: 'The assistant stops answering Facebook and Instagram comments until you resume.',
    resume: 'The assistant starts answering new comments again.',
  },
  news_paused: {
    label: 'Pause news',
    pause: 'News stops being collected, drafted and posted until you resume.',
    resume: 'News starts being collected and drafted again.',
  },
}

/** "Finish setup" hints from the concierge checklist, in the order they matter. */
const HINT: Record<string, string> = {
  logo: 'add logo', banner: 'add banner', rera_no: 'add RERA number', areas: 'add areas', photo: 'add his photo',
  first_listing: 'add first listing', three_listings: 'reach 3 listings', consent: 'record consent',
}
export function setupHints(a: Pick<AgentSummary, 'checklist'>, max = 3): string[] {
  return a.checklist.filter((c) => !c.done).map((c) => HINT[c.key] ?? c.label.toLowerCase()).slice(0, max)
}

export function createAdminApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): AdminApi {
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
      res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1/admin${path}`, { method: init.method ?? 'GET', headers, body })
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
  const r = (id: string) => `/invite-requests/${encodeURIComponent(id)}`
  return {
    overview: () => request<AdminOverview>('/overview'),
    setControls: (changes) => request<AdminControls>('/controls', { method: 'POST', json: changes }),
    inviteRequests: async () => (await request<{ items: InviteRequest[] }>('/invite-requests')).items ?? [],
    invite: (id) => request<InvitedRequest>(`${r(id)}/invite`, { method: 'POST' }),
    dismiss: (id) => request<InviteRequest>(`${r(id)}/dismiss`, { method: 'POST' }),
  }
}

// ---- fixtures (local/dev mode) ----
const counts = (k: number): WindowCounts => ({
  leads: 3 * k, leads_by_source: { chat: k, whatsapp: k, facebook_comment: k }, chat_leads: k, whatsapp_leads: k, interest_taps: 4 * k,
  comments_answered: 2 * k, posts_published: { facebook_page: k, instagram: k }, news_published: k,
})

export function fixtureOverview(): AdminOverview {
  return {
    generated_at: '2026-10-02T06:00:00Z',
    counts: { today: counts(1), week: counts(5) },
    waiting: { posts: 4, news: 2, invite_requests: 2 },
    invite_requests: [
      { id: 'fx-r1', name: 'Vikram Joshi', mobile: '98******21', city: 'Pune', message: 'I sell flats in Wakad and Hinjewadi', created_at: '2026-10-01T09:00:00Z', status: 'new' },
      { id: 'fx-r2', name: 'Sneha Deshpande', mobile: '97******08', city: 'Pune', message: '', created_at: '2026-10-01T12:30:00Z', status: 'new' },
    ],
    agents: [],
    health: [
      { key: 'facebook', label: 'Facebook', status: 'ok', text: 'Connected', fix: '' },
      { key: 'instagram', label: 'Instagram', status: 'bad', text: 'Instagram disconnected: Meta rejected our token', fix: 'Run deploy/gcp/meta_connect.ps1 to reconnect (docs/META_SETUP.md)' },
      { key: 'whatsapp', label: 'WhatsApp', status: 'warn', text: 'On, in practice mode: replies are worked out but not sent', fix: 'Set WHATSAPP_DRY_RUN=false on the server to send replies' },
      { key: 'ai', label: 'AI', status: 'ok', text: 'Answering', fix: '' },
      { key: 'posting', label: 'Posting', status: 'ok', text: 'Running (practice mode: nothing is sent)', fix: '', last_run_at: '2026-10-02T05:55:00Z' },
      { key: 'comments', label: 'Comments', status: 'ok', text: 'Running', fix: '', last_run_at: '2026-10-02T05:59:00Z' },
      { key: 'news', label: 'News', status: 'warn', text: 'Switched off on the server', fix: 'Set NEWSROOM_ENABLED=true on the server', last_run_at: null },
    ],
    controls: { posting_paused: false, comments_paused: false, news_paused: false, updated_at: null, updated_by: null },
  }
}

export function createFixtureAdminApi(): AdminApi {
  const concierge = createFixtureConciergeApi()
  const state = fixtureOverview()
  const find = (id: string) => {
    const req = state.invite_requests.find((x) => x.id === id)
    if (!req) throw new ApiError(404, 'Invite request not found')
    return req
  }
  const drop = (id: string) => {
    state.invite_requests = state.invite_requests.filter((x) => x.id !== id)
    state.waiting.invite_requests = state.invite_requests.length
  }
  return {
    overview: async () => ({ ...state, agents: await concierge.list(), invite_requests: [...state.invite_requests], waiting: { ...state.waiting } }),
    setControls: async (changes) => {
      state.controls = { ...state.controls, ...changes, updated_at: new Date().toISOString(), updated_by: 'owner' }
      for (const [flag, key] of [['posting_paused', 'posting'], ['comments_paused', 'comments'], ['news_paused', 'news']] as const) {
        const row = state.health.find((h) => h.key === key)
        if (row && flag in changes) Object.assign(row, changes[flag] ? { status: 'warn', text: 'Paused by you', fix: 'Use the switch under Controls to resume' } : { status: 'ok', text: 'Running', fix: '' })
      }
      return { ...state.controls }
    },
    inviteRequests: async () => [...state.invite_requests],
    invite: async (id) => {
      const req = find(id)
      const created = await concierge.create({ name: req.name, mobile: '9876500021', label: `${req.name}, website request` })
      drop(id)
      return { ...created, request: { ...req, status: 'invited' } }
    },
    dismiss: async (id) => {
      const req = find(id)
      drop(id)
      return { ...req, status: 'dismissed' }
    },
  }
}

const real = createAdminApi({ getToken })
let fake: AdminApi | null = null
const impl = (): AdminApi => (isFixtureMode() ? (fake ??= createFixtureAdminApi()) : real)

/** What the screen imports: the fixture API in fixture mode, else the real one. */
export const adminApi: AdminApi = {
  overview: () => impl().overview(),
  setControls: (c) => impl().setControls(c),
  inviteRequests: () => impl().inviteRequests(),
  invite: (id) => impl().invite(id),
  dismiss: (id) => impl().dismiss(id),
}
