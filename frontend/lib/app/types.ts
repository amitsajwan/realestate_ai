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
  created_at: string
  last_activity_at: string
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
  updateLead(id: string, stage: Stage, note?: string): Promise<LeadDetail>
}
