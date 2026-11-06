/**
 * Studio home ("Today", 2026-10-27 rework): the pure rules behind the screen, kept apart so they are tested without rendering.
 *
 * Before this the home screen had three lists that said the same thing in different words: "Needs you now" counted the buyers to
 * call, "AI recommends" gave each of them a full-width card with a big button, and "Hot buyers" showed them a third time. An agent
 * scrolled past seven blue cards to reach this week's numbers. Now there is one call list (each person once, with Call and
 * WhatsApp on the row) and one to-do list (everything else, one row each, the per-listing marketing nudges folded into one row).
 */
import { contactLine } from './leads'
import type { BusinessToday, Lead, RecommendedAction } from './types'

/** Notification kinds that become to-do rows. */
export const PASSED_KIND = 'buyer_passed'
export const INVITE_KIND = 'invite_request'
export const TRIAL_KIND = 'trial_claimed'
export const SEO_KIND = 'seo_week'

export type CallTone = 'bad' | 'action' | 'hot' | 'due'

export interface CallItem {
  id: string
  name: string
  phone: string | null
  /** Why this person is on today's list, in a few words. */
  why: string
  tone: CallTone
}

/** The call list is short on purpose: the rest are one tap away on Leads. */
export const CALL_LIST_MAX = 5

const firstWord = (s: string) => s.trim().split(/\s+/)[0] || s

/**
 * Who to call or message today, each person once, most urgent first: overdue follow-ups, the AI's "call now" picks, leads nobody
 * has answered yet (longest waiting first), follow-ups due today, then hot buyers. Phones come from the leads list when the source
 * row has none.
 */
export function callList(today: Pick<BusinessToday, 'follow_ups' | 'hot_buyers' | 'actions'> | null, leads: Lead[], now: Date = new Date()): CallItem[] {
  const byId = new Map(leads.map((l) => [l.id, l]))
  const seen = new Set<string>()
  const out: CallItem[] = []
  const add = (id: string | undefined, name: string, phone: string | null | undefined, why: string, tone: CallTone) => {
    if (!id || seen.has(id)) return
    const lead = byId.get(id)
    if (lead && (lead.stage === 'won' || lead.stage === 'lost')) return
    seen.add(id)
    out.push({ id, name: name || lead?.name || 'Buyer', phone: phone || lead?.phone || null, why, tone })
  }
  const follow = today?.follow_ups ?? []
  for (const f of follow.filter((x) => x.overdue)) add(f.id, f.name, f.phone, f.reason ? `Overdue: ${f.reason}` : 'Follow-up overdue', 'bad')
  for (const a of (today?.actions ?? []).filter((x) => x.type === 'call' || x.type === 'follow_up')) {
    const lead = a.lead_id ? byId.get(a.lead_id) : undefined
    add(a.lead_id, lead?.name ?? a.title.replace(/^(Call|Follow up with)\s+/i, ''), lead?.phone, a.detail || a.title, a.type === 'call' ? 'hot' : 'bad')
  }
  const waiting = leads
    .filter((l) => l.contact?.state === 'not_contacted' || l.contact?.state === 'waiting_you')
    .sort((a, b) => (a.contact?.at ?? '').localeCompare(b.contact?.at ?? ''))
  for (const l of waiting) {
    const c = contactLine(l.contact, now)
    add(l.id, l.name, l.phone, c?.text ?? 'Waiting for you', c?.tone === 'bad' ? 'bad' : 'action')
  }
  for (const f of follow.filter((x) => !x.overdue)) add(f.id, f.name, f.phone, f.reason ? `Today: ${f.reason}` : 'Follow-up due today', 'due')
  for (const h of today?.hot_buyers ?? []) add(h.id, h.name, h.phone, h.requirement_line ? `Hot buyer · ${h.requirement_line}` : 'Hot buyer', 'hot')
  return out
}

/** The opening line of a WhatsApp to someone on the call list. */
export function callListGreeting(name: string): string {
  return `Hi ${firstWord(name)}, this is regarding your property enquiry.`
}

export interface TodoRow {
  key: string
  href: string
  n: number
  text: string
}

export interface TodoCounts {
  inbox: number
  passed: number
  posts: number
  invites: number
  trials: number
  seo: number
  /** Live listings with no photos (weekly report). */
  photos: number
  /** Listings past their "still available?" date, and how many of them buyers no longer see. */
  freshness: number
  hidden?: number
}

const plural = (n: number, one: string, many: string) => (n === 1 ? one : many)

/**
 * Everything that is not a phone call, one row each. The per-listing "Start marketing" nudges become one row that opens the
 * listing's marketing when there is one, else the live listings.
 */
export function todoRows(c: TodoCounts, actions: RecommendedAction[] = []): TodoRow[] {
  const marketing = actions.filter((a) => a.type === 'create_marketing')
  const confirmN = c.freshness
  const hidden = c.hidden ? ` (${c.hidden} hidden from buyers)` : ''
  const rows: TodoRow[] = [
    { key: 'passed', href: '/studio/inbox', n: c.passed, text: plural(c.passed, 'buyer was passed to you', 'buyers were passed to you') },
    { key: 'inbox', href: '/studio/inbox?tab=needs', n: c.inbox, text: plural(c.inbox, 'message waiting for your answer', 'messages waiting for your answer') },
    { key: 'freshness', href: '/studio/listings?tab=needs', n: confirmN, text: plural(confirmN, 'listing to confirm as still available', 'listings to confirm as still available') + hidden },
    { key: 'photos', href: '/studio/listings?tab=live', n: c.photos, text: plural(c.photos, 'live listing has no photos', 'live listings have no photos') },
    {
      key: 'marketing',
      href: marketing.length === 1 && marketing[0].listing_id ? `/studio/listings/${marketing[0].listing_id}/marketing` : '/studio/listings?tab=live',
      n: marketing.length,
      text: marketing.length === 1 ? marketing[0].title : 'listings without marketing yet: posts and a reel bring buyers',
    },
    { key: 'posts', href: '/studio/content', n: c.posts, text: plural(c.posts, 'post waiting for your OK', 'posts waiting for your OK') },
    { key: 'invites', href: '/studio/admin', n: c.invites, text: plural(c.invites, 'request to join', 'requests to join') },
    { key: 'trials', href: '/studio/agents?tab=signedup', n: c.trials, text: plural(c.trials, 'agent took the free trial', 'agents took the free trial') },
    { key: 'seo', href: '/studio/seo?tab=rankings', n: Math.min(c.seo, 1), text: 'SEO week to read, with pages to ask Google for' },
  ]
  return rows.filter((r) => r.n > 0)
}

export interface SetupStep {
  key: 'brand' | 'rera' | 'listing' | 'share'
  done: boolean
  title: string
  detail: string
  href: string
}

/**
 * A new agent's first steps, shown on home until all are done: the look of the website, the RERA agent number, the first listing,
 * and the first share of the website. "Shared" is known only on this phone (the WhatsApp share button remembers it).
 */
export function setupSteps(s: { hasLogo: boolean; hasRera: boolean; listings: number; shared: boolean; owner: boolean }): SetupStep[] {
  const steps: SetupStep[] = [
    { key: 'brand', done: s.hasLogo, title: 'Add your logo and photo', detail: 'Your website and posts carry your name and look.', href: '/studio/profile' },
    { key: 'rera', done: s.hasRera, title: 'Add your MahaRERA agent number', detail: 'It shows on your website and posts. Needed to keep your account active.', href: '/studio/profile#brand-rera' },
    { key: 'listing', done: s.listings > 0, title: 'Add your first listing', detail: 'Type it the way you would say it. It takes a minute.', href: '/studio/listings/new' },
    { key: 'share', done: s.shared, title: 'Share your website on WhatsApp', detail: 'Send it to your buyer groups. Every enquiry comes to Leads.', href: '/studio/profile' },
  ]
  return s.owner ? steps.filter((x) => x.key !== 'rera') : steps
}

const SHARED_KEY = 'app_site_shared'

export function markSiteShared(): void {
  try {
    window.localStorage.setItem(SHARED_KEY, '1')
  } catch {
    /* storage blocked: the step stays open, which is harmless */
  }
}

export function siteShared(): boolean {
  try {
    return typeof window !== 'undefined' && window.localStorage.getItem(SHARED_KEY) === '1'
  } catch {
    return false
  }
}

/** "Good morning" by the phone's clock. */
export function greeting(now: Date = new Date()): string {
  const h = now.getHours()
  return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
}
