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
