import { getMarketingConfig } from '@/lib/marketing/config'
import { indexXml, sitemapGroups } from '@/lib/site/sitemap'

// Built when a crawler asks (never at build time, when the API is not there); lib/site/sitemap.ts keeps it for 10 minutes
export const dynamic = 'force-dynamic'

/** The sitemap index robots.txt names: core pages, agents, builders, and one sitemap per Pune place (/sitemaps/<name>.xml). */
export async function GET(): Promise<Response> {
  const xml = indexXml(getMarketingConfig().siteUrl, await sitemapGroups())
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'public, max-age=300' } })
}
