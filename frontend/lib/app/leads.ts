import { formatInr, timeAgo, waDigits } from './format'
import { whatsappChatUrl } from './share'
import { t } from './strings'
import type { Financing, Lead, LeadEvent, NextActionType, Requirement, Timeline } from './types'

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
