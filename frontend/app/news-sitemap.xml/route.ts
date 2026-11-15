import { getMarketingConfig } from '@/lib/marketing/config'
import { fetchNews } from '@/lib/news/data'
import { newsSitemapXml } from '@/lib/news/sitemap'

// Built when Google asks (never at build time, when the API is not there); the news list itself is cached for a minute
export const dynamic = 'force-dynamic'

/** The Google News sitemap: the stories of the last two days (lib/news/sitemap.ts). Named in robots.txt beside the index. */
export async function GET(): Promise<Response> {
  const res = await fetchNews(50)
  const xml = newsSitemapXml(getMarketingConfig().siteUrl, res.items)
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'public, max-age=300' } })
}
