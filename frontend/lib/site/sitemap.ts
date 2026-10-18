import type { MetadataRoute } from 'next'
import { INSIGHTS } from '@/lib/marketing/insights'
import { LOCALITIES, getLocality, localitySlug } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'
import { fetchNews } from '@/lib/news/data'
import { fetchPosts, postPath } from '@/lib/posts/data'
import { getCommunities } from '@/components/localities/communities'
import { getCatalog, getSitemapEntries } from '@/lib/site/api'
import { getFacets } from '@/lib/site/facets'
import { fetchTopics, topicPath } from '@/lib/site/topics'
import { livePages } from '@/lib/site/filters'
import { getBuilders } from '@/lib/site/hubs'
import { getRegisterProjects, getRegisterPlaces, placePath } from '@/lib/site/register'
import { agentPath } from '@/lib/site/slug'

const day = (d?: string | null): Date | undefined => {
  const t = d ? new Date(d) : null
  return t && !isNaN(t.getTime()) ? t : undefined
}

const POSTS_MAX = 500 // the API's most per call: every published post for years

export type SitemapEntry = MetadataRoute.Sitemap[number]
/** Which sitemap a page is listed in: 'core', 'agents', 'builders', 'projects' (shared pages whose area we can't place) or
 *  'area-<place slug>', one per Pune place in the register, so Search Console shows how much of each area is indexed. */
export type Grouped = { group: string; entry: SitemapEntry }[]

/** Pages that are public and worth indexing: the fixed pages, then news stories and the agent pages that have real content
 *  (the backend leaves out the demo agent, unpublished previews and sample listings), Avasetu's shared project pages and the
 *  2 BHK / budget pages that have enough projects. Built when Google asks for it, so new
 *  stories, listings and projects are listed without a deploy. Every post's own page is listed too, dated by its post. */
export async function buildSitemap(): Promise<Grouped> {
  const base = getMarketingConfig().siteUrl
  const at = (path: string, priority: number, date?: string | null): SitemapEntry => ({ url: base + path, lastModified: day(date), priority })
  const [news, agents, projects, posts, register, places, hoods, builders, facets, topics] = await Promise.all([fetchNews(50), getSitemapEntries(), getCatalog(), fetchPosts(POSTS_MAX), getRegisterProjects(undefined, true), getRegisterPlaces(), getCommunities(), getBuilders(), getFacets(), fetchTopics()])
  const placeSlug = new Map(places.map((p) => [p.key, p.slug]))
  const placeByName = new Map(places.flatMap((p) => [[p.slug, p.slug], [localitySlug(p.name), p.slug]]))
  const area = (slug?: string | null) => (slug ? 'area-' + slug : 'projects')
  const areaOfLocality = (name?: string | null) => {
    const s = localitySlug(name)
    const key = getLocality(s)?.key
    return area((key && placeSlug.get(key)) || placeByName.get(s))
  }
  const listedRegnos = new Set(projects.map((p) => p.rera_no))   // those redirect to the shared agent page, listed above
  const shared = new Set(projects.flatMap((p) => p.agents.map((a) => a.slug + '/' + a.project_slug)))
  const fallbackLocalities = new Map<string, string | null | undefined>()
  for (const e of agents.listings) {
    const slug = localitySlug(e.locality)
    if (slug && !getLocality(slug)) fallbackLocalities.set(slug, e.updated_at)
  }
  for (const p of projects) {
    const slug = localitySlug(p.locality)
    const date = [p.rera?.checked_at, p.updated_at].filter(Boolean).sort().pop()
    if (slug && !getLocality(slug)) {
      const prev = fallbackLocalities.get(slug)
      if (!fallbackLocalities.has(slug) || (date && (!prev || date > prev))) fallbackLocalities.set(slug, date)
    }
  }
  const latest = new Map<string, string | null | undefined>() // agent slug -> newest change on their site
  for (const e of [...agents.listings, ...agents.projects]) {
    const prev = latest.get(e.agent_slug)
    if (!latest.has(e.agent_slug) || (e.updated_at && (!prev || e.updated_at > prev))) latest.set(e.agent_slug, e.updated_at)
  }
  const core = (entry: SitemapEntry) => ({ group: 'core', entry })
  return [
    core(at('/', 1)),
    core(at('/localities', 0.8)),
    core(at('/pune-maharera-tracker', 0.8)),
    ...LOCALITIES.map((l) => core(at(`/localities/${l.slug}`, 0.8, l.updated))),
    ...[...fallbackLocalities].map(([slug, d]) => core(at(`/localities/${slug}`, 0.5, d))),
    ...hoods.map((h) => core(at(`/localities/${h.area_slug}/${h.slug}`, 0.6, h.updated))),
    core(at('/news', 0.8)),
    ...news.items.map((n) => core(at(`/news/${n.id}`, 0.6, n.published_at ?? n.as_of))),
    core(at('/insights', 0.7)),
    ...INSIGHTS.map((a) => core(at(`/insights/${a.slug}`, 0.7, a.updated))),
    ...topics.map((t) => core(at(topicPath(t.slug), 0.8, t.checked_on))),
    core(at('/posts', 0.6)),
    ...posts.posts.flatMap((p) => (p.slug ? [core(at(postPath(p.slug), 0.6, p.published_at))] : [])),
    ...[...latest].map(([slug, d]) => ({ group: 'agents', entry: at(agentPath(slug), 0.7, d) })),
    core(at('/projects', 0.9)),
    ...projects.map((p) => ({ group: areaOfLocality(p.locality), entry: at('/projects/' + p.slug, 0.9, [p.rera?.checked_at, p.updated_at].filter(Boolean).sort().pop()) })),
    ...livePages(projects).map((f) => core(at(f.path, 0.7))),
    // Avasetu's own page for each MahaRERA project with real facts (thin ones are noindex and left out)
    // (dated by page_updated, when the page's facts last changed; no date when unknown; finished projects rank lower)
    // one page per Pune area listing its projects, once one of them has real facts
    ...places.filter((p) => p.indexable > 0).map((p) => ({ group: area(p.slug), entry: at(placePath(p.slug), 0.6) })),
    // each place's lists that grew from searches (docs/plan/area-intent-pages.md): live and with 3+ projects; dated by the newest
    // change among their projects, or the day the page went live
    ...facets.filter((f) => f.indexable).map((f) => ({ group: area(f.place_slug), entry: at(f.path, 0.7, f.page_updated) })),
    ...register.filter((r) => r.indexable && !listedRegnos.has(r.regno))
      .map((r) => ({ group: area(r.place ? placeSlug.get(r.place) : null),
        entry: at('/projects/' + r.slug, r.active === false ? 0.4 : 0.7, r.page_updated) })),   // our own page date only; MahaRERA's old dates never
    // one page per builder with two or more indexable projects (docs/plan/rank-loop.md R6)
    ...builders.filter((b) => b.indexable).map((b) => ({ group: 'builders', entry: at('/builders/' + b.slug, 0.6, b.page_updated) })),
    // an agent's copy of a project on a shared page names that page as canonical, so only the others are listed
    ...agents.projects.filter((p) => !shared.has(p.agent_slug + '/' + p.slug)).map((p) => ({ group: 'agents', entry: at(agentPath(p.agent_slug, 'projects/' + p.slug), 0.6, p.updated_at) })),
    ...agents.listings.map((l) => ({ group: 'agents', entry: at(agentPath(l.agent_slug, 'listings/' + l.id), 0.6, l.updated_at) })),
    core(at('/for-agents', 0.6)),
    core(at('/request-invite', 0.3)),
    core(at('/trial', 0.6)),
    core(at('/privacy', 0.2)),
    core(at('/terms', 0.2)),
  ]
}

/** Every page, in one list (what the sitemap files hold between them). */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  return (await buildSitemap()).map((g) => g.entry)
}

const FRESH_MS = 10 * 60 * 1000   // the index and its sitemaps are read together; build the list once for all of them
const THIN_MS = 60 * 1000         // a list without register projects is an API outage: try again soon
type Cached = { at: number; ttl: number; groups: Promise<Map<string, SitemapEntry[]>> }
const holder = globalThis as unknown as { __avasetuSitemap?: Cached }

/** The pages per sitemap, shared by /sitemap.xml and /sitemaps/<name>.xml (one build per 10 minutes per server). */
export function sitemapGroups(now = Date.now()): Promise<Map<string, SitemapEntry[]>> {
  const c = holder.__avasetuSitemap
  if (c && now - c.at < c.ttl) return c.groups
  const next: Cached = { at: now, ttl: FRESH_MS, groups: Promise.resolve(new Map()) }
  next.groups = buildSitemap().then((all) => {
    const m = new Map<string, SitemapEntry[]>()
    for (const { group, entry } of all) m.set(group, [...(m.get(group) ?? []), entry])
    if (![...m.keys()].some((k) => k.startsWith('area-'))) next.ttl = THIN_MS
    return m
  }, (e) => {
    holder.__avasetuSitemap = undefined
    throw e
  })
  holder.__avasetuSitemap = next
  return next.groups
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const iso = (d: SitemapEntry['lastModified']) => {
  const t = d ? new Date(d) : null
  return t && !isNaN(t.getTime()) ? t.toISOString() : null
}
const HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n'
const NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'

export function urlsetXml(entries: SitemapEntry[]): string {
  const rows = entries.map((e) => {
    const m = iso(e.lastModified)
    return `<url><loc>${esc(e.url)}</loc>${m ? `<lastmod>${m}</lastmod>` : ''}${e.priority != null ? `<priority>${e.priority}</priority>` : ''}</url>`
  })
  return `${HEAD}<urlset xmlns="${NS}">\n${rows.join('\n')}\n</urlset>\n`
}

/** The sitemap index: one <sitemap> per group, dated by its newest page. */
export function indexXml(base: string, groups: Map<string, SitemapEntry[]>): string {
  const rows = [...groups].sort(([a], [b]) => (a === 'core' ? -1 : b === 'core' ? 1 : a.localeCompare(b))).map(([name, entries]) => {
    const newest = entries.map((e) => iso(e.lastModified)).filter((d): d is string => !!d).sort().pop()
    return `<sitemap><loc>${esc(`${base}/sitemaps/${name}.xml`)}</loc>${newest ? `<lastmod>${newest}</lastmod>` : ''}</sitemap>`
  })
  return `${HEAD}<sitemapindex xmlns="${NS}">\n${rows.join('\n')}\n</sitemapindex>\n`
}
