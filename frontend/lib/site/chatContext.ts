/**
 * What the visitor is looking at, taken from the page path, so the chat assistant greets them for THAT page and asks the question that
 * fits it (backend app/modules/chat/service.py page_for). The kind of page, and its subject as a slug:
 *   /                                              home
 *   /projects/<slug>, /check/<slug>                project     { project }
 *   /projects/area/<place>[/<list>][/<n>-bhk]...   list        { locality, list?, bhk? }   (list: top | new-launches | ready-to-move)
 *   /2-bhk/<area>, /3-bhk/<area>, /price/<b>/<a>   list        { locality, bhk? }
 *   /localities/<slug>[/<community>]               area        { locality }
 *   /guides/<slug>, /insights/<slug>               guide       { topic }
 *   /builders/<slug>                               builder     { builder }
 *   /news..., /pune-maharera-tracker               news
 *   /agents, /trial, /request-invite, /for-agents  agents      (the only pages where the chat greets agents)
 *   /agent/<slug>/listings/<id> (or /<slug>/<id>)  listing     { listing_id, site: 'agent' }
 *   /agent/<slug>/...                              home        { site: 'agent' }   (an agent's own site: its visitors are buyers)
 *   anything else                                  other
 * The server checks every slug against our records; this only reads the URL.
 */
export type PageKind = 'home' | 'project' | 'list' | 'area' | 'builder' | 'guide' | 'news' | 'listing' | 'agents' | 'other'
export type ListKind = 'top' | 'new-launches' | 'ready-to-move'

export interface ChatContext {
  page?: PageKind
  site?: 'agent'
  listing_id?: string
  locality?: string
  post_id?: string
  project?: string
  list?: ListKind
  bhk?: number
  builder?: string
  topic?: string
}

/** The pages for agents (the agents' marketing pages). Everywhere else the visitor is a buyer. */
export const AGENT_PAGES = ['/agents', '/trial', '/request-invite', '/for-agents']

const ID = /^[A-Za-z0-9_-]{1,64}$/
const SLUG = /^[a-z][a-z-]{1,39}$/
const PROJECT = /^[a-z0-9][a-z0-9-]{1,119}$/
const LISTS: readonly string[] = ['top', 'new-launches', 'ready-to-move']

function bhkOf(seg: string | undefined): number | undefined {
  const m = /^([1-4])-bhk$/.exec(seg || '')
  return m ? Number(m[1]) : undefined
}

export function chatContextFromPath(pathname: string | null | undefined): ChatContext | undefined {
  if (pathname == null) return undefined
  const clean = pathname.split('?')[0].split('#')[0]
  const parts = clean.split('/').filter(Boolean)
  const [a, b, c] = parts
  if (!a) return { page: 'home' }
  if (AGENT_PAGES.some((p) => clean === p || clean.startsWith(p + '/'))) return { page: 'agents' }
  if (a === 'agent') {
    const id = c === 'listings' ? parts[3] : c
    if (b && id && id !== 'projects' && ID.test(id)) return { page: 'listing', site: 'agent', listing_id: id }
    return { page: 'home', site: 'agent' }
  }
  if (a === 'projects' && b === 'area' && c && SLUG.test(c)) {
    const rest = parts.slice(3)
    const list = rest.find((s) => LISTS.includes(s)) as ListKind | undefined
    const bhk = rest.map(bhkOf).find((n) => n !== undefined)
    return { page: 'list', locality: c, ...(list ? { list } : {}), ...(bhk ? { bhk } : {}) }
  }
  // a project page (and its MahaRERA check): the chat answers about that project, and does not ask which area
  if ((a === 'projects' || a === 'check') && parts.length === 2 && b !== 'upcoming' && PROJECT.test(b)) return { page: 'project', project: b }
  if ((a === '2-bhk' || a === '3-bhk') && b && SLUG.test(b)) return { page: 'list', locality: b, bhk: Number(a[0]) }
  if (a === 'price' && c && SLUG.test(c)) return { page: 'list', locality: c }
  if (a === 'localities' && b && SLUG.test(b)) return { page: 'area', locality: b }
  if ((a === 'guides' || a === 'insights') && b && PROJECT.test(b)) return { page: 'guide', topic: b }
  if (a === 'builders' && b && PROJECT.test(b)) return { page: 'builder', builder: b }
  if (a === 'news' || a === 'pune-maharera-tracker') return { page: 'news' }
  return { page: 'other' }
}
