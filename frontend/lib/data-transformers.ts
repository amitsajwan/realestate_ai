/**
 * Data Transformation Utilities
 * =============================
 * Centralized data transformation logic to ensure consistent data flow
 * between API responses and UI components.
 */

export interface Property {
  id: string
  title: string
  description?: string
  price: number
  address: string
  location: string
  bedrooms: number
  bathrooms: number
  area: number
  area_sqft: number
  type: string
  property_type: string
  status: 'for-sale' | 'for-rent' | 'sold' | 'draft' | 'archived' | 'active'
  dateAdded: string
  created_at: string
  image?: string
  images?: string[]
  features?: string[]
  amenities?: string
}

export interface PropertyAnalytics {
  total_properties: number
  published_properties: number
  draft_properties: number
  archived_properties: number
  average_price: number
  total_value: number
  price_range_distribution: Record<string, number>
  property_type_distribution: Record<string, number>
  location_distribution: Record<string, number>
  status_distribution: Record<string, number>
  average_days_on_market: number
  conversion_rate: number
  top_performing_properties: Property[]
  recent_activity: any[]
}

export interface Lead {
  id: string
  name: string
  email: string
  phone: string
  location?: string
  address?: string
  property_type?: string
  budget_min?: number
  budget_max?: number
  status: 'new' | 'contacted' | 'qualified' | 'converted' | 'lost'
  source: string
  score: number
  notes?: string
  created_at: string
  updated_at: string
}

/**
 * Transform properties array into analytics data
 */
export function transformPropertiesToAnalytics(properties: Property[]): PropertyAnalytics {
  if (!properties || properties.length === 0) {
    return {
      total_properties: 0,
      published_properties: 0,
      draft_properties: 0,
      archived_properties: 0,
      average_price: 0,
      total_value: 0,
      price_range_distribution: {},
      property_type_distribution: {},
      location_distribution: {},
      status_distribution: {},
      average_days_on_market: 0,
      conversion_rate: 0,
      top_performing_properties: [],
      recent_activity: []
    }
  }

  // Calculate basic metrics
  const totalProperties = properties.length
  const publishedProperties = properties.filter(p => p.status === 'for-sale' || p.status === 'for-rent' || p.status === 'active').length
  const draftProperties = properties.filter(p => p.status === 'draft').length
  const archivedProperties = properties.filter(p => p.status === 'archived').length
  
  const totalValue = properties.reduce((sum, p) => sum + (p.price || 0), 0)
  const averagePrice = totalProperties > 0 ? Math.round(totalValue / totalProperties) : 0

  // Calculate distributions
  const propertyTypeDistribution = properties.reduce((acc, prop) => {
    const type = prop.property_type || prop.type || 'unknown'
    acc[type] = (acc[type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const locationDistribution = properties.reduce((acc, prop) => {
    const location = prop.location || prop.address || 'unknown'
    acc[location] = (acc[location] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const statusDistribution = properties.reduce((acc, prop) => {
    const status = prop.status || 'unknown'
    acc[status] = (acc[status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // Calculate price range distribution
  const priceRangeDistribution = properties.reduce((acc, prop) => {
    const price = prop.price || 0
    let range = 'unknown'
    
    if (price < 1000000) range = 'Under 10L'
    else if (price < 2000000) range = '10L - 20L'
    else if (price < 5000000) range = '20L - 50L'
    else if (price < 10000000) range = '50L - 1Cr'
    else range = 'Above 1Cr'
    
    acc[range] = (acc[range] || 0) + 1
    return acc
  }, {
    'Under 10L': 0,
    '10L - 20L': 0,
    '20L - 50L': 0,
    '50L - 1Cr': 0,
    'Above 1Cr': 0
  } as Record<string, number>)

  // Calculate average days on market (simplified)
  const now = new Date()
  const averageDaysOnMarket = properties.reduce((sum, prop) => {
    const createdDate = new Date(prop.created_at || prop.dateAdded || now)
    const daysDiff = Math.floor((now.getTime() - createdDate.getTime()) / (1000 * 60 * 60 * 24))
    return sum + Math.max(0, daysDiff)
  }, 0) / totalProperties

  // Get top performing properties (by price, simplified)
  const topPerformingProperties = [...properties]
    .sort((a, b) => (b.price || 0) - (a.price || 0))
    .slice(0, 5)

  return {
    total_properties: totalProperties,
    published_properties: publishedProperties,
    draft_properties: draftProperties,
    archived_properties: archivedProperties,
    average_price: averagePrice,
    total_value: totalValue,
    price_range_distribution: priceRangeDistribution,
    property_type_distribution: propertyTypeDistribution,
    location_distribution: locationDistribution,
    status_distribution: statusDistribution,
    average_days_on_market: Math.round(averageDaysOnMarket),
    conversion_rate: 0, // Would need lead data to calculate
    top_performing_properties: topPerformingProperties,
    recent_activity: [] // Would need activity data
  }
}

/**
 * Transform properties array into dashboard stats
 */
export function transformPropertiesToStats(properties: Property[]) {
  const analytics = transformPropertiesToAnalytics(properties)
  
  return {
    total_properties: analytics.total_properties,
    active_listings: analytics.published_properties,
    total_leads: 0, // Would need lead data
    total_users: 1, // Would need user data
    total_views: analytics.total_properties * 10, // Mock calculation
    monthly_leads: Math.floor(analytics.total_properties * 2), // Mock calculation
    revenue: `₹${(analytics.total_value / 100000).toFixed(0)}L`
  }
}

/**
 * Transform properties for display in components
 */
export function transformPropertiesForDisplay(properties: Property[]) {
  return properties.map(prop => ({
    id: prop.id,
    title: prop.title,
    description: prop.description,
    price: prop.price,
    address: prop.address || prop.location,
    bedrooms: prop.bedrooms,
    bathrooms: prop.bathrooms,
    area: prop.area || prop.area_sqft,
    type: prop.property_type || prop.type,
    status: prop.status === 'active' ? 'for-sale' : prop.status,
    dateAdded: prop.created_at || prop.dateAdded,
    image: prop.image,
    images: prop.images
  }))
}

/**
 * Safe property access with defaults
 */
export function safePropertyAccess<T>(obj: any, path: string, defaultValue: T): T {
  try {
    return path.split('.').reduce((current, key) => current?.[key], obj) ?? defaultValue
  } catch {
    return defaultValue
  }
}

/**
 * Format currency for display
 */
export function formatCurrency(amount: number): string {
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(1)}Cr`
  } else if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(0)}L`
  } else {
    return `₹${amount.toLocaleString()}`
  }
}

/**
 * Calculate percentage safely
 */
export function calculatePercentage(part: number, total: number): number {
  if (total === 0) return 0
  return Math.round((part / total) * 100)
}