import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { getToken } from './session'

/** People publicly asking about homes, found by the radar (backend docs/RADAR.md). Operator only. */
export interface RadarMatch {
  listing_id: string
  title: string
  locality: string
  bhk: number | null
  price_inr: number | null
}

/** What the AI read from the comment (backend radar/models.py Intent). */
export interface RadarIntent {
  role: 'buyer' | 'renter' | 'investor' | 'broker' | 'seller' | 'noise'
  intent: number
  stage: 'exploring' | 'comparing' | 'ready' | 'post_visit' | 'unknown'
  area: string | null
  project: string | null
  property_type?: string | null
  bhk: number | null
  budget_min_inr: number | null
  budget_max_inr: number | null
  timeline: string | null
  language: string
  question: string | null
  answered_already: boolean
}

export interface RadarSignal {
  id: string
  source: string
  url: string
  text: string
  context: string
  author: string
  posted_at: string | null
  status: string
  area: string | null
  score: number | null
  why: string[] | null
  matches: RadarMatch[] | null
  draft: string | null
  link: string | null
  intent: RadarIntent | null
  project: { name: string; regno: string; path: string; line: string } | null
  critic?: { helpful?: number; human?: number; grounded?: boolean; notes?: string[] } | null
  draft_origin?: 'llm' | 'rewrite' | 'writer' | 'template' | null
  learn?: boolean | null
  asked_again?: number | null
  clicks?: number | null
  agent_id?: string | null
  followup?: RadarFollowup | null
}

export interface RadarFollowup {
  state: 'waiting' | 'waiting_2' | 'replied' | 'clicked' | 'nudge' | 'closed'
  due_at: string | null
  their_reply?: string
  draft?: string
}

export type RadarSource = 'youtube' | 'reddit' | 'rss' | 'instagram'
export type RadarWatchKind = 'query' | 'video' | 'subreddit' | 'feed' | 'hashtag'
export const WATCH_KINDS: Record<RadarSource, RadarWatchKind[]> = {
  youtube: ['query', 'video'], reddit: ['subreddit', 'query'], rss: ['feed'], instagram: ['hashtag'],
}

export interface RadarWatch {
  id: string
  source: RadarSource
  kind: RadarWatchKind
  value: string
  area: string | null
  title: string | null
  active: boolean
  hits: number | null
  checks: number | null
  converted: number | null
  mean: number
  origin: string | null
  reason: string | null
  retired: string | null
}

export interface RadarTheme { theme: string; count: number; faq: string; examples: string[] }
export interface RadarDemand { area: string; name: string; weeks: { week: string; questions: number; themes: RadarTheme[] }[] }

export interface RadarRuns {
  discovery: { _id: string; started_at: string; summary: string; proposed: { source: string; kind: string; value: string; area: string | null; reason: string }[]; steps: { thought: string; tool: string }[] }[]
  jobs: { _id: string; at: string; result?: Record<string, unknown> }[]
  models: { kind: string; at: string; active?: boolean; eval?: Record<string, unknown>; rules?: string[] }[]
}

export type RadarLabel = 'sent' | 'skipped' | 'converted'
export type SkipReason = 'broker' | 'not_buyer' | 'wrong_area' | 'already_answered' | 'old' | 'other'

export interface RadarMetrics {
  by_source: Record<string, Record<string, number>>
  by_area: Record<string, Record<string, number>>
  precision_at_10: number | null
  llm_calls: number
  llm_per_shown: number | null
  llm_today: number
  searches_today: number
}

async function request<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let body: string | undefined
  if (init.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(init.json)
  }
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/radar${path}`, { method: init.method ?? 'GET', headers, body })
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

export const radarApi = {
  signals: (area?: string) => request<RadarSignal[]>(`/signals${area ? `?area=${encodeURIComponent(area)}` : ''}`),
  label: (id: string, label: RadarLabel, reason?: SkipReason, finalReply?: string) =>
    request<{ ok: boolean }>(`/signals/${encodeURIComponent(id)}/label`, {
      method: 'POST',
      json: { label, reason: reason ?? null, final_reply: finalReply ?? null },
    }),
  manual: (url: string, text: string, area?: string) =>
    request<RadarSignal>('/manual', { method: 'POST', json: { url, text, area: area || null } }),
  metrics: () => request<RadarMetrics>('/metrics'),
  followups: () => request<RadarSignal[]>('/followups'),
  followupDone: (id: string, action: 'sent' | 'handed' | 'closed') =>
    request<{ ok: boolean }>(`/followups/${encodeURIComponent(id)}`, { method: 'POST', json: { action } }),
  watches: () => request<RadarWatch[]>('/watches'),
  addWatch: (source: RadarSource, kind: RadarWatchKind, value: string, area?: string) =>
    request<{ ok: boolean }>('/watches', { method: 'POST', json: { source, kind, value, area: area || null } }),
  toggleWatch: (id: string, active: boolean) =>
    request<{ ok: boolean }>(`/watches/${encodeURIComponent(id)}`, { method: 'PATCH', json: { active } }),
  themes: () => request<RadarDemand[]>('/themes'),
  runs: () => request<RadarRuns>('/runs'),
}
