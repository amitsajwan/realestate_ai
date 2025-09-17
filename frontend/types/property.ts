/**
 * Property Types
 * ==============
 * TypeScript interfaces that match the backend unified property schemas
 */

export interface PropertyCreate {
  title: string;
  type: string;
  bedrooms: number;
  bathrooms: number;
  price: number;
  price_unit: string;
  city: string;
  area: number;
  address: string;
  description: string;
  amenities: string[];
  // Additional fields for unified properties
  property_type?: string;
  location?: {
    latitude?: number;
    longitude?: number;
    address: string;
    city: string;
    state?: string;
    country?: string;
    zip_code?: string;
  };
  features?: string[];
  images?: string[];
  virtual_tour_url?: string;
  floor_plan_url?: string;
  year_built?: number;
  parking_spaces?: number;
  garden_area?: number;
  balcony_area?: number;
  furnished?: boolean;
  pet_friendly?: boolean;
  security_features?: string[];
  nearby_amenities?: string[];
  property_tax?: number;
  maintenance_fee?: number;
  hoa_fee?: number;
  utilities_included?: string[];
  availability_date?: string;
  listing_type?: 'sale' | 'rent' | 'lease';
  status?: 'active' | 'inactive' | 'sold' | 'rented' | 'pending';
}

export interface PropertyUpdate {
  title?: string;
  type?: string;
  bedrooms?: number;
  bathrooms?: number;
  price?: number;
  price_unit?: string;
  city?: string;
  area?: number;
  address?: string;
  description?: string;
  amenities?: string[];
  property_type?: string;
  location?: {
    latitude?: number;
    longitude?: number;
    address?: string;
    city?: string;
    state?: string;
    country?: string;
    zip_code?: string;
  };
  features?: string[];
  images?: string[];
  virtual_tour_url?: string;
  floor_plan_url?: string;
  year_built?: number;
  parking_spaces?: number;
  garden_area?: number;
  balcony_area?: number;
  furnished?: boolean;
  pet_friendly?: boolean;
  security_features?: string[];
  nearby_amenities?: string[];
  property_tax?: number;
  maintenance_fee?: number;
  hoa_fee?: number;
  utilities_included?: string[];
  availability_date?: string;
  listing_type?: 'sale' | 'rent' | 'lease';
  status?: 'active' | 'inactive' | 'sold' | 'rented' | 'pending';
}

export interface PropertyResponse {
  id: string;
  user_id: string;
  title: string;
  type: string;
  bedrooms: number;
  bathrooms: number;
  price: number;
  price_unit: string;
  city: string;
  area: number;
  address: string;
  description: string;
  amenities: string[];
  property_type: string;
  location: {
    latitude?: number;
    longitude?: number;
    address: string;
    city: string;
    state?: string;
    country?: string;
    zip_code?: string;
  };
  features: string[];
  images: string[];
  virtual_tour_url?: string;
  floor_plan_url?: string;
  year_built?: number;
  parking_spaces?: number;
  garden_area?: number;
  balcony_area?: number;
  furnished: boolean;
  pet_friendly: boolean;
  security_features: string[];
  nearby_amenities: string[];
  property_tax?: number;
  maintenance_fee?: number;
  hoa_fee?: number;
  utilities_included: string[];
  availability_date?: string;
  listing_type: 'sale' | 'rent' | 'lease';
  status: 'active' | 'inactive' | 'sold' | 'rented' | 'pending';
  created_at: string;
  updated_at: string;
  // Analytics fields
  views?: number;
  likes?: number;
  shares?: number;
  inquiries?: number;
  // AI suggestions
  ai_suggestions?: {
    title_suggestions?: string[];
    description_suggestions?: string[];
    marketing_angles?: string[];
    target_audience?: string[];
    pricing_suggestions?: {
      min_price?: number;
      max_price?: number;
      recommended_price?: number;
      reasoning?: string;
    };
  };
  // Market insights
  market_insights?: {
    average_price_per_sqft?: number;
    market_trend?: 'rising' | 'stable' | 'declining';
    days_on_market?: number;
    comparable_properties?: any[];
    neighborhood_analysis?: any;
  };
}

export interface PropertiesResponse {
  properties: PropertyResponse[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface AIPropertySuggestion {
  title_suggestions: string[];
  description_suggestions: string[];
  marketing_angles: string[];
  target_audience: string[];
  pricing_suggestions: {
    min_price: number;
    max_price: number;
    recommended_price: number;
    reasoning: string;
  };
  market_insights: {
    average_price_per_sqft: number;
    market_trend: 'rising' | 'stable' | 'declining';
    days_on_market: number;
    comparable_properties: any[];
    neighborhood_analysis: any;
  };
}

export interface PublishingRequest {
  propertyId: string;
  channels: string[];
  scheduled_at?: string;
  custom_message?: string;
  hashtags?: string[];
  target_audience?: string[];
}

export interface PublishingStatusResponse {
  property_id: string;
  status: 'published' | 'pending' | 'failed' | 'scheduled';
  channels: {
    [channel: string]: {
      status: 'published' | 'pending' | 'failed' | 'scheduled';
      external_id?: string;
      url?: string;
      error?: string;
      published_at?: string;
    };
  };
  published_at?: string;
  scheduled_at?: string;
  error?: string;
}