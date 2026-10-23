import { formatInr, timeAgo, waDigits } from './format'
import { whatsappChatUrl } from './share'
import { t } from './strings'
import type { ContactStatus, Financing, Lead, LeadChannel, LeadEvent, NextActionType, Requirement, Timeline } from './types'

const VERBS: Record<string, string> = {
  page_view: 'Visited your website',
  listing_view: 'Viewed',
  share: 'Shared',
  call_click: 'Tapped Call on',
  whatsapp_click: 'Tapped WhatsApp on',
  inquiry: 'Sent an enquiry about',
  call_answered: 'You called: answered',
  call_no_answer: 'You called: no answer',
}

const SOURCES: Record<string, string> = {
  whatsapp: 'WhatsApp', instagram: 'Instagram', facebook: 'Facebook', direct: 'Direct', fbgroup: 'Facebook group', facebook_comment: 'Facebook comment',
  instagram_comment: 'Instagram comment', chat: 'Website chat', google: 'Google', bing: 'Bing', youtube: 'YouTube', chatgpt: 'ChatGPT',
  twitter: 'X (Twitter)', linkedin: 'LinkedIn', reddit: 'Reddit', perplexity: 'Perplexity', unknown: 'Not recorded',
}

const TAG_PREFIX: Record<string, string> = { fb: 'Facebook', ig: 'Instagram', wa: 'WhatsApp', yt: 'YouTube' }

/** "google" -> "Google"; a post/ad tag "fb_room2_brand-ad" -> "Facebook · room2 brand (ad)". */
export function sourceLabel(source?: string | null): string {
  if (!source) return ''
  const known = SOURCES[source.toLowerCase()]
  if (known) return known
  const m = /^(fb|ig|wa|yt)_(.+?)(-ad)?$/i.exec(source)
  if (m) return `${TAG_PREFIX[m[1].toLowerCase()]} · ${m[2].replace(/[_-]+/g, ' ')}${m[3] ? ' (ad)' : ''}`
  return source.charAt(0).toUpperCase() + source.slice(1)
}

const CHANNELS: Record<LeadChannel, string> = {
  form: 'Enquiry form', chat: 'Website chat', whatsapp: 'WhatsApp message', dm: 'Direct message', comment: 'Comment on a post', post_link: 'Post link',
}

/** How they reached us: "Enquiry form", "Website chat", ... */
export function channelLabel(channel?: LeadChannel | null): string {
  return channel ? CHANNELS[channel] ?? channel : ''
}

/** Where they came from, one key per lead: the source (tag or referring site), 'direct' when tracked but no referrer, else 'unknown'. */
export function originKey(lead: Pick<Lead, 'source' | 'first_touch'>): string {
  const s = lead.source && lead.source !== 'chat' ? lead.source.toLowerCase() : ''
  return s || (lead.first_touch ? 'direct' : 'unknown')
}

/** "Viewed 2 BHK in Baner - Instagram - 2h ago" */
export function eventLabel(ev: LeadEvent, listingTitle?: string | null, now?: Date): string {
  if (ev.type.startsWith('call_')) return [VERBS[ev.type] ?? 'You called', timeAgo(ev.ts, now)].join(' - ')
  const verb = ev.type === 'page_view' && ev.path ? 'Opened' : VERBS[ev.type] ?? ev.type.replace(/_/g, ' ')
  const what = ev.type === 'page_view' ? (ev.path ? ` ${ev.path}` : '') : ` ${listingTitle || (ev.listing_id ? 'a listing' : ev.path || 'your site')}`
  return [`${verb}${what}`, sourceLabel(ev.source), timeAgo(ev.ts, now)].filter(Boolean).join(' - ')
}

/** "https://www.google.com/" -> "www.google.com"; anything unparsable comes back as given. */
function referrerHost(url: string): string {
  try {
    return new URL(url).host
  } catch {
    return url
  }
}

/** "Enquiry form · Came from Google (www.google.com) · landed on /projects/x · enquired on /agent/avasetu". */
export function cameFromLine(lead: Pick<Lead, 'source' | 'first_touch' | 'channel'>): string {
  const ft = lead.first_touch
  const key = originKey(lead)
  let from: string
  if (ft?.referrer) from = `Came from ${key !== 'direct' ? sourceLabel(key) : referrerHost(ft.referrer)} (${referrerHost(ft.referrer)})`
  else if (ft?.app) from = `Came from ${sourceLabel(ft.app)} (opened inside the ${sourceLabel(ft.app)} app)`
  else if (key === 'direct') from = 'Came directly (no referring site: typed, saved, or an app that hides it)'
  else if (key === 'unknown') from = 'Where they came from was not recorded (before 17 Oct)'
  else from = `Came from ${sourceLabel(key)}`
  const landed = ft?.landing ? `landed on ${ft.landing}` : ''
  const enquired = ft?.enquiry_page && ft.enquiry_page !== ft.landing ? `enquired on ${ft.enquiry_page}` : ''
  return [channelLabel(lead.channel), from, landed, enquired].filter(Boolean).join(' · ')
}

/** Most recent activity first (owner, 2026-10-17: 'not sorted by time'); hotter first only when the time is the same. Hot is a filter. */
export function sortLeads(leads: Lead[]): Lead[] {
  return [...leads].sort((a, b) => b.last_activity_at.localeCompare(a.last_activity_at) || b.score - a.score)
}

/** "₹80 L - ₹90 L", "Under ₹50 L", "₹2 Cr+", or '' when there is no budget. Money is integer rupees. */
export function budgetRange(min?: number | null, max?: number | null): string {
  const lo = min != null && min > 0 ? min : null
  const hi = max != null && max > 0 ? max : null
  if (lo && hi) return `₹${formatInr(lo)} - ₹${formatInr(hi)}`
  if (hi) return `Under ₹${formatInr(hi)}`
  if (lo) return `₹${formatInr(lo)}+`
  return ''
}

const TIMELINE_KEY: Record<Timeline, Parameters<typeof t>[0]> = {
  now: 'timelineNow',
  '1_3_months': 'timeline1_3',
  '3_6_months': 'timeline3_6',
  exploring: 'timelineExploring',
}
const FINANCING_KEY: Record<Financing, Parameters<typeof t>[0]> = {
  home_loan: 'finHomeLoan',
  own_funds: 'finOwnFunds',
  undecided: 'finUndecided',
}

/** Chips for the "What they want" row: BHK, budget, localities, timeline, financing (only what is known). */
export function requirementChips(req?: Requirement | null): string[] {
  if (!req) return []
  const chips: string[] = []
  if (req.bhk) chips.push(`${req.bhk} BHK`)
  const budget = budgetRange(req.budget_min_inr, req.budget_max_inr)
  if (budget) chips.push(budget)
  chips.push(...(req.localities ?? []))
  if (req.timeline) chips.push(t(TIMELINE_KEY[req.timeline]))
  if (req.financing) chips.push(t(FINANCING_KEY[req.financing]))
  return chips
}

export function requirementSourceNote(req?: Requirement | null): string {
  if (!req) return ''
  return req.source === 'stated' ? t('reqStated') : req.source === 'inferred' ? t('reqInferred') : t('reqMixed')
}

/** wa.me link to a lead's number with the (possibly edited) message, URL-encoded. */
export function buildWhatsappUrl(phone: string, text: string): string {
  return whatsappChatUrl(waDigits(phone), text.trim() ? text : undefined)
}

/** ISO timestamp for `days` from now at 10:00 local time (used by the follow-up quick buttons). */
export function followUpAt(days: number, now: Date = new Date()): string {
  const d = new Date(now)
  d.setDate(d.getDate() + days)
  d.setHours(10, 0, 0, 0)
  return d.toISOString()
}

/** "Overdue", "Due today", or "Due 3 Oct". */
export function dueLabel(dueAt: string | null | undefined, overdue: boolean, now: Date = new Date()): string {
  if (!dueAt) return ''
  const due = new Date(dueAt)
  if (isNaN(due.getTime())) return ''
  if (overdue) return `${t('overdue')} (${due.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })})`
  if (due.toDateString() === now.toDateString()) return t('dueToday')
  return `${t('dueOn')} ${due.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}`
}

export const NEXT_ACTION_LABEL: Record<NextActionType, Parameters<typeof t>[0]> = {
  call: 'actCall',
  whatsapp: 'actWhatsapp',
  schedule_visit: 'actScheduleVisit',
  follow_up: 'actFollowUp',
}

const VIA: Record<string, string> = { whatsapp: 'WhatsApp', messenger: 'Messenger', instagram: 'Instagram', website: 'website chat', call: 'phone' }
const HOURS_BEFORE_LATE = 2
/** Colours for contactLine's tone (like CHANNEL_CHIP in inbox.ts). */
export const CONTACT_TONE = { bad: 'bg-red-50 text-red-700', action: 'bg-[#f0b440] text-[#0f2340]', wait: 'bg-blue-50 text-blue-800', ok: 'bg-green-50 text-green-800' }

/**
 * One line for "who is waiting for whom", and how loud to show it: bad = someone is waiting on us (a new lead nobody reached in
 * 2 hours, or their message unanswered), action = waiting on us but fresh, wait = we are waiting on them, ok = talking.
 */
export function contactLine(c: ContactStatus | null | undefined, now: Date = new Date()): { text: string; tone: 'bad' | 'action' | 'wait' | 'ok' } | null {
  if (!c || c.state === 'closed') return null
  const ago = c.at ? timeAgo(c.at, now) : ''
  // naive UTC from the server, like timeAgo
  const late = !!c.at && now.getTime() - Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(c.at) ? c.at : c.at + 'Z') > HOURS_BEFORE_LATE * 3600 * 1000
  const via = c.channel ? VIA[c.channel] ?? c.channel : ''
  switch (c.state) {
    case 'not_contacted':
      return { text: `Not contacted yet · came in ${ago}`, tone: late ? 'bad' : 'action' }
    case 'waiting_you':
      return { text: `They replied on ${via} ${ago} · waiting for you`, tone: late ? 'bad' : 'action' }
    case 'no_reply':
      return { text: `${c.by === 'bot' ? 'Bot' : 'You'} messaged on ${via} ${ago} · no reply yet`, tone: 'wait' }
    case 'no_answer':
      return { text: `Called ${ago} · no answer`, tone: 'wait' }
    case 'in_touch':
      return { text: c.channel === 'call' ? `Spoke on the phone ${ago}` : `In touch on ${via} · last word ${c.by === 'bot' ? 'from the bot' : 'from you'} ${ago}`, tone: 'ok' }
    default:
      return { text: 'Contacted', tone: 'ok' }
  }
}
