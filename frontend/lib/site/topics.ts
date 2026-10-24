/**
 * Topic pages (backend app/modules/calendar/topics.py, files in calendar/topics/<slug>.json): one information page per subject
 * our guide reels keep coming back to (first: the MHADA Pune lottery). No sign-up, no selling.
 * GET /api/v1/public/topics          live topics (sitemap)
 * GET /api/v1/public/topics/{slug}   one topic with the reels posted about it
 * A list comes back empty on any failure; a page is null on a 404 and ok:false on an outage (never a cached 404).
 */
import { cleanPosts, type PublicPost } from '@/lib/posts/data'
import { dontCacheThisRender } from './noCacheOnError'
import { serverApiBase } from './api'

/** Every text comes in the page's own language and in English. */
export type Text = { mr?: string; hi?: string; en: string }
export type TextList = { mr?: string[]; hi?: string[]; en: string[] }

/** How much of a project is still for sale, from the booked share filed on MahaRERA: resale 95%+, open under 30%, limited between. */
export type Availability = 'resale' | 'limited' | 'open'

export interface TopicTable {
  title?: Text
  columns: string[]
  rows: Array<{ cells: string[]; href?: string; tag?: Availability }>
  note?: Text
}

/** A banner at the end of a section: its button opens our chat with `message` as the visitor's first line. */
export interface TopicCta {
  text: Text
  button: Text
  message: Text
}

export interface TopicSummary {
  slug: string
  title: Text
  summary: Text
  status: 'open' | 'closed' | 'results' | null
  checked_on: string | null
  lang: 'mr' | 'hi' | 'en'
}

export interface Topic extends TopicSummary {
  status_line: Text
  dates: Array<{ label: Text; value: Text; state: 'confirmed' | 'planned' | 'unconfirmed' }>
  /** `text` is a lead paragraph; `table` rows are facts (numbers, names) in one language, `href` links a row to our own page.
   *  A section with more than one table lists them under `tables`. An item may open with a **bold lead-in:**. */
  sections: Array<{ id: string; heading: Text; text?: Text; items: TextList; table?: TopicTable; tables?: TopicTable[]; cta?: TopicCta }>
  results: { heading: Text; text: Text; links: Array<{ label: Text; url: string }> } | null
  faq: Array<{ q: Text; a: Text }>
  links: Array<{ label: Text; url: string }>
  warning: Text
  sources: Array<{ name: string; url?: string; read_on?: string }>
  updates: PublicPost[]
}

export const SLUG = /^[a-z0-9-]{1,80}$/

async function getJson(path: string): Promise<{ status: number; body: unknown } | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(`${serverApiBase()}/api/v1/public/topics${path}`, {
      headers: { Accept: 'application/json' }, next: { revalidate: 60 }, signal: ctrl.signal,
    })
    return { status: res.status, body: res.ok ? await res.json() : null }
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

export async function fetchTopics(): Promise<TopicSummary[]> {
  const res = await getJson('')
  return res && Array.isArray(res.body) ? (res.body as TopicSummary[]) : []
}

export type TopicResult = { ok: true; topic: Topic } | { ok: false; notFound: boolean }

export async function fetchTopic(slug: string): Promise<TopicResult> {
  if (!SLUG.test(slug)) return { ok: false, notFound: true }
  const res = await getJson(`/${slug}`)
  if (res?.status === 404) return { ok: false, notFound: true }
  if (!res || res.status >= 400 || !res.body || typeof res.body !== 'object') {
    await dontCacheThisRender()
    return { ok: false, notFound: false }
  }
  const t = res.body as Topic
  return { ok: true, topic: { ...t, updates: cleanPosts(t.updates) } }
}

/** The text in the topic's own language, else English. */
export function say(t: Text | undefined, lang: Topic['lang']): string {
  if (!t) return ''
  return t[lang] || t.en
}

export function sayList(t: TextList | undefined, lang: Topic['lang']): string[] {
  if (!t) return []
  return t[lang] || t.en
}

export const topicPath = (slug: string) => `/guides/${slug}`

/** A section's tables in order: the single `table`, then any under `tables`. */
export function sectionTables(sec: Topic['sections'][number]): TopicTable[] {
  return [...(sec.table ? [sec.table] : []), ...(sec.tables ?? [])]
}

/** "**Lead:** rest" split for a bold lead-in; a text without one has lead null. */
export function leadIn(text: string): { lead: string | null; rest: string } {
  const m = /^\*\*(.+?)\*\*\s*([\s\S]*)$/.exec(text)
  return m ? { lead: m[1], rest: m[2] } : { lead: null, rest: text }
}
