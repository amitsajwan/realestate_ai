import { serverApiBase } from '@/lib/site/api'
import { BRAND_NAME } from '@/lib/brand'

/** One published post, as returned by GET /api/v1/public/posts. */
export interface PublicPost {
  id: string
  kind: 'post' | 'showcase' | 'reel'
  channel: 'facebook' | 'instagram'
  channels: Array<'facebook' | 'instagram'>
  title: string
  excerpt: string
  image_url: string | null
  permalink: string
  links: Array<{ channel: 'facebook' | 'instagram'; url: string }>
  published_at: string
  sample: boolean
}

export type PostsResult = { ok: true; posts: PublicPost[] } | { ok: false; posts: [] }

const safeUrl = (u: unknown): u is string => typeof u === 'string' && /^https:\/\//.test(u)

/** Keep only well-formed rows with https links, so a bad row can never become a broken or unsafe link. */
export function cleanPosts(raw: unknown): PublicPost[] {
  if (!Array.isArray(raw)) return []
  const out: PublicPost[] = []
  for (const r of raw) {
    if (!r || typeof r !== 'object') continue
    const p = r as Record<string, unknown>
    const links = (Array.isArray(p.links) ? p.links : [])
      .filter((l): l is { channel: 'facebook' | 'instagram'; url: string } =>
        !!l && (l.channel === 'facebook' || l.channel === 'instagram') && safeUrl(l.url))
    if (!links.length || typeof p.id !== 'string') continue
    out.push({
      id: p.id,
      kind: p.kind === 'showcase' || p.kind === 'reel' ? p.kind : 'post',
      channel: links[0].channel,
      channels: links.map((l) => l.channel),
      title: typeof p.title === 'string' ? p.title : BRAND_NAME,
      excerpt: typeof p.excerpt === 'string' ? p.excerpt : '',
      image_url: safeUrl(p.image_url) ? p.image_url : null,
      permalink: links[0].url,
      links,
      published_at: typeof p.published_at === 'string' ? p.published_at : '',
      sample: p.sample === true,
    })
  }
  return out
}

/** Server-side fetch, cached 60 s. An outage is reported as ok:false (shown honestly), never as fake content. */
export async function fetchPosts(limit = 12): Promise<PostsResult> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(`${serverApiBase()}/api/v1/public/posts?limit=${limit}`, {
      headers: { Accept: 'application/json' }, next: { revalidate: 60 }, signal: ctrl.signal,
    })
    if (!res.ok) return { ok: false, posts: [] }
    return { ok: true, posts: cleanPosts(await res.json()) }
  } catch {
    return { ok: false, posts: [] }
  } finally {
    clearTimeout(timer)
  }
}

export function formatPostDate(iso: string): string {
  const d = new Date(iso)
  if (!iso || Number.isNaN(d.getTime())) return ''
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' }).format(d)
}

export const POSTS_TEXT = {
  heading: `Latest from ${BRAND_NAME}`,
  lead: 'Homes and guides we have posted on Facebook and Instagram.',
  all: 'See all posts',
  empty: 'First posts going out now',
  emptyLead: 'Nothing is posted yet. Follow us on Facebook or Instagram and they will show here as they go out.',
  error: 'Posts are not loading right now',
  errorLead: 'Please try again in a minute, or see them directly on Facebook or Instagram.',
  sampleBadge: 'Sample home',
  sampleNote: 'A sample home, shown to illustrate how a post looks.',
  pageTitle: `Latest posts | ${BRAND_NAME}`,
  pageDescription: `The newest posts from ${BRAND_NAME} on Facebook and Instagram: homes, guides and Pune area notes.`,
}
