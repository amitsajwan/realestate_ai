/** Studio client for /inbox/live: who is on the site right now and today's reading (docs/plan/site-live-presence.md D2). */
import { isFixtureMode } from './client'
import { request } from './whatsapp'

export interface LiveWho {
  /** you = a browser signed in to Studio: listed, never counted */
  kind: 'visitor' | 'lead' | 'you'
  /** "Visitor 3", the lead's name when this browser already belongs to one, or "You" */
  label: string
  lead_id?: string
}

/** Device, approximate area and network (from the connection at the moment of the visit; the address itself is not kept) */
export interface LiveAbout {
  /** "Android phone · Chrome", "iPhone · Instagram app" */
  device?: string | null
  /** "Pune, Maharashtra": approximate, phones are often routed through Mumbai */
  area?: string | null
  /** "Jio", "Airtel", "ACT Fibernet" */
  network?: string | null
}

export interface LiveStep {
  page: string
  /** India time, "21:05" */
  at: string
  ts?: string
  /** seconds the page was visible; null for pages before reading time was counted */
  read_s?: number | null
  /** how this page was reached (views from 2026-11-16 on): tapped a link, went back, a new tab, a reload */
  via?: 'link' | 'back' | 'new_tab' | 'reload'
  /** the tapped link's words */
  link?: string
  /** the page they were on before (or that opened this tab) */
  from_page?: string
}

export interface LiveVisitor extends LiveAbout {
  who: LiveWho
  page: string
  /** a ping in the last 90 s: the page is open and visible, not just left in a tab */
  reading: boolean
  pages: number
  minutes: number
  /** the origins report's key: google, instagram, a src= tag, direct... */
  came_from: string
  /** the outside page that sent them: "google.co.in", "Google app (search or Discover)", "reddit.com/r/pune/..." */
  outside?: string | null
  journey: LiveStep[]
}

export interface LiveToday {
  date: string
  visitors: number
  visits: number
  pages: number
  one_page_visits: number
  avg_read_s: number | null
  top_pages: Array<{ page: string; views: number; avg_read_s: number | null }>
  left_from: Array<{ page: string; visits: number }>
  /** today's visits, newest first (your own included, marked "You") */
  stories: LiveStory[]
}

/** One visit as the owner reads it: when, from where, on what, the pages in order and what they did */
export interface LiveStory extends LiveAbout {
  who: LiveWho
  /** India time, "00:38" */
  start: string
  end: string
  minutes: number
  here_now: boolean
  came_from: string
  outside?: string | null
  /** from Google: the searches Search Console says bring clicks to the first page (Google never says what this person typed) */
  searched?: string[]
  landing: string
  pages: number
  read_s: number
  steps: LiveStep[]
  did: Array<{ what: string; at: string }>
}

/** "Android phone · Chrome · Pune approx. · Jio": what we know of the visitor's device and connection */
export function aboutLine(a: LiveAbout): string {
  return [a.device, a.area ? `${a.area.split(',')[0]} approx.` : null, a.network].filter(Boolean).join(' · ')
}

export interface Live {
  as_of: string
  now: { count: number; visitors: LiveVisitor[] }
  today: LiveToday
}

const EMPTY_TODAY: LiveToday = { date: '', visitors: 0, visits: 0, pages: 0, one_page_visits: 0, avg_read_s: null, top_pages: [], left_from: [], stories: [] }

export async function getLive(): Promise<Live> {
  const empty: Live = { as_of: new Date().toISOString(), now: { count: 0, visitors: [] }, today: EMPTY_TODAY }
  if (isFixtureMode()) return empty
  return (await request<Live>('/inbox/live')) ?? empty
}

/** A robot that read the site today (backend seo/aivisits.robots_today): owner only. */
export interface RobotRead {
  agent: string
  group: 'answer' | 'search' | 'training' | 'engine' | 'seo' | 'preview' | 'script' | 'other'
  reads: number
  last_at: string
  last_path: string | null
}
export interface RobotsToday { day: string; reads: number; robots: RobotRead[] }

export const ROBOT_GROUP: Record<RobotRead['group'], string> = {
  answer: 'AI answering a question', search: 'Search crawler', training: 'AI training crawler', engine: 'Other search engine',
  seo: 'SEO tool', preview: 'Link preview', script: 'Script or test browser', other: 'Other robot',
}

/** The robots that read the site today; null for anyone but the owner (403) or on any failure, so the list just does not show. */
export async function getRobots(): Promise<RobotsToday | null> {
  if (isFixtureMode()) return null
  try {
    return await request<RobotsToday>('/newsroom/robots')
  } catch {
    return null
  }
}

const words = (slug: string) => {
  const s = decodeURIComponent(slug).replace(/[-_]+/g, ' ').trim()
  return s.charAt(0).toUpperCase() + s.slice(1)
}

// first path part -> what that page is (the buyer site's routes, frontend/app)
const KINDS: Record<string, string> = {
  projects: 'Project', guides: 'Guide', localities: 'Area', builders: 'Builder', insights: 'Insight', posts: 'Post',
  check: 'Project check',
}
const PAGES: Record<string, string> = {
  '/': 'Home page', '/projects': 'All projects', '/news': 'News', '/localities': 'All areas', '/builders': 'All builders',
  '/check': 'Project check', '/insights': 'Insights', '/posts': 'Posts', '/for-agents': 'For agents', '/for-agents/guide': 'Agent guide',
  '/pune-maharera-tracker': 'MahaRERA tracker', '/privacy': 'Privacy policy', '/agents': 'Agents list', '/trial': 'Free trial (agents)',
  '/request-invite': 'Agent invite form', '/enquire': 'Enquiry form',
}

/** "/projects/godrej-ivara-pune" -> "Project: Godrej ivara pune". A page we do not know by name shows its path. */
export function pageLabel(path: string): string {
  const p = (path || '/').split(/[?#]/)[0].replace(/\/+$/, '') || '/'
  if (PAGES[p]) return PAGES[p]
  const parts = p.split('/').filter(Boolean)
  if (parts[0] === 'projects' && parts[1] === 'area' && parts[2]) {
    return `Projects in ${words(parts[2])}` + (parts.length > 3 ? ` (${parts.slice(3).map(words).join(', ').toLowerCase()})` : '')
  }
  if (parts[0] === 'projects' && parts[1] === 'upcoming' && parts[2]) return `Coming soon: ${words(parts[2])}`
  if (parts[0] === 'news' && parts[1] === 'track' && parts[2]) return `Tracker: ${words(parts[2])}`
  if (parts[0] === 'news' && parts[1]) return 'News story'
  if (parts[0] === 'agent' && parts[1]) {
    if (parts[2] === 'projects' && parts[3] === 'compare') return 'Compare projects'
    if (parts[2] === 'projects' && parts[3]) return `Project: ${words(parts[3])}`
    if (parts[2] === 'listings') return 'A listing'
    return 'Agent home page'
  }
  if (KINDS[parts[0]] && parts[1]) return `${KINDS[parts[0]]}: ${words(parts[parts.length - 1])}`
  return p
}

/** 75 -> "1m 15s", 40 -> "40s"; nothing for no reading time yet */
export function readTime(seconds?: number | null): string {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m ? `${m}m${s ? ` ${s}s` : ''}` : `${s}s`
}

/** How one step of a visit was reached, in words; `before` is the page of the step above it. Empty when the browser did not say. */
export function howReached(s: LiveStep, before?: string): string {
  const elsewhere = s.from_page && s.from_page !== before ? ` on ${pageLabel(s.from_page)}` : ''
  if (s.via === 'link') return s.link ? `Tapped “${s.link}”${elsewhere}` : `Tapped a link${elsewhere}`
  if (s.via === 'back') return 'Went back'
  if (s.via === 'new_tab') return `Opened in a new tab from ${pageLabel(s.from_page || '/')}`
  if (s.via === 'reload') return 'Reloaded the page'
  if (s.from_page) return elsewhere ? `Moved on from ${pageLabel(s.from_page)}` : 'Moved on (search box, a button or a form)'
  return ''
}

/** Where a visit started, in words: "Google search (google.co.in)", "Instagram app", "Tagged link ig_ivara", "Opened directly". */
export function startLine(cameFrom: string, outside: string | null | undefined, label: string): string {
  if (cameFrom === 'direct' || cameFrom === 'unknown') return 'Opened directly: typed, a bookmark, or an app that hides where from'
  return outside && !label.toLowerCase().includes(outside.toLowerCase()) ? `${label} (${outside})` : label
}
