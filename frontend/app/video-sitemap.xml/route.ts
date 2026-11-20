import { getMarketingConfig } from '@/lib/marketing/config'
import { getFromSpace } from '@/lib/site/register'
import { videoSitemapXml } from '@/lib/site/videoSitemap'

export const dynamic = 'force-dynamic'

/** Every project page's "from space" video (robots.txt names it). */
export async function GET(): Promise<Response> {
  const xml = videoSitemapXml(getMarketingConfig().siteUrl.replace(/\/$/, ''), await getFromSpace())
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'public, max-age=600' } })
}
