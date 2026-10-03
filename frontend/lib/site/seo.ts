import type { Metadata } from 'next'
import { formatPrice, truncate, bhkLabel } from './format'
import { agentPath, siteOrigin } from './slug'
import type { AgentProfile, PublicListing, PublicProject } from './types'

export function firstImage(l: PublicListing): string | undefined {
  const imgs = (l.media || []).filter((m) => m.kind === 'image').sort((a, b) => a.order - b.order)
  return imgs.length ? imgs[0].url : undefined
}

export function listingDescription(l: PublicListing): string {
  return l.description.en || l.description.hi || l.description.mr || ''
}

function build(title: string, description: string, path: string, image?: string): Metadata {
  const url = siteOrigin() + path
  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: { title, description, url, type: 'website', locale: 'en_IN', images: image ? [{ url: image }] : undefined },
    twitter: { card: image ? 'summary_large_image' : 'summary', title, description, images: image ? [image] : undefined },
  }
}

/** A preview site (owner-only flag) must never be indexed: the agent has not agreed to publish it yet. */
export const isPreviewAgent = (agent: Pick<AgentProfile, 'branding_data'> | null | undefined): boolean => agent?.branding_data?.preview === true

/** The fictional demo agent: its sample homes must never show up in Google as if they were for sale. */
export const isDemoAgent = (agent: Pick<AgentProfile, 'branding_data'> | null | undefined): boolean => agent?.branding_data?.demo === true

export function withPreview(agent: AgentProfile, md: Metadata): Metadata {
  if (isPreviewAgent(agent)) return { ...md, robots: { index: false, follow: false } }
  if (isDemoAgent(agent)) return { ...md, robots: { index: false, follow: true } }
  return md
}

export function agentMetadata(agent: AgentProfile, listings: PublicListing[], city: string): Metadata {
  const tag = agent.branding_data && agent.branding_data.tagline
  const title = agent.agent_name + (city ? ' | Real estate in ' + city : ' | Real estate agent')
  const description = truncate(tag ? tag + '. ' + (agent.bio || '') : agent.bio || 'Browse properties from ' + agent.agent_name, 160)
  const image = agent.photo || (listings.length ? firstImage(listings[0]) : undefined) || undefined
  return withPreview(agent, build(title, description, agentPath(agent.slug), image))
}

export function listingMetadata(agent: AgentProfile, l: PublicListing): Metadata {
  const title = l.title + ' | ' + formatPrice(l.price_inr, l.transaction)
  const description = truncate(
    [bhkLabel(l.bhk, l.property_type), l.locality + ', ' + l.city].join(' in ') + '. ' + listingDescription(l),
    160
  )
  return withPreview(agent, build(title, description, agentPath(agent.slug, 'listings/' + l.id), firstImage(l) || agent.photo || undefined))
}

export function agentJsonLd(agent: AgentProfile, city: string): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'RealEstateAgent',
    name: agent.agent_name,
    url: siteOrigin() + agentPath(agent.slug),
    image: agent.photo || undefined,
    description: agent.bio || undefined,
    telephone: agent.phone || undefined,
    address: { '@type': 'PostalAddress', streetAddress: agent.office_address || undefined, addressLocality: city || undefined, addressCountry: 'IN' },
    knowsLanguage: agent.languages && agent.languages.length ? agent.languages : undefined,
  }
}

export function listingJsonLd(agent: AgentProfile, l: PublicListing): Record<string, unknown> {
  const url = siteOrigin() + agentPath(agent.slug, 'listings/' + l.id)
  const images = (l.media || []).filter((m) => m.kind === 'image').map((m) => m.url)
  return {
    '@context': 'https://schema.org',
    '@type': ['Product', 'Residence'],
    name: l.title,
    url,
    description: listingDescription(l) || undefined,
    image: images.length ? images : undefined,
    numberOfRooms: l.bhk || undefined,
    floorSize: l.carpet_sqft ? { '@type': 'QuantitativeValue', value: l.carpet_sqft, unitCode: 'FTK' } : undefined,
    address: { '@type': 'PostalAddress', streetAddress: l.project_name || undefined, addressLocality: l.locality, addressRegion: l.city, addressCountry: 'IN' },
    offers: {
      '@type': 'Offer',
      price: l.price_inr,
      priceCurrency: 'INR',
      availability: l.status === 'live' ? 'https://schema.org/InStock' : 'https://schema.org/LimitedAvailability',
      url,
      seller: { '@type': 'RealEstateAgent', name: agent.agent_name, telephone: agent.phone || undefined },
    },
  }
}

/** JSON for a <script type="application/ld+json">; escapes "<" so content can't close the tag. */
export function jsonLdString(obj: Record<string, unknown>): string {
  return JSON.stringify(obj).replace(/</g, '\\u003c')
}

export function projectMetadata(agent: AgentProfile, p: PublicProject, priceText: string): Metadata {
  const title = `${p.name}, ${p.locality} | ${agent.agent_name}`
  const description = truncate([priceText, p.positioning, 'MahaRERA ' + p.rera_no].filter(Boolean).join('. '), 160)
  const image = p.media.find((m) => m.kind === 'image')?.url
  return withPreview(agent, build(title, description, agentPath(agent.slug, 'projects/' + p.slug), image))
}
