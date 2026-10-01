import type { Metadata } from 'next'
import type { MarketingConfig } from './config'
import { LOGO, TAGLINE } from '@/lib/brand'

export interface PageMeta {
  title: string
  description: string
  path: string
  /** Path under /public, e.g. /landing/30-home-actions.jpg */
  image?: { path: string; width: number; height: number; alt: string }
}

export function pageMetadata(cfg: MarketingConfig, m: PageMeta): Metadata {
  const url = cfg.siteUrl + (m.path === '/' ? '' : m.path)
  // every page gets a brand preview so a shared link (Facebook, WhatsApp) shows a card, not a bare title
  const img = m.image ?? { path: '/brand/og.jpg', width: 1200, height: 630, alt: cfg.businessName + ': ' + TAGLINE }
  const image = { url: cfg.siteUrl + img.path, width: img.width, height: img.height, alt: img.alt }
  return {
    title: m.title,
    description: m.description,
    alternates: { canonical: url },
    openGraph: {
      title: m.title, description: m.description, url, siteName: cfg.businessName, type: 'website', locale: 'en_IN',
      images: image ? [image] : undefined,
    },
    twitter: { card: image ? 'summary_large_image' : 'summary', title: m.title, description: m.description, images: image ? [image.url] : undefined },
  }
}

/** Organization structured data. Only facts we actually have: name, url, description, and contact when configured. */
export function organizationJsonLd(cfg: MarketingConfig, description: string, sameAs?: string[]): Record<string, unknown> {
  const contact: Record<string, unknown>[] = []
  if (cfg.email) contact.push({ '@type': 'ContactPoint', contactType: 'customer support', email: cfg.email })
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: cfg.businessName,
    url: cfg.siteUrl,
    logo: cfg.siteUrl + LOGO.icon512,
    description,
    areaServed: { '@type': 'City', name: 'Pune' },
    sameAs: sameAs && sameAs.length ? sameAs : undefined,
    contactPoint: contact.length ? contact : undefined,
  }
}

/** JSON for a <script type="application/ld+json">; escapes "<" so content can't close the tag. */
export function jsonLdString(obj: Record<string, unknown>): string {
  return JSON.stringify(obj).replace(/</g, '\\u003c')
}
