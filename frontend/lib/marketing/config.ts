/**
 * Business name and contact details for the public pages. Everything comes from NEXT_PUBLIC_* env;
 * nothing is invented: an unset email or WhatsApp number is simply not shown.
 *
 * NEXT_PUBLIC_* values are inlined at build time, so each variable is read by its full literal name.
 */
export interface MarketingConfig {
  businessName: string
  /** Contact email, or null when not configured (never show an address then). */
  email: string | null
  /** WhatsApp number as digits with country code (e.g. 919876543210), or null. */
  whatsappDigits: string | null
  /** Human-readable form ("+91 98765 43210"), or null. */
  whatsappDisplay: string | null
  /** https://wa.me/... link, or null. */
  whatsappUrl: string | null
  /** Site origin without a trailing slash, for canonical and Open Graph URLs. */
  siteUrl: string
}

export const DEFAULT_BUSINESS_NAME = 'PUNE Property'

export interface MarketingEnv {
  NEXT_PUBLIC_BUSINESS_NAME?: string
  NEXT_PUBLIC_CONTACT_EMAIL?: string
  NEXT_PUBLIC_CONTACT_WHATSAPP?: string
  NEXT_PUBLIC_SITE_URL?: string
}

function cleanEmail(raw?: string): string | null {
  const v = (raw || '').trim()
  return /^[^\s@<>"']+@[^\s@<>"']+\.[^\s@<>"']+$/.test(v) ? v : null
}

function cleanWhatsapp(raw?: string): string | null {
  let d = (raw || '').replace(/\D/g, '')
  if (/^[6-9]\d{9}$/.test(d)) d = '91' + d
  return d.length >= 11 && d.length <= 15 ? d : null
}

function display(digits: string): string {
  if (/^91[6-9]\d{9}$/.test(digits)) return '+91 ' + digits.slice(2, 7) + ' ' + digits.slice(7)
  return '+' + digits
}

export function buildMarketingConfig(env: MarketingEnv): MarketingConfig {
  const wa = cleanWhatsapp(env.NEXT_PUBLIC_CONTACT_WHATSAPP)
  return {
    businessName: (env.NEXT_PUBLIC_BUSINESS_NAME || '').trim() || DEFAULT_BUSINESS_NAME,
    email: cleanEmail(env.NEXT_PUBLIC_CONTACT_EMAIL),
    whatsappDigits: wa,
    whatsappDisplay: wa ? display(wa) : null,
    whatsappUrl: wa ? 'https://wa.me/' + wa : null,
    siteUrl: (env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').trim().replace(/\/+$/, ''),
  }
}

export function getMarketingConfig(): MarketingConfig {
  return buildMarketingConfig({
    NEXT_PUBLIC_BUSINESS_NAME: process.env.NEXT_PUBLIC_BUSINESS_NAME,
    NEXT_PUBLIC_CONTACT_EMAIL: process.env.NEXT_PUBLIC_CONTACT_EMAIL,
    NEXT_PUBLIC_CONTACT_WHATSAPP: process.env.NEXT_PUBLIC_CONTACT_WHATSAPP,
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL,
  })
}

export const hasContact = (c: MarketingConfig): boolean => !!(c.email || c.whatsappUrl)
