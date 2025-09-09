export interface PropertyType {
  id: string
  title: string
  description: string
  price: number
  location: string
  bedrooms: number
  bathrooms: number
  area_sqft: number
  property_type: string
  features: string[]
  amenities: string
  publishing_status: 'draft' | 'published' | 'archived'
  published_at?: string
  target_languages: string[]
  publishing_channels: string[]
  facebook_page_mappings: Record<string, string>
  created_at: string
  updated_at: string
}

export interface PropertyFormData {
  title: string
  description: string
  price: number
  location: string
  bedrooms: number
  bathrooms: number
  area_sqft: number
  property_type: string
  features: string[]
  amenities: string
}

export interface PublishingRequest {
  property_id: string
  target_languages: string[]
  publishing_channels: string[]
  facebook_page_mappings: Record<string, string>
  auto_translate: boolean
}

export interface PublishingStatus {
  property_id: string
  publishing_status: string
  published_at?: string
  published_channels: string[]
  language_status: Record<string, string>
  facebook_posts: Record<string, string>
  analytics_data: Record<string, any>
}