import { timeAgo } from './format'
import type { Lead, LeadEvent } from './types'

const VERBS: Record<string, string> = {
  page_view: 'Visited your website',
  listing_view: 'Viewed',
  share: 'Shared',
  call_click: 'Tapped Call on',
  whatsapp_click: 'Tapped WhatsApp on',
  inquiry: 'Sent an enquiry about',
}

const SOURCES: Record<string, string> = { whatsapp: 'WhatsApp', instagram: 'Instagram', facebook: 'Facebook', direct: 'Direct' }

export function sourceLabel(source?: string | null): string {
  if (!source) return ''
  return SOURCES[source.toLowerCase()] ?? source.charAt(0).toUpperCase() + source.slice(1)
}

/** "Viewed 2 BHK in Baner - Instagram - 2h ago" */
export function eventLabel(ev: LeadEvent, listingTitle?: string | null, now?: Date): string {
  const verb = VERBS[ev.type] ?? ev.type.replace(/_/g, ' ')
  const what = ev.type === 'page_view' ? '' : ` ${listingTitle || (ev.listing_id ? 'a listing' : 'your site')}`
  return [`${verb}${what}`, sourceLabel(ev.source), timeAgo(ev.ts, now)].filter(Boolean).join(' - ')
}

/** Hottest first; ties keep most recent first. */
export function sortLeads(leads: Lead[]): Lead[] {
  return [...leads].sort((a, b) => b.score - a.score || b.last_activity_at.localeCompare(a.last_activity_at))
}
