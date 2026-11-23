import { getLocality, localityNameFromSlug, type Locality, type LocalityTier } from '@/lib/marketing/localities'

/** The area an area page is about: one of our curated guides (LOCALITIES), or a place name an agent typed, which gets a stub with
 *  the general buyer checks and stays out of search. Moved from app/localities/[slug]/page.tsx (2026-11-23). */
export type PageLocality = (Locality & { fallback?: false }) | {
  fallback: true
  slug: string
  key: string
  name: string
  tier: LocalityTier
  listingName: string
  tagline: string
  summary: string
  suits: string[]
  gettingAround: string[]
  checks: string[]
  faqs: { q: string; a: string }[]
  guides: string[]
  sources: { label: string; href: string }[]
  updated?: string
  updatedLabel?: string
}

export function pageLocality(slug: string): PageLocality {
  const l = getLocality(slug)
  return l ? { ...l, fallback: false } : fallbackLocality(slug)
}

export function fallbackLocality(slug: string): PageLocality {
  const name = localityNameFromSlug(slug)
  return {
    fallback: true,
    slug, key: slug.replace(/-/g, '_'), name, tier: 'affordable', listingName: name,
    tagline: 'Live listings and projects agents have added',
    summary: `We do not have a full buyer guide for ${name} yet. This page shows live listings and projects agents have added, plus the checks every buyer should do before a visit or booking.`,
    suits: ['Buyers shortlisting homes in this locality', 'Buyers who want a working page to share listings from agents', 'Buyers ready to verify project details before paying a token amount'],
    gettingAround: ['We do not quote travel times. Try your own commute at 9:00 am and 6:30 pm on a weekday before you decide.'],
    checks: [
      'RERA registration number of the project, looked up on the MahaRERA website',
      'Carpet area in the agreement, and the price per sq ft of carpet area',
      'Where the water comes from, and what the power backup covers',
      'Possession date in the agreement compared with the one on the RERA page',
      'The full cost: stamp duty, registration, GST where applicable, parking and maintenance deposit',
    ],
    faqs: [
      { q: `Do you have a full guide for ${name}?`, a: 'Not yet. Until we have sourced locality facts, this page shows only live listings, projects agents have added and general buyer checks.' },
      { q: 'What should I verify before visiting?', a: 'Check the RERA number, the exact carpet area, possession date, water and power backup, and the full cost sheet before you pay anything.' },
    ],
    guides: [], sources: [],
  }
}
