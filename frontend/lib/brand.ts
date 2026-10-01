/**
 * The platform brand: one source of truth for the name, tagline, sign-off, hashtag, colours and logo files.
 * Avasetu (आवासेतु: āvās = home + setu = bridge). Guide: docs/brand/avasetu/README.md. Mirrors backend app/core/brand.py.
 *
 * Pune is the first city: area copy ('homes in Pune', 'Kharadi, Wagholi') is not the brand and stays where it is.
 * NEXT_PUBLIC_* values are inlined at build time, so each variable is read by its full literal name.
 */
export const BRAND_NAME = 'Avasetu'
export const BRAND_NAME_DEVANAGARI = 'आवासेतु'
export const TAGLINE = 'Your bridge to the right home'
export const TAGLINE_HI = 'सही घर तक आपका सेतु'
export const TAGLINE_MR = 'योग्य घरापर्यंत तुमचा सेतू'
export const TEAM = 'Avasetu team'
export const HASHTAG = '#Avasetu'
export const NAVY = '#102340'
export const GOLD = '#F0B13B'

/** Title used where a page has no title of its own. */
export const DEFAULT_TITLE = `${BRAND_NAME}: ${TAGLINE}`
export const DEFAULT_DESCRIPTION = 'Homes, guides and trusted local agents in Pune. Clear price, area, possession and RERA details, in plain words.'

/** Logo files under /public/brand (rendered from docs/brand/avasetu). */
export const LOGO = {
  mark: '/brand/mark.svg', // gold disc, navy roof over a bridge arch: use on navy or white
  markPng: '/brand/mark.png',
  markNavy: '/brand/mark-navy.svg', // navy rounded tile, gold strokes: app icons
  icon32: '/brand/icon-32.png',
  icon192: '/brand/icon-192.png',
  icon512: '/brand/icon-512.png',
  appleTouch: '/brand/apple-touch-icon.png',
  og: '/brand/og.jpg',
}

/** Production site origin while there is no domain; set NEXT_PUBLIC_SITE_URL to change it (one setting). */
export const DEFAULT_SITE_URL = 'https://34-180-39-243.sslip.io'

/** The public site origin (no trailing slash): NEXT_PUBLIC_SITE_URL, else the production default. Printed links and QR codes use it. */
export const siteUrl = (): string => ((process.env.NEXT_PUBLIC_SITE_URL || '').trim() || DEFAULT_SITE_URL).replace(/\/+$/, '')

/** Slug of the fictional demo agent page (backend/scripts/create_demo_agent.py creates it): NEXT_PUBLIC_DEMO_AGENT_SLUG, else 'demo'. */
export const DEFAULT_DEMO_AGENT_SLUG = 'demo'
export const demoAgentSlug = (): string => {
  const v = (process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG || '').trim().toLowerCase()
  return /^[a-z0-9][a-z0-9-]{0,59}$/.test(v) ? v : DEFAULT_DEMO_AGENT_SLUG
}
export const demoAgentPath = (): string => '/agent/' + demoAgentSlug()

/** The business name shown on public pages: NEXT_PUBLIC_BUSINESS_NAME, else the brand. */
export const businessName = (): string => (process.env.NEXT_PUBLIC_BUSINESS_NAME || '').trim() || BRAND_NAME
