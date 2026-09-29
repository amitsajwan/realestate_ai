/**
 * Single place that decides which agent a request is for.
 * Today: path slug (/agent/<slug>). Later: host-based (<slug>.<ROOT_DOMAIN> or a custom domain)
 * via Next middleware that rewrites to /agent/<slug>; pages keep calling resolveAgentSlug().
 */
const SLUG_RE = /^[a-z0-9](?:[a-z0-9-]{0,58}[a-z0-9])?$/
const RESERVED = ['www', 'app', 'api', 'studio', 'join', 'admin', 'static']

export function normalizeSlug(raw: string | null | undefined): string | null {
  if (!raw) return null
  let s = raw
  try {
    s = decodeURIComponent(raw)
  } catch {
    return null
  }
  s = s.trim().toLowerCase()
  return SLUG_RE.test(s) ? s : null
}

/** Subdomain slug from a Host header, given the platform root domain (e.g. "example.in"). */
export function slugFromHost(host: string | null | undefined, rootDomain: string | null | undefined): string | null {
  if (!host || !rootDomain) return null
  const h = host.toLowerCase().replace(/:\d+$/, '')
  const root = rootDomain.toLowerCase().replace(/:\d+$/, '')
  if (h === root || h.slice(-(root.length + 1)) !== '.' + root) return null
  const sub = h.slice(0, -(root.length + 1))
  if (sub.indexOf('.') >= 0 || RESERVED.indexOf(sub) >= 0) return null
  return normalizeSlug(sub)
}

/** Path slug wins; otherwise host-based. */
export function resolveAgentSlug(opts: { pathSlug?: string | null; host?: string | null; rootDomain?: string | null }): string | null {
  return normalizeSlug(opts.pathSlug) || slugFromHost(opts.host, opts.rootDomain)
}

/** Public origin of the site (canonical / OG). Env NEXT_PUBLIC_SITE_URL, else localhost dev. */
export function siteOrigin(): string {
  return (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/+$/, '')
}

/** Path to an agent's pages. All internal links go through this so host-based routing can drop the prefix. */
export function agentPath(slug: string, rest = ''): string {
  return '/agent/' + slug + (rest ? '/' + rest.replace(/^\/+/, '') : '')
}
