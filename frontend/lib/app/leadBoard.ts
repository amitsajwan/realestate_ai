/** Lead board (backend /lead-board, inbox/board.py): the owner's open buyer leads without name or number, for signed-in agents to ask for. */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, fetchOnceMore, parseErrorBody } from './api'
import type { PassResult } from './inbox'
import { getToken } from './session'

export type OfferKind = 'none' | 'fee' | 'share'

export interface BoardAsk {
  offer_kind: OfferKind
  offer_value: number | null
  /** "₹2,000 for the lead", "25% of the brokerage on closing", or null for no offer. */
  offer: string | null
  note: string | null
  at: string
}

export interface OwnerAsk extends BoardAsk { agent_id: string; agent_name: string }

export interface BoardCard {
  ref: string
  project: string | null
  areas: string[]
  bhk: string | null
  budget: string | null
  when: string | null
  paying: string | null
  wants: string | null
  came_from: string
  /** "Came in 2 days ago" */
  age: string
  created_at: string
  last_active_at: string
  temperature: 'hot' | 'warm' | 'cold'
  /** talked = they wrote back or picked up our call; number = they left a mobile number, nothing more yet. */
  genuine: 'talked' | 'number'
  signals: string[]
  /** How many agents asked (offers stay sealed). */
  asked: number
  mine: BoardAsk | null
  /** Passed to an agent before (by hand or a rule): giving it moves it from them. */
  with_agent: boolean
  /** Owner only. */
  lead_id?: string
  /** Owner only: the agent who has it now. */
  holder?: string | null
  asks?: OwnerAsk[]
}

export interface Board { items: BoardCard[]; owner: boolean; days: number }

/** The link the owner sends to agents. */
export const BOARD_PATH = '/studio/lead-board'

async function call<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
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
    res = await fetchOnceMore(() => fetch(`${API_BASE_URL}/api/v1/lead-board${path}`, { method: init.method ?? 'GET', headers, body }), init.method)
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

export const boardApi = {
  get: () => call<Board>(''),
  ask: (ref: string, offer_kind: OfferKind, offer_value: number | null, note: string) =>
    call<BoardAsk>(`/${encodeURIComponent(ref)}/ask`, { method: 'POST', json: { offer_kind, offer_value, note: note || null } }),
  withdraw: (ref: string) => call<{ ok: boolean }>(`/${encodeURIComponent(ref)}/ask`, { method: 'DELETE' }),
  /** Owner: take a lead off the board. */
  remove: (ref: string) => call<{ ok: boolean }>(`/${encodeURIComponent(ref)}/remove`, { method: 'POST' }),
  give: (ref: string, agentId: string) => call<PassResult>(`/${encodeURIComponent(ref)}/give`, { method: 'POST', json: { agent_id: agentId } }),
}

/** The card's headline: the project they asked about, else what and where. */
export function boardTitle(c: Pick<BoardCard, 'project' | 'bhk' | 'areas'>): string {
  if (c.project) return c.project
  const where = c.areas.slice(0, 2).join(', ')
  return `${c.bhk ?? 'A home'}${where ? ` in ${where}` : ' in Pune'}`
}

/** The WhatsApp text the owner sends agents with the link: how many buyers, and where. */
export function shareText(items: BoardCard[], url: string): string {
  const areas = Array.from(new Set(items.flatMap((c) => c.areas))).slice(0, 4)
  const talked = items.filter((c) => c.genuine === 'talked').length
  return [
    `${items.length} buyer lead${items.length === 1 ? '' : 's'} on Avasetu${areas.length ? ` (${areas.join(', ')})` : ''}${talked ? `, ${talked} already spoke with us` : ''}.`,
    'See what each buyer wants and ask for the ones you can serve. Name and number come to you when the lead is given to you.',
    url,
    'Avasetu team',
  ].join('\n\n')
}
