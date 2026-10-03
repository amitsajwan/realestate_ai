import { fixtureAgent, fixtureListing, fixtureListings } from './fixtures'
import type { AgentProfile, ListingsPage, PublicListing, PublicProject } from './types'

// Server-side data access for the public site. Server components need an ABSOLUTE url:
// SITE_API_URL (server-only) > NEXT_PUBLIC_API_URL > http://localhost:8000.

export function serverApiBase(): string {
  const env = process.env.SITE_API_URL || process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL
  return (env || 'http://localhost:8000').replace(/\/+$/, '')
}

export const fixturesForced = (): boolean => process.env.SITE_USE_FIXTURES === '1'
const isDev = (): boolean => process.env.NODE_ENV !== 'production'

type Result<T> = { ok: true; data: T } | { ok: false; notFound: boolean }

async function getJson<T>(path: string): Promise<Result<T>> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    const res = await fetch(serverApiBase() + path, {
      headers: { Accept: 'application/json' },
      next: { revalidate: 30 },
      signal: ctrl.signal,
    })
    if (res.status === 404) return { ok: false, notFound: true }
    if (!res.ok) throw new Error('API ' + res.status)
    return { ok: true, data: (await res.json()) as T }
  } catch (e) {
    return { ok: false, notFound: false }
  } finally {
    clearTimeout(timer)
  }
}

/**
 * An outage (timeout, 5xx, network) must NOT look like "page not found": that would show buyers a wrong 404 and can
 * get the page dropped from Google. Only a genuine 404 from the API means not-found; anything else throws so the
 * error boundary renders a temporary-error page that is not cached as a 404.
 */
function unavailable(): never {
  throw new Error('Agent site data is temporarily unavailable')
}

/** True when an unreachable API in development should fall back to fixtures. */
const devFallback = (r: Result<unknown>): boolean => !r.ok && !r.notFound && isDev()

export async function getAgent(slug: string): Promise<AgentProfile | null> {
  if (fixturesForced()) return fixtureAgent(slug)
  const r = await getJson<AgentProfile>('/api/v1/agent/public/' + encodeURIComponent(slug))
  if (r.ok) return r.data
  if (devFallback(r)) return fixtureAgent(slug)
  return r.notFound ? null : unavailable()
}

export async function getListings(slug: string): Promise<ListingsPage> {
  if (fixturesForced()) return fixtureListings(slug) || { items: [], total: 0 }
  const r = await getJson<ListingsPage>('/api/v1/public/agents/' + encodeURIComponent(slug) + '/listings?limit=60')
  if (r.ok) return { items: r.data.items || [], total: r.data.total || 0 }
  if (devFallback(r)) return fixtureListings(slug) || { items: [], total: 0 }
  return r.notFound ? { items: [], total: 0 } : unavailable()
}

export async function getListing(slug: string, id: string): Promise<PublicListing | null> {
  if (fixturesForced()) return fixtureListing(slug, id)
  const r = await getJson<PublicListing>('/api/v1/public/listings/' + encodeURIComponent(id))
  if (r.ok) {
    // A listing must be shown only under its own agent's site.
    const owner = r.data.agent && r.data.agent.slug
    return owner && owner !== slug ? null : r.data
  }
  if (devFallback(r)) return fixtureListing(slug, id)
  return r.notFound ? null : unavailable()
}

/** The agent's live builder projects (agentprojects module); empty for agents without any, or under fixtures. */
export async function getProjects(slug: string): Promise<PublicProject[]> {
  if (fixturesForced()) return []
  const r = await getJson<{ items: PublicProject[] }>('/api/v1/public/agents/' + encodeURIComponent(slug) + '/projects')
  if (r.ok) return r.data.items || []
  if (devFallback(r)) return []
  return r.notFound ? [] : unavailable()
}

export async function getProject(slug: string, project: string): Promise<PublicProject | null> {
  if (fixturesForced()) return null
  const r = await getJson<PublicProject>('/api/v1/public/agents/' + encodeURIComponent(slug) + '/projects/' + encodeURIComponent(project))
  if (r.ok) return r.data
  if (devFallback(r)) return null
  return r.notFound ? null : unavailable()
}

/** Real (never sample) listings in a locality across all public agents; empty on any outage so the page still renders. */
export async function getLocalityListings(locality: string): Promise<PublicListing[]> {
  if (fixturesForced()) return []
  const r = await getJson<ListingsPage>('/api/v1/public/localities/' + encodeURIComponent(locality) + '/listings?limit=12')
  return r.ok ? r.data.items || [] : []
}

/** Best guess at the agent's city for the hero. */
export function agentCity(agent: AgentProfile, listings: PublicListing[]): string {
  if (agent.city) return agent.city
  if (listings.length) return listings[0].city
  return ''
}
