import { dontCacheThisRender } from '@/lib/site/noCacheOnError'
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
  /** every slide of a carousel (https), cover first; empty when there is none */
  images: string[]
  /** the page on our own site the post points to, when it has one */
  site_url: string | null
  permalink: string
  links: Array<{ channel: 'facebook' | 'instagram'; url: string }>
  published_at: string
  sample: boolean
  /** the post's own page is postPath(slug); null only for a row from an older backend */
  slug?: string | null
  /** an area key from backend app/core/areas.py (e.g. 'upper_kharadi'), or null */
  area?: string | null
  /** 'agents' for our recruitment posts, 'buyers' for everything else */
  audience?: 'agents' | 'buyers'
}

/** One post with its full text, as returned by GET /api/v1/public/posts/{slug}. */
export interface PublicPostFull extends PublicPost {
  slug: string
  /** the whole caption: no hashtags or phone numbers, links only to our own site */
  text: string
}

export type PostsResult = { ok: true; posts: PublicPost[] } | { ok: false; posts: [] }
export type PostResult = { ok: true; post: PublicPostFull } | { ok: false; notFound: boolean }

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const AREA_KEY = /^[a-z_]+$/

/** The address of a post's own page. */
export const postPath = (slug: string): string => `/posts/${slug}`

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
      images: (Array.isArray(p.images) ? p.images : []).filter(safeUrl).slice(0, 10),
      site_url: safeUrl(p.site_url) ? p.site_url : null,
      permalink: links[0].url,
      links,
      published_at: typeof p.published_at === 'string' ? p.published_at : '',
      sample: p.sample === true,
      slug: typeof p.slug === 'string' && SLUG.test(p.slug) ? p.slug : null,
      area: typeof p.area === 'string' && AREA_KEY.test(p.area) ? p.area : null,
      audience: p.audience === 'agents' ? 'agents' : 'buyers',
    })
  }
  return out
}

/** One post for its page: a well-formed row with a slug, plus its text. */
export function cleanPost(raw: unknown): PublicPostFull | null {
  const [p] = cleanPosts([raw])
  if (!p || !p.slug) return null
  const text = (raw as Record<string, unknown>).text
  return { ...p, slug: p.slug, text: typeof text === 'string' ? text : p.excerpt }
}

async function getJson(path: string): Promise<{ status: number; body: unknown } | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(`${serverApiBase()}/api/v1/public/posts${path}`, {
      headers: { Accept: 'application/json' }, next: { revalidate: 60 }, signal: ctrl.signal,
    })
    return { status: res.status, body: res.ok ? await res.json() : null }
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

/** Server-side fetch, cached 60 s; `area` (an area key) keeps only that area's posts. An outage is reported as ok:false
 *  (shown honestly), never as fake content. */
export async function fetchPosts(limit = 12, area?: string): Promise<PostsResult> {
  const res = await getJson(`?limit=${limit}` + (area ? `&area=${encodeURIComponent(area)}` : ''))
  if (!res || res.status >= 400) { await dontCacheThisRender(); return { ok: false, posts: [] } }
  return { ok: true, posts: cleanPosts(res.body) }
}

/** One post for its page. notFound only when the API says so (404), never for an outage. */
export async function fetchPost(slug: string): Promise<PostResult> {
  if (!SLUG.test(slug)) return { ok: false, notFound: true }
  const res = await getJson(`/${encodeURIComponent(slug)}`)
  if (!res) { await dontCacheThisRender(); return { ok: false, notFound: false } }
  if (res.status === 404) return { ok: false, notFound: true }
  const post = res.status < 400 ? cleanPost(res.body) : null
  if (!post) await dontCacheThisRender()
  return post ? { ok: true, post } : { ok: false, notFound: false }
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
  allPosts: 'All posts',
  seeProject: 'See the project',
  moreAbout: (area: string) => `More about ${area}`,
  postedOn: 'Posted on',
  reel: 'Reel',
  watchOn: (channel: string) => `Watch on ${channel}`,
  viewOn: (channel: string) => `View on ${channel}`,
  failed: 'This post is not loading right now',
  failedLead: 'Please try again in a minute.',
}
