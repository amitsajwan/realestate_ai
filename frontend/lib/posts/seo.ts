import type { Metadata } from 'next'
import type { MarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { LOGO } from '@/lib/brand'
import { postPath, type PublicPostFull } from './data'

const clip = (s: string, n: number) => (s.length <= n ? s : s.slice(0, n - 1).replace(/\s+\S*$/, '') + '…')

/** The search snippet: the text after the title line, in one line. */
export function postDescription(post: PublicPostFull): string {
  const body = post.text.split('\n').map((l) => l.trim()).filter(Boolean)
  const rest = (body[0] && post.title.startsWith(body[0].slice(0, 40)) ? body.slice(1) : body).join(' ')
  return clip((rest || post.excerpt || post.title).replace(/https?:\/\/\S+/g, '').replace(/\s+/g, ' ').trim(), 160)
}

/** Page metadata for one post: its own title, its picture as the shared preview, canonical /posts/<slug>. */
export function postMetadata(cfg: MarketingConfig, post: PublicPostFull): Metadata {
  const path = postPath(post.slug)
  const description = postDescription(post)
  const base = pageMetadata(cfg, { title: `${clip(post.title, 70)} | ${cfg.businessName}`, description, path })
  const picture = post.images[0] ?? post.image_url
  const image = picture ? { url: picture, width: 1080, height: 1350, alt: post.title } : undefined
  return {
    ...base,
    openGraph: {
      title: post.title, description, url: cfg.siteUrl + path, siteName: cfg.businessName, type: 'article', locale: 'en_IN',
      publishedTime: post.published_at || undefined, images: image ? [image] : base.openGraph?.images,
    },
    twitter: { card: 'summary_large_image', title: post.title, description, images: image ? [image.url] : base.twitter?.images },
  }
}

/** schema.org Article for a post we wrote and published ourselves: what the page shows, nothing more. */
export function postJsonLd(cfg: MarketingConfig, post: PublicPostFull, areaName?: string): Record<string, unknown> {
  const images = post.images.length ? post.images : post.image_url ? [post.image_url] : [cfg.siteUrl + '/brand/og.jpg']
  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: clip(post.title, 110),
    description: postDescription(post),
    inLanguage: 'en-IN',
    mainEntityOfPage: cfg.siteUrl + postPath(post.slug),
    datePublished: post.published_at || undefined,
    dateModified: post.published_at || undefined,
    image: images.slice(0, 5),
    author: { '@type': 'Organization', name: `${cfg.businessName} team`, url: cfg.siteUrl },
    publisher: { '@type': 'Organization', name: cfg.businessName, url: cfg.siteUrl, logo: { '@type': 'ImageObject', url: cfg.siteUrl + LOGO.icon512 } },
    contentLocation: areaName ? { '@type': 'Place', name: `${areaName}, Pune` } : undefined,
    sameAs: post.links.map((l) => l.url),
    isAccessibleForFree: true,
  }
}
