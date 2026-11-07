import type { Metadata } from 'next'
import { bhkLabel, fitDescription, formatPrice, truncate } from './format'
import { BRAND_NAME, isHouseAgent } from '@/lib/brand'
import { agentPath, siteOrigin } from './slug'
import { monthsLater } from './check'
import { displayName } from './theme'
import { formatDay } from './projects'
import type { AgentProfile, CatalogProject, PublicListing, PublicProject } from './types'
import { earliestPossession, webFact, type WebFacts } from './webfacts'

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

const AGENT_TITLE_AREAS = 3   // a title longer than this is cut off in Google's results

/** The areas the agent named on their site and their MahaRERA agent number, the two things people search an agent by. */
function agentFacts(agent: AgentProfile): { areas: string[]; rera: string } {
  const b = (agent.branding_data || {}) as { areas?: unknown; rera_agent_no?: unknown }
  const areas = Array.isArray(b.areas) ? b.areas.filter((a): a is string => typeof a === 'string' && !!a.trim()) : []
  return { areas: areas.slice(0, AGENT_TITLE_AREAS), rera: typeof b.rera_agent_no === 'string' ? b.rera_agent_no : '' }
}

export function agentMetadata(agent: AgentProfile, listings: PublicListing[], city: string): Metadata {
  const tag = agent.branding_data && agent.branding_data.tagline
  const { areas, rera } = agentFacts(agent)
  // the business name when there is one: House Deal's login is in a person's name, and the tab read "Sharad | Real estate in Pune"
  const place = [areas.join(', '), city].filter(Boolean).join(', ')
  const title = displayName(agent) + (areas.length ? ' | Real estate agent in ' + place : city ? ' | Real estate in ' + city : ' | Real estate agent')
  const homes = listings.length ? listings.length + ' live listing' + (listings.length > 1 ? 's' : '') + '. ' : ''
  const number = rera ? 'MahaRERA agent ' + rera + '. ' : ''
  const description = truncate(number + homes + (tag ? tag + '. ' + (agent.bio || '') : agent.bio || 'Browse properties from ' + agent.agent_name), 160)
  const image = agent.photo || (listings.length ? firstImage(listings[0]) : undefined) || undefined
  const md = withPreview(agent, build(title, description, agentPath(agent.slug), image))
  // The team's own site ("Avasetu Homes") was Google's first answer for "avasetu pune", ahead of the home page (2026-10-29).
  // It holds a few of our listings, their project and the enquiry form every buyer button on the site opens, so it stays and
  // keeps working (no redirect); it names the buyers' home as its canonical, so the brand's links and searches go there. Its
  // listing and project pages keep their own canonicals.
  return isHouseAgent(agent.slug) ? { ...md, alternates: { canonical: siteOrigin() } } : md
}

/** What someone types for this home: 'KP Supernova 2 BHK in Mohammadwadi, Pune'. The project's own name first when there is one. */
function listingSearchName(l: PublicListing): string {
  const shops = ['office', 'shop', 'commercial'].includes(l.property_type)
  const what = shops ? 'shops and offices' : bhkLabel(l.bhk, l.property_type)
  const where = [l.locality, l.city].filter(Boolean).join(', ')
  return (l.project_name ? l.project_name + ' ' + what : l.title) + (where && !/ in /i.test(l.project_name ? what : l.title) ? ' in ' + where : '')
}

export function listingMetadata(agent: AgentProfile, l: PublicListing): Metadata {
  const title = listingSearchName(l) + ': ' + formatPrice(l.price_inr, l.transaction)
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
    name: displayName(agent),
    url: siteOrigin() + agentPath(agent.slug),
    image: agent.photo || undefined,
    description: agent.bio || undefined,
    areaServed: agentFacts(agent).areas.map((a) => ({ '@type': 'Place', name: a })),
    identifier: agentFacts(agent).rera ? { '@type': 'PropertyValue', propertyID: 'MahaRERA', value: agentFacts(agent).rera } : undefined,
    address: { '@type': 'PostalAddress', streetAddress: agent.office_address || undefined, addressLocality: city || undefined, addressCountry: 'IN' },
    knowsLanguage: agent.languages && agent.languages.length ? agent.languages : undefined,
    // the team's own site belongs to the Avasetu organisation, whose page is the home page (the Organization there)
    parentOrganization: isHouseAgent(agent.slug) ? { '@type': 'Organization', name: BRAND_NAME, url: siteOrigin() } : undefined,
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
      seller: { '@type': 'RealEstateAgent', name: agent.agent_name },
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
  const image = p.media.find((m) => m.kind === 'image' && !m.slide)?.url
  const md = build(title, description, agentPath(agent.slug, 'projects/' + p.slug), image)
  // Avasetu's shared page is the one to rank: every agent's copy of the project names it as the canonical address
  if (p.catalog_slug) md.alternates = { canonical: siteOrigin() + '/projects/' + p.catalog_slug }
  return withPreview(agent, md)
}

/** Metadata for Avasetu's shared project page (/projects/<slug>): the title says what buyers search for (price, possession),
 *  the description carries the facts only we put together (each tower's MahaRERA date, bookings, checked web facts). */
export function catalogProjectMetadata(p: CatalogProject, priceText: string, web: WebFacts | null = null): Metadata {
  const when = earliestPossession(p)
  const from = p.price_min != null ? formatPrice(p.price_min) : ''
  const options = [
    when && from ? `${p.name}, ${p.locality}: Price ${from}, Possession ${when}` : '',
    when ? `${p.name}, ${p.locality}: Price, Possession ${when}` : '',
    when && from ? `${p.name}: Price ${from}, Possession ${when}` : '',
    `${p.name}, ${p.locality}, Pune: Price, MahaRERA`,
  ].filter(Boolean)
  const title = options.find((t) => t.length <= 60) ?? `${p.name}, ${p.locality}`
  const regs = (p.registrations ?? []).filter((r) => r.completion)
  const later = regs.filter((r) => r.completion && formatDay(r.completion.slice(0, 7)) !== when)
  // net of MahaRERA's 2026 blanket extension, as on the page (possessionLines)
  const moved = p.rera?.completion_at_registration && p.rera.completion_now
    && monthsLater(p.rera.completion_now, p.rera.completion_at_registration, p.rera.registered_on)
    ? `, moved from ${formatDay(p.rera.completion_at_registration.slice(0, 7))}` : ''
  const land = webFact(web, 'land_acres'), open = webFact(web, 'open_space_pct')
  // over ~160 characters the land and open space go first, then the other towers' dates, the bookings, the "moved from"
  const description = fitDescription((has) => [
    priceText,
    when ? `MahaRERA possession ${when}${later.length && has(2) ? ` (${later.map((r) => `${r.tower}: ${formatDay(r.completion!.slice(0, 7))}`).join(', ')})` : ''}${has(4) ? moved : ''}` : '',
    p.rera?.units_total && has(3) ? `${p.rera.units_booked ?? 0} of ${p.rera.units_total} homes booked` : '',
    (land || open) && has(1) ? [land?.text, open ? open.text + ' open space' : ''].filter(Boolean).join(', ') : '',
    'MahaRERA ' + p.rera_no,
  ].filter(Boolean).join('. '))
  const image = p.media.find((m) => m.kind === 'image' && !m.slide)?.url
  return build(title, description, '/projects/' + p.slug, image ? absolute(image) : undefined)
}

const absolute = (u: string): string => (/^https?:/.test(u) ? u : siteOrigin() + u)

/** ApartmentComplex data: only what the page shows. */
export function projectJsonLd(p: PublicProject, url: string): Record<string, unknown> {
  const photo = p.media.find((m) => m.kind === 'image' && !m.slide)
  return {
    '@context': 'https://schema.org', '@type': 'ApartmentComplex', name: p.name, url,
    address: { '@type': 'PostalAddress', streetAddress: p.address || undefined, addressLocality: p.locality, addressRegion: 'Maharashtra', postalCode: p.pincode || undefined, addressCountry: 'IN' },
    image: photo ? [absolute(photo.url)] : undefined,
    numberOfAccommodationUnits: p.rera?.units_total ?? undefined,
    // a project registered tower by tower: every registration the page lists (one-registration projects stay as before)
    identifier: (p.registrations?.length ?? 0) > 1
      ? p.registrations!.map((r) => ({ '@type': 'PropertyValue', propertyID: 'MahaRERA registration', name: r.tower, value: r.regno, url: r.url || undefined }))
      : undefined,
  }
}
