// Client-side tracking helpers. Everything here fails silently: tracking must never break the page.
import { API_BASE_URL } from '@/lib/config/api'
import { getToken } from '@shared/session'
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

const LAST_KEY = 'site_last_page'
const CLICK_KEY = 'site_last_click'
const CLICK_FRESH_MS = 30_000 // a tap this recent on a link to this page is how they got here
const BACK_FRESH_MS = 5_000
const LINK_LEN = 80
let watching = false
let poppedAt = 0

export type Via = 'link' | 'back' | 'new_tab' | 'reload'

/** How a page view was reached inside the site: the page before it, how they moved, and the tapped link's words. */
export interface StepFrom {
  prev?: string
  via?: Via
  link?: string
}

/** The words a visitor saw on a link: its own text, else its label, else a picture's description. */
export function linkWords(a: Element): string {
  const own = (a.textContent || '').replace(/\s+/g, ' ').trim()
  const label = a.getAttribute('aria-label') || a.getAttribute('title') || a.querySelector('img[alt]')?.getAttribute('alt') || ''
  return (own || label.trim()).slice(0, LINK_LEN)
}

/**
 * Starts noticing taps on links to our own pages and the Back/Forward buttons, once per tab, so the next page view can say how it
 * was reached (readStep). Captures before the site's own handlers, and never stops a click.
 */
export function watchNavigation(): void {
  if (watching || typeof window === 'undefined') return
  watching = true
  try {
    document.addEventListener('click', (ev) => {
      try {
        const a = (ev.target as Element | null)?.closest?.('a[href]') as HTMLAnchorElement | null
        if (!a) return
        const to = new URL(a.href, window.location.href)
        if (to.host !== window.location.host) return
        window.sessionStorage.setItem(CLICK_KEY, JSON.stringify({ to: to.pathname, text: linkWords(a), at: Date.now() }))
      } catch {
        /* ignore */
      }
    }, true)
    window.addEventListener('popstate', () => { poppedAt = Date.now() })
  } catch {
    /* ignore */
  }
}

/**
 * Where this page view came from inside the site. Call once per view: it moves this tab's "last page" on to this one. The first
 * page of a tab opened from one of our pages names that page (a new tab); a page after the first says if they tapped a link (and
 * its words) or went back. A reload names no earlier page.
 */
export function readStep(now: () => number = Date.now): StepFrom {
  try {
    const path = window.location.pathname
    const last = window.sessionStorage.getItem(LAST_KEY)
    window.sessionStorage.setItem(LAST_KEY, path)
    let click: { to?: string; text?: string; at?: number } | null = null
    try {
      click = JSON.parse(window.sessionStorage.getItem(CLICK_KEY) || 'null')
    } catch {
      click = null
    }
    window.sessionStorage.removeItem(CLICK_KEY)
    if (!last) {
      try {
        const r = document.referrer ? new URL(document.referrer) : null
        if (r && r.host === window.location.host && r.pathname !== path) return { prev: r.pathname, via: 'new_tab' }
      } catch {
        /* ignore */
      }
      return {}
    }
    if (last === path) return { via: 'reload' }
    if (click && click.to === path && now() - (click.at || 0) <= CLICK_FRESH_MS) {
      return { prev: last, via: 'link', ...(click.text ? { link: click.text } : {}) }
    }
    if (poppedAt && now() - poppedAt >= 0 && now() - poppedAt <= BACK_FRESH_MS) return { prev: last, via: 'back' }
    return { prev: last } // moved some other way: the search box, a button, a form
  } catch {
    return {}
  }
}

/** `viewId` names this page view, so its "still reading" pings (startReading) add their time to it. `step` says how it was reached. */
export function trackEvent(type: SiteEventType, agentSlug: string, listingId?: string, viewId?: string, step?: StepFrom): void {
  try {
    post('event', {
      ...buildTouch(agentSlug, listingId), type, ...(viewId ? { view_id: viewId } : {}), ...(step || {}), ...(isStaff() ? { staff: true } : {}),
    })
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
  /** the "Call me back" button: the number only, so the name may be empty (backend InquiryIn.callback) */
  callback?: boolean
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
