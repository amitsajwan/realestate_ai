/** Studio Inbox: every conversation (WhatsApp, Messenger/Instagram, website chat) in one list, one thread per person (backend /conversations). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export type InboxChannel = 'whatsapp' | 'messenger' | 'instagram' | 'website'
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
    res = await fetch(`${API_BASE_URL}/api/v1/conversations${path}`, { method: init.method ?? 'GET', headers, body })
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
}

export const CHANNEL_LABEL: Record<string, string> = { whatsapp: 'WhatsApp', messenger: 'Messenger', instagram: 'Instagram', website: 'Website chat' }
export const CHANNEL_CHIP: Record<string, string> = {
  whatsapp: 'bg-green-100 text-green-800', messenger: 'bg-blue-100 text-blue-800', instagram: 'bg-purple-100 text-purple-800', website: 'bg-gray-100 text-gray-700',
}
