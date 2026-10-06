/**
 * Fixture mode: an in-memory (+ localStorage) fake implementing AppApi, so the whole flow works with no backend.
 * Enabled by NEXT_PUBLIC_APP_FIXTURES=1, by localStorage app_fixtures=1, or automatically in development
 * when the API is unreachable (see client.ts).
 */
import { ApiError } from './api'
import { formatInr, parseInr } from './format'
import { budgetRange, buildWhatsappUrl } from './leads'
import { activityFor } from './fixtures-activity'
import { computeFreshness } from './freshness'
import { actionsFor, buildFixturePack, matchingFor, performanceFor } from './fixtures-marketing'
import { nextOutcome, resultsFor } from './fixtures-outcomes'
import { buildPublications, FIXTURE_SOCIAL_STATUS } from './fixtures-social'
import { outcomePatchError } from './outcomes'
import type {
  AIDraft,
  AIDraftRequest,
  AboutSuggestRequest,
  AboutSuggestion,
  AppApi,
  BusinessToday,
  DraftLanguage,
  FollowupDraft,
  Lead,
  LeadDetail,
  LeadMatch,
  LeadPatch,
  Listing,
  ListingActivity,
  ListingInput,
  ListingStatus,
  MarketingPack,
  MatchingLeads,
  NextAction,
  Publication,
  Requirement,
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
  packs: Record<string, MarketingPack>
  publications?: Publication[]
}

export const FIXTURE_STATE_KEY = 'app_fixture_state_v6'
const KEY = FIXTURE_STATE_KEY
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
const ahead = (hours: number) => ago(-hours)

const TIMELINE_TEXT: Record<string, string> = { now: 'right away', '1_3_months': 'within 1-3 months', '3_6_months': 'within 3-6 months', exploring: 'just exploring' }
const FIN_TEXT: Record<string, string> = { home_loan: 'on a home loan', own_funds: 'with own funds', undecided: '' }
const TIMELINE_SHORT: Record<string, string> = { now: 'Now', '1_3_months': '1-3 months', '3_6_months': '3-6 months', exploring: 'Just looking' }

const req = (over: Partial<Requirement>): Requirement => ({
  bhk: null, budget_min_inr: null, budget_max_inr: null, timeline: null, financing: null, localities: [], source: 'stated', ...over,
})

export function requirementLine(r?: Requirement | null): string | null {
  if (!r) return null
  const parts = [
    r.bhk ? `${r.bhk} BHK` : '',
    budgetRange(r.budget_min_inr, r.budget_max_inr).replace(/₹| /g, ''),
    r.localities.join(', '),
    r.timeline ? TIMELINE_SHORT[r.timeline] : '',
  ].filter(Boolean)
  return parts.length ? parts.join(' · ') : null
}

/** Transparent rule score (same idea as the backend): type 10, BHK 25, budget 40 (+10% = half), locality 25. */
export function scoreMatch(r: Requirement, l: Listing): LeadMatch {
  let pct = 10
  const reasons: string[] = ['Property type fits']
  if (r.bhk && l.bhk === r.bhk) { pct += 25; reasons.push(`${l.bhk} BHK as wanted`) }
  else if (!r.bhk) pct += 12
  const lo = r.budget_min_inr ?? 0
  const hi = r.budget_max_inr
  if (hi == null && !lo) pct += 20
  else if (l.price_inr >= lo && (hi == null || l.price_inr <= hi)) { pct += 40; reasons.push('Inside budget') }
  else if (hi != null && l.price_inr <= hi * 1.1) { pct += 20; reasons.push('Slightly above budget') }
  if (r.localities.length === 0) pct += 10
  else if (r.localities.some((x) => x.toLowerCase() === l.locality.toLowerCase())) { pct += 25; reasons.push(`In ${l.locality}`) }
  return { listing_id: l.id, title: l.title, price_inr: l.price_inr, locality: l.locality, match_pct: Math.min(100, pct), reasons }
}

function isOpen(l: LeadDetail) { return l.stage !== 'won' && l.stage !== 'lost' }
function endOfToday() { const d = new Date(); d.setHours(23, 59, 59, 999); return d.getTime() }

function computeMatches(l: LeadDetail, listings: Listing[]): LeadMatch[] {
  if (!l.requirement) return []
  return listings
    .filter((x) => x.status === 'live')
    .map((x) => scoreMatch(l.requirement!, x))
    .filter((m) => m.match_pct >= 50)
    .sort((a, b) => b.match_pct - a.match_pct)
    .slice(0, 3)
}

function computeNextAction(l: LeadDetail): NextAction {
  const ageH = (Date.now() - new Date(l.created_at).getTime()) / 3_600_000
  if (l.stage === 'site_visit') return { type: 'follow_up', reason: 'Confirm the visit' }
  if (l.temperature === 'hot') return { type: 'schedule_visit', reason: 'Very interested, book a site visit' }
  if (l.stage === 'new' && l.phone && ageH > 24) return { type: 'call', reason: 'Respond within a day' }
  if (l.requirement?.timeline === 'now' || l.requirement?.timeline === '1_3_months') return { type: 'whatsapp', reason: 'Wants to buy soon' }
  return { type: 'follow_up', reason: 'Keep in touch' }
}

function computeSummary(l: LeadDetail, m: LeadMatch[]): string {
  const r = l.requirement
  const parts: string[] = []
  if (r) {
    const budget = budgetRange(r.budget_min_inr, r.budget_max_inr)
    const want = [r.bhk ? `a ${r.bhk} BHK` : 'a property', budget && `around ${budget}`, r.localities.length ? `in ${r.localities.join(', ')}` : '', r.timeline ? TIMELINE_TEXT[r.timeline] : '', r.financing ? FIN_TEXT[r.financing] : ''].filter(Boolean)
    parts.push(`Wants ${want.join(' ')}.`)
  } else {
    parts.push('Has not said what they want yet.')
  }
  const views = l.timeline.filter((e) => e.type === 'listing_view').length
  if (views) parts.push(`Viewed your listings ${views} time${views > 1 ? 's' : ''}.`)
  if (l.timeline.some((e) => e.type === 'whatsapp_click')) parts.push('Tapped WhatsApp.')
  if (m[0]) parts.push(`${m[0].title} is a ${m[0].match_pct}% match.`)
  return parts.join(' ')
}

function enrich(l: LeadDetail, listings: Listing[]): LeadDetail {
  const matches = computeMatches(l, listings)
  const due = l.follow_up?.due_at ?? null
  return {
    ...l,
    requirement_line: requirementLine(l.requirement),
    ai_summary: computeSummary(l, matches),
    next_action: computeNextAction(l),
    matches,
    follow_up: { due_at: due, overdue: !!due && new Date(due).getTime() < Date.now() && isOpen(l) },
  }
}

const firstName = (n: string) => n.split(' ')[0]

/** Deterministic follow-up text. Hindi has a small template; Marathi falls back to English (as the contract allows). */
export function draftFor(l: LeadDetail, matches: LeadMatch[], language: DraftLanguage, listingTitle?: string): FollowupDraft {
  const based: string[] = []
  const days = Math.floor((Date.now() - new Date(l.last_activity_at).getTime()) / 86_400_000)
  if (days >= 1) based.push(`No reply for ${days} day${days > 1 ? 's' : ''}`)
  const budget = budgetRange(l.requirement?.budget_min_inr, l.requirement?.budget_max_inr)
  if (budget) based.push(`Budget ${budget.replace(/₹| /g, '')}`)
  const top = matches[0]
  if (top) based.push(`${top.title} matches ${top.match_pct}%`)
  if (listingTitle) based.push(`They enquired about ${listingTitle}`)
  if (based.length === 0) based.push('They enquired recently')
  const name = firstName(l.name)
  const useHi = language === 'hi'
  const message = useHi
    ? `नमस्ते ${name} जी, आपने ${listingTitle ?? 'हमारी प्रॉपर्टी'} के बारे में पूछा था.${top ? ` ${top.title} (₹${formatInr(top.price_inr)}) भी आपके बजट में है.` : ''} क्या आप इस हफ्ते साइट विज़िट के लिए आ सकते हैं?`
    : `Hi ${name}, thank you for your interest${listingTitle ? ` in ${listingTitle}` : ''}.${budget ? ` I have kept your budget of ${budget} in mind.` : ''}${top ? ` ${top.title} at ₹${formatInr(top.price_inr)} in ${top.locality} could suit you well.` : ''} Would you like to visit this week?`
  return { message, whatsapp_url: buildWhatsappUrl(l.phone, message), language: useHi ? 'hi' : 'en', based_on: based }
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
    first_listing_id: 'l1', outcome: null, created_at: ago(30), last_activity_at: ago(2), notes: [], timeline: [],
    requirement: null, follow_up: { due_at: null, overdue: false }, ...over,
  })
  return {
    site: null,
    seq: 100,
    packs: {},
    listings: [
      listing('l1', { title: '2 BHK in Baner', locality: 'Baner', bhk: 2, price_inr: 8_500_000, carpet_sqft: 850,
        possession: 'ready', created_at: ago(20), published_at: ago(20), freshness_confirmed_at: ago(24 * 4),
        description: { en: 'Bright 2 BHK, ready possession, near Balewadi High Street.' } }),
      listing('l2', { title: '3 BHK in Wakad', locality: 'Wakad', bhk: 3, price_inr: 12_500_000, status: 'draft', published_at: null,
        description: { en: 'Spacious 3 BHK.' } }),
      listing('l3', { title: '2 BHK near Baner Road', locality: 'Baner', bhk: 2, price_inr: 9_200_000, carpet_sqft: 910,
        published_at: ago(24 * 30), freshness_confirmed_at: ago(24 * 30), // 30 days: the app asks "still available?"
        description: { en: '2 BHK with a large balcony.' } }),
      listing('l4', { title: '3 BHK in Kharadi', locality: 'Kharadi', bhk: 3, price_inr: 14_000_000, carpet_sqft: 1150,
        published_at: ago(24 * 52), freshness_confirmed_at: ago(24 * 52), // 52 days: hidden from buyers until confirmed
        description: { en: 'Premium 3 BHK near the IT park.' } }),
      listing('l5', { title: '1 BHK in Hinjewadi', locality: 'Hinjewadi', bhk: 1, price_inr: 4_200_000, carpet_sqft: 520,
        description: { en: 'Compact 1 BHK for first-time buyers.' } }),
    ],
    leads: [
      lead('c1', { name: 'Rohit Deshmukh', phone: '+919822012345', score: 78, temperature: 'hot', message: 'Can I visit this Sunday?',
        source: 'instagram', last_activity_at: ago(2), created_at: ago(2),
        requirement: req({ bhk: 2, budget_min_inr: 8_000_000, budget_max_inr: 9_000_000, localities: ['Baner'], timeline: '1_3_months', financing: 'home_loan' }),
        timeline: [
          { type: 'page_view', source: 'instagram', ts: ago(30) },
          { type: 'listing_view', listing_id: 'l1', source: 'instagram', ts: ago(29) },
          { type: 'whatsapp_click', listing_id: 'l1', source: 'instagram', ts: ago(3) },
          { type: 'inquiry', listing_id: 'l1', source: 'instagram', ts: ago(2) }] }),
      lead('c2', { name: 'Sneha Kulkarni', phone: '+919890123456', score: 40, temperature: 'warm', stage: 'contacted',
        message: 'Is the price negotiable?', last_activity_at: ago(50), first_listing_id: 'l4',
        requirement: req({ bhk: 3, budget_min_inr: 12_000_000, budget_max_inr: 20_000_000, localities: ['Kharadi'], timeline: '3_6_months', financing: 'undecided', source: 'mixed' }),
        follow_up: { due_at: ago(20), overdue: true },
        timeline: [
          { type: 'listing_view', listing_id: 'l4', source: 'whatsapp', ts: ago(52) },
          { type: 'inquiry', listing_id: 'l4', source: 'whatsapp', ts: ago(50) }] }),
      lead('c3', { name: 'Imran Shaikh', phone: '+919767654321', score: 12, temperature: 'cold', source: 'facebook',
        created_at: ago(200), last_activity_at: ago(200), timeline: [{ type: 'page_view', source: 'facebook', ts: ago(200) }] }),
      lead('c4', { name: 'Priya Nair', phone: '+919811223344', score: 85, temperature: 'hot', stage: 'site_visit', source: 'whatsapp',
        message: '2bhk in baner under 95 lakh, need it soon, own funds', last_activity_at: ago(6), created_at: ago(100),
        requirement: req({ bhk: 2, budget_min_inr: 7_000_000, budget_max_inr: 9_500_000, localities: ['Baner'], timeline: 'now', financing: 'own_funds', source: 'inferred' }),
        follow_up: { due_at: ahead(3), overdue: false },
        timeline: [
          { type: 'listing_view', listing_id: 'l1', source: 'whatsapp', ts: ago(90) },
          { type: 'listing_view', listing_id: 'l3', source: 'whatsapp', ts: ago(80) },
          { type: 'whatsapp_click', listing_id: 'l3', source: 'whatsapp', ts: ago(70) },
          { type: 'inquiry', listing_id: 'l3', source: 'whatsapp', ts: ago(6) }] }),
      lead('c5', { name: 'Vikram Joshi', phone: '+919922334455', score: 33, temperature: 'warm', stage: 'contacted', source: 'direct',
        first_listing_id: 'l5', last_activity_at: ago(30), created_at: ago(120),
        requirement: req({ bhk: 1, budget_max_inr: 5_000_000, localities: ['Hinjewadi'], timeline: 'exploring', financing: 'home_loan' }),
        follow_up: { due_at: ahead(72), overdue: false },
        timeline: [{ type: 'listing_view', listing_id: 'l5', source: 'direct', ts: ago(30) }] }),
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
const AREA_GUIDE: Record<string, { name: string; connectivity: string[]; offices: string[] }> = {
  kharadi: { name: 'Kharadi', connectivity: ["On Pune's eastern IT corridor, close to large office campuses.", 'Metro Line 4 (Kharadi to Khadakwasla) is approved, not running yet. Check the latest status with Maha-Metro.'], offices: ['EON Free Zone', 'World Trade Center Pune'] },
  'upper kharadi': { name: 'Upper Kharadi', connectivity: ['On the same eastern corridor as Kharadi and Wagholi.', 'Metro Line 4 (Kharadi to Khadakwasla) is approved, not running yet. Check the latest status with Maha-Metro.', 'Metro Corridor 2B (Ramwadi to Wagholi) is approved, not running yet. Check the latest status with Maha-Metro.'], offices: [] },
  wagholi: { name: 'Wagholi', connectivity: ['On the eastern corridor of Pune, further out than Kharadi.', 'Metro Corridor 2B (Ramwadi to Wagholi) is approved, not running yet. Check the latest status with Maha-Metro.'], offices: [] },
}

/** Mirrors POST /listings/ai/about-suggest: keyword matches from the agent's words, area lines only from the guide. */
export function fakeAboutSuggestion(req: AboutSuggestRequest): AboutSuggestion {
  const s = (req.description || '').toLowerCase()
  const agent = 'agent' as const
  const out: AboutSuggestion = { highlights: [], amenities: [], nearby: [], connectivity: [], fields: {}, project_name: req.project_name ?? null, area_known: false, area_name: null }
  for (const [label, rx] of [['Parking', /parking/], ['Lift', /\blift/], ['Gym', /\bgym/], ['Swimming pool', /pool/], ['Security', /security|cctv|guard/], ['Power backup', /power backup|generator/], ['Garden', /garden/], ['Clubhouse', /club ?house/]] as Array<[string, RegExp]>) {
    if (rx.test(s)) out.amenities.push({ text: label, source: agent })
  }
  for (const [label, rx] of [['East facing', /east[\s-]*facing/], ['Corner flat', /corner flat/], ['Ready to move', /ready[\s-]*to[\s-]*move/]] as Array<[string, RegExp]>) {
    if (rx.test(s)) out.highlights.push({ text: label, source: agent })
  }
  if (/school (nearby|close)|near .*school/.test(s)) out.nearby.push({ type: 'school', name: 'School nearby', source: agent })
  const park = s.match(/(\d|one|two)\s*(covered|open|car)?\s*parking/)
  if (park) out.fields.parking = { text: `${park[1]}${park[2] ? ' ' + park[2] : ''} parking`.replace(/^./, (c) => c.toUpperCase()), source: agent }
  if (/24\s*x\s*7 water/.test(s)) out.fields.water = { text: '24x7 water supply', source: agent }
  const maint = s.match(/maintenance\s*(?:rs\.?|₹)?\s*(\d[\d,]*)/)
  if (maint) out.fields.maintenance = { text: `₹${maint[1]} per month`, source: agent }
  const guide = AREA_GUIDE[(req.locality || '').toLowerCase().replace(/-/g, ' ').trim()]
  if (guide) {
    out.area_known = true
    out.area_name = guide.name
    out.connectivity = guide.connectivity.map((text) => ({ text, source: 'area_guide' as const }))
    out.nearby.push(...guide.offices.map((name) => ({ type: 'office' as const, name, source: 'area_guide' as const })))
  }
  return out
}

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
  /** What the API returns: the stored listing plus the computed freshness / days_since_confirmed. */
  const view = (l: Listing): Listing => ({ ...l, ...computeFreshness(l) })
  const stamp = <T extends Listing>(l: T): T => ({ ...l, updated_at: new Date().toISOString() })
  const shareUrlFor = (id: string) => `https://example.test/agent/${load().site?.slug ?? 'demo'}/listings/${id}?src=whatsapp`
  const matchesFor = (l: Listing) => {
    const st = load()
    return matchingFor(l, st.leads.map((x) => enrich(x, st.listings)), scoreMatch, shareUrlFor(l.id), buildWhatsappUrl)
  }

  return {
    async requestOtp() { return { sent: true, dev_code: FIXTURE_OTP } },
    async updateSite() { return {} },
    async getFacebookInterest() { return [] },
    async getChatConversations() { return [] },
    async getFacebookStatus() { return { ok: true, reconnect: false, checked_at: null } },
    async getWeeklyReport() {
      return { period_days: 7, numbers: { visitors: 0, listing_views: 0, new_enquiries: 0, qualified_enquiries: 0, site_visits: 0, facebook_interest: 0, chats: 0, chat_leads: 0, live_listings: 0 }, top_listing: null, todo: [], share_text: '' }
    },
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
      return [...items].sort((a, b) => b.updated_at.localeCompare(a.updated_at)).map(view)
    },
    async getListing(id) { return view(find(id)) },
    async createListing(input) {
      const now = new Date().toISOString()
      const l: Listing = {
        id: nextId('l'), agent_id: 'fixture-agent', status: 'draft', visibility: 'network', transaction: 'sale',
        property_type: 'apartment', title: '', description: { en: '' }, price_inr: 0, city: '', locality: '',
        amenities: [], media: [], created_at: now, updated_at: now, ...input,
      } as Listing
      load().listings.unshift(l)
      save()
      return view(l)
    },
    async updateListing(id, patch) {
      const l = find(id)
      // Computed fields are never stored (the real API ignores them too).
      const { freshness: _f, days_since_confirmed: _d, ...clean } = patch as ListingInput & { freshness?: unknown; days_since_confirmed?: unknown }
      Object.assign(l, clean)
      Object.assign(l, stamp(l))
      save()
      return view(l)
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
      return view(l)
    },
    async setListingStatus(id, status: ListingStatus) {
      const l = find(id)
      const reactivated = status === 'live' && (l.status === 'paused' || l.status === 'expired')
      l.status = status
      if (reactivated) l.freshness_confirmed_at = new Date().toISOString() // contract: reactivation re-stamps freshness
      Object.assign(l, stamp(l))
      save()
      return view(l)
    },
    async confirmAvailable(id) {
      const l = find(id)
      if (l.status !== 'live' && l.status !== 'under_offer') throw fixtureError(409, 'Only live listings can be confirmed')
      l.freshness_confirmed_at = new Date().toISOString()
      Object.assign(l, stamp(l))
      save()
      return view(l)
    },
    async aiDraft(req: AIDraftRequest) {
      await new Promise((r) => setTimeout(r, 600))
      if (!req.text?.trim() && !req.audio && req.image_count < 1) throw fixtureError(400, 'Send text, audio or photos')
      return fakeDraft(req.text ?? '', req.image_count, !!req.audio)
    },
    async suggestAbout(req: AboutSuggestRequest) {
      await new Promise((r) => setTimeout(r, 300))
      return fakeAboutSuggestion(req)
    },
    async uploadImages(files: File[]) {
      return Promise.all(files.map(async (f, i) => ({ id: `img${Date.now()}${i}`, url: await fileToDataUrl(f), original_name: f.name })))
    },

    async listLeads(stage?: Stage) {
      const st = load()
      const leads: Lead[] = st.leads
        .filter((l) => !stage || l.stage === stage)
        .map((l) => {
          const { notes, timeline, requirement, follow_up, ...lead } = l
          return { ...lead, requirement_line: requirementLine(requirement) }
        })
      return leads.sort((a, b) => b.score - a.score)
    },
    async getLead(id) {
      const l = load().leads.find((x) => x.id === id)
      if (!l) throw fixtureError(404, 'Lead not found')
      return enrich(l, load().listings)
    },
    async updateLead(id, stageOrPatch, note) {
      const l = load().leads.find((x) => x.id === id)
      if (!l) throw fixtureError(404, 'Lead not found')
      const patch: LeadPatch = typeof stageOrPatch === 'string' ? { stage: stageOrPatch, note } : stageOrPatch
      const bad = outcomePatchError(patch)
      if (bad) throw fixtureError(422, bad)
      const picked = patch.outcome?.listing_id
      if (picked && !load().listings.some((x) => x.id === picked)) throw fixtureError(422, 'That property is not one of your listings.')
      const now = new Date().toISOString()
      const outcome = nextOutcome(l, patch, load().listings, now)
      if (outcome !== undefined) l.outcome = outcome
      if (patch.stage && patch.stage !== l.stage) {
        l.stage = patch.stage
        // Contract: moving to contacted schedules a follow-up in 2 days unless one is supplied.
        if (patch.stage === 'contacted' && !patch.follow_up_at) l.follow_up = { due_at: ahead(48), overdue: false }
      }
      if (patch.follow_up_at) l.follow_up = { due_at: patch.follow_up_at, overdue: false }
      l.last_activity_at = now
      if (patch.note) l.notes = [...l.notes, { text: patch.note, ts: now, stage: l.stage }]
      save()
      const out = enrich(l, load().listings)
      // Contract: marking won with a listing suggests updating that listing (the app asks; nothing changes here).
      const deal = patch.stage === 'won' && l.outcome?.listing_id ? load().listings.find((x) => x.id === l.outcome!.listing_id) : undefined
      if (deal) out.suggest_listing_status = { listing_id: deal.id, status: deal.transaction === 'rent' ? 'rented' : 'sold' }
      return out
    },
    async getToday(): Promise<BusinessToday> {
      const st = load()
      const leads = st.leads.map((l) => enrich(l, st.listings))
      const open = leads.filter(isOpen)
      const dueBy = endOfToday()
      const due = open.filter((l) => l.follow_up?.due_at && new Date(l.follow_up.due_at).getTime() <= dueBy)
      const counts = {
        new_enquiries_24h: leads.filter((l) => Date.now() - new Date(l.created_at).getTime() < 86_400_000).length,
        hot: open.filter((l) => l.temperature === 'hot').length,
        site_visits: leads.filter((l) => l.stage === 'site_visit').length,
        follow_ups_due: due.length,
        uncontacted: leads.filter((l) => l.stage === 'new').length,
      }
      const headline = counts.uncontacted > 0
        ? `${counts.uncontacted} buyer${counts.uncontacted > 1 ? 's' : ''} ${counts.uncontacted > 1 ? "haven't" : "hasn't"} been contacted today.`
        : counts.follow_ups_due > 0
          ? `${counts.follow_ups_due} follow-up${counts.follow_ups_due > 1 ? 's are' : ' is'} due today.`
          : "You're all caught up."
      return {
        counts,
        headline,
        results: resultsFor(st.leads),
        actions: actionsFor(st.listings, leads, st.packs ?? {}, (l) => matchesFor(l).length),
        hot_buyers: open
          .filter((l) => l.temperature === 'hot')
          .sort((a, b) => b.score - a.score)
          .slice(0, 5)
          .map((l) => ({
            id: l.id, name: l.name, phone: l.phone, score: l.score, temperature: l.temperature,
            requirement_line: l.requirement_line ?? null,
            top_match: l.matches?.[0] ? { title: l.matches[0].title, match_pct: l.matches[0].match_pct } : null,
          })),
        follow_ups: due
          .sort((a, b) => a.follow_up!.due_at!.localeCompare(b.follow_up!.due_at!))
          .slice(0, 10)
          .map((l) => ({
            id: l.id, name: l.name, phone: l.phone, due_at: l.follow_up!.due_at!, overdue: l.follow_up!.overdue,
            reason: l.next_action?.reason ?? 'Follow up',
          })),
      }
    },
    async createFollowupDraft(id, language = 'en') {
      const st = load()
      const l = st.leads.find((x) => x.id === id)
      if (!l) throw fixtureError(404, 'Lead not found')
      const e = enrich(l, st.listings)
      const listingTitle = st.listings.find((x) => x.id === l.first_listing_id)?.title
      return draftFor(e, e.matches ?? [], language, listingTitle)
    },

    async createMarketingPack(listingId, language = 'en') {
      const st = load()
      const l = find(listingId)
      if (l.status !== 'live' && l.status !== 'under_offer') throw fixtureError(409, 'Only live listings can be marketed')
      st.packs = st.packs ?? {}
      const version = (st.packs[listingId]?.version ?? 0) + 1
      const pack = buildFixturePack(l, language, version, shareUrlFor(listingId), st.site?.name)
      st.packs[listingId] = pack
      save()
      return JSON.parse(JSON.stringify(pack)) as MarketingPack
    },
    async getMarketingPack(listingId) {
      find(listingId)
      const pack = load().packs?.[listingId]
      if (!pack) throw fixtureError(404, 'No marketing pack yet')
      return JSON.parse(JSON.stringify(pack)) as MarketingPack
    },
    async startMarketingRun(listingId) {
      const l = find(listingId)
      if (l.status !== 'live' && l.status !== 'under_offer') throw fixtureError(409, 'Only live listings can be marketed')
      const now = new Date().toISOString()
      return {
        id: 'run-' + listingId, listing_id: listingId, status: 'done', step: 'posts', page_url: shareUrlFor(listingId),
        facts: { usable: 0, held: 0, maharera: null, how: 'Demo mode: no live facts', nearby: 0, notes: [] },
        posts: [], dropped: {}, error: '', created_at: now, facts_done_at: now, finished_at: now,
      }
    },
    async editRunPost() {
      throw fixtureError(409, 'Demo mode: no campaign to edit')
    },
    async redoRunPost() {
      throw fixtureError(409, 'Demo mode: no campaign to improve')
    },
    async sendRunToCalendar() {
      throw fixtureError(409, 'Demo mode: nothing to send to the calendar')
    },
    async getMarketingRun(listingId) {
      find(listingId)
      return null
    },
    async getMatchingLeads(listingId): Promise<MatchingLeads> {
      const l = find(listingId)
      return {
        listing: { id: l.id, title: l.title, price_inr: l.price_inr, locality: l.locality, share_url: shareUrlFor(l.id) },
        buyers: matchesFor(l),
      }
    },
    async getPerformance() {
      const st = load()
      return performanceFor(st.listings, st.leads)
    },
    async getListingActivity(id, limit = 50): Promise<ListingActivity> {
      const st = load()
      const l = find(id)
      const perf = performanceFor(st.listings, st.leads).find((p) => p.listing_id === id)
      return activityFor(l, st.leads, perf, new Date(), limit)
    },

    async getSocialStatus() {
      return JSON.parse(JSON.stringify(FIXTURE_SOCIAL_STATUS))
    },
    async publishToSocial(listingId, req) {
      const st = load()
      const l = find(listingId)
      if (!req.approve || !req.consent) throw fixtureError(422, 'Approval and consent are required')
      if (l.status !== 'live' && l.status !== 'under_offer') throw fixtureError(409, 'Only live listings can be posted')
      const pack = st.packs?.[listingId]
      if (!pack) throw fixtureError(409, 'Create the marketing pack first')
      st.publications = st.publications ?? []
      const done = st.publications.filter(
        (p) => p.listing_id === listingId && p.pack_version === pack.version && (p.status === 'published' || p.status === 'dry_run'),
      )
      if (!req.force && req.channels.some((c) => done.some((p) => p.channel === c))) {
        throw fixtureError(409, 'Already posted for this version. Send force to post again')
      }
      const created = buildPublications(pack, 'fixture-agent', req, () => nextId('pub'), new Date().toISOString())
      st.publications = [...[...created].reverse(), ...st.publications] // newest first
      save()
      return JSON.parse(JSON.stringify(created))
    },
    async listPublications(listingId) {
      find(listingId)
      const items = (load().publications ?? []).filter((p) => p.listing_id === listingId)
      return JSON.parse(JSON.stringify(items))
    },
    async retryPublication(id) {
      const st = load()
      const p = (st.publications ?? []).find((x) => x.id === id)
      if (!p) throw fixtureError(404, 'Publication not found')
      if (p.status !== 'failed') throw fixtureError(409, 'Only failed posts can be retried')
      p.status = 'dry_run'
      p.error = null
      p.attempts += 1
      p.updated_at = new Date().toISOString()
      save()
      return JSON.parse(JSON.stringify(p))
    },
  }
}

function safeLocal(): FixtureStorage | null {
  try { return window.localStorage } catch { return null }
}
