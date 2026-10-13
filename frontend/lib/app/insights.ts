/** Owner Insights: GET/POST /api/v1/newsroom/insights/* (backend/app/modules/areastats/owner.py; docs/plan/insights-and-seo.md O1 O2 O6). */
import { API_BASE_URL } from '@/lib/config/api'
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

export type FoundState = 'searching' | 'stuck' | 'found' | 'added' | 'ignored'

export interface FoundItem {
  regno: string
  state: FoundState
  name: string | null
  first_seen: string | null
  last_seen: string | null
  tried_names: string[]
  owner_names: string[]
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
export const searchAs = (regno: string, name: string) => call<{ queued: boolean }>(`found/${encodeURIComponent(regno)}/search-as`, { name })
export const ignoreFound = (regno: string) => call<{ ignored: boolean }>(`found/${encodeURIComponent(regno)}/ignore`, {})
export const getSystem = () => call<SystemView>('system')
