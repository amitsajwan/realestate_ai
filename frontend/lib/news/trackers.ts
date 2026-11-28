import { dontCacheThisRender } from '@/lib/site/noCacheOnError'
import { fixturesForced, serverApiBase } from '@/lib/site/api'
import type { NewsArea } from './data'

/** One link to a report: `url` may be a Google News redirect (`is_redirect`): link it, never print it. */
export interface TrackerLink { name: string; url: string | null; is_redirect: boolean }
/** One line of a tracker's timeline: a report's headline as its publisher wrote it, and the other publishers with the same story. */
export interface TrackerReport { date: string; headline: string; source: string; url: string | null; is_redirect: boolean; also: TrackerLink[] }
export interface TrackerStatusRow { date: string; stage: number | null; status: string; sources: string[] }
/** A Pune place the tracker touches: its page is /projects/area/<slug>. */
export interface TrackerPlace { slug: string; name: string }
/** The next date the tracker expects ('2027-01' or '2027-01-15') and what is expected then; only while it is still ahead. */
export interface TrackerNext { date: string; what: string }
export interface TrackerFaq { q: string; a: string }

/** One tracker (GET /api/v1/public/trackers[/{slug}]): a thing in Pune that keeps changing, with where it stands today in our words. */
export interface Tracker {
  slug: string
  name: string
  title: string
  summary: string
  kind: 'project' | 'rule' | 'rate'
  areas: NewsArea[]
  places: TrackerPlace[]
  /** The stages a project goes through ([] for rules and rates, or when the stage is not known for sure) and the current one. */
  stages: string[]
  stage: number | null
  status: string
  /** The day the status is true from (YYYY-MM-DD) and the publishers it was written from. */
  status_date: string
  status_sources: string[]
  next: TrackerNext | null
  means: string
  updated: string
  report_count: number
  /** Reports newer than the status line: the page says so, so a reader knows the status may be about to change. */
  newer_reports: number
  latest: TrackerReport | null
  /** Detail only. */
  history: TrackerStatusRow[]
  timeline: TrackerReport[]
  faq: TrackerFaq[]
}

const https = (u: unknown): u is string => typeof u === 'string' && /^https:\/\//.test(u)
const str = (v: unknown): string => (typeof v === 'string' ? v : '')
const day = (v: unknown): string => (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : '')
const num = (v: unknown): number => (typeof v === 'number' && Number.isFinite(v) ? v : 0)
const names = (v: unknown): string[] => (Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string' && !!x.trim()) : [])

function link(raw: unknown): TrackerLink | null {
  const o = raw as Record<string, unknown> | null
  return o && str(o.name).trim() ? { name: str(o.name).trim(), url: https(o.url) ? o.url : null, is_redirect: o.is_redirect === true } : null
}

function report(raw: unknown): TrackerReport | null {
  const o = raw as Record<string, unknown> | null
  if (!o || !str(o.headline).trim()) return null
  return {
    date: day(o.date), headline: str(o.headline).trim(), source: str(o.source), url: https(o.url) ? o.url : null, is_redirect: o.is_redirect === true,
    also: (Array.isArray(o.also) ? o.also : []).flatMap((a) => { const l = link(a); return l ? [l] : [] }),
  }
}

/** Keep only well-formed trackers; a stage outside the list is dropped rather than drawn wrong. */
export function cleanTracker(raw: unknown): Tracker | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  if (typeof r.slug !== 'string' || !/^[a-z0-9-]+$/.test(r.slug) || !str(r.name).trim() || !str(r.status).trim()) return null
  const stages = names(r.stages)
  const stage = typeof r.stage === 'number' && r.stage >= 0 && r.stage < stages.length ? r.stage : null
  return {
    slug: r.slug, name: str(r.name).trim(), title: str(r.title).trim() || str(r.name).trim(), summary: str(r.summary),
    kind: r.kind === 'rule' || r.kind === 'rate' ? r.kind : 'project',
    areas: (Array.isArray(r.areas) ? r.areas : []).flatMap((a): NewsArea[] => {
      const o = a as Record<string, unknown>
      return o && typeof o.slug === 'string' && typeof o.name === 'string' ? [{ key: str(o.key) || undefined, slug: o.slug, name: o.name }] : []
    }),
    places: (Array.isArray(r.places) ? r.places : []).flatMap((p): TrackerPlace[] => {
      const o = p as Record<string, unknown>
      return o && typeof o.slug === 'string' && /^[a-z0-9-]+$/.test(o.slug) && str(o.name).trim() ? [{ slug: o.slug, name: str(o.name).trim() }] : []
    }),
    next: nextOf(r.next),
    stages, stage, status: str(r.status).trim(), status_date: day(r.status_date), status_sources: names(r.status_sources),
    means: str(r.means), updated: day(r.updated), report_count: num(r.report_count), newer_reports: num(r.newer_reports),
    latest: report(r.latest),
    history: (Array.isArray(r.history) ? r.history : []).flatMap((h): TrackerStatusRow[] => {
      const o = h as Record<string, unknown>
      return o && str(o.status).trim()
        ? [{ date: day(o.date), stage: typeof o.stage === 'number' && o.stage >= 0 && o.stage < stages.length ? o.stage : null, status: str(o.status).trim(), sources: names(o.sources) }]
        : []
    }),
    timeline: (Array.isArray(r.timeline) ? r.timeline : []).flatMap((t) => { const x = report(t); return x ? [x] : [] }),
    faq: (Array.isArray(r.faq) ? r.faq : []).flatMap((f): TrackerFaq[] => {
      const o = f as Record<string, unknown>
      return o && str(o.q).trim() && str(o.a).trim() ? [{ q: str(o.q).trim(), a: str(o.a).trim() }] : []
    }),
  }
}

function nextOf(raw: unknown): TrackerNext | null {
  const o = raw as Record<string, unknown> | null
  return o && typeof o.date === 'string' && /^\d{4}-\d{2}(-\d{2})?$/.test(o.date) && str(o.what).trim() ? { date: o.date, what: str(o.what).trim() } : null
}

async function getJson(path: string): Promise<{ status: number; body: unknown } | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(`${serverApiBase()}/api/v1/public/trackers${path}`, { headers: { Accept: 'application/json' }, next: { revalidate: 60 }, signal: ctrl.signal })
    return { status: res.status, body: res.ok ? await res.json() : null }
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

export const trackerPath = (slug: string): string => `/news/track/${slug}`
export const TRACKERS_PATH = '/news/track'
/** A place's own page on the site (the projects there, and what is changing near it). */
export const placePath = (slug: string): string => `/projects/area/${slug}`

/** Every tracker, most recently changed first; `area` (an area key or page slug) keeps those that touch it plus the city-wide rates.
 *  An outage gives [] and the page renders without the block (never fake content). */
export async function fetchTrackers(area?: string): Promise<Tracker[]> {
  if (fixturesForced()) return []
  const res = await getJson(area ? `?area=${encodeURIComponent(area)}` : '')
  if (!res || res.status >= 400) { await dontCacheThisRender(); return [] }
  return (Array.isArray(res.body) ? res.body : []).flatMap((t) => { const x = cleanTracker(t); return x ? [x] : [] })
}

export type TrackerResult = { ok: true; tracker: Tracker } | { ok: false; notFound: boolean }

export async function fetchTracker(slug: string): Promise<TrackerResult> {
  if (fixturesForced()) return { ok: false, notFound: true }
  const res = await getJson(`/${encodeURIComponent(slug)}`)
  if (!res) { await dontCacheThisRender(); return { ok: false, notFound: false } }
  if (res.status === 404) return { ok: false, notFound: true }
  const t = res.status < 400 ? cleanTracker(res.body) : null
  return t ? { ok: true, tracker: t } : { ok: false, notFound: false }
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** '2026-10-23' as '23 Oct 2026' (a calendar day: no time zone to shift it); a month alone ('2027-01') as 'Jan 2027'. */
export function trackerDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '')
  if (m) return `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}`
  const mo = /^(\d{4})-(\d{2})$/.exec(iso || '')
  return mo ? `${MONTHS[Number(mo[2]) - 1]} ${mo[1]}` : ''
}

/** The questions a tracker page shows, as FAQPage data with the same words; null when the tracker has none. */
export function trackerFaqJsonLd(t: Tracker): Record<string, unknown> | null {
  if (!t.faq.length) return null
  return {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: t.faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
  }
}

export const KIND_LABEL: Record<Tracker['kind'], string> = { project: 'Project', rule: 'Rule', rate: 'Rate' }

export const TRACKER_TEXT = {
  heading: 'What is changing',
  lead: 'Roads, metro, the new airport, hospitals, water rules and loan rates: where each one stands today, in our words, with every report behind it.',
  statusAsOf: 'Status as of',
  newer: (n: number) => (n === 1 ? 'A newer report is below: this status may be about to change.' : `${n} newer reports are below: this status may be about to change.`),
  reports: (n: number) => (n === 1 ? '1 report' : `${n} reports`),
  latest: 'Latest report',
  means: 'What it means for you',
  history: 'How the status changed',
  timeline: 'Reports',
  timelineLead: 'Headlines as their publishers wrote them, newest first. The same story from several publishers is one line.',
  also: 'Also reported by',
  sources: 'From reports by',
  how: 'How we keep these pages',
  howLead: 'Every report about a tracked thing is added to its page as it comes in. The status line is rewritten from those reports when they show something moved, and checked before it goes up: every figure, date and name in it must be in a report. A line saying a thing has opened goes up only after we check it ourselves. We keep the older lines so you can see what changed. Approved is not the same as built, and built is not the same as open: we say which one it is.',
  all: 'All trackers',
  areaHeading: (area: string) => `What is changing near ${area}`,
  areaLead: 'Projects and rules that touch this area, and the loan and stamp duty rates every buyer pays.',
  h1: (name: string) => `${name} status`,
  whereItStands: (date: string) => `Where it stands (${date})`,
  next: 'Next expected',
  places: 'Places it touches',
  placesLead: 'Homes and projects in these places, with what is changing near each.',
  faq: 'Questions buyers ask',
  updated: (date: string) => `Last updated ${date}`,
  indexTitle: 'Pune infrastructure and rules tracker: what is changing, status today',
  indexHeading: 'What is changing in Pune',
  indexLead: 'Every road, bridge, metro line, airport, rule and rate we follow, with where it stands today and the dated reports behind it. Newest change first.',
}
