import { dontCacheThisRender } from '@/lib/site/noCacheOnError'
import { fixturesForced, serverApiBase } from '@/lib/site/api'
import { FIXTURE_NEWS } from './fixtures'
import { BRAND_NAME, TEAM } from '@/lib/brand'

/** One approved news item, as returned by GET /api/v1/public/news (list) and /public/news/{id} (detail adds the long parts). */
/** An area the item is about: `key` is the backend's area key (app/core/areas.py), `slug` its page: /localities/<slug>. */
export interface NewsArea { key?: string; slug: string; name: string }
export interface NewsItem {
  /** The item's address: a readable slug for a story ("lohegaon-hospital-opd-awaiting-approval-f5ddee"), the digest's own id
   *  ("digest-2026-w40"). /news/<old id> still answers with this id, and the page redirects there. */
  id: string
  kind: 'story' | 'digest'
  headline: string
  summary: string
  pillar: string
  pillar_label: string
  areas: NewsArea[]
  source_name: string
  /** The original article link. May be a Google redirect: never print it, only link it as "Read the original at <source>". */
  source_url: string | null
  as_of: string | null
  image_url: string | null
  permalinks: Array<{ channel: 'facebook' | 'instagram'; url: string }>
  published_at: string | null
  our_view: string
  what_to_check: string
  /** The fixed 'Worth checking: ...' line the social captions carry (chosen by the backend from a fixed list per pillar), or null when the
   *  item has none (education and digest items). */
  buyer_line: string | null
  disclaimer: string
  /** A digest's entries; `linked` is false for one with no page of its own (a MahaRERA project in a roundup). */
  items: Array<{ id: string; headline: string; source_name: string; line: string; linked: boolean }>
  tip: string
}

export type NewsListResult = { ok: true; items: NewsItem[] } | { ok: false; items: [] }
export type NewsItemResult = { ok: true; item: NewsItem } | { ok: false; notFound: boolean }

const https = (u: unknown): u is string => typeof u === 'string' && /^https:\/\//.test(u)
const str = (v: unknown): string => (typeof v === 'string' ? v : '')

/** Keep only well-formed rows; unsafe or non-https links are dropped, so a bad row can never become a broken or unsafe link. */
export function cleanNewsItem(raw: unknown): NewsItem | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  if (typeof r.id !== 'string' || !r.id || typeof r.headline !== 'string' || !r.headline.trim()) return null
  const areas = (Array.isArray(r.areas) ? r.areas : []).flatMap((a): NewsArea[] => {
    const o = a as Record<string, unknown>
    if (!o || typeof o.slug !== 'string' || typeof o.name !== 'string') return []
    return [typeof o.key === 'string' ? { key: o.key, slug: o.slug, name: o.name } : { slug: o.slug, name: o.name }]
  })
  const links = (Array.isArray(r.permalinks) ? r.permalinks : []).flatMap((l): NewsItem['permalinks'] => {
    const o = l as Record<string, unknown>
    return o && (o.channel === 'facebook' || o.channel === 'instagram') && https(o.url) ? [{ channel: o.channel, url: o.url }] : []
  })
  const items = (Array.isArray(r.items) ? r.items : []).flatMap((i): NewsItem['items'] => {
    const o = i as Record<string, unknown>
    return o && typeof o.id === 'string' && o.id
      ? [{ id: o.id, headline: str(o.headline), source_name: str(o.source_name), line: str(o.line), linked: o.linked !== false }] : []
  })
  return {
    id: r.id, kind: r.kind === 'digest' ? 'digest' : 'story', headline: r.headline.trim(), summary: str(r.summary),
    pillar: str(r.pillar), pillar_label: str(r.pillar_label) || 'News', areas,
    source_name: str(r.source_name), source_url: https(r.source_url) ? r.source_url : null,
    as_of: str(r.as_of) || null, image_url: https(r.image_url) ? r.image_url : null, permalinks: links,
    published_at: str(r.published_at) || null, our_view: str(r.our_view), what_to_check: str(r.what_to_check),
    buyer_line: str(r.buyer_line).trim() || null,
    disclaimer: str(r.disclaimer), items, tip: str(r.tip),
  }
}

export function cleanNewsList(raw: unknown): NewsItem[] {
  return (Array.isArray(raw) ? raw : []).flatMap((r) => { const n = cleanNewsItem(r); return n ? [n] : [] })
}

async function getJson(path: string): Promise<{ status: number; body: unknown } | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(`${serverApiBase()}/api/v1/public/news${path}`, { headers: { Accept: 'application/json' }, next: { revalidate: 60 }, signal: ctrl.signal })
    return { status: res.status, body: res.ok ? await res.json() : null }
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

/** The site path of one item. */
export const newsPath = (id: string): string => `/news/${encodeURIComponent(id)}`

/** Server-side list, cached 60 s. An outage is reported as ok:false (shown honestly), never as fake content. `area` (an area key
 *  from app/core/areas.py, e.g. "upper_kharadi") keeps the stories about that area. */
export async function fetchNews(limit = 20, area?: string): Promise<NewsListResult> {
  if (fixturesForced()) {
    const items = area ? FIXTURE_NEWS.filter((n) => n.kind === 'story' && n.areas.some((a) => a.key === area || a.slug === area)) : FIXTURE_NEWS
    return { ok: true, items: items.slice(0, limit) }
  }
  const res = await getJson(`?limit=${limit}${area ? `&area=${encodeURIComponent(area)}` : ''}`)
  if (!res || res.status >= 400) { await dontCacheThisRender(); return { ok: false, items: [] } }
  return { ok: true, items: cleanNewsList(res.body) }
}

export async function fetchNewsItem(id: string): Promise<NewsItemResult> {
  if (fixturesForced()) {
    // like the API: the address, or an older one of a story (its stored id or an older slug), found by the slug's last 6 characters
    const old = id.split('-').pop()?.slice(0, 6) ?? ''
    const item = FIXTURE_NEWS.find((n) => n.id === id) ?? FIXTURE_NEWS.find((n) => n.kind === 'story' && !!old && n.id.endsWith(`-${old}`))
    return item ? { ok: true, item } : { ok: false, notFound: true }
  }
  const res = await getJson(`/${encodeURIComponent(id)}`)
  if (!res) { await dontCacheThisRender(); return { ok: false, notFound: false } }
  if (res.status === 404) return { ok: false, notFound: true }
  const item = cleanNewsItem(res.body)
  return item ? { ok: true, item } : { ok: false, notFound: false }
}

export function formatNewsDate(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  // Day, month and year in India time, written out here so the month is always 'Sep' (ICU data differs between Node and browsers: 'Sept').
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'numeric', year: 'numeric', timeZone: 'Asia/Kolkata' }).formatToParts(d).map((x) => [x.type, x.value]))
  return `${Number(p.day)} ${MONTHS[Number(p.month) - 1]} ${p.year}`
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** True when the original link is a Google News redirect (long, ugly, and previews Google): the site never shows it as text. */
export const isGoogleRedirect = (u: string | null): boolean => !!u && /news\.google\.com|google\.com\/rss/i.test(u)

export const NEWS_TEXT = {
  heading: 'Pune property news',
  lead: 'Short summaries in our own words of what is happening with roads, metro, approvals and rules in the Pune areas we cover. Each one names its source and the date.',
  homeHeading: 'Pune property news',
  homeLead: 'Roads, metro, approvals and rules, each with its source.',
  empty: 'No news yet',
  emptyLead: 'We publish a note when there is something worth knowing in the Pune areas we cover. Follow us on Facebook or Instagram to see it first.',
  error: 'News is not loading right now',
  errorLead: 'Please try again in a minute, or see our latest posts on Facebook or Instagram.',
  badge: 'Summary of a news report',
  asOf: 'As of',
  readOriginal: (source: string) => `Read the original at ${source || 'the source'}`,
  weCheck: 'What to check',
  ourView: 'Our view',
  ourViewNote: 'This is our own reading, not a fact from the source.',
  summaryNote: 'Our summary in our own words. The facts are from the source named below.',
  how: 'How we write news',
  howLead: 'We read public reports, then write a short note in our own words. Every note names its source, the date its facts are true from, and what you should check yourself. We do not predict prices and we do not praise or criticise any builder. Approved is not the same as running: we say which one it is.',
  interestTitle: (area: string) => `Looking in ${area}?`,
  interestLead: `Tell us what you are looking for and the ${TEAM} will get back to you.`,
  interestCta: (area: string) => `I am interested in ${area}`,
  pageTitle: `Pune property news | ${BRAND_NAME}`,
  pageDescription: 'Short summaries of Pune property news in plain words: roads, metro, approvals and rules, each with its source and date.',
  moreAbout: (area: string) => `More about ${area}`,
  all: 'All news',
  digestHeading: 'In this digest',
  tipHeading: 'Buyer tip',
}
