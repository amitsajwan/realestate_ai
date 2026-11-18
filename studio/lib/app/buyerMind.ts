/** The buyer mind's Lead Brief for one lead (backend /buyer-mind, docs/plan/buyer-mind.md). It never sends anything: the agent
 * edits the draft and sends it from their own WhatsApp. */
import { API_BASE_URL } from '@shared/config/api'
import { ApiError, fetchOnceMore, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export interface BriefAlternative { slug: string; name: string | null; why: string | null }

export interface LeadBrief {
  buyer: string | null
  /** What their words and actions suggest: a reading, never told to the buyer as a fact. */
  implied: string[]
  unknown: string[]
  asked_for: string | null
  can_answer: 'yes' | 'partly' | 'no'
  /** Problems the agent must know or tell them (possession after their move-in date...). */
  flags: string[]
  alternatives: BriefAlternative[]
  /** A range with its source and date; indicative, never a quote. */
  price_idea: string | null
  next_step: string | null
  when: 'today' | 'tomorrow' | 'this week'
  temperature: 'hot' | 'warm' | 'cold'
  /** Null when the checks dropped it (see problems) or the brief came from the lead's facts alone. */
  draft: string | null
  why: string | null
  confidence: 'high' | 'medium' | 'low'
  /** What the checks left out, and why. */
  problems: string[]
  /** mind = the model thought it through; rules = the model gave nothing usable, so it is the lead's facts alone. */
  by: 'mind' | 'rules'
}

export interface BriefView {
  brief: LeadBrief | null
  at: string | null
  outcome: 'done' | 'forced' | 'failed' | null
  lookups: string[]
  profile: { said: Record<string, string>; implied: string[]; unknown: string[] } | null
}

export const EMPTY_VIEW: BriefView = { brief: null, at: null, outcome: null, lookups: [], profile: null }

async function call<T>(path: string, method = 'GET'): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let res: Response
  try {
    res = await fetchOnceMore(() => fetch(`${API_BASE_URL}/api/v1/buyer-mind${path}`, { method, headers }), method)
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your internet.')
  }
  const text = await res.text()
  let data: unknown = null
  if (text) {
    try { data = JSON.parse(text) } catch { data = { detail: text.slice(0, 200) } }
  }
  if (!res.ok) throw parseErrorBody(data, res.status)
  return data as T
}

export const buyerMindApi = {
  brief: (leadId: string): Promise<BriefView> =>
    (isFixtureMode() ? Promise.resolve(EMPTY_VIEW) : call<BriefView>(`/leads/${encodeURIComponent(leadId)}`)),
  /** Think about this lead now (a few seconds to a minute; once per 2 minutes a lead). */
  think: (leadId: string): Promise<BriefView> => {
    if (isFixtureMode()) return Promise.reject(new ApiError(400, 'The buyer brief needs the live app.'))
    return call<BriefView>(`/leads/${encodeURIComponent(leadId)}/think`, 'POST')
  },
}

export const TEMPERATURE_LABEL: Record<LeadBrief['temperature'], string> = { hot: '🔥 Hot', warm: 'Warm', cold: 'Cold' }
export const CAN_ANSWER_LABEL: Record<LeadBrief['can_answer'], string> = {
  yes: 'We can answer this', partly: 'We can partly answer this', no: 'We cannot answer this yet',
}
