/** Pure helpers for the listing activity screen (docs/contracts/activity.md). No I/O here. */
import { sourceLabel } from './leads'
import { t } from './strings'
import type { ActivityEventType, ListingActivity } from './types'

type Daily = ListingActivity['daily']

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const IST_OFFSET_MS = 330 * 60_000

/** "2026-10-03" -> "3 Oct". Pure string maths, so the phone's time zone never shifts the day. */
export function dayLabel(date: string): string {
  const m = date.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!m) return date
  const month = MONTHS[Number(m[2]) - 1]
  return month ? `${Number(m[3])} ${month}` : date
}

/** The India (IST) calendar date of an instant, as YYYY-MM-DD. The backend buckets its daily series the same way. */
export function istDateKey(at: Date | number | string): string {
  const ms = at instanceof Date ? at.getTime() : typeof at === 'number' ? at : new Date(at).getTime()
  return new Date(ms + IST_OFFSET_MS).toISOString().slice(0, 10)
}

/** Round a maximum up to a tidy ceiling (4, 5, 10, 20, 50, 100 ...) so bar heights stay comparable. */
export function niceMax(n: number): number {
  if (!isFinite(n) || n <= 4) return 4
  const pow = Math.pow(10, Math.floor(Math.log10(n)))
  for (const step of [1, 2, 5, 10]) if (n <= step * pow) return step * pow
  return 10 * pow
}

export interface ChartBar {
  date: string
  views: number
  enquiries: number
  /** Bar height as a fraction of the plot, 0..1. */
  height: number
}

export interface ChartModel {
  max: number
  bars: ChartBar[]
  totalViews: number
  totalEnquiries: number
}

/** Scale the daily series so the tallest bar fits: heights are fractions of a tidy maximum. */
export function chartScale(daily: Daily | null | undefined): ChartModel {
  const days = daily ?? []
  const max = niceMax(days.reduce((m, d) => Math.max(m, d.views), 0))
  return {
    max,
    bars: days.map((d) => ({ date: d.date, views: d.views, enquiries: d.enquiries, height: Math.min(1, Math.max(0, d.views / max)) })),
    totalViews: days.reduce((n, d) => n + d.views, 0),
    totalEnquiries: days.reduce((n, d) => n + d.enquiries, 0),
  }
}

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

/** Text version of the chart for screen readers: "Last 14 days: 47 views and 3 enquiries. Busiest day: 12 Oct with 9 views." */
export function chartSummary(daily: Daily | null | undefined): string {
  const days = daily ?? []
  const { totalViews, totalEnquiries } = chartScale(days)
  if (days.length === 0 || (totalViews === 0 && totalEnquiries === 0)) return t('actChartNone')
  const parts = [`${t('actLast14')}: ${plural(totalViews, 'view', 'views')} and ${plural(totalEnquiries, 'enquiry', 'enquiries')}.`]
  const best = days.reduce((b, d) => (d.views > b.views ? d : b), days[0])
  if (best.views > 0) parts.push(`Busiest day: ${dayLabel(best.date)} with ${plural(best.views, 'view', 'views')}.`)
  return parts.join(' ')
}

/** Dates to print under the chart: first, middle and last day. */
export function axisLabels(daily: Daily | null | undefined): string[] {
  const days = daily ?? []
  if (days.length === 0) return []
  if (days.length < 3) return days.map((d) => dayLabel(d.date))
  return [days[0], days[Math.floor((days.length - 1) / 2)], days[days.length - 1]].map((d) => dayLabel(d.date))
}

/** "just now", "5m ago", "2h ago", "Yesterday", "3d ago", then a plain date ("12 Oct") after a week. */
export function activityTime(iso: string, now: Date = new Date()): string {
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(iso)
  const then = new Date(hasZone ? iso : iso + 'Z')
  if (isNaN(then.getTime())) return ''
  const min = Math.floor(Math.max(0, now.getTime() - then.getTime()) / 60_000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const days = Math.floor(hr / 24)
  if (days === 1) return t('actYesterday')
  if (days < 7) return `${days}d ago`
  return dayLabel(istDateKey(then))
}

export interface SourceRow {
  key: string
  label: string
  views: number
  enquiries: number
  /** Views as a fraction of the top source, 0..1 (for the little bar). */
  share: number
}

/** Sources with the most views first; ties by enquiries then name. "direct" reads "Direct". */
export function sourceRows(bySource: ListingActivity['by_source'] | null | undefined): SourceRow[] {
  const rows = Object.entries(bySource ?? {}).map(([key, v]) => ({ key, label: sourceLabel(key) || key, views: v?.views ?? 0, enquiries: v?.enquiries ?? 0 }))
  rows.sort((a, b) => b.views - a.views || b.enquiries - a.enquiries || a.label.localeCompare(b.label))
  const top = rows.reduce((m, r) => Math.max(m, r.views), 0)
  return rows.map((r) => ({ ...r, share: top > 0 ? r.views / top : 0 }))
}

/** True when there is nothing to show yet, so the screen leads with "share the link". */
export function activityIsEmpty(a: ListingActivity): boolean {
  return (a.totals?.views ?? 0) === 0 && (a.totals?.enquiries ?? 0) === 0 && (a.feed ?? []).length === 0
}

export const FEED_DOT: Record<ActivityEventType, string> = {
  view: 'bg-blue-400',
  whatsapp_click: 'bg-green-500',
  call_click: 'bg-purple-500',
  share: 'bg-gray-400',
  enquiry: 'bg-amber-500',
}
