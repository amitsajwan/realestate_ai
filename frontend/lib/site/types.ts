// Types mirror docs/contracts/listing.md (public shapes) and agent_public_service.

export type Transaction = 'sale' | 'rent'
export type Lang = 'en' | 'hi' | 'mr'

export interface ListingMedia {
  url: string
  kind: 'image' | 'video'
  order: number
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
  created_at?: string
  updated_at?: string
  published_at?: string | null
  agent?: { slug: string; agent_name: string; phone?: string | null; photo?: string | null }
}

export interface AgentBranding {
  tagline?: string
  colors?: { primary?: string; secondary?: string; accent?: string }
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
