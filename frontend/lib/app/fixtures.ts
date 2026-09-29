/**
 * Fixture mode: an in-memory (+ localStorage) fake implementing AppApi, so the whole flow works with no backend.
 * Enabled by NEXT_PUBLIC_APP_FIXTURES=1, by localStorage app_fixtures=1, or automatically in development
 * when the API is unreachable (see client.ts).
 */
import { ApiError } from './api'
import { parseInr } from './format'
import type {
  AIDraft,
  AIDraftRequest,
  AppApi,
  Lead,
  LeadDetail,
  Listing,
  ListingInput,
  ListingStatus,
  SiteCreateInput,
  Stage,
} from './types'

export interface FixtureStorage {
  getItem(k: string): string | null
  setItem(k: string, v: string): void
}

interface State {
  listings: Listing[]
  leads: LeadDetail[]
  site: { slug: string; name: string } | null
  seq: number
}

const KEY = 'app_fixture_state_v1'
const FIXTURE_OTP = '123456'
export const FIXTURE_TOKEN = 'fixture-token'

const REQUIRED = ['title', 'transaction', 'property_type', 'price_inr', 'city', 'locality', 'description.en']
const LOCALITIES: Record<string, string> = {
  baner: 'Pune', wakad: 'Pune', hinjewadi: 'Pune', kothrud: 'Pune', aundh: 'Pune', kharadi: 'Pune',
  hadapsar: 'Pune', 'viman nagar': 'Pune', andheri: 'Mumbai', powai: 'Mumbai', bandra: 'Mumbai', thane: 'Mumbai',
  whitefield: 'Bengaluru', koramangala: 'Bengaluru', gachibowli: 'Hyderabad', dwarka: 'Delhi',
}

const svgPlaceholder = (label: string) =>
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="#dbeafe"/><text x="320" y="250" font-size="36" text-anchor="middle" fill="#1e3a8a" font-family="sans-serif">${label}</text></svg>`,
  )

function ago(hours: number): string {
  return new Date(Date.now() - hours * 3_600_000).toISOString()
}

function seed(): State {
  const base = { agent_id: 'fixture-agent', visibility: 'network' as const, amenities: ['Parking', 'Lift'] }
  const listing = (id: string, over: Partial<Listing>): Listing => ({
    ...base, id, status: 'live', transaction: 'sale', property_type: 'apartment', title: '', price_inr: 0,
    city: 'Pune', locality: '', description: { en: '' }, media: [{ url: svgPlaceholder('Photo'), kind: 'image', order: 0 }],
    created_at: ago(72), updated_at: ago(48), published_at: ago(48), ...over,
  })
  const lead = (id: string, over: Partial<LeadDetail>): LeadDetail => ({
    id, name: '', phone: '+919800000000', stage: 'new', source: 'whatsapp', message: null, score: 10, temperature: 'cold',
    first_listing_id: 'l1', created_at: ago(30), last_activity_at: ago(2), notes: [], timeline: [], ...over,
  })
  return {
    site: null,
    seq: 100,
    listings: [
      listing('l1', { title: '2 BHK in Baner', locality: 'Baner', bhk: 2, price_inr: 8_500_000, carpet_sqft: 850,
        description: { en: 'Bright 2 BHK, ready possession, near Balewadi High Street.' } }),
      listing('l2', { title: '3 BHK in Wakad', locality: 'Wakad', bhk: 3, price_inr: 12_500_000, status: 'draft', published_at: null,
        description: { en: 'Spacious 3 BHK.' } }),
    ],
    leads: [
      lead('c1', { name: 'Rohit Deshmukh', phone: '+919822012345', score: 78, temperature: 'hot', message: 'Can I visit this Sunday?',
        source: 'instagram', last_activity_at: ago(2), timeline: [
          { type: 'page_view', source: 'instagram', ts: ago(30) },
          { type: 'listing_view', listing_id: 'l1', source: 'instagram', ts: ago(29) },
          { type: 'whatsapp_click', listing_id: 'l1', source: 'instagram', ts: ago(3) },
          { type: 'inquiry', listing_id: 'l1', source: 'instagram', ts: ago(2) }] }),
      lead('c2', { name: 'Sneha Kulkarni', phone: '+919890123456', score: 40, temperature: 'warm', stage: 'contacted',
        message: 'Is the price negotiable?', last_activity_at: ago(26), timeline: [
          { type: 'listing_view', listing_id: 'l1', source: 'whatsapp', ts: ago(27) },
          { type: 'inquiry', listing_id: 'l1', source: 'whatsapp', ts: ago(26) }] }),
      lead('c3', { name: 'Imran Shaikh', phone: '+919767654321', score: 12, temperature: 'cold', source: 'facebook',
        last_activity_at: ago(200), timeline: [{ type: 'page_view', source: 'facebook', ts: ago(200) }] }),
    ],
  }
}

function fixtureError(status: number, detail: string, missing: string[] = []) {
  const fields: Record<string, string> = {}
  missing.forEach((m) => (fields[m] = 'Required'))
  return new ApiError(status, detail, fields, missing)
}

/** Downscale a photo to a small data URL so it fits localStorage; falls back to a plain FileReader. */
export function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve) => {
    const fallback = (): string => {
      const p = svgPlaceholder(file.name.slice(0, 18) || 'Photo')
      resolve(p)
      return p
    }
    try {
      const reader = new FileReader()
      reader.onerror = fallback
      reader.onload = () => {
        const src = String(reader.result)
        if (typeof document === 'undefined') {
          resolve(src)
          return
        }
        const img = new Image()
        img.onerror = () => resolve(src.length < 200_000 ? src : fallback())
        img.onload = () => {
          try {
            const scale = Math.min(1, 640 / Math.max(img.width, img.height))
            const c = document.createElement('canvas')
            c.width = Math.max(1, Math.round(img.width * scale))
            c.height = Math.max(1, Math.round(img.height * scale))
            c.getContext('2d')!.drawImage(img, 0, 0, c.width, c.height)
            resolve(c.toDataURL('image/jpeg', 0.6))
          } catch {
            resolve(fallback())
          }
        }
        img.src = src
      }
      reader.readAsDataURL(file)
    } catch {
      fallback()
    }
  })
}

/** Heuristic stand-in for the AI listing draft: enough to exercise every review-screen state. */
export function fakeDraft(text: string, imageCount: number, hasAudio: boolean): AIDraft {
  const raw = hasAudio && !text.trim() ? '2 BHK flat in Baner Pune, 85 lakh, ready possession' : text
  const s = raw.toLowerCase()
  const draft: ListingInput = { amenities: [], media: [] }
  const confidence: Record<string, number> = {}
  const warnings: string[] = []

  const bhk = s.match(/(\d(?:\.\d)?)\s*bhk/)
  if (bhk) { draft.bhk = parseFloat(bhk[1]); confidence.bhk = 0.95 }
  const price = s.match(/(\d+(?:\.\d+)?)\s*(cr|crore|lakh|lac|lacs|l|k)\b/) || s.match(/(?:rs\.?|₹)\s*([\d,]+)/)
  if (price) {
    const p = parseInr(price[2] ? `${price[1]} ${price[2]}` : price[1])
    if (p) { draft.price_inr = p; confidence.price_inr = 0.9 }
  }
  draft.transaction = /\brent|per month|\/month|pm\b/.test(s) ? 'rent' : 'sale'
  confidence.transaction = /\brent|\bsale|buy/.test(s) ? 0.95 : 0.6
  draft.property_type = /villa/.test(s) ? 'villa' : /plot|land/.test(s) ? 'plot' : /shop/.test(s) ? 'shop' : /office/.test(s) ? 'office' : 'apartment'
  confidence.property_type = /flat|apartment|bhk|villa|plot|shop|office/.test(s) ? 0.9 : 0.55
  const loc = Object.keys(LOCALITIES).find((l) => s.includes(l))
  if (loc) {
    draft.locality = loc.replace(/\b\w/g, (c) => c.toUpperCase())
    draft.city = LOCALITIES[loc]
    confidence.locality = 0.9
    confidence.city = 0.65
  }
  if (/ready/.test(s)) { draft.possession = 'ready'; confidence.possession = 0.55 }
  const sqft = s.match(/(\d{3,4})\s*(?:sq\.?\s*ft|sqft)/)
  if (sqft) { draft.carpet_sqft = parseInt(sqft[1], 10); confidence.carpet_sqft = 0.8 }
  if (draft.bhk || draft.locality) {
    draft.title = `${draft.bhk ? `${draft.bhk} BHK ` : ''}${draft.property_type === 'apartment' ? 'Apartment' : draft.property_type} in ${draft.locality ?? draft.city ?? 'your area'}`
    confidence.title = 0.7
  }
  if (raw.trim()) {
    draft.description = { en: raw.trim().charAt(0).toUpperCase() + raw.trim().slice(1) + '.' }
    confidence['description.en'] = 0.8
  }
  if (draft.price_inr && draft.price_inr < 1_000_000 && draft.transaction === 'sale') warnings.push('Price looks low for a sale. Please check it.')

  const missing = REQUIRED.filter((f) => {
    if (f === 'description.en') return !draft.description?.en
    return !(draft as Record<string, unknown>)[f]
  })
  return { draft, confidence, missing, transcript: hasAudio ? raw : null, warnings }
}

export function createFixtureApi(storage?: FixtureStorage | null): AppApi {
  const store: FixtureStorage | null =
    storage !== undefined ? storage : typeof window !== 'undefined' ? safeLocal() : null
  let memory: State | null = null

  function load(): State {
    if (memory) return memory
    try {
      const raw = store?.getItem(KEY)
      if (raw) return (memory = JSON.parse(raw) as State)
    } catch { /* corrupt or blocked */ }
    return (memory = seed())
  }
  function save() {
    try { store?.setItem(KEY, JSON.stringify(memory)) } catch { /* quota: memory only */ }
  }
  const nextId = (p: string) => `${p}${++load().seq}`
  const find = (id: string) => {
    const l = load().listings.find((x) => x.id === id)
    if (!l) throw fixtureError(404, 'Listing not found')
    return l
  }
  const stamp = <T extends Listing>(l: T): T => ({ ...l, updated_at: new Date().toISOString() })

  return {
    async requestOtp() { return { sent: true, dev_code: FIXTURE_OTP } },
    async verifyOtp(phone, code) {
      if (code !== FIXTURE_OTP) throw fixtureError(400, 'Incorrect OTP')
      const site = load().site
      return { access_token: FIXTURE_TOKEN, token_type: 'bearer', is_new_user: !site, has_site: !!site,
        site_url: site ? `https://example.test/agent/${site.slug}` : null }
    },
    async createSite(input: SiteCreateInput) {
      const s = load()
      const slug = (input.preferred_slug || input.name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
      const created = !s.site
      s.site = s.site ?? { slug, name: input.name }
      save()
      return { slug: s.site.slug, site_url: `https://example.test/agent/${s.site.slug}`, agent_name: s.site.name,
        tagline: `Trusted property advisor in ${input.city}`, created }
    },

    async listListings(status) {
      const items = load().listings.filter((l) => !status || l.status === status)
      return [...items].sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    },
    async getListing(id) { return { ...find(id) } },
    async createListing(input) {
      const now = new Date().toISOString()
      const l: Listing = {
        id: nextId('l'), agent_id: 'fixture-agent', status: 'draft', visibility: 'network', transaction: 'sale',
        property_type: 'apartment', title: '', description: { en: '' }, price_inr: 0, city: '', locality: '',
        amenities: [], media: [], created_at: now, updated_at: now, ...input,
      } as Listing
      load().listings.unshift(l)
      save()
      return { ...l }
    },
    async updateListing(id, patch) {
      const l = find(id)
      Object.assign(l, patch)
      Object.assign(l, stamp(l))
      save()
      return { ...l }
    },
    async publishListing(id) {
      const l = find(id)
      const missing = REQUIRED.filter((f) => {
        if (f === 'description.en') return !l.description?.en
        return !(l as unknown as Record<string, unknown>)[f]
      })
      if (missing.length) throw fixtureError(422, `Missing: ${missing.join(', ')}`, missing)
      l.status = 'live'
      l.published_at = new Date().toISOString()
      l.freshness_confirmed_at = l.published_at
      Object.assign(l, stamp(l))
      save()
      return { ...l }
    },
    async setListingStatus(id, status: ListingStatus) {
      const l = find(id)
      l.status = status
      Object.assign(l, stamp(l))
      save()
      return { ...l }
    },
    async aiDraft(req: AIDraftRequest) {
      await new Promise((r) => setTimeout(r, 600))
      if (!req.text?.trim() && !req.audio && req.image_count < 1) throw fixtureError(400, 'Send text, audio or photos')
      return fakeDraft(req.text ?? '', req.image_count, !!req.audio)
    },
    async uploadImages(files: File[]) {
      return Promise.all(files.map(async (f, i) => ({ id: `img${Date.now()}${i}`, url: await fileToDataUrl(f), original_name: f.name })))
    },

    async listLeads(stage?: Stage) {
      const leads: Lead[] = load().leads.filter((l) => !stage || l.stage === stage).map(({ notes, timeline, ...lead }) => lead)
      return leads.sort((a, b) => b.score - a.score)
    },
    async getLead(id) {
      const l = load().leads.find((x) => x.id === id)
      if (!l) throw fixtureError(404, 'Lead not found')
      return { ...l }
    },
    async updateLead(id, stage, note) {
      const l = load().leads.find((x) => x.id === id)
      if (!l) throw fixtureError(404, 'Lead not found')
      l.stage = stage
      l.last_activity_at = new Date().toISOString()
      if (note) l.notes = [...l.notes, { text: note, ts: l.last_activity_at, stage }]
      save()
      return { ...l }
    },
  }
}

function safeLocal(): FixtureStorage | null {
  try { return window.localStorage } catch { return null }
}
