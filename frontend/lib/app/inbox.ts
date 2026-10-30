/** Studio Inbox: every conversation (WhatsApp, Messenger/Instagram, website chat) in one list, one thread per person (backend /conversations). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, fetchOnceMore, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export type InboxChannel = 'whatsapp' | 'messenger' | 'instagram' | 'website' | 'facebook_comment' | 'instagram_comment'
/** them = the person who wrote to us; bot = our assistant; you = a person on our side (sent from the inbox). */
export type InboxFrom = 'them' | 'bot' | 'you'

export interface InboxThread {
  id: string
  channel: InboxChannel | string
  name: string | null
  /** Masked by the server, like 99******83 (WhatsApp only). */
  phone: string
  role: 'agent' | 'buyer' | string
  last_text: string
  last_from: InboxFrom | null
  last_at: string | null
  /** Their message is the last one: nobody has answered it. */
  needs_you: boolean
  lead_id: string | null
  lead_saved: boolean
  window_open: boolean
  opted_out: boolean
  can_reply: boolean
  summary: string
  messages: number
  /** WhatsApp: when a person last sent the approved follow-up template (allowed once per 24 hours). */
  follow_up_sent_at?: string | null
  /** out = you passed this buyer to an agent; in = the owner passed this buyer to you. */
  passed: 'out' | 'in' | null
  passed_at: string | null
  /** Comments: the post they commented on, and why it needs you. */
  post_url?: string | null
  reason?: string | null
}

export interface InboxMessage {
  from: InboxFrom
  text: string
  at: string | null
  status: string | null
  error: string | null
}

export interface InboxThreadFull extends InboxThread {
  thread: InboxMessage[]
  bot_paused_until: string | null
  /** The owner may pass this buyer to an agent. */
  can_pass?: boolean
  passed_to_name: string | null
}

export interface PassAgent {
  agent_id: string
  name: string
  has_whatsapp: boolean
  /** Their site's address, so two accounts with one business name can be told apart. */
  slug?: string | null
}

/** What the agent gets when a buyer is passed: every fact on the lead, as label/value lines and as the message text. */
export interface HandoverCard {
  lines: { label: string; value: string }[]
  /** Facts nobody has asked yet (budget, BHK, when, home loan): the agent asks them on the first call. */
  missing: string[]
  text: string
}

export interface PassRule { id: string; agent_id: string; kind: 'area' | 'project'; label: string }

export interface Handover {
  card: HandoverCard
  project: { slug: string; name: string; area: string | null; regno: string } | null
  /** The owner's rule that would pass this lead by itself, if one matches. */
  rule: PassRule | null
  /** The lead's areas: the project's first, then the ones they named. */
  areas: string[]
}

export interface PassResult {
  passed_to: string
  lead_id: string | null
  card: HandoverCard
  /** The agent template from our WhatsApp number: sent, dry_run, failed, no_mobile (null for a chat with no lead). */
  whatsapp_status: string | null
  whatsapp_error: string | null
  rule_added: { kind: 'area' | 'project'; label: string } | null
  /** wa.me link to the agent with the card, sent from the owner's own WhatsApp. Null if the agent's site has no mobile. */
  whatsapp_url: string | null
}

export interface PassedLead {
  lead_id: string
  name: string | null
  passed_at: string
  agent_id: string
  agent_name: string
  /** owner = passed by hand, auto = by a rule, site = the buyer enquired on the agent's own site (the owner watches it) */
  by: 'owner' | 'auto' | string
  rule: string | null
  whatsapp_status: string | null
  whatsapp_error: string | null
  text: string | null
  whatsapp_url: string | null
}

export interface RouteRow extends PassRule { agent_name: string; passed: number }

export type Always = 'area' | 'project' | null

/** The agent template reached them (dry run counts outside production). */
export const whatsappWent = (status: string | null) => status === 'sent' || status === 'dry_run'

async function call<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let body: string | undefined
  if (init.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(init.json)
  }
  let res: Response
  try {
    res = await fetchOnceMore(() => fetch(`${API_BASE_URL}/api/v1/conversations${path}`, { method: init.method ?? 'GET', headers, body }), init.method)
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your internet.')
  }
  const text = await res.text()
  let data: unknown = null
  if (text) {
    try { data = JSON.parse(text) } catch { data = { detail: text.slice(0, 200) } }
  }
  if (!res.ok) throw parseErrorBody(data, res.status)
  return data as T
}

// ---- fixtures (local/dev mode): a few conversations so the Inbox can be walked through without a backend ----
const minsAgo = (m: number) => new Date(Date.now() - m * 60_000).toISOString()
function fixtureThreads(): InboxThreadFull[] {
  const base = {
    phone: '', role: 'buyer', lead_id: null, lead_saved: false, window_open: false, opted_out: false, can_reply: false, summary: '',
    messages: 0, passed: null, passed_at: null, bot_paused_until: null, passed_to_name: null, follow_up_sent_at: null,
  }
  return [
    { ...base, id: 'fx-wa-1', channel: 'whatsapp', name: 'Rohit Deshmukh', phone: '98******45', lead_id: 'c1', lead_saved: true, window_open: true,
      can_reply: true, summary: '2 BHK in Baner, 80L-90L', needs_you: true, last_from: 'them', last_text: 'Can I visit this Sunday?', last_at: minsAgo(25),
      messages: 3, thread: [
        { from: 'them', text: 'Hi, is the 2 BHK in Baner still available?', at: minsAgo(140), status: null, error: null },
        { from: 'bot', text: 'Yes, it is available. 850 sq ft carpet, ready to move, ₹85 L. Would you like to visit?', at: minsAgo(139), status: 'sent', error: null },
        { from: 'them', text: 'Can I visit this Sunday?', at: minsAgo(25), status: null, error: null }] },
    { ...base, id: 'fx-ig-1', channel: 'instagram_comment', name: 'pune.homes.hunt', needs_you: true, reason: 'they asked for the price',
      post_url: 'https://instagram.com/', last_from: 'them', last_text: 'Price please?', last_at: minsAgo(90), messages: 1,
      thread: [{ from: 'them', text: 'Price please?', at: minsAgo(90), status: null, error: null }] },
    { ...base, id: 'fx-web-1', channel: 'website', name: null, needs_you: false, last_from: 'bot', summary: '1 BHK in Hinjewadi',
      last_text: 'Sure, I have noted 1 BHK in Hinjewadi under 50 L. Can I take your number so the agent can call you?', last_at: minsAgo(300), messages: 4,
      thread: [
        { from: 'them', text: 'Looking for 1 BHK in Hinjewadi', at: minsAgo(305), status: null, error: null },
        { from: 'bot', text: 'Sure, I have noted 1 BHK in Hinjewadi under 50 L. Can I take your number so the agent can call you?', at: minsAgo(300), status: 'sent', error: null }] },
  ]
}
let fxThreads: InboxThreadFull[] | null = null
const fx = () => (fxThreads ??= fixtureThreads())
const fxFind = (id: string) => {
  const t = fx().find((x) => x.id === id)
  if (!t) throw new ApiError(404, 'Conversation not found')
  return t
}
const fixtureInbox = {
  threads: async (): Promise<InboxThread[]> => fx().map(({ thread: _t, ...rest }) => rest),
  thread: async (id: string): Promise<InboxThreadFull> => fxFind(id),
  reply: async (id: string, text: string): Promise<InboxThreadFull> => {
    const t = fxFind(id)
    t.thread = [...t.thread, { from: 'you', text, at: new Date().toISOString(), status: 'dry_run', error: null }]
    Object.assign(t, { needs_you: false, last_from: 'you', last_text: text, last_at: new Date().toISOString() })
    return t
  },
  done: async (id: string): Promise<InboxThreadFull> => Object.assign(fxFind(id), { needs_you: false }),
}

export const inboxApi = {
  threads: async (): Promise<InboxThread[]> => (isFixtureMode() ? fixtureInbox.threads() : (await call<{ items: InboxThread[] }>('')).items ?? []),
  thread: (id: string) => (isFixtureMode() ? fixtureInbox.thread(id) : call<InboxThreadFull>(`/${encodeURIComponent(id)}`)),
  reply: (id: string, text: string) =>
    (isFixtureMode() ? fixtureInbox.reply(id, text) : call<InboxThreadFull>(`/${encodeURIComponent(id)}/reply`, { method: 'POST', json: { text } })),
  /** A comment thread was answered on Facebook/Instagram (or needs no answer). */
  done: (id: string) => (isFixtureMode() ? fixtureInbox.done(id) : call<InboxThreadFull>(`/${encodeURIComponent(id)}/done`, { method: 'POST' })),
  agents: async (): Promise<PassAgent[]> => (await call<{ items: PassAgent[] }>('/agents')).items ?? [],
  /** Every chat with this lead (WhatsApp, Messenger/Instagram, website chat), newest first. */
  forLead: async (leadId: string): Promise<InboxThreadFull[]> =>
    (isFixtureMode() ? [] : (await call<{ items: InboxThreadFull[] }>(`/lead/${encodeURIComponent(leadId)}`)).items ?? []),
  /** Message a lead from our WhatsApp number: the thread id; when they have not written in 24 hours, the approved follow-up goes out first. */
  startWithLead: (leadId: string) => call<{ id: string; sent: boolean }>(`/lead/${encodeURIComponent(leadId)}/whatsapp`, { method: 'POST' }),
  pass: (id: string, agentId: string, always: Always = null) =>
    call<PassResult>(`/${encodeURIComponent(id)}/pass`, { method: 'POST', json: { agent_id: agentId, always } }),
  /** Owner: the card the agent would get for this lead, and the rule that would pick the agent. */
  handover: (leadId: string) => call<Handover>(`/lead/${encodeURIComponent(leadId)}/handover`),
  passLead: (leadId: string, agentId: string, always: Always = null) =>
    call<PassResult>(`/lead/${encodeURIComponent(leadId)}/pass`, { method: 'POST', json: { agent_id: agentId, always } }),
  /** Owner: the last 14 days' passes (a passed lead leaves the owner's Leads). */
  passed: async (): Promise<PassedLead[]> => (isFixtureMode() ? [] : (await call<{ items: PassedLead[] }>('/passed')).items ?? []),
  routes: async (): Promise<RouteRow[]> => (await call<{ items: RouteRow[] }>('/routes')).items ?? [],
  addRoute: (agentId: string, kind: 'area' | 'project', label: string) =>
    call<{ id: string }>('/routes', { method: 'POST', json: { agent_id: agentId, kind, label } }),
  removeRoute: (id: string) => call<{ removed: string }>(`/routes/${encodeURIComponent(id)}`, { method: 'DELETE' }),
}

export const CHANNEL_LABEL: Record<string, string> = {
  whatsapp: 'WhatsApp', messenger: 'Messenger', instagram: 'Instagram', website: 'Website chat',
  facebook_comment: 'Facebook comment', instagram_comment: 'Instagram comment',
}
export const isComment = (channel: string) => channel.endsWith('_comment')
export const CHANNEL_CHIP: Record<string, string> = {
  whatsapp: 'bg-green-100 text-green-800', messenger: 'bg-blue-100 text-blue-800', instagram: 'bg-purple-100 text-purple-800', website: 'bg-gray-100 text-gray-700',
  facebook_comment: 'bg-blue-50 text-blue-800 ring-1 ring-blue-200', instagram_comment: 'bg-purple-50 text-purple-800 ring-1 ring-purple-200',
}

/** Ready lines for the reply box: a tap fills the box (it is still sent by hand, and can be changed first). */
export const QUICK_REPLIES = [
  'Thank you! I will call you in a few minutes.',
  'Yes, it is available. When would you like to visit?',
  'Please share a good time to call you.',
  'Sharing the details and photos here shortly.',
]
