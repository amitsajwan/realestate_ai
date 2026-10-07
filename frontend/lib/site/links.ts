import { formatPrice } from './format'
import { waNumber } from './phone'
import type { PublicListing } from './types'

/** Call/WhatsApp buttons show only when NEXT_PUBLIC_SHOW_AGENT_PHONE=true (read at call time; baked in at build). */
export function showDirectContact(): boolean {
  return process.env.NEXT_PUBLIC_SHOW_AGENT_PHONE === 'true'
}

export function whatsappLink(phone: string | null | undefined, message: string): string | null {
  const n = waNumber(phone)
  return n ? 'https://wa.me/' + n + '?text=' + encodeURIComponent(message) : null
}

export function telLink(phone: string | null | undefined): string | null {
  const n = waNumber(phone)
  return n ? 'tel:+' + n : null
}

export function whatsappMessage(agentName: string, listing?: PublicListing | null, url?: string): string {
  if (!listing) return 'Hi ' + agentName + ', I found your website and I am interested in your properties.'
  const where = [listing.project_name, listing.locality].filter(Boolean).join(', ')
  return (
    'Hi ' + agentName + ', I am interested in "' + listing.title + '"' +
    (where ? ' (' + where + ')' : '') + ' listed at ' +
    formatPrice(listing.price_inr, listing.transaction) + '.' + (url ? ' ' + url : '')
  )
}

/** Append a query param to an absolute or relative URL (keeps any #hash). */
export function withParam(url: string, key: string, value: string): string {
  const parts = url.split('#')
  const base = parts[0]
  const sep = base.indexOf('?') >= 0 ? '&' : '?'
  return base + sep + encodeURIComponent(key) + '=' + encodeURIComponent(value) + (parts[1] ? '#' + parts[1] : '')
}
