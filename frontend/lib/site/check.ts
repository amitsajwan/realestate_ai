/**
 * The project check (docs/plan/project-check.md): what a project's possession date did, from MahaRERA only. The same rule as
 * backend areastats/check.py, so the web card and the DM answer agree. Never "on time" or "safe": we hold no construction progress.
 */
import { monthYear } from './register'

export type CheckState = 'passed' | 'moved' | 'unchanged' | 'dated' | 'no_date'

export function checkState(completionNow: string | null | undefined, monthsLater: number | null | undefined, today = new Date()): CheckState {
  if (!completionNow) return 'no_date'
  if (completionNow < today.toISOString().slice(0, 10)) return 'passed'
  if (monthsLater) return 'moved'
  return monthsLater === 0 ? 'unchanged' : 'dated'
}

const months = (m: number) => `${m} month${m === 1 ? '' : 's'}`

/** The pill on a search result: a few words. */
export function checkPill(s: CheckState, monthsLater?: number | null): string {
  switch (s) {
    case 'passed': return 'Date passed'
    case 'moved': return `Moved ${months(monthsLater ?? 0)} later`
    case 'unchanged': return 'Date unchanged'
    case 'dated': return 'Date filed'
    default: return 'No date yet'
  }
}

/** The card's headline and the line under it. */
export function checkVerdict(s: CheckState, now: string | null | undefined, first: string | null | undefined, monthsLater?: number | null,
  extension = 0): { title: string; sub: string } {
  const ext = extension && first && now !== first
    ? ` MahaRERA added ${months(extension)} to most projects' dates in August 2026 (Order 66/2026).` : ''
  if (ext && s === 'unchanged') {
    return { title: `Builder's date unchanged: ${monthYear(first)}`, sub: `MahaRERA now shows ${monthYear(now)}.${ext}` }
  }
  switch (s) {
    case 'passed': return { title: `Possession date has passed: ${monthYear(now)}`, sub: 'Ask the builder for the occupancy certificate (OC) and the handover date in writing.' }
    case 'moved': return { title: `Possession moved ${months(monthsLater ?? 0)} later`, sub: `Now ${monthYear(now)}. It was ${monthYear(first)} when the project was registered.${ext}` }
    case 'unchanged': return { title: `Possession date unchanged: ${monthYear(now)}`, sub: `The same date the builder filed at registration${first ? ` (${monthYear(first)})` : ''}.` }
    case 'dated': return { title: `Possession date: ${monthYear(now)}`, sub: 'As filed on MahaRERA.' }
    default: return { title: 'No possession date on MahaRERA yet', sub: 'The builder has not filed one, or MahaRERA has not shown it.' }
  }
}

/** Tailwind classes per state: the verdict block and the pill. Colours say what the date did, nothing more. */
export const CHECK_STYLE: Record<CheckState, { block: string; pill: string }> = {
  passed: { block: 'bg-rose-50 text-rose-950 ring-rose-200', pill: 'bg-rose-50 text-rose-800 ring-rose-200' },
  moved: { block: 'bg-amber-50 text-amber-950 ring-amber-200', pill: 'bg-amber-50 text-amber-900 ring-amber-200' },
  unchanged: { block: 'bg-emerald-50 text-emerald-950 ring-emerald-200', pill: 'bg-emerald-50 text-emerald-800 ring-emerald-200' },
  dated: { block: 'bg-slate-50 text-slate-900 ring-slate-200', pill: 'bg-slate-100 text-slate-700 ring-slate-300' },
  no_date: { block: 'bg-slate-50 text-slate-900 ring-slate-200', pill: 'bg-slate-100 text-slate-700 ring-slate-300' },
}

/** MahaRERA Order 66/2026 (backend pages.extension_months): 4 months MahaRERA added itself in August 2026 to projects registered
 * before 1 Aug 2026 whose date fell on or after 28 Feb 2026. 0 when it does not apply. */
export function extensionMonths(now: string | null | undefined, registeredOn: string | null | undefined): number {
  return registeredOn && registeredOn < '2026-08-01' && now && now >= '2026-06-28' ? 4 : 0
}

/** Whole months the builder moved a date later (backend pages.months_later), net of MahaRERA's 2026 extension: 0 when not
 * later; null when either date is unknown. */
export function monthsLater(now: string | null | undefined, first: string | null | undefined, registeredOn?: string | null): number | null {
  const a = /^(\d{4})-(\d{2})-(\d{2})/.exec(first || ''), b = /^(\d{4})-(\d{2})-(\d{2})/.exec(now || '')
  if (!a || !b) return null
  if ((now as string) <= (first as string)) return 0
  const n = (Number(b[1]) - Number(a[1])) * 12 + (Number(b[2]) - Number(a[2])) - (Number(b[3]) < Number(a[3]) - 3 ? 1 : 0)
  return Math.max(0, n - extensionMonths(now, registeredOn))
}

/** Projects this viewer checked, newest first (this browser only: a convenience, never the record). */
export interface SavedCheck { slug: string; regno: string; name: string }
const SAVED_KEY = 'avasetu.checks'

export function savedChecks(): SavedCheck[] {
  try {
    const v = JSON.parse(window.localStorage.getItem(SAVED_KEY) || '[]')
    return Array.isArray(v) ? v.filter((x) => x && typeof x.slug === 'string').slice(0, 8) : []
  } catch {
    return []
  }
}

export function saveCheck(c: SavedCheck): void {
  try {
    const rest = savedChecks().filter((x) => x.regno !== c.regno)
    window.localStorage.setItem(SAVED_KEY, JSON.stringify([c, ...rest].slice(0, 8)))
  } catch { /* private window or blocked storage: nothing to remember */ }
}

export function forgetCheck(regno: string): void {
  try {
    window.localStorage.setItem(SAVED_KEY, JSON.stringify(savedChecks().filter((x) => x.regno !== regno)))
  } catch { /* nothing stored */ }
}
