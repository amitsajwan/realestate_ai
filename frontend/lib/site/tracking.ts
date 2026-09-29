// Client-side tracking helpers. Everything here fails silently: tracking must never break the page.
import { API_BASE_URL } from '@/lib/config/api'
import type { Attribution } from './types'

export type SiteEventType = 'page_view' | 'listing_view' | 'share' | 'call_click' | 'whatsapp_click'

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

export interface TouchBody {
  agent_slug: string
  anon_id: string
  listing_id?: string
  source?: string
  utm: Record<string, string>
}

export function buildTouch(agentSlug: string, listingId?: string): TouchBody {
  const a = readAttribution()
  const body: TouchBody = { agent_slug: agentSlug, anon_id: getAnonId(), utm: a.utm }
  if (listingId) body.listing_id = listingId
  if (a.source) body.source = a.source
  return body
}

export function trackEvent(type: SiteEventType, agentSlug: string, listingId?: string): void {
  try {
    const payload = JSON.stringify({ ...buildTouch(agentSlug, listingId), type })
    const url = API_BASE_URL + '/api/v1/t/event'
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

export interface InquiryInput {
  name: string
  phone: string
  message?: string
  consent: boolean
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
