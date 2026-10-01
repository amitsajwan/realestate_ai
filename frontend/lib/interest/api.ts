import { serverApiBase } from '@/lib/site/api'

export interface InterestSubject {
  code: string
  kind: 'listing' | 'post' | 'page'
  channel: string
  title: string
  subtitle: string
  locality: string
  image_url: string
  agent_name: string
  sample: boolean
  consent_wording: string
}

export interface HubItem {
  kind: 'listing' | 'post' | 'page'
  ref: string
  title: string
  subtitle: string
  image_url: string
  interest_code: string | null
  permalink: string | null
  sample: boolean
}

export interface Hub {
  brand: string
  line: string
  items: HubItem[]
  links: { website: string; invite: string; facebook: string | null; instagram: string | null }
}

/** Server-side fetch. null = the link is not valid (404); anything else throws so it is not cached as a 404. */
export async function getInterest(code: string): Promise<InterestSubject | null> {
  if (!/^[a-z0-9]{4,12}$/i.test(code)) return null
  const res = await fetch(serverApiBase() + '/api/v1/public/interest/' + encodeURIComponent(code), {
    headers: { Accept: 'application/json' },
    next: { revalidate: 30 },
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Interest link temporarily unavailable')
  return (await res.json()) as InterestSubject
}

/** The hub must always render: on an outage it shows an empty, still useful page (links only). */
export async function getHub(): Promise<Hub | null> {
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/hub', { headers: { Accept: 'application/json' }, next: { revalidate: 60 } })
    return res.ok ? ((await res.json()) as Hub) : null
  } catch {
    return null
  }
}

/** Absolute URL for a share preview image (relative paths are served by this same site). */
export function absoluteImage(site: string, url: string): string | undefined {
  if (!url) return undefined
  return /^https?:\/\//.test(url) ? url : site + (url.startsWith('/') ? url : '/' + url)
}

export function anonId(): string {
  try {
    let id = window.localStorage.getItem('pp_anon')
    if (!id) {
      id = 'a' + Math.random().toString(36).slice(2, 12) + Date.now().toString(36)
      window.localStorage.setItem('pp_anon', id)
    }
    return id
  } catch {
    return 'a' + Math.random().toString(36).slice(2, 14)
  }
}

export const apiPath = (code: string, tail = '') => `/api/v1/public/interest/${encodeURIComponent(code)}${tail}`
