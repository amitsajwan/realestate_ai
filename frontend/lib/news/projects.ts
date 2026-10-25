import { displayName, getRegisterProject, projectSummary } from '@/lib/site/register'
import type { NewsItem } from './data'

/** A project a story names, as its page shows it: the name buyers know, its one-line summary and its page. */
export interface StoryProject { slug: string; name: string; line: string }

/** The story's projects from their own pages (docs/plan/insights-and-seo.md S4: news story → projects it names). A page that is
 *  gone or cannot be read now is left out, and towers of one project (several registrations, one page) show once. */
export async function storyProjects(item: Pick<NewsItem, 'projects'>): Promise<StoryProject[]> {
  const pages = await Promise.all((item.projects ?? []).slice(0, 5).map((p) => getRegisterProject(p.slug).catch(() => null)))
  const seen = new Set<string>()
  return pages.flatMap((r) => {
    if (!r || seen.has(r.slug)) return []
    seen.add(r.slug)
    return [{ slug: r.slug, name: displayName(r), line: projectSummary(r) }]
  })
}
