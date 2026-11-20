import { getMarketingConfig } from '@/lib/marketing/config'
import { getProjectVideos, projectVideoSitemapXml } from '@/lib/site/projectVideos'

// Built when a crawler asks (never at build time, when the API is not there)
export const dynamic = 'force-dynamic'

/** The video sitemap of the projects' listing videos: each watch page (/projects/<slug>/video) with its video. The sitemap
 *  index (/sitemap.xml) names it. */
export async function GET(): Promise<Response> {
  const xml = projectVideoSitemapXml(getMarketingConfig().siteUrl, await getProjectVideos())
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'public, max-age=600' } })
}
