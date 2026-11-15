import { BRAND_NAME } from '@/lib/brand'
import { newsPath, type NewsItem } from './data'

/** Google News reads a news sitemap for the last two days' stories only (older ones are dropped by it anyway). */
export const NEWS_SITEMAP_WINDOW_MS = 2 * 24 * 60 * 60 * 1000

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const when = (d?: string | null): Date | null => {
  const t = d ? new Date(d) : null
  return t && !isNaN(t.getTime()) ? t : null
}

/** The stories a news sitemap lists: published (or dated) inside the window, newest first, at most 1,000 as the format allows. */
export function recentNews(items: NewsItem[], now: number): Array<{ item: NewsItem; date: Date }> {
  return items
    .flatMap((item) => { const d = when(item.published_at ?? item.as_of); return d ? [{ item, date: d }] : [] })
    .filter(({ date }) => now - date.getTime() <= NEWS_SITEMAP_WINDOW_MS && date.getTime() <= now)
    .sort((a, b) => b.date.getTime() - a.date.getTime())
    .slice(0, 1000)
}

/** A Google News sitemap (the `news` namespace): one entry per recent story with the publication, its language, the date and
 *  the headline. Submitted in Search Console beside the sitemap index; also named in robots.txt. An empty list still gives a
 *  valid, empty sitemap. */
export function newsSitemapXml(base: string, items: NewsItem[], now: number = Date.now()): string {
  const rows = recentNews(items, now).map(({ item, date }) =>
    `<url><loc>${esc(base + newsPath(item.id))}</loc><news:news><news:publication><news:name>${esc(BRAND_NAME)}</news:name>` +
    `<news:language>en</news:language></news:publication><news:publication_date>${date.toISOString()}</news:publication_date>` +
    `<news:title>${esc(item.headline)}</news:title></news:news></url>`)
  return '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n' +
    rows.join('\n') + (rows.length ? '\n' : '') + '</urlset>\n'
}
