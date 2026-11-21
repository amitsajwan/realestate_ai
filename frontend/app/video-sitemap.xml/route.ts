import { getMarketingConfig } from '@/lib/marketing/config'
import { getFromSpace } from '@/lib/site/register'
import { videoSitemapXml } from '@/lib/site/videoSitemap'
import { getAreasFromSpace } from '@/lib/site/areaFromSpace'

export const dynamic = 'force-dynamic'

/** Every project's and area's "from space" video (robots.txt names it). */
export async function GET(): Promise<Response> {
  const xml = videoSitemapXml(getMarketingConfig().siteUrl.replace(/\/$/, ''), ...(await Promise.all([getFromSpace(), getAreasFromSpace()])))
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'public, max-age=600' } })
}
