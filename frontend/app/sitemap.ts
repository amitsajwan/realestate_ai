import type { MetadataRoute } from 'next'
import { INSIGHTS } from '@/lib/marketing/insights'
import { LOCALITIES } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'
import { fetchNews } from '@/lib/news/data'
import { fetchPosts, postPath } from '@/lib/posts/data'
import { getCatalog, getSitemapEntries } from '@/lib/site/api'
import { livePages } from '@/lib/site/filters'
import { agentPath } from '@/lib/site/slug'

const day = (d?: string | null): Date | undefined => {
  const t = d ? new Date(d) : null
  return t && !isNaN(t.getTime()) ? t : undefined
}

const POSTS_MAX = 500 // the API's most per call: every published post for years

/** Pages that are public and worth indexing: the fixed pages, then news stories and the agent pages that have real content
 *  (the backend leaves out the demo agent, unpublished previews and sample listings), Avasetu's shared project pages and the
 *  2 BHK / budget pages that have enough projects. Built when Google asks for it, so new
 *  stories, listings and projects are listed without a deploy. Every post's own page is listed too, dated by its post. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = getMarketingConfig().siteUrl
  const at = (path: string, priority: number, date?: string | null) => ({ url: base + path, lastModified: day(date), priority })
  const [news, agents, projects, posts] = await Promise.all([fetchNews(50), getSitemapEntries(), getCatalog(), fetchPosts(POSTS_MAX)])
  const shared = new Set(projects.flatMap((p) => p.agents.map((a) => a.slug + '/' + a.project_slug)))
  const latest = new Map<string, string | null | undefined>() // agent slug -> newest change on their site
  for (const e of [...agents.listings, ...agents.projects]) {
    const prev = latest.get(e.agent_slug)
    if (!latest.has(e.agent_slug) || (e.updated_at && (!prev || e.updated_at > prev))) latest.set(e.agent_slug, e.updated_at)
  }
  return [
    at('/', 1),
    at('/localities', 0.8),
    ...LOCALITIES.map((l) => at(`/localities/${l.slug}`, 0.8, l.updated)),
    at('/news', 0.8),
    ...news.items.map((n) => at(`/news/${n.id}`, 0.6, n.published_at ?? n.as_of)),
    at('/insights', 0.7),
    ...INSIGHTS.map((a) => at(`/insights/${a.slug}`, 0.7, a.updated)),
    at('/posts', 0.6),
    ...posts.posts.flatMap((p) => (p.slug ? [at(postPath(p.slug), 0.6, p.published_at)] : [])),
    ...[...latest].map(([slug, d]) => at(agentPath(slug), 0.7, d)),
    at('/projects', 0.9),
    ...projects.map((p) => at('/projects/' + p.slug, 0.9, [p.rera?.checked_at, p.updated_at].filter(Boolean).sort().pop())),
    ...livePages(projects).map((f) => at(f.path, 0.7)),
    // an agent's copy of a project on a shared page names that page as canonical, so only the others are listed
    ...agents.projects.filter((p) => !shared.has(p.agent_slug + '/' + p.slug)).map((p) => at(agentPath(p.agent_slug, 'projects/' + p.slug), 0.6, p.updated_at)),
    ...agents.listings.map((l) => at(agentPath(l.agent_slug, 'listings/' + l.id), 0.6, l.updated_at)),
    at('/for-agents', 0.6),
    at('/request-invite', 0.3),
    at('/privacy', 0.2),
    at('/terms', 0.2),
  ]
}
