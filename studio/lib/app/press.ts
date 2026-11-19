/** The monthly press agent: this month's story facts and the pitch drafts to Pune journalists (backend
 * app/modules/press). Owner only. The owner sends every pitch by hand (CLAUDE.md rule 6: nothing here sends). */
import { API_BASE_URL } from '@shared/config/api'
import { ApiError, parseErrorBody } from './api'
import { getToken } from './session'
import { isFixtureMode } from './client'
import { pressFixture } from './fixtures-owner'

export interface PressFact {
  text: string
  area: string | null
  topic: string
  source: string
  as_of: string
}

export interface PressStory {
  month: string | null
  facts: PressFact[]
  headline_facts: PressFact[]
}

export interface PressJournalist {
  name: string | null
  outlet: string
  email: string | null
  contact_page: string | null
}

export interface PressArticle {
  title: string
  url: string
  date: string
}

export type PressStatus = 'draft' | 'sent' | 'skipped'

export interface PressPitch {
  id: string
  month: string
  journalist: PressJournalist
  article: PressArticle
  email: string | null
  subject: string
  body: string
  origin: 'llm' | 'template' | string
  status: PressStatus
  replied: boolean
  link_won_url: string | null
}

export interface PressSummary {
  sent: number
  replied: number
  links_won: number
}

export interface PressPitchPatch {
  subject?: string
  body?: string
  status?: PressStatus
  replied?: boolean
  link_won_url?: string | null
}

async function request<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
  if (isFixtureMode()) return pressFixture(path, init.method, init.json) as T
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
    res = await fetch(`${API_BASE_URL}/api/v1/press${path}`, { method: init.method ?? 'GET', headers, body })
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

export const pressApi = {
  story: () => request<PressStory>('/story'),
  pitches: (month?: string) => request<PressPitch[]>(`/pitches${month ? `?month=${encodeURIComponent(month)}` : ''}`),
  summary: () => request<PressSummary>('/summary'),
  patch: (id: string, body: PressPitchPatch) => request<PressPitch>(`/pitches/${encodeURIComponent(id)}`, { method: 'PATCH', json: body }),
  runNow: () => request<{ month: string; facts: number; pitches: number; pruned: number }>('/run', { method: 'POST' }),
}

/** A Gmail compose link for this pitch: the owner reviews, then sends from their own account. Falls back to `mailto:`
 * when there is no email on file (the owner finds the contact first). */
export function gmailComposeUrl(pitch: PressPitch): string {
  const to = pitch.email ?? ''
  const params = new URLSearchParams({ view: 'cm', fs: '1', to, su: pitch.subject, body: pitch.body })
  return `https://mail.google.com/mail/?${params.toString()}`
}

export function mailtoUrl(pitch: PressPitch): string {
  const params = new URLSearchParams({ subject: pitch.subject, body: pitch.body })
  return `mailto:${pitch.email ?? ''}?${params.toString()}`
}
