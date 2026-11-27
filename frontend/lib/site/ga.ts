// Google Analytics 4 for the public site (docs/plan/ga4.md). A second count beside our own tracking, real phones' page speed, and
// Search Console beside what visitors did, in Google's reports. Our own events stay the record of leads and visits.
// Everything here fails silently and does nothing when the tag is off: tracking must never break the page.
import { chatContextFromPath } from './chatContext'

/** The Avasetu web stream's Measurement ID (public, not a secret). NEXT_PUBLIC_GA_ID overrides it; set it empty to turn GA4 off. */
export const DEFAULT_GA_ID = 'G-3MYR5F1C05'

/** The Measurement ID to send to, or '' when GA4 is off. Only production builds send: dev, tests and `next dev` never count. */
export function gaId(env?: { NEXT_PUBLIC_GA_ID?: string; NODE_ENV?: string }): string {
  // read by name: Next writes only literal process.env.NEXT_PUBLIC_* reads into the browser bundle, never process.env whole
  const nodeEnv = env ? env.NODE_ENV : process.env.NODE_ENV
  const raw = env ? env.NEXT_PUBLIC_GA_ID : process.env.NEXT_PUBLIC_GA_ID
  if (nodeEnv !== 'production') return ''
  const id = (raw ?? DEFAULT_GA_ID).trim()
  return /^G-[A-Z0-9]{4,20}$/.test(id) ? id : ''
}

type Gtag = (...args: unknown[]) => void

/** gtag.js's own address for this stream; TrackingBeacon loads it with next/script. */
export function gaScriptSrc(id: string): string {
  return 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id)
}

/**
 * The gtag queue, set up once per tab before the first event: Google's standard snippet, done here rather than in an inline
 * script so a page view sent while gtag.js is still loading waits in the queue behind the config instead of being lost.
 * send_page_view is off: TrackingBeacon sends each page view itself (not a 404, not a Studio user's visit), with its dimensions.
 */
function gtagOf(id: string = gaId()): Gtag | undefined {
  if (!id || typeof window === 'undefined') return undefined
  const w = window as unknown as { gtag?: Gtag; dataLayer?: unknown[] }
  if (typeof w.gtag !== 'function') {
    w.dataLayer = w.dataLayer || []
    w.gtag = function gtag() {
      // gtag.js reads the arguments object itself, not an array
      // eslint-disable-next-line prefer-rest-params
      w.dataLayer!.push(arguments)
    }
    w.gtag('js', new Date())
    w.gtag('config', id, { send_page_view: false })
  }
  return w.gtag
}

/** Our event names -> GA4's. Page views are sent as GA4's own page_view; an enquiry is GA4's recommended generate_lead. */
export const GA_EVENT_NAMES: Record<string, string> = {
  page_view: 'page_view',
  listing_view: 'page_view',
  share: 'share',
  call_click: 'call_click',
  whatsapp_click: 'whatsapp_click',
  chat_open: 'chat_open',
  satellite_open: 'satellite_open',
  streetview_open: 'streetview_open',
  inquiry: 'generate_lead',
}

export interface PageParams {
  page_type: string
  area?: string
  agent: string
  in_search: 'yes' | 'no'
}

/** What GA4 is told about a page: its kind, its place, whose site it is, and whether it asks to be in Google's index. */
export function pageParams(pathname: string, agentSlug: string, robots?: string | null): PageParams {
  const ctx = chatContextFromPath(pathname) || {}
  const p: PageParams = {
    page_type: ctx.page || 'other',
    agent: agentSlug || 'avasetu',
    in_search: /noindex/i.test(robots || '') ? 'no' : 'yes',
  }
  if (ctx.locality) p.area = ctx.locality
  return p
}

function currentPageParams(agentSlug: string): PageParams {
  const robots = document.querySelector('meta[name="robots"]')?.getAttribute('content')
  return pageParams(window.location.pathname, agentSlug, robots)
}

/** Sends one of our events to GA4 under its GA4 name, with the page's dimensions. Unknown names are not sent. */
export function gaEvent(type: string, agentSlug: string, extra?: Record<string, string | number>): void {
  try {
    const gtag = gtagOf()
    const name = GA_EVENT_NAMES[type]
    if (!gtag || !name) return
    const params: Record<string, unknown> = { ...currentPageParams(agentSlug), ...(extra || {}) }
    if (name === 'page_view') {
      params.page_location = window.location.href
      params.page_title = document.title
    }
    gtag('event', name, params)
  } catch {
    /* never throw from tracking */
  }
}

export interface Vital {
  id: string
  name: string
  value: number
  rating?: string
}

/** A Core Web Vital as a GA4 event: CLS is a small fraction, so it is sent x1000 to keep it as a whole number. */
export function vitalParams(m: Vital, agentSlug: string, pathname: string): Record<string, string | number> {
  const p = pageParams(pathname, agentSlug)
  return {
    value: Math.round(m.name === 'CLS' ? m.value * 1000 : m.value),
    metric_id: m.id,
    metric_value: m.value,
    metric_rating: m.rating || '',
    page_type: p.page_type,
    ...(p.area ? { area: p.area } : {}),
  }
}

export function gaVital(m: Vital, agentSlug: string): void {
  try {
    const gtag = gtagOf()
    if (!gtag) return
    gtag('event', m.name, vitalParams(m, agentSlug, window.location.pathname))
  } catch {
    /* ignore */
  }
}
