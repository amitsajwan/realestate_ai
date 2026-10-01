/** Typed client, types and fixtures for the Studio Agents screens (owner concierge, backend /concierge). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'
import type { Listing, ListingInput } from './types'
import { BRAND_NAME } from '@/lib/brand'

/** The exact wording the agent agrees to. Must match the backend, which refuses any other text. */
export const CONSENT_TEXT =
  `I agree that ${BRAND_NAME} may feature me and my listings on the ${BRAND_NAME} Facebook Page, Instagram and website, with my name and RERA number, and that buyers' interest comes to my inbox.`

export type PostChannel = 'facebook_page' | 'instagram'
export const CHANNEL_LABEL: Record<PostChannel, string> = { facebook_page: `${BRAND_NAME} Facebook Page`, instagram: `${BRAND_NAME} Instagram` }

export interface ChecklistItem {
  key: string
  label: string
  done: boolean
}
export interface AgentSummary {
  id: string
  name: string
  label: string
  slug: string | null
  /** Masked by the server, like 98******10. */
  mobile: string
  site_url: string | null
  checklist: ChecklistItem[]
  progress: { done: number; total: number }
  listing_count: number
  consent_given: boolean
  last_activity: string | null
}
export interface ConsentState {
  text: string
  given?: boolean
  at?: string
  recorded_by?: string
}
export interface AgentDetail extends AgentSummary {
  listings: Listing[]
  consent: ConsentState
}
export interface CreatedAgent {
  agent: AgentSummary
  created: boolean
  /** Shown once: only a hash is stored. Null when the agent already existed and no new code was asked for. */
  code: string | null
  reissued: boolean
  whatsapp_message: string | null
  whatsapp_url: string | null
}
export interface CreateAgentInput {
  name: string
  mobile: string
  label?: string
  reissue?: boolean
}
export interface Caption {
  text: string
  image_urls: string[]
  link: string | null
}
export type Captions = Partial<Record<PostChannel, Caption>>
export interface PostResult {
  channel: PostChannel
  status: string
  permalink?: string | null
  error?: string | null
}
/** Same shape the Brand editor (A1) loads and saves; kept loose so new fields need no change here. */
export type BrandingData = Record<string, unknown>

export interface ConciergeApi {
  list(): Promise<AgentSummary[]>
  create(input: CreateAgentInput): Promise<CreatedAgent>
  get(id: string): Promise<AgentDetail>
  setConsent(id: string, given: boolean): Promise<ConsentState>
  createListing(id: string, body: ListingInput): Promise<Listing>
  updateListing(id: string, listingId: string, body: ListingInput): Promise<Listing>
  publishListing(id: string, listingId: string): Promise<Listing>
  getBranding(id: string): Promise<BrandingData>
  saveBranding(id: string, data: BrandingData): Promise<BrandingData>
  makePack(id: string, listingId: string): Promise<void>
  captions(id: string, listingId: string, channels?: PostChannel[]): Promise<Captions>
  post(id: string, listingId: string, channels?: PostChannel[]): Promise<PostResult[]>
}

export function friendlyConciergeError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'The Agents area is only for the owner.'
    if (e.status === 404) return 'This agent or listing was not found. Go back and refresh.'
    if (e.status === 429) return 'Too many requests. Wait a minute and try again.'
    return e.detail
  }
  return e instanceof Error ? e.message : 'Something went wrong'
}

/** "Rahul Sharma" -> "Rahul"; used in button labels. */
export const firstName = (name: string) => name.trim().split(/\s+/)[0] || name

/** How complete an agent's setup is, 0 to 1. */
export const progressFraction = (p: { done: number; total: number }) => (p.total ? p.done / p.total : 0)

export function createConciergeApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): ConciergeApi {
  const base = opts.baseUrl ?? API_BASE_URL
  async function request<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    const token = opts.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
    let body: string | undefined
    if (init.json !== undefined) {
      headers['Content-Type'] = 'application/json'
      body = JSON.stringify(init.json)
    }
    let res: Response
    try {
      res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1/concierge${path}`, { method: init.method ?? 'GET', headers, body })
    } catch {
      throw new ApiError(0, 'Cannot reach the server. Check your internet.')
    }
    const text = await res.text()
    let data: unknown = null
    if (text) {
      try {
        data = JSON.parse(text)
      } catch {
        data = { detail: text.slice(0, 200) }
      }
    }
    if (!res.ok) throw parseErrorBody(data, res.status)
    return data as T
  }
  const a = (id: string) => `/agents/${encodeURIComponent(id)}`
  const l = (id: string, lid: string) => `${a(id)}/listings/${encodeURIComponent(lid)}`
  return {
    list: async () => (await request<{ items: AgentSummary[] }>('/agents')).items ?? [],
    create: (input) => request<CreatedAgent>('/agents', { method: 'POST', json: input }),
    get: (id) => request<AgentDetail>(a(id)),
    setConsent: (id, given) => request<ConsentState>(`${a(id)}/consent`, { method: 'POST', json: given ? { given: true, text: CONSENT_TEXT } : { given: false } }),
    createListing: (id, body) => request<Listing>(`${a(id)}/listings`, { method: 'POST', json: body }),
    updateListing: (id, lid, body) => request<Listing>(l(id, lid), { method: 'PATCH', json: body }),
    publishListing: (id, lid) => request<Listing>(`${l(id, lid)}/publish`, { method: 'POST' }),
    getBranding: (id) => request<BrandingData>(`${a(id)}/branding`),
    saveBranding: (id, data) => request<BrandingData>(`${a(id)}/branding`, { method: 'POST', json: data }),
    makePack: async (id, lid) => {
      await request<unknown>(`${l(id, lid)}/pack`, { method: 'POST', json: {} })
    },
    captions: async (id, lid, channels) =>
      (await request<{ captions: Captions }>(`${l(id, lid)}/captions`, { method: 'POST', json: channels ? { channels } : {} })).captions ?? {},
    post: async (id, lid, channels) => {
      const r = await request<{ publications: Array<PostResult & { channel: PostChannel }> }>(`${l(id, lid)}/post`, { method: 'POST', json: channels ? { channels } : {} })
      return (r.publications ?? []).map((p) => ({ channel: p.channel, status: p.status, permalink: p.permalink ?? null, error: p.error ?? null }))
    },
  }
}

// ---- fixtures (local/dev mode): a small stateful fake so every screen can be walked through without a backend ----
const ITEMS = (done: string[]): ChecklistItem[] =>
  [['logo', 'Logo'], ['banner', 'Banner'], ['rera_no', 'RERA agent number'], ['areas', 'Areas'], ['photo', 'Photo'], ['first_listing', 'First listing'], ['three_listings', '3 listings'], ['consent', 'Consent to be featured']]
    .map(([key, label]) => ({ key, label, done: done.includes(key) }))

function listing(agent: string, n: number, over: Partial<Listing> = {}): Listing {
  return {
    id: `fx-l${n}`, agent_id: agent, status: 'live', visibility: 'network', transaction: 'sale', property_type: 'apartment',
    title: '2 BHK in Baner, ready to move', description: { en: 'Bright 2 BHK near the main road.' }, price_inr: 8500000, city: 'Pune', locality: 'Baner',
    bhk: 2, carpet_sqft: 1050, amenities: ['Gym', 'Parking'], media: [], created_at: '2026-09-20T10:00:00Z', updated_at: '2026-09-28T10:00:00Z', ...over,
  }
}

export function fixtureAgents(): AgentDetail[] {
  const mk = (id: string, name: string, label: string, slug: string, mobile: string, done: string[], listings: Listing[], consent: boolean): AgentDetail => ({
    id, name, label, slug, mobile, site_url: `https://punepropertyhub.example/agent/${slug}`, checklist: ITEMS(done),
    progress: { done: done.length, total: 8 }, listing_count: listings.filter((x) => x.status === 'live').length, consent_given: consent,
    last_activity: '2026-09-30T08:30:00Z', listings,
    consent: consent ? { text: CONSENT_TEXT, given: true, at: '2026-09-29T09:00:00Z', recorded_by: 'owner' } : { text: CONSENT_TEXT },
  })
  return [
    mk('fx-a1', 'Rahul Sharma', 'Rahul, Baner', 'rahul-sharma', '98******10', ['logo', 'banner', 'rera_no', 'areas', 'photo', 'first_listing', 'consent'],
      [listing('fx-a1', 1), listing('fx-a1', 2, { title: '3 BHK in Aundh with terrace', locality: 'Aundh', bhk: 3, price_inr: 14500000 }), listing('fx-a1', 3, { status: 'draft', title: '1 BHK rent in Wakad', transaction: 'rent', price_inr: 18000, locality: 'Wakad', bhk: 1 })], true),
    mk('fx-a2', 'Priya Kulkarni', 'Priya, Kothrud', 'priya-kulkarni', '99******42', ['areas', 'photo'], [], false),
    mk('fx-a3', 'Sandeep Patil', 'Sandeep, Hinjewadi', 'sandeep-patil', '97******05', [], [], false),
  ]
}

export function createFixtureConciergeApi(): ConciergeApi {
  const agents = fixtureAgents()
  let seq = 100
  const find = (id: string) => {
    const a = agents.find((x) => x.id === id)
    if (!a) throw new ApiError(404, 'Agent not found')
    return a
  }
  const recount = (a: AgentDetail) => {
    a.listing_count = a.listings.filter((x) => x.status === 'live').length
    const done = new Set(a.checklist.filter((c) => c.done).map((c) => c.key))
    a.listing_count >= 1 ? done.add('first_listing') : done.delete('first_listing')
    a.listing_count >= 3 ? done.add('three_listings') : done.delete('three_listings')
    a.consent_given ? done.add('consent') : done.delete('consent')
    a.checklist = a.checklist.map((c) => ({ ...c, done: done.has(c.key) }))
    a.progress = { done: done.size, total: a.checklist.length }
  }
  const attribution = (a: AgentDetail) => `Listed by ${a.name} | RERA agent reg: A52100012345`
  return {
    list: async () => agents.map(({ listings: _l, consent: _c, ...s }) => s),
    create: async (input) => {
      const id = `fx-a${++seq}`
      const slug = input.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
      const digits = input.mobile.replace(/\D/g, '').slice(-10)
      const agent: AgentDetail = {
        id, name: input.name, label: input.label ?? '', slug, mobile: `${digits.slice(0, 2)}******${digits.slice(-2)}`, site_url: `https://punepropertyhub.example/agent/${slug}`,
        checklist: ITEMS([]), progress: { done: 0, total: 8 }, listing_count: 0, consent_given: false, last_activity: new Date().toISOString(), listings: [], consent: { text: CONSENT_TEXT },
      }
      agents.unshift(agent)
      const code = '482913'
      const msg = `Hi ${firstName(input.name)}, welcome to ${BRAND_NAME}! Open https://avasetu.example/join, enter ${digits} and your personal code ${code}. Please don't share it.`
      return { agent, created: true, code, reissued: false, whatsapp_message: msg, whatsapp_url: `https://wa.me/91${digits}?text=${encodeURIComponent(msg)}` }
    },
    get: async (id) => ({ ...find(id) }),
    setConsent: async (id, given) => {
      const a = find(id)
      a.consent_given = given
      a.consent = given ? { text: CONSENT_TEXT, given: true, at: new Date().toISOString(), recorded_by: 'owner' } : { text: CONSENT_TEXT, given: false }
      recount(a)
      return a.consent
    },
    createListing: async (id, body) => {
      const a = find(id)
      const l = { ...listing(id, ++seq, { status: 'draft' }), ...(body as Partial<Listing>) } as Listing
      a.listings.unshift(l)
      return l
    },
    updateListing: async (id, lid, body) => {
      const a = find(id)
      const i = a.listings.findIndex((x) => x.id === lid)
      if (i < 0) throw new ApiError(404, 'Listing not found')
      a.listings[i] = { ...a.listings[i], ...(body as Partial<Listing>) }
      return a.listings[i]
    },
    publishListing: async (id, lid) => {
      const a = find(id)
      const l = a.listings.find((x) => x.id === lid)
      if (!l) throw new ApiError(404, 'Listing not found')
      l.status = 'live'
      recount(a)
      return l
    },
    getBranding: async (id) => ({ business_name: find(id).name + ' Realty', tagline: 'Homes you can trust in Pune' }),
    saveBranding: async (_id, data) => data,
    makePack: async () => undefined,
    captions: async (id, _lid, channels = ['facebook_page', 'instagram']) => {
      const a = find(id)
      const out: Captions = {}
      if (channels.includes('facebook_page'))
        out.facebook_page = { text: `Ready 2 BHK in Baner, Pune. Bright rooms, gym and parking.\n\n${attribution(a)}\nInterested? https://punepropertyhub.example/i/k7m2x9p\n\n\u{1F517} Details and photos: https://punepropertyhub.example/agent/${a.slug}/listings/fx-l1`, image_urls: [], link: null }
      if (channels.includes('instagram'))
        out.instagram = { text: `2 BHK in Baner, Pune. Gym, parking, ready to move.\n\n${attribution(a)}\nInterested? Link in our bio.\n\n#Pune #Baner #PuneProperty`, image_urls: [], link: null }
      return out
    },
    post: async (id, _lid, channels = ['facebook_page', 'instagram']) => {
      if (!find(id).consent_given) throw new ApiError(409, "Record the agent's consent before posting his listings")
      return channels.map((channel) => ({ channel, status: 'dry_run', permalink: null, error: null }))
    },
  }
}

const real = createConciergeApi({ getToken })
let fake: ConciergeApi | null = null
const impl = (): ConciergeApi => (isFixtureMode() ? (fake ??= createFixtureConciergeApi()) : real)

/** What the screens import: the fixture API in fixture mode, else the real one. */
export const conciergeApi: ConciergeApi = {
  list: () => impl().list(),
  create: (i) => impl().create(i),
  get: (id) => impl().get(id),
  setConsent: (id, g) => impl().setConsent(id, g),
  createListing: (id, b) => impl().createListing(id, b),
  updateListing: (id, l, b) => impl().updateListing(id, l, b),
  publishListing: (id, l) => impl().publishListing(id, l),
  getBranding: (id) => impl().getBranding(id),
  saveBranding: (id, d) => impl().saveBranding(id, d),
  makePack: (id, l) => impl().makePack(id, l),
  captions: (id, l, c) => impl().captions(id, l, c),
  post: (id, l, c) => impl().post(id, l, c),
}
