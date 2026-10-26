/** Studio client for /inbox/live: who is on the site right now and today's reading (docs/plan/site-live-presence.md D2). */
import { isFixtureMode } from './client'
import { request } from './whatsapp'

export interface LiveWho {
  kind: 'visitor' | 'lead'
  /** "Visitor 3", or the lead's name when this browser already belongs to one */
  label: string
  lead_id?: string
}

export interface LiveStep {
  page: string
  ts: string
  /** seconds the page was visible; null for pages before reading time was counted */
  read_s?: number | null
}

export interface LiveVisitor {
  who: LiveWho
  page: string
  /** a ping in the last 90 s: the page is open and visible, not just left in a tab */
  reading: boolean
  pages: number
  minutes: number
  /** the origins report's key: google, instagram, a src= tag, direct... */
  came_from: string
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
}

export interface Live {
  as_of: string
  now: { count: number; visitors: LiveVisitor[] }
  today: LiveToday
}

const EMPTY_TODAY: LiveToday = { date: '', visitors: 0, visits: 0, pages: 0, one_page_visits: 0, avg_read_s: null, top_pages: [], left_from: [] }

export async function getLive(): Promise<Live> {
  const empty: Live = { as_of: new Date().toISOString(), now: { count: 0, visitors: [] }, today: EMPTY_TODAY }
  if (isFixtureMode()) return empty
  return (await request<Live>('/inbox/live')) ?? empty
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
  '/pune-maharera-tracker': 'MahaRERA tracker', '/privacy': 'Privacy policy',
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
