// Types mirror docs/contracts/listing.md (public shapes) and agent_public_service.

export type Transaction = 'sale' | 'rent'
export type Lang = 'en' | 'hi' | 'mr'

export interface ListingMedia {
  url: string
  kind: 'image' | 'video'
  order: number
}

/** `about` as the public listing endpoint returns it (the agent-side faq is never included). */
export interface PublicAbout {
  project_name?: string | null
  builder_known_as?: string | null
  highlights?: string[]
  amenities?: string[]
  nearby?: Array<{ type: string; name: string; minutes?: number | null }>
  connectivity?: string[]
  water?: string | null
  power_backup?: string | null
  maintenance?: string | null
  society?: string | null
  parking?: string | null
  possession_note?: string | null
  rera_note?: string | null
}

export interface PublicListing {
  id: string
  agent_id?: string
  status: string
  transaction: Transaction
  property_type: string
  title: string
  description: { en?: string; hi?: string; mr?: string }
  price_inr: number
  city: string
  locality: string
  project_name?: string | null
  bhk?: number | null
  carpet_sqft?: number | null
  super_built_up_sqft?: number | null
  floor?: number | null
  total_floors?: number | null
  furnishing?: 'unfurnished' | 'semi' | 'furnished' | null
  possession?: string | null
  rera_no?: string | null
  amenities: string[]
  media: ListingMedia[]
  about?: PublicAbout | null
  created_at?: string
  updated_at?: string
  published_at?: string | null
  agent?: { slug: string; agent_name: string; phone?: string | null; photo?: string | null }
}

export interface AgentBranding {
  tagline?: string
  /** Legacy stored colours: not used for rendering (the preset / custom_primary decide). */
  colors?: { primary?: string; secondary?: string; accent?: string }
  logo?: string | null
  social?: { instagram?: string; facebook?: string }
  // A1 brand profile (all optional; see docs/handoff/A1-brand.md)
  business_name?: string
  about?: string
  banner?: string | null
  preset?: 'navy-gold' | 'emerald' | 'terracotta' | 'royal-purple' | 'slate-teal' | 'cream-ink'
  custom_primary?: string | null
  rera_agent_no?: string | null
  areas?: string[]
  languages?: string[]
  years_experience?: number | null
  /** Owner-only: the fictional demo agent page (shows a DEMO ribbon). Agents cannot set it. */
  demo?: boolean
  /** Owner-only: a site prepared for an agent who has not agreed to publish yet (unlisted, shows a PREVIEW note). */
  preview?: boolean
}

export interface AgentProfile {
  agent_name: string
  slug: string
  bio?: string | null
  photo?: string | null
  phone?: string | null
  email?: string | null
  languages?: string[]
  specialties?: string[]
  office_address?: string | null
  city?: string | null
  experience?: string | null
  branding_data?: AgentBranding | null
  view_count?: number
}

export interface ListingsPage {
  items: PublicListing[]
  total: number
}

export interface Attribution {
  source?: string
  utm: Record<string, string>
}

/** Where a project fact comes from (backend agentprojects Source). */
export type FactSource = 'maharera' | 'builder' | 'agent' | 'avasetu' | 'osm'

export interface ProjectConfiguration {
  label: string
  bhk: number
  carpet_sqft: number
  price_inr: number
  price_per_sqft: number
  source: FactSource
}

export interface ProjectRera {
  regno: string
  name: string
  promoter: string
  project_type: string
  registered_on?: string | null
  completion_at_registration?: string | null
  completion_now?: string | null
  units_total?: number | null
  units_booked?: number | null
  url: string
  checked_at?: string | null
}

export interface PublicProject {
  id: string
  slug: string
  name: string
  builder: string
  locality: string
  address: string
  pincode: string
  rera_no: string
  scope_note: string
  configurations: ProjectConfiguration[]
  price_min?: number | null
  price_max?: number | null
  bhk_options: number[]
  possession_target?: string | null
  positioning: string
  who_it_suits: string[]
  highlights: string[]
  amenities: string[]
  specs: Record<string, string>
  provenance: Record<string, FactSource>
  nearby: { name: string; km?: number | null; source: FactSource }[]
  place?: { lat: number; lon: number; source: FactSource; note: string } | null
  maps_query: string
  media: { url: string; caption: string; credit: string; artist_impression: boolean; kind: 'image' | 'video' }[]
  rera?: ProjectRera | null
  booked_pct?: number | null
  completion_moved_months?: number | null
  updated_at?: string | null
}
