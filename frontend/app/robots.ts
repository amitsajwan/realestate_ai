import type { MetadataRoute } from 'next'
import { getMarketingConfig } from '@/lib/marketing/config'

export default function robots(): MetadataRoute.Robots {
  const base = getMarketingConfig().siteUrl
  return {
    rules: [{ userAgent: '*', allow: '/', disallow: ['/studio', '/join', '/api/', '/login', '/register'] }],
    sitemap: `${base}/sitemap.xml`,
  }
}
