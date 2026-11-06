/**
 * When the chat may speak first (docs/plan/chat-reach.md). The server picks the words from what the visitor read; this only keeps count
 * of the time the site has been in view and asks at a few moments. A note sits beside the chat button and never opens by itself.
 */
import { safeUrl, type ChatLink } from './chatApi'

export const TICK_SECONDS = 5
const ASK_AT = [30, 90, 120, 180]
const ASK_UNTIL = 1200
const SEEN_KEY = 'pp_chat_visit_s'
const OFF_KEY = 'pp_chat_nudge_off'
const MUTE_MS = 7 * 24 * 60 * 60 * 1000

/** Pages where a note would get in the way: a form being filled in, a sign-in, the agents' pages and agents' own sites. */
const QUIET = ['/enquire', '/login', '/register', '/join', '/onboarding', '/request-invite', '/trial', '/agents', '/for-agents', '/agent/', '/studio', '/dashboard', '/profile']

/** Seconds of this visit in view at which we ask the server: a few early, then each minute, since the visit worth a word may come late
 *  (2026-11-06: a visitor read for half an hour, then made a plan). The server says one note a day, whoever asks. */
export function askNow(seconds: number): boolean {
  return ASK_AT.includes(seconds) || (seconds > 180 && seconds <= ASK_UNTIL && seconds % 60 === 0)
}

export function nudgeAllowed(path: string): boolean {
  if (path === '/home-plan') return false      // answering the plan's questions; the plan itself is a fine moment
  return !QUIET.some((p) => path === p || path.startsWith(p.endsWith('/') ? p : p + '/'))
}

export function isMuted(now: number): boolean {
  try {
    const at = Number(window.localStorage.getItem(OFF_KEY) || 0)
    return !!at && now - at < MUTE_MS
  } catch {
    return true
  }
}

export function mute(now: number): void {
  try { window.localStorage.setItem(OFF_KEY, String(now)) } catch { /* ignore */ }
}

/** Adds to this tab's count and returns it. */
export function addSeconds(by: number): number {
  try {
    const next = Number(window.sessionStorage.getItem(SEEN_KEY) || 0) + by
    window.sessionStorage.setItem(SEEN_KEY, String(next))
    return next
  } catch {
    return 0
  }
}

export interface Nudge { text: string; quick_replies: string[]; link: ChatLink | null }

export function parseNudge(data: unknown): Nudge | null {
  const d = (data && typeof data === 'object' ? data : null) as Record<string, unknown> | null
  if (!d || typeof d.text !== 'string' || !d.text.trim()) return null
  const quick = Array.isArray(d.quick_replies) ? (d.quick_replies as unknown[]).filter((q): q is string => typeof q === 'string') : []
  const l = d.link as Record<string, unknown> | null | undefined
  const url = safeUrl(l?.url)
  return { text: d.text, quick_replies: quick, link: url && typeof l?.label === 'string' ? { label: l.label, url } : null }
}
