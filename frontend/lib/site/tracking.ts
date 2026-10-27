// Client-side tracking helpers. Everything here fails silently: tracking must never break the page.
import { API_BASE_URL } from '@/lib/config/api'
import { getToken } from '@/lib/app/session'
import type { Attribution } from './types'

export type SiteEventType = 'page_view' | 'listing_view' | 'share' | 'call_click' | 'whatsapp_click' | 'chat_open'

const KEY = 'site_anon_id'
let memoryId: string | null = null

function randomId(): string {
  const c = typeof crypto !== 'undefined' ? (crypto as Crypto) : undefined
  if (c && typeof c.randomUUID === 'function') return c.randomUUID().replace(/-/g, '')
  let s = ''
  for (let i = 0; i < 32; i++) s += Math.floor(Math.random() * 16).toString(16)
  return s
}

export function getAnonId(): string {
  try {
    const existing = window.localStorage.getItem(KEY)
    if (existing && existing.length >= 8) return existing
    const id = randomId()
    window.localStorage.setItem(KEY, id)
    return id
  } catch {
    if (!memoryId) memoryId = randomId()
    return memoryId
  }
}

const SRC_KEY = 'site_attribution'

/** Source + utm_* from the URL. First-touch is remembered for the tab session so navigation keeps attribution. */
export function readAttribution(search?: string): Attribution {
  const utm: Record<string, string> = {}
  let source: string | undefined
  try {
    const q = new URLSearchParams(search !== undefined ? search : window.location.search)
    const src = q.get('src')
    if (src) source = src.slice(0, 40)
    q.forEach((v, k) => {
      if (k.indexOf('utm_') === 0 && v) utm[k] = v.slice(0, 100)
    })
    if (source || Object.keys(utm).length) {
      try {
        window.sessionStorage.setItem(SRC_KEY, JSON.stringify({ source, utm }))
      } catch {
        /* ignore */
      }
      return { source, utm }
    }
    const saved = window.sessionStorage.getItem(SRC_KEY)
    if (saved) return JSON.parse(saved) as Attribution
  } catch {
    /* ignore */
  }
  return { source, utm }
}

const VISIT_KEY = 'site_visit'

export interface VisitPages {
  path?: string
  landing?: string
  referrer?: string
}

/** The current page, plus the first page of this tab session and the outside site that sent the visitor there. */
export function readVisitPages(): VisitPages {
  try {
    const path = window.location.pathname + window.location.search
    const saved = window.sessionStorage.getItem(VISIT_KEY)
    if (saved) return { path, ...(JSON.parse(saved) as VisitPages) }
    let referrer: string | undefined
    try {
      // our own pages are not a source; only an outside site is
      if (document.referrer && new URL(document.referrer).host !== window.location.host) referrer = document.referrer
    } catch {
      /* ignore */
    }
    const first: VisitPages = { landing: path, ...(referrer ? { referrer } : {}) }
    try {
      window.sessionStorage.setItem(VISIT_KEY, JSON.stringify(first))
    } catch {
      /* ignore */
    }
    return { path, ...first }
  } catch {
    return {}
  }
}

export interface TouchBody extends VisitPages {
  agent_slug: string
  anon_id: string
  listing_id?: string
  source?: string
  utm: Record<string, string>
}

export function buildTouch(agentSlug: string, listingId?: string): TouchBody {
  const a = readAttribution()
  const body: TouchBody = { agent_slug: agentSlug, anon_id: getAnonId(), utm: a.utm, ...readVisitPages() }
  if (listingId) body.listing_id = listingId
  if (a.source) body.source = a.source
  return body
}

function post(route: string, body: object): void {
  try {
    const payload = JSON.stringify(body)
    const url = API_BASE_URL + '/api/v1/t/' + route
    if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
      const blob = new Blob([payload], { type: 'application/json' })
      if (navigator.sendBeacon(url, blob)) return
    }
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      keepalive: true,
    }).catch(() => undefined)
  } catch {
    /* never throw from tracking */
  }
}

/** A browser signed in to Studio is the agent's own: its visits show as "You" in the Live panel and are not counted. */
function isStaff(): boolean {
  try {
    return !!getToken()
  } catch {
    return false
  }
}

/** `viewId` names this page view, so its "still reading" pings (startReading) add their time to it. */
export function trackEvent(type: SiteEventType, agentSlug: string, listingId?: string, viewId?: string): void {
  try {
    post('event', { ...buildTouch(agentSlug, listingId), type, ...(viewId ? { view_id: viewId } : {}), ...(isStaff() ? { staff: true } : {}) })
  } catch {
    /* never throw from tracking */
  }
}

export function newViewId(): string {
  return randomId().slice(0, 24)
}

export const PING_EVERY_MS = 30_000
export const MAX_PINGS = 40 // 20 minutes of pings per page; the server caps one page's reading time at 30 minutes anyway

/**
 * Counts the seconds this page is visible (a hidden tab is not reading) and tells the server every 30 s, when the tab is
 * hidden, and when the page is left. Plan: docs/plan/site-live-presence.md D1. Returns the stop function, which sends the last
 * count. Sends nothing if the seconds have not grown since the last ping.
 */
export function startReading(agentSlug: string, viewId: string, now: () => number = Date.now): () => void {
  if (typeof document === 'undefined' || typeof window === 'undefined') return () => undefined
  let shown = 0
  let since: number | null = document.visibilityState === 'hidden' ? null : now()
  let sent = 0
  let pings = 0
  const seconds = () => Math.floor((shown + (since === null ? 0 : now() - since)) / 1000)
  const flush = () => {
    const s = seconds()
    if (s <= sent || pings >= MAX_PINGS) return
    sent = s
    pings += 1
    post('ping', { agent_slug: agentSlug, anon_id: getAnonId(), view_id: viewId, seconds: s })
  }
  const onVisibility = () => {
    if (document.visibilityState === 'hidden') {
      if (since !== null) shown += now() - since
      since = null
      flush()
    } else if (since === null) {
      since = now()
    }
  }
  const timer = window.setInterval(() => { if (since !== null) flush() }, PING_EVERY_MS)
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('pagehide', flush)
  return () => {
    window.clearInterval(timer)
    document.removeEventListener('visibilitychange', onVisibility)
    window.removeEventListener('pagehide', flush)
    flush()
  }
}

export interface InquiryInput {
  name: string
  phone: string
  message?: string
  consent: boolean
  bhk?: number
  budget_min_inr?: number
  budget_max_inr?: number | null
  timeline?: string
  financing?: string
}

export async function submitInquiry(agentSlug: string, listingId: string | undefined, input: InquiryInput): Promise<boolean> {
  try {
    const res = await fetch(API_BASE_URL + '/api/v1/t/inquiry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...buildTouch(agentSlug, listingId), ...input }),
    })
    return res.ok
  } catch {
    return false
  }
}
