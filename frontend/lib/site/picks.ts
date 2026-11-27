/** A buyer's picks without signing in: up to COMPARE_MAX projects to compare side by side and a shortlist to send the family.
 *  Kept in the browser (localStorage), and always also in the page's address (/compare?projects=a,b, /shortlist?ids=a,b), so a
 *  link sent on WhatsApp opens the same list on another phone. Both pages are noindex, follow: every combination of projects
 *  would be a near copy of the project pages they link to (seo-system.md section 9, no thin indexable pages). */

export const COMPARE_KEY = 'avasetu_compare_ids'
export const SAVED_KEY = 'avasetu_shortlist'
export const COMPARE_MAX = 3
export const SAVED_MAX = 12
/** fired on window when either list changes, so every button and the bar on the page redraw together */
export const PICKS_EVENT = 'avasetu-picks'

export type PickList = 'compare' | 'saved'
const KEY: Record<PickList, string> = { compare: COMPARE_KEY, saved: SAVED_KEY }
const MAX: Record<PickList, number> = { compare: COMPARE_MAX, saved: SAVED_MAX }

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,15}$/

/** The project slugs in a query value ("a,b" or ["a", "b"]): valid ones only, each once, at most `max`, in the order given. */
export function parseSlugs(raw: string | string[] | null | undefined, max: number): string[] {
  const parts = (Array.isArray(raw) ? raw.join(',') : raw ?? '').split(',').map((s) => s.trim().toLowerCase())
  const out: string[] = []
  for (const s of parts) {
    if (out.length >= max) break
    if (SLUG.test(s) && !out.includes(s)) out.push(s)
  }
  return out
}

/** Add a slug, or take it out when it is there already. A full list drops its oldest pick to make room. */
export function toggle(list: string[], slug: string, max: number): string[] {
  if (list.includes(slug)) return list.filter((s) => s !== slug)
  return [...list, slug].slice(-max)
}

export const comparePath = (slugs: string[]): string => (slugs.length ? `/compare?projects=${slugs.join(',')}` : '/compare')
export const shortlistPath = (slugs: string[]): string => (slugs.length ? `/shortlist?ids=${slugs.join(',')}` : '/shortlist')

/** The message the shortlist sends on WhatsApp: the projects by name, and the link that opens the same list. */
export function shortlistMessage(names: string[], url: string): string {
  const lines = names.map((n, i) => `${i + 1}. ${n}`)
  return [`My shortlist of Pune projects (MahaRERA checked):`, ...lines, '', url].join('\n')
}

/** wa.me with no number: WhatsApp asks whom to send it to, so the buyer picks the family group. */
export const whatsappShare = (text: string): string => 'https://wa.me/?text=' + encodeURIComponent(text)

/** The list kept in this browser; empty on the server or when storage is blocked (private mode, a full quota). */
export function readPicks(list: PickList): string[] {
  try {
    if (typeof window === 'undefined') return []
    return parseSlugs(window.localStorage.getItem(KEY[list]), MAX[list])
  } catch {
    return []
  }
}

export function writePicks(list: PickList, slugs: string[]): void {
  try {
    window.localStorage.setItem(KEY[list], parseSlugs(slugs, MAX[list]).join(','))
  } catch {
    // storage blocked: the page's address still carries the list
  }
  try {
    window.dispatchEvent(new Event(PICKS_EVENT))
  } catch {
    // no window (tests without a DOM)
  }
}

export function togglePick(list: PickList, slug: string): string[] {
  const next = toggle(readPicks(list), slug, MAX[list])
  writePicks(list, next)
  return next
}
