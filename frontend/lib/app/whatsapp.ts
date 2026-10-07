/** Studio client for WhatsApp chats (backend /whatsapp/conversations) and agent notifications (/notifications). Self-contained so the
 * shared AppApi does not change; in fixture mode it returns empty lists. */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export interface WhatsAppMessage {
  role: 'user' | 'bot'
  text: string
  ts: string
  /** For our replies: sent | dry_run (test mode, not sent) | refused (outside 24 hours) | failed */
  status?: string | null
}
export interface WhatsAppConversation {
  id: string
  channel: 'whatsapp'
  name: string | null
  /** Masked, like +91 98******10. The full number is on the lead. */
  phone: string
  lead_id: string | null
  summary: string
  needs_human: boolean
  opted_out: boolean
  updated_at: string | null
  language: string
  interest_title: string | null
  window_open: boolean
  messages: WhatsAppMessage[]
}
export interface AppNotification {
  id: string
  kind: 'new_whatsapp_lead' | 'whatsapp_needs_you' | string
  summary: string
  ref: { lead_id?: string; conversation_id?: string }
  created_at: string
  read: boolean
}
export interface NotificationList {
  items: AppNotification[]
  unread: number
}

type FetchImpl = typeof fetch

async function request<T>(path: string, init: { method?: string } = {}, fetchImpl?: FetchImpl): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let res: Response
  try {
    res = await (fetchImpl ?? fetch)(`${API_BASE_URL}/api/v1${path}`, { method: init.method ?? 'GET', headers })
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

export async function getWhatsAppConversations(fetchImpl?: FetchImpl): Promise<WhatsAppConversation[]> {
  if (isFixtureMode()) return []
  const data = await request<WhatsAppConversation[]>('/whatsapp/conversations', {}, fetchImpl)
  return Array.isArray(data) ? data : []
}

export async function getNotifications(unreadOnly = false, fetchImpl?: FetchImpl): Promise<NotificationList> {
  if (isFixtureMode()) return { items: [], unread: 0 }
  const data = await request<NotificationList>(`/notifications${unreadOnly ? '?unread=true' : ''}`, {}, fetchImpl)
  return { items: data?.items ?? [], unread: data?.unread ?? 0 }
}

export async function markNotificationRead(id: string, fetchImpl?: FetchImpl): Promise<void> {
  if (isFixtureMode()) return
  await request<unknown>(`/notifications/${encodeURIComponent(id)}/read`, { method: 'POST' }, fetchImpl)
}

export const REPLY_STATUS_LABEL: Record<string, string> = {
  sent: 'Sent',
  dry_run: 'Test mode, not sent',
  refused: 'Not sent: more than 24 hours since they wrote',
  failed: 'Could not send',
}
