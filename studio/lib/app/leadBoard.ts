/** Lead board (backend /lead-board, inbox/board.py): the owner's open buyer leads without name or number, for signed-in agents to ask for. */
import { API_BASE_URL } from '@shared/config/api'
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

export interface BoardActivity {
  /** Pages in the order first opened, with minutes read (0 = under half a minute). */
  pages: { label: string; minutes: number }[]
  more_pages: number
  page_count: number
  projects_seen: number
  visits: number
  days: number
  read_min: number
  device: 'Phone' | 'Tablet' | 'Computer' | null
  city: string | null
  taps: string[]
  enquiries: number
}

/** "2 visits on 2 days · 9 min reading · Phone · Wagholi" */
export function activityLine(a: BoardActivity): string {
  const parts = [
    a.visits ? `${a.visits} visit${a.visits === 1 ? '' : 's'}${a.days > 1 ? ` on ${a.days} days` : ''}` : null,
    a.read_min ? `${a.read_min} min reading` : null,
    a.device,
    a.city,
  ]
  return parts.filter(Boolean).join(' · ')
}

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
  /** talked = they wrote back or picked up our call; number = they left a mobile number, nothing more yet; no_number = they said what
   *  they want but left no number. */
  genuine: 'called' | 'replied' | 'number' | 'no_number'
  signals: string[]
  /** What they did on the site (no names or numbers). */
  activity: BoardActivity
  /** A reason to look twice, e.g. they also opened our pages for agents. */
  caution: string | null
  /** How many agents asked (offers stay sealed). */
  asked: number
  mine: BoardAsk | null
  /** "Given to an agent 2 hours after it came in": another agent has it, so it cannot be asked for. */
  given: string | null
  /** Owner only. */
  lead_id?: string
  asks?: OwnerAsk[]
}

/** Owner: an agent to send the board to from the owner's own WhatsApp. */
export interface BoardAgent { agent_id: string; name: string; first_name: string; whatsapp: string; listings: number; asked: number }

/** What buyers did on our pages in the last `days` (robots and our own browsers left out): real activity, never made up. */
export interface BoardDemand {
  days: number
  /** People who read our pages. */
  visitors: number
  enquiries: number
  /** Leads on the board that came in within `days`. */
  new_leads: number
  /** Most-read areas: people who read the area's pages, and enquiries made on them. */
  areas: { area: string; readers: number; enquiries: number }[]
}

export interface Board { items: BoardCard[]; owner: boolean; /** "View as an agent": read only. */ preview?: boolean; demand?: BoardDemand }

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
  /** asAgent: the board as any other agent sees it. */
  get: (asAgent = false) => call<Board>(asAgent ? '?as_agent=true' : ''),
  ask: (ref: string, offer_kind: OfferKind, offer_value: number | null, note: string) =>
    call<BoardAsk>(`/${encodeURIComponent(ref)}/ask`, { method: 'POST', json: { offer_kind, offer_value, note: note || null } }),
  withdraw: (ref: string) => call<{ ok: boolean }>(`/${encodeURIComponent(ref)}/ask`, { method: 'DELETE' }),
  /** Owner: take a lead off the board. */
  remove: (ref: string) => call<{ ok: boolean }>(`/${encodeURIComponent(ref)}/remove`, { method: 'POST' }),
  /** Owner: the agents to send the board to. */
  agents: async (): Promise<BoardAgent[]> => (await call<{ items: BoardAgent[] }>('/agents')).items ?? [],
  give: (ref: string, agentId: string) => call<PassResult>(`/${encodeURIComponent(ref)}/give`, { method: 'POST', json: { agent_id: agentId } }),
}

/** Leads per area, busiest first (ties by name): the counts on the area chips. A lead in two areas counts in both. */
export function areaCounts(items: Pick<BoardCard, 'areas'>[]): { area: string; count: number }[] {
  const n = new Map<string, number>()
  for (const c of items) for (const a of new Set(c.areas)) n.set(a, (n.get(a) ?? 0) + 1)
  return Array.from(n, ([area, count]) => ({ area, count })).sort((x, y) => y.count - x.count || x.area.localeCompare(y.area))
}

/** The card's headline: the project they asked about, else what and where. */
export function boardTitle(c: Pick<BoardCard, 'project' | 'bhk' | 'areas'>): string {
  if (c.project) return c.project
  const where = c.areas.slice(0, 2).join(', ')
  return `${c.bhk ?? 'A home'}${where ? ` in ${where}` : ' in Pune'}`
}

/** The WhatsApp text the owner sends agents with the link: how many buyers, and where. */
export function shareText(items: BoardCard[], url: string, firstName?: string): string {
  const areas = Array.from(new Set(items.flatMap((c) => c.areas))).slice(0, 4)
  const replied = items.filter((c) => c.genuine === 'called' || c.genuine === 'replied').length
  return [
    ...(firstName ? [`Namaste ${firstName} ji, Avasetu team here.`] : []),
    `${items.length} buyer lead${items.length === 1 ? '' : 's'} on Avasetu${areas.length ? ` (${areas.join(', ')})` : ''}${replied ? `, ${replied} already replied to us` : ''}.`,
    'See what each buyer wants and ask for the ones you can serve. Name and number come to you when the lead is given to you.',
    url,
    'Avasetu team',
  ].join('\n\n')
}
