/** Types mirroring docs/contracts/listing.md (frozen for Sprint 1) and the built onboarding/tracking modules. */

export type ListingStatus = 'draft' | 'live' | 'under_offer' | 'sold' | 'rented' | 'paused' | 'expired'
export type Visibility = 'private' | 'network' | 'public'
export type Transaction = 'sale' | 'rent'
export type PropertyType = 'apartment' | 'villa' | 'house' | 'plot' | 'commercial' | 'office' | 'shop'
export type Furnishing = 'unfurnished' | 'semi' | 'furnished'

export interface Media {
  url: string
  kind: 'image' | 'video'
  order: number
}

export interface Description {
  en: string
  hi?: string
  mr?: string
}

export interface Listing {
  id: string
  agent_id: string
  status: ListingStatus
  visibility: Visibility
  transaction: Transaction
  property_type: PropertyType
  title: string
  description: Description
  price_inr: number
  city: string
  locality: string
  project_name?: string | null
  bhk?: number | null
  carpet_sqft?: number | null
  super_built_up_sqft?: number | null
  floor?: number | null
  total_floors?: number | null
  furnishing?: Furnishing | null
  possession?: string | null // 'ready' | 'under_construction' | date string
  rera_no?: string | null
  amenities: string[]
  media: Media[]
  created_at: string
  updated_at: string
  published_at?: string | null
  freshness_confirmed_at?: string | null
}

/** Body of POST /listings and PATCH /listings/{id}. */
export type ListingInput = Partial<
  Omit<Listing, 'id' | 'agent_id' | 'status' | 'created_at' | 'updated_at' | 'published_at'>
>

export interface AIDraft {
  draft: ListingInput
  confidence: Record<string, number>
  missing: string[]
  transcript?: string | null
  warnings: string[]
}

export interface AIDraftRequest {
  text?: string
  audio?: Blob
  images?: File[]
  image_count: number
}

export interface OtpRequested {
  sent: boolean
  dev_code?: string | null
  mode?: 'otp' | 'invite' // invite: the agent already has a personal code (pilot)
}

export interface LoginResult {
  access_token: string
  token_type: string
  is_new_user: boolean
  has_site: boolean
  site_url?: string | null
}

export interface SiteCreateInput {
  name: string
  city: string
  languages?: string[]
  specialties?: string[]
  photo?: string
  whatsapp?: string
  preferred_slug?: string
}

export interface SiteResult {
  slug: string
  site_url: string
  agent_name: string
  tagline: string
  created: boolean
}

export type Stage = 'new' | 'contacted' | 'site_visit' | 'negotiating' | 'won' | 'lost'
export type Temperature = 'hot' | 'warm' | 'cold'

export interface Lead {
  id: string
  name: string
  phone: string
  stage: Stage
  source?: string | null
  message?: string | null
  score: number
  temperature: Temperature
  first_listing_id?: string | null
  /** e.g. "2 BHK · 80L-90L · Baner · 1-3 months" (docs/contracts/qualification.md section 3). */
  requirement_line?: string | null
  created_at: string
  last_activity_at: string
}

export type Timeline = 'now' | '1_3_months' | '3_6_months' | 'exploring'
export type Financing = 'home_loan' | 'own_funds' | 'undecided'

export interface Requirement {
  bhk: number | null
  budget_min_inr: number | null
  budget_max_inr: number | null
  timeline: Timeline | null
  financing: Financing | null
  localities: string[]
  /** stated = buyer filled the fields; inferred = parsed from the message; mixed = both */
  source: 'stated' | 'inferred' | 'mixed'
}

export type NextActionType = 'call' | 'whatsapp' | 'schedule_visit' | 'follow_up'
export interface NextAction {
  type: NextActionType
  reason: string
}

export interface LeadMatch {
  listing_id: string
  title: string
  price_inr: number
  locality: string
  match_pct: number
  reasons: string[]
}

export interface FollowUpState {
  due_at: string | null
  overdue: boolean
}

/** Body of PATCH /inbox/leads/{id}. */
export interface LeadPatch {
  stage?: Stage
  note?: string
  follow_up_at?: string
}

export interface FollowupDraft {
  message: string
  whatsapp_url: string
  language: string
  based_on: string[]
}

export type DraftLanguage = 'en' | 'hi' | 'mr'

export interface TodayHotBuyer {
  id: string
  name: string
  phone: string
  score: number
  temperature: Temperature
  requirement_line: string | null
  top_match: { title: string; match_pct: number } | null
}

export interface TodayFollowUp {
  id: string
  name: string
  phone: string
  due_at: string
  overdue: boolean
  reason: string
}

/** GET /inbox/today ("Your business today"). */
export interface BusinessToday {
  counts: {
    new_enquiries_24h: number
    hot: number
    site_visits: number
    follow_ups_due: number
    uncontacted: number
  }
  hot_buyers: TodayHotBuyer[]
  follow_ups: TodayFollowUp[]
  headline: string
  /** "AI recommends" list (docs/contracts/marketing.md section 4). Absent on older backends. */
  actions?: RecommendedAction[]
}

export type RecommendedActionType = 'call' | 'follow_up' | 'send_property' | 'create_marketing'

export interface RecommendedAction {
  type: RecommendedActionType
  title: string
  detail: string
  priority: 1 | 2 | 3
  lead_id?: string
  listing_id?: string
  buyer_count?: number
}

export interface LeadEvent {
  type: string // page_view | listing_view | share | call_click | whatsapp_click | inquiry
  listing_id?: string | null
  source?: string | null
  ts: string
}

export interface LeadNote {
  text: string
  ts: string
  stage?: Stage
}

export interface LeadDetail extends Lead {
  requirement?: Requirement | null
  ai_summary?: string
  next_action?: NextAction
  matches?: LeadMatch[]
  follow_up?: FollowUpState
  notes: LeadNote[]
  consent?: unknown
  timeline: LeadEvent[]
}

/** One entry of the legacy POST /api/v1/uploads/images response `files[]`. */
export interface UploadedFile {
  id: string
  url: string
  thumbnail_url?: string | null
  original_name?: string
}

export type ImageKind = 'cover' | 'facts' | 'amenities' | 'cta' | 'status'

export interface ImageAsset {
  kind: ImageKind
  url: string
  width: number
  height: number
}

export interface ReelBeat {
  seconds: string
  text: string
  visual: string
}

/** docs/contracts/marketing.md section 1. */
export interface MarketingPack {
  listing_id: string
  language: DraftLanguage
  version: number
  generated_at: string
  angle: string
  headline: string
  instagram: { caption: string; hashtags: string[]; images: ImageAsset[] }
  facebook: { post: string }
  whatsapp: { message: string; status_text: string; status_image: ImageAsset | null }
  reel: { hook: string; beats: ReelBeat[]; cta: string; duration_s: number }
  share_url: string
}

export interface MatchingBuyer {
  lead_id: string
  name: string
  phone: string
  temperature: Temperature
  score: number
  requirement_line: string | null
  match_pct: number
  reasons: string[]
  draft: { message: string; whatsapp_url: string }
}

/** GET /inbox/matching-leads?listing_id= (contract section 2). */
export interface MatchingLeads {
  listing: { id: string; title: string; price_inr: number; locality: string; share_url: string }
  buyers: MatchingBuyer[]
}

export interface PerformanceItem {
  listing_id: string
  title: string
  price_inr: number
  status: ListingStatus
  views: number
  unique_visitors: number
  enquiries: number
  qualified: number
  site_visits: number
  by_source: Record<string, number>
}

/** The client interface implemented by both the real API and the fixture API. */
export interface AppApi {
  requestOtp(phone: string): Promise<OtpRequested>
  verifyOtp(phone: string, code: string): Promise<LoginResult>
  createSite(input: SiteCreateInput): Promise<SiteResult>
  listListings(status?: ListingStatus): Promise<Listing[]>
  getListing(id: string): Promise<Listing>
  createListing(input: ListingInput): Promise<Listing>
  updateListing(id: string, patch: ListingInput): Promise<Listing>
  publishListing(id: string): Promise<Listing>
  setListingStatus(id: string, status: ListingStatus): Promise<Listing>
  aiDraft(req: AIDraftRequest): Promise<AIDraft>
  uploadImages(files: File[]): Promise<UploadedFile[]>
  listLeads(stage?: Stage): Promise<Lead[]>
  getLead(id: string): Promise<LeadDetail>
  /** Legacy form `updateLead(id, stage, note?)` still works; the patch form also carries follow_up_at. */
  updateLead(id: string, stageOrPatch: Stage | LeadPatch, note?: string): Promise<LeadDetail>
  getToday(): Promise<BusinessToday>
  createFollowupDraft(id: string, language?: DraftLanguage): Promise<FollowupDraft>
  /** Generate or regenerate the marketing pack (version += 1). 409 when the listing is not live. */
  createMarketingPack(listingId: string, language?: DraftLanguage): Promise<MarketingPack>
  /** The existing pack, or a 404 ApiError when none was generated yet. */
  getMarketingPack(listingId: string): Promise<MarketingPack>
  getMatchingLeads(listingId: string): Promise<MatchingLeads>
  getPerformance(): Promise<PerformanceItem[]>
}
