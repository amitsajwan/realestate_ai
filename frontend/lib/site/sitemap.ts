import type { MetadataRoute } from 'next'
import { INSIGHTS } from '@/lib/marketing/insights'
import { LOCALITIES, getLocality, localitySlug } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'
import { fetchNews } from '@/lib/news/data'
import { fetchTrackers, trackerPath } from '@/lib/news/trackers'
import { getCatalog, getSitemapEntries } from '@/lib/site/api'
import { getFacets, withoutMovedSizePages } from '@/lib/site/facets'
import { fetchTopics, topicPath } from '@/lib/site/topics'
import { livePages } from '@/lib/site/filters'
import { getBuilders } from '@/lib/site/hubs'
import { getRegisterProjects, getRegisterPlaces, placePath } from '@/lib/site/register'
import { agentPath } from '@/lib/site/slug'
import { isHouseAgent } from '@/lib/brand'

const day = (d?: string | null): Date | undefined => {
  const t = d ? new Date(d) : null
  return t && !isNaN(t.getTime()) ? t : undefined
}

export type SitemapEntry = MetadataRoute.Sitemap[number]
/** Which sitemap a page is listed in: 'core', 'agents', 'builders', 'projects' (shared pages whose area we can't place) or
 *  'area-<place slug>', one per Pune place in the register, so Search Console shows how much of each area is indexed. */
export type Grouped = { group: string; entry: SitemapEntry }[]

/** A list for the sitemap that comes back empty keeps the last one read. The news, guides, trackers and builders reads have no
 *  retry, so a build while the backend restarts (every deploy) got none of them and still counted as good (it has the area
 *  sitemaps): Google was then given a sitemap without the guides, the 8 trackers, the news and builders.xml (2026-10-31). A
 *  list that really empties stays until the server restarts. */
function lastGood<T>(key: string, list: T[]): T[] {
  const kept = (holder.__avasetuSitemapLists ??= {})
  if (list.length) kept[key] = list
  return list.length ? list : ((kept[key] as T[] | undefined) ?? list)
}

/** Pages that are public and worth indexing: the fixed pages, then news stories and the agent pages that have real content
 *  (the backend leaves out the demo agent, unpublished previews and sample listings), Avasetu's shared project pages and the
 *  2 BHK / budget pages that have enough projects. Built when Google asks for it, so new
 *  stories, listings and projects are listed without a deploy. Left out since the site-wide drop of 2026-10-26 (pages made in
 *  bulk from one template or written by a model): neighbourhood articles, locality pages without a guide of their own, and
 *  our social posts' pages. They stay up for visitors, noindex. */
export async function buildSitemap(): Promise<Grouped> {
  const base = getMarketingConfig().siteUrl
  const at = (path: string, priority: number, date?: string | null): SitemapEntry => ({ url: base + path, lastModified: day(date), priority })
  const [newsRead, agents, projects, register, places, buildersRead, facets, topicsRead, trackersRead] = await Promise.all([fetchNews(50), getSitemapEntries(), getCatalog(), getRegisterProjects(undefined, true), getRegisterPlaces(), getBuilders(), getFacets(), fetchTopics(), fetchTrackers()])
  const news = { items: lastGood('news', newsRead.items) }
  const [builders, topics, trackers] = [lastGood('builders', buildersRead), lastGood('topics', topicsRead), lastGood('trackers', trackersRead)]
  const placeSlug = new Map(places.map((p) => [p.key, p.slug]))
  const placeByName = new Map(places.flatMap((p) => [[p.slug, p.slug], [localitySlug(p.name), p.slug]]))
  const area = (slug?: string | null) => (slug ? 'area-' + slug : 'projects')
  const areaOfLocality = (name?: string | null) => {
    const s = localitySlug(name)
    const key = getLocality(s)?.key
    return area((key && placeSlug.get(key)) || placeByName.get(s))
  }
  const listedRegnos = new Set(projects.map((p) => p.rera_no))   // those redirect to the shared agent page, listed above
  // a listing of a project with its own page in search shows that page and names it as canonical (2026-10-30): only the project
  const registerRegnos = new Set(register.map((r) => r.regno))
  const shared = new Set(projects.flatMap((p) => p.agents.map((a) => a.slug + '/' + a.project_slug)))
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
    // a locality with a guide of the same slug names the guide as its canonical page, so only the guide is listed
    ...LOCALITIES.filter((l) => !topics.some((t) => t.slug === l.slug)).map((l) => core(at(`/localities/${l.slug}`, 0.8, l.updated))),
    core(at('/news', 0.8)),
    ...trackers.map((t) => core(at(trackerPath(t.slug), 0.8, t.updated))),
    ...news.items.map((n) => core(at(`/news/${n.id}`, 0.6, n.published_at ?? n.as_of))),
    core(at('/insights', 0.7)),
    ...INSIGHTS.map((a) => core(at(`/insights/${a.slug}`, 0.7, a.updated))),
    ...topics.map((t) => core(at(topicPath(t.slug), 0.8, t.checked_on))),
    // the team's own agent page names the home page as canonical (lib/site/seo agentMetadata), so it is not listed itself
    ...[...latest].filter(([slug]) => !isHouseAgent(slug)).map(([slug, d]) => ({ group: 'agents', entry: at(agentPath(slug), 0.7, d) })),
    core(at('/projects', 0.9)),
    // the East Pune home plan's questions and office counts (docs/plan/home-plan.md); each family's plan is noindex and left out
    core(at('/home-plan', 0.7)),
    ...projects.map((p) => ({ group: areaOfLocality(p.locality), entry: at('/projects/' + p.slug, 0.9, [p.rera?.checked_at, p.updated_at].filter(Boolean).sort().pop()) })),
    ...withoutMovedSizePages(livePages(projects), facets).map((f) => core(at(f.path, 0.7))),
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
    core(at('/builders', 0.6)),
    ...builders.filter((b) => b.indexable).map((b) => ({ group: 'builders', entry: at('/builders/' + b.slug, b.brand ? 0.8 : 0.6, b.page_updated) })),
    // an agent's copy of a project on a shared page names that page as canonical, so only the others are listed
    ...agents.projects.filter((p) => !shared.has(p.agent_slug + '/' + p.slug)).map((p) => ({ group: 'agents', entry: at(agentPath(p.agent_slug, 'projects/' + p.slug), 0.6, p.updated_at) })),
    ...agents.listings.filter((l) => !(l.rera_no && registerRegnos.has(l.rera_no)))
      .map((l) => ({ group: 'agents', entry: at(agentPath(l.agent_slug, 'listings/' + l.id), 0.6, l.updated_at) })),
    // the agents' one page in search; the trial, invite and printable pitch pages are reached from our own links and WhatsApp,
    // and are noindex so they never stand for the brand (owner 2026-10-29: buyers first)
    core(at('/agents', 0.7)),
    core(at('/privacy', 0.2)),
    core(at('/terms', 0.2)),
  ]
}

/** Every page, in one list (what the sitemap files hold between them). */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  return (await buildSitemap()).map((g) => g.entry)
}

const FRESH_MS = 10 * 60 * 1000   // the index and its sitemaps are read together; build the list once for all of them
const THIN_MS = 60 * 1000         // a list without any area sitemap means the API did not answer: try again soon
type Groups = Map<string, SitemapEntry[]>
type Cached = { at: number; ttl: number; groups: Promise<Groups> }
const holder = globalThis as unknown as { __avasetuSitemap?: Cached; __avasetuSitemapGood?: Groups; __avasetuSitemapLists?: Record<string, unknown[]> }

/** The pages per sitemap, shared by /sitemap.xml and /sitemaps/<name>.xml (one build per 10 minutes per server). A build that
 *  comes back without area sitemaps (the API was slow or restarting) never replaces the last good one: Google keeps seeing
 *  every page, and the build is tried again a minute later. */
export function sitemapGroups(now = Date.now()): Promise<Groups> {
  const c = holder.__avasetuSitemap
  if (c && now - c.at < c.ttl) return c.groups
  const next: Cached = { at: now, ttl: FRESH_MS, groups: Promise.resolve(new Map()) }
  next.groups = buildSitemap().then((all) => {
    const m: Groups = new Map()
    for (const { group, entry } of all) m.set(group, [...(m.get(group) ?? []), entry])
    if ([...m.keys()].some((k) => k.startsWith('area-'))) {
      holder.__avasetuSitemapGood = m
      return m
    }
    next.ttl = THIN_MS
    return holder.__avasetuSitemapGood ?? m
  }, (e) => {
    holder.__avasetuSitemap = undefined
    if (holder.__avasetuSitemapGood) return holder.__avasetuSitemapGood
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
