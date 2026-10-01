import type { Metadata } from 'next'
import type { MarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { isGoogleRedirect, type NewsItem } from './data'

const clip = (s: string, n: number) => (s.length <= n ? s : s.slice(0, n - 1).replace(/\s+\S*$/, '') + '…')

/** Page metadata for one news item. The shared preview is our own card, so a link on Facebook or WhatsApp shows us, not Google. */
export function newsMetadata(cfg: MarketingConfig, item: NewsItem): Metadata {
  const path = `/news/${item.id}`
  const description = clip(item.summary || item.headline, 200)
  const base = pageMetadata(cfg, { title: `${item.headline} | ${cfg.businessName}`, description, path })
  const image = item.image_url ? { url: item.image_url, width: 1080, height: 1080, alt: item.headline } : undefined
  const url = cfg.siteUrl + path
  return {
    ...base,
    openGraph: {
      title: item.headline, description, url, siteName: cfg.businessName, type: 'article', locale: 'en_IN',
      publishedTime: item.published_at ?? undefined, modifiedTime: item.as_of ?? undefined, section: item.pillar_label,
      images: image ? [image] : base.openGraph?.images,
    },
    twitter: { card: 'summary_large_image', title: item.headline, description, images: image ? [image.url] : undefined },
  }
}

/** schema.org NewsArticle that says what it is: our own summary of someone else's report, with that source named (isBasedOn).
 *  The original link is included only when it is a real article address, never a Google redirect. */
export function newsJsonLd(cfg: MarketingConfig, item: NewsItem): Record<string, unknown> {
  const source: Record<string, unknown> | undefined = item.source_name && item.kind !== 'digest' ? {
    '@type': 'NewsArticle', name: `${item.source_name} report`, publisher: { '@type': 'Organization', name: item.source_name },
    url: item.source_url && !isGoogleRedirect(item.source_url) ? item.source_url : undefined,
  } : undefined
  return {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    headline: clip(item.headline, 110),
    description: clip(item.summary || item.headline, 300),
    abstract: `A short summary written by the ${cfg.businessName} team. The facts are from the source named in isBasedOn.`,
    articleSection: item.pillar_label,
    inLanguage: 'en-IN',
    mainEntityOfPage: `${cfg.siteUrl}/news/${item.id}`,
    datePublished: item.published_at ?? item.as_of ?? undefined,
    dateModified: item.as_of ?? item.published_at ?? undefined,
    image: item.image_url ? [item.image_url] : undefined,
    author: { '@type': 'Organization', name: `${cfg.businessName} team` },
    publisher: { '@type': 'Organization', name: cfg.businessName, url: cfg.siteUrl },
    isBasedOn: source,
    contentLocation: item.areas.length ? item.areas.map((a) => ({ '@type': 'Place', name: `${a.name}, Pune` })) : undefined,
    creativeWorkStatus: 'Summary',
    isAccessibleForFree: true,
  }
}
