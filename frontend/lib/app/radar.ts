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
}

export type RadarLabel = 'sent' | 'skipped' | 'converted'
export type SkipReason = 'broker' | 'not_buyer' | 'wrong_area' | 'already_answered' | 'old' | 'other'

export interface RadarMetrics {
  by_source: Record<string, Record<string, number>>
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
}
