import type { PhotoQuality } from './quality'
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
  /** Photo quality (lib/app/quality.ts): the analysis, the enhanced copy beside the original, and which one to show. */
  quality?: PhotoQuality | null
  enhanced_url?: string | null
  use_enhanced?: boolean | null
}

export interface Description {
  en: string
  hi?: string
  mr?: string
}

/** Project and area knowledge the assistant answers from (docs/contracts/engagement.md). Every field optional. */
export type NearbyType = 'school' | 'hospital' | 'transit' | 'office' | 'market' | 'park' | 'other'
export interface AboutNearby { type: NearbyType; name: string; minutes?: number | null }
export interface AboutFaq { q: string; a: string }
export interface About {
  project_name?: string | null
  builder_known_as?: string | null
  highlights?: string[]
  amenities?: string[]
  nearby?: AboutNearby[]
  connectivity?: string[]
  water?: string | null
  power_backup?: string | null
  maintenance?: string | null
  society?: string | null
  parking?: string | null
  possession_note?: string | null
  rera_note?: string | null
  faq?: AboutFaq[]
}

export type AboutSource = 'agent' | 'area_guide'
export interface AboutSuggestRequest { locality?: string; project_name?: string; bhk?: number; description: string }
/** DRAFT from POST /listings/ai/about-suggest: nothing is saved until the agent keeps items. */
export interface AboutSuggestion {
  highlights: Array<{ text: string; source: AboutSource }>
  amenities: Array<{ text: string; source: AboutSource }>
  nearby: Array<AboutNearby & { source: AboutSource }>
  connectivity: Array<{ text: string; source: AboutSource }>
  fields: Partial<Record<'water' | 'power_backup' | 'maintenance' | 'parking' | 'society', { text: string; source: AboutSource }>>
  project_name?: string | null
  area_known: boolean
  area_name?: string | null
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
  about?: About | null
  created_at: string
  updated_at: string
  published_at?: string | null
  freshness_confirmed_at?: string | null
  /** docs/contracts/activity.md section 2. Absent on older backends (treated as fresh). */
  freshness?: Freshness
  days_since_confirmed?: number | null
}

/** fresh: nothing to do. confirm: the app asks "Is this still available?". hidden: buyers cannot see it until confirmed. */
export type Freshness = 'fresh' | 'confirm' | 'hidden'

/** Body of POST /listings and PATCH /listings/{id}. */
export type ListingInput = Partial<
  Omit<
    Listing,
    'id' | 'agent_id' | 'status' | 'created_at' | 'updated_at' | 'published_at' | 'freshness' | 'days_since_confirmed'
  >
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
  instagram?: string
  facebook_url?: string
  logo?: string
  /** Optional brand fields (A1): business name and preset can be set when the site is created. */
  business_name?: string
  preset?: string
}

export interface FacebookInterest {
  id: string
  /** Where the comment was made. Older rows have no channel and mean Facebook. */
  channel?: 'facebook' | 'instagram' | null
  post_id: string
  listing_id: string | null
  from_name: string | null
  text: string
  intent: 'interested' | 'question' | 'praise' | 'complaint' | 'spam' | 'other'
  language: string
  status: 'replied' | 'dry_run' | 'needs_human' | 'ignored' | 'capped' | 'failed'
  reply: string | null
  needs_human: boolean
  reason: string
  created_time: string | null
  permalink: string | null
}

export interface ChatConversation {
  id: string
  updated_at: string | null
  needs_human: boolean
  lead_created: boolean
  summary: string
  questions: string[]
  name: string | null
  messages: number
}

export interface WeeklyReport {
  period_days: number
  numbers: {
    visitors: number; listing_views: number; new_enquiries: number; qualified_enquiries: number; site_visits: number
    facebook_interest: number; chats: number; chat_leads: number; live_listings: number
  }
  top_listing: { listing_id: string; title: string | null; views: number; enquiries: number } | null
  todo: Array<{ kind: string; text: string; count: number }>
  share_text: string
}

export interface FacebookStatus {
  ok: boolean
  reconnect: boolean
  checked_at: string | null
  /** Present once Instagram comments have been checked. */
  instagram?: { ok: boolean; reconnect: boolean; checked_at: string | null }
}

export interface SiteUpdateInput {
  photo?: string
  logo?: string
  instagram?: string
  facebook_url?: string
  // brand profile (empty string / null / [] clears a value; omitted fields stay)
  business_name?: string
  tagline?: string
  about?: string
  banner?: string
  preset?: string
  custom_primary?: string
  rera_agent_no?: string
  areas?: string[]
  languages?: string[]
  years_experience?: number | null
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

export type LostReason = 'price' | 'bought_elsewhere' | 'not_responding' | 'changed_mind' | 'other'

/** Stored result of a won/lost lead (docs/contracts/outcomes.md). */
export interface LeadOutcome {
  result: 'won' | 'lost'
  deal_price_inr: number | null
  listing_id: string | null
  lost_reason: LostReason | null
  closed_at: string
}

/** Body `outcome` of PATCH /inbox/leads/{id}: won fields only with stage won, lost_reason only with stage lost. */
export interface OutcomeInput {
  deal_price_inr?: number
  listing_id?: string
  lost_reason?: LostReason
}

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
  /** Set when the lead is won or lost; null otherwise. Absent on older backends. */
  outcome?: LeadOutcome | null
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
  /** Only together with stage won or lost. */
  outcome?: OutcomeInput
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
  /** Deals closed in the last 30 days (docs/contracts/outcomes.md). Absent on older backends. */
  results?: TodayResults
}

export interface TodayResults {
  period_days: number
  deals_won: number
  deal_value_inr: number
  deals_lost: number
  top_source: string | null
  lost_reasons: Partial<Record<LostReason, number>>
}

export type RecommendedActionType = 'call' | 'follow_up' | 'send_property' | 'create_marketing' | 'confirm_listing'

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
  /** Only in the PATCH response, when the lead was marked won with a listing. The app offers to call setListingStatus. */
  suggest_listing_status?: { listing_id: string; status: 'sold' | 'rented' } | null
}

/** One entry of the legacy POST /api/v1/uploads/images response `files[]`. */
export interface UploadedFile {
  id: string
  url: string
  thumbnail_url?: string | null
  original_name?: string
  quality?: PhotoQuality | null
  enhanced_url?: string | null
  use_enhanced?: boolean | null
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
  group?: { post: string } | null
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
  /** Won leads attributed to this listing. Absent on older backends. */
  deals?: number
  deal_value_inr?: number
  deals_by_source?: Record<string, number>
}

export type SocialChannel = 'facebook_page' | 'instagram'
export type PublicationStatus = 'queued' | 'published' | 'failed' | 'dry_run'

/** docs/contracts/social.md: one attempt to post a listing's marketing pack to one brand channel. */
export interface Publication {
  id: string
  listing_id: string
  agent_id: string
  channel: SocialChannel
  pack_version: number
  status: PublicationStatus
  external_id: string | null
  permalink: string | null
  error: string | null
  consent: { given_at: string; text: string }
  approved_at: string
  created_at: string
  updated_at: string
  attempts: number
  payload: { text: string; image_urls: string[] }
}

/** GET /social/status (no secrets). */
export interface SocialStatus {
  dry_run: boolean
  channels: Record<SocialChannel, boolean>
  brand: string
  media_url_ok: boolean
}

export interface SocialPublishRequest {
  channels: SocialChannel[]
  approve: boolean
  consent: boolean
  force?: boolean
}

export type ActivityEventType = 'view' | 'whatsapp_click' | 'call_click' | 'share' | 'enquiry'

/** GET /inbox/listings/{id}/activity (docs/contracts/activity.md section 1). */
export interface ListingActivity {
  listing: { id: string; title: string; status: ListingStatus; price_inr: number }
  totals: {
    views: number
    unique_visitors: number
    enquiries: number
    qualified: number
    site_visits: number
    deals: number
    whatsapp_clicks: number
    call_clicks: number
    shares: number
  }
  by_source: Record<string, { views: number; enquiries: number }>
  /** Last 14 India (IST) days, oldest first, zero-filled. */
  daily: Array<{ date: string; views: number; enquiries: number }>
  /** Newest first. */
  feed: ActivityFeedItem[]
  /** Hottest first, max 10. */
  people: ActivityPerson[]
}

export interface ActivityFeedItem {
  ts: string
  type: ActivityEventType
  /** Visitors are anonymous ("Visitor 2"); a visitor who became a lead shows the lead's name. */
  who: { kind: 'visitor' | 'lead'; label: string; lead_id?: string }
  source: string | null
  text: string
}

export interface ActivityPerson {
  lead_id: string
  name: string
  temperature: Temperature
  score: number
  requirement_line: string | null
  last_activity_at: string
}

/** The client interface implemented by both the real API and the fixture API. */
export interface AppApi {
  requestOtp(phone: string): Promise<OtpRequested>
  verifyOtp(phone: string, code: string): Promise<LoginResult>
  createSite(input: SiteCreateInput): Promise<SiteResult>
  updateSite(input: SiteUpdateInput): Promise<unknown>
  getFacebookInterest(): Promise<FacebookInterest[]>
  getChatConversations(): Promise<ChatConversation[]>
  getFacebookStatus(): Promise<FacebookStatus>
  getWeeklyReport(): Promise<WeeklyReport>
  listListings(status?: ListingStatus): Promise<Listing[]>
  getListing(id: string): Promise<Listing>
  createListing(input: ListingInput): Promise<Listing>
  updateListing(id: string, patch: ListingInput): Promise<Listing>
  publishListing(id: string): Promise<Listing>
  setListingStatus(id: string, status: ListingStatus): Promise<Listing>
  aiDraft(req: AIDraftRequest): Promise<AIDraft>
  suggestAbout(req: AboutSuggestRequest): Promise<AboutSuggestion>
  uploadImages(files: File[]): Promise<UploadedFile[]>
  listLeads(stage?: Stage): Promise<Lead[]>
  getLead(id: string): Promise<LeadDetail>
  /** Legacy form `updateLead(id, stage, note?)` still works; the patch form also carries follow_up_at and, with won/lost, `outcome`. */
  updateLead(id: string, stageOrPatch: Stage | LeadPatch, note?: string): Promise<LeadDetail>
  getToday(): Promise<BusinessToday>
  createFollowupDraft(id: string, language?: DraftLanguage): Promise<FollowupDraft>
  /** Generate or regenerate the marketing pack (version += 1). 409 when the listing is not live. */
  createMarketingPack(listingId: string, language?: DraftLanguage): Promise<MarketingPack>
  /** The existing pack, or a 404 ApiError when none was generated yet. */
  getMarketingPack(listingId: string): Promise<MarketingPack>
  getMatchingLeads(listingId: string): Promise<MatchingLeads>
  getPerformance(): Promise<PerformanceItem[]>
  /** Per-listing activity (views, sources, people, feed). 404 for a listing that is not yours. */
  getListingActivity(id: string, limit?: number): Promise<ListingActivity>
  /** "Yes, still available": stamps the listing as confirmed. 409 unless it is live or under offer. */
  confirmAvailable(id: string): Promise<Listing>
  /** Social publishing to the Avasetu brand accounts (docs/contracts/social.md). */
  getSocialStatus(): Promise<SocialStatus>
  /** Posts only on this call; needs approve and consent both true. 409: no pack yet, listing not live, or already posted (without force). */
  publishToSocial(listingId: string, req: SocialPublishRequest): Promise<Publication[]>
  /** Newest first. */
  listPublications(listingId: string): Promise<Publication[]>
  /** Only for a failed publication. */
  retryPublication(id: string): Promise<Publication>
}
