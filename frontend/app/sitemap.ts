import type { MetadataRoute } from 'next'
import { INSIGHTS } from '@/lib/marketing/insights'
import { LOCALITIES } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'

/** Pages that are public, stable and worth indexing. Agent sites are added once they have real listings. */
export default function sitemap(): MetadataRoute.Sitemap {
  const base = getMarketingConfig().siteUrl
  const at = (path: string, priority: number, date?: string) => ({ url: base + path, lastModified: date ? new Date(date) : undefined, priority })
  return [
    at('/', 1),
    at('/for-agents', 0.9),
    at('/news', 0.8),
    at('/posts', 0.7),
    at('/localities', 0.8),
    ...LOCALITIES.map((l) => at(`/localities/${l.slug}`, 0.8, l.updated)),
    at('/insights', 0.7),
    ...INSIGHTS.map((a) => at(`/insights/${a.slug}`, 0.7, a.updated)),
    at('/request-invite', 0.4),
    at('/privacy', 0.2),
    at('/terms', 0.2),
  ]
}
