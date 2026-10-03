import type { MetadataRoute } from 'next'
import { getMarketingConfig } from '@/lib/marketing/config'

/** The signed-in app and one-off links stay out of search; everything public is crawlable. */
export const PRIVATE_PATHS = [
  '/api/', '/studio', '/join', '/login', '/register', '/i/',
  '/dashboard', '/onboarding', '/profile', '/properties', '/analytics', '/social-publishing',
]

export default function robots(): MetadataRoute.Robots {
  const base = getMarketingConfig().siteUrl
  return {
    rules: [{ userAgent: '*', allow: '/', disallow: PRIVATE_PATHS }],
    sitemap: `${base}/sitemap.xml`,
    host: base,
  }
}
