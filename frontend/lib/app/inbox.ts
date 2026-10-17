/** Studio Inbox: every conversation (WhatsApp, Messenger/Instagram, website chat) in one list, one thread per person (backend /conversations). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, fetchOnceMore, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export type InboxChannel = 'whatsapp' | 'messenger' | 'instagram' | 'website' | 'facebook_comment' | 'instagram_comment'
/** them = the person who wrote to us; bot = our assistant; you = a person on our side (sent from the inbox). */
export type InboxFrom = 'them' | 'bot' | 'you'

export interface InboxThread {
  id: string
  channel: InboxChannel | string
  name: string | null
  /** Masked by the server, like 99******83 (WhatsApp only). */
  phone: string
  role: 'agent' | 'buyer' | string
  last_text: string
  last_from: InboxFrom | null
  last_at: string | null
  /** Their message is the last one: nobody has answered it. */
  needs_you: boolean
  lead_id: string | null
  lead_saved: boolean
  window_open: boolean
  opted_out: boolean
  can_reply: boolean
  summary: string
  messages: number
  /** out = you passed this buyer to an agent; in = the owner passed this buyer to you. */
  passed: 'out' | 'in' | null
  passed_at: string | null
  /** Comments: the post they commented on, and why it needs you. */
  post_url?: string | null
  reason?: string | null
}

export interface InboxMessage {
  from: InboxFrom
  text: string
  at: string | null
  status: string | null
  error: string | null
}

export interface InboxThreadFull extends InboxThread {
  thread: InboxMessage[]
  bot_paused_until: string | null
  /** The owner may pass this buyer to an agent. */
  can_pass?: boolean
  passed_to_name: string | null
}

export interface PassAgent {
  agent_id: string
  name: string
  has_whatsapp: boolean
}

export interface PassResult {
  passed_to: string
  lead_id: string | null
  /** wa.me link to the agent with the buyer's details, sent from the owner's own WhatsApp. Null if the agent's site has no mobile. */
  whatsapp_url: string | null
}

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
    res = await fetchOnceMore(() => fetch(`${API_BASE_URL}/api/v1/conversations${path}`, { method: init.method ?? 'GET', headers, body }), init.method)
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

export const inboxApi = {
  threads: async (): Promise<InboxThread[]> => (isFixtureMode() ? [] : (await call<{ items: InboxThread[] }>('')).items ?? []),
  thread: (id: string) => call<InboxThreadFull>(`/${encodeURIComponent(id)}`),
  reply: (id: string, text: string) => call<InboxThreadFull>(`/${encodeURIComponent(id)}/reply`, { method: 'POST', json: { text } }),
  /** A comment thread was answered on Facebook/Instagram (or needs no answer). */
  done: (id: string) => call<InboxThreadFull>(`/${encodeURIComponent(id)}/done`, { method: 'POST' }),
  agents: async (): Promise<PassAgent[]> => (await call<{ items: PassAgent[] }>('/agents')).items ?? [],
  pass: (id: string, agentId: string) => call<PassResult>(`/${encodeURIComponent(id)}/pass`, { method: 'POST', json: { agent_id: agentId } }),
}

export const CHANNEL_LABEL: Record<string, string> = {
  whatsapp: 'WhatsApp', messenger: 'Messenger', instagram: 'Instagram', website: 'Website chat',
  facebook_comment: 'Facebook comment', instagram_comment: 'Instagram comment',
}
export const isComment = (channel: string) => channel.endsWith('_comment')
export const CHANNEL_CHIP: Record<string, string> = {
  whatsapp: 'bg-green-100 text-green-800', messenger: 'bg-blue-100 text-blue-800', instagram: 'bg-purple-100 text-purple-800', website: 'bg-gray-100 text-gray-700',
  facebook_comment: 'bg-blue-50 text-blue-800 ring-1 ring-blue-200', instagram_comment: 'bg-purple-50 text-purple-800 ring-1 ring-purple-200',
}
