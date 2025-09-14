import {
  transformPropertiesToAnalytics,
  transformPropertiesToStats,
  transformPropertiesForDisplay,
  safePropertyAccess,
  formatCurrency,
  calculatePercentage,
  type Property,
} from '@/lib/data-transformers'

describe('Data Transformers', () => {
  const mockProperties: Property[] = [
    {
      id: '1',
      title: 'Luxury Villa',
      description: 'Beautiful villa with garden',
      price: 5000000,
      address: '123 Main St, Mumbai',
      location: 'Mumbai',
      bedrooms: 4,
      bathrooms: 3,
      area: 2500,
      area_sqft: 2500,
      type: 'villa',
      property_type: 'villa',
      status: 'for-sale',
      dateAdded: '2024-01-01',
      created_at: '2024-01-01T00:00:00Z',
      image: 'villa.jpg',
      images: ['villa1.jpg', 'villa2.jpg'],
      features: ['garden', 'pool'],
      amenities: 'Garden, Pool, Gym'
    },
    {
      id: '2',
      title: 'Modern Apartment',
      description: 'City center apartment',
      price: 2500000,
      address: '456 Park Ave, Delhi',
      location: 'Delhi',
      bedrooms: 2,
      bathrooms: 2,
      area: 1200,
      area_sqft: 1200,
      type: 'apartment',
      property_type: 'apartment',
      status: 'for-rent',
      dateAdded: '2024-01-02',
      created_at: '2024-01-02T00:00:00Z',
      image: 'apartment.jpg',
      images: ['apt1.jpg'],
      features: ['balcony'],
      amenities: 'Gym, Parking'
    },
    {
      id: '3',
      title: 'Draft Property',
      description: 'Not ready yet',
      price: 1000000,
      address: '789 Side St, Bangalore',
      location: 'Bangalore',
      bedrooms: 1,
      bathrooms: 1,
      area: 800,
      area_sqft: 800,
      type: 'apartment',
      property_type: 'apartment',
      status: 'draft',
      dateAdded: '2024-01-03',
      created_at: '2024-01-03T00:00:00Z',
      image: 'draft.jpg',
      images: [],
      features: [],
      amenities: ''
    }
  ]

  describe('transformPropertiesToAnalytics', () => {
    it('should transform properties to analytics data correctly', () => {
      const result = transformPropertiesToAnalytics(mockProperties)

      expect(result.total_properties).toBe(3)
      expect(result.published_properties).toBe(2) // for-sale + for-rent
      expect(result.draft_properties).toBe(1)
      expect(result.archived_properties).toBe(0)
      expect(result.average_price).toBe(2833333) // (5000000 + 2500000 + 1000000) / 3
      expect(result.total_value).toBe(8500000)
    })

    it('should calculate property type distribution correctly', () => {
      const result = transformPropertiesToAnalytics(mockProperties)

      expect(result.property_type_distribution).toEqual({
        villa: 1,
        apartment: 2
      })
    })

    it('should calculate location distribution correctly', () => {
      const result = transformPropertiesToAnalytics(mockProperties)

      expect(result.location_distribution).toEqual({
        'Mumbai': 1,
        'Delhi': 1,
        'Bangalore': 1
      })
    })

    it('should calculate status distribution correctly', () => {
      const result = transformPropertiesToAnalytics(mockProperties)

      expect(result.status_distribution).toEqual({
        'for-sale': 1,
        'for-rent': 1,
        'draft': 1
      })
    })

    it('should calculate price range distribution correctly', () => {
      const result = transformPropertiesToAnalytics(mockProperties)

      expect(result.price_range_distribution).toEqual({
        'Under 10L': 0,
        '10L - 20L': 1, // 1000000
        '20L - 50L': 1, // 2500000
        '50L - 1Cr': 1, // 5000000
        'Above 1Cr': 0
      })
    })

    it('should handle empty properties array', () => {
      const result = transformPropertiesToAnalytics([])

      expect(result.total_properties).toBe(0)
      expect(result.published_properties).toBe(0)
      expect(result.average_price).toBe(0)
      expect(result.property_type_distribution).toEqual({})
    })

    it('should handle null/undefined properties', () => {
      const result = transformPropertiesToAnalytics(null as any)

      expect(result.total_properties).toBe(0)
      expect(result.published_properties).toBe(0)
    })
  })

  describe('transformPropertiesToStats', () => {
    it('should transform properties to dashboard stats', () => {
      const result = transformPropertiesToStats(mockProperties)

      expect(result.total_properties).toBe(3)
      expect(result.active_listings).toBe(2)
      expect(result.revenue).toBe('₹85L')
    })
  })

  describe('transformPropertiesForDisplay', () => {
    it('should transform properties for display correctly', () => {
      const result = transformPropertiesForDisplay(mockProperties)

      expect(result).toHaveLength(3)
      expect(result[0]).toEqual({
        id: '1',
        title: 'Luxury Villa',
        description: 'Beautiful villa with garden',
        price: 5000000,
        address: '123 Main St, Mumbai',
        bedrooms: 4,
        bathrooms: 3,
        area: 2500,
        type: 'villa',
        status: 'for-sale',
        dateAdded: '2024-01-01T00:00:00Z',
        image: 'villa.jpg',
        images: ['villa1.jpg', 'villa2.jpg']
      })
    })
  })

  describe('safePropertyAccess', () => {
    it('should safely access nested properties', () => {
      const obj = { user: { profile: { name: 'John' } } }
      
      expect(safePropertyAccess(obj, 'user.profile.name', 'Unknown')).toBe('John')
      expect(safePropertyAccess(obj, 'user.profile.age', 0)).toBe(0)
      expect(safePropertyAccess(obj, 'user.address.street', 'No Street')).toBe('No Street')
    })

    it('should handle null/undefined objects', () => {
      expect(safePropertyAccess(null, 'any.path', 'default')).toBe('default')
      expect(safePropertyAccess(undefined, 'any.path', 'default')).toBe('default')
    })

    it('should handle invalid paths', () => {
      const obj = { user: { name: 'John' } }
      expect(safePropertyAccess(obj, 'invalid.path', 'default')).toBe('default')
    })
  })

  describe('formatCurrency', () => {
    it('should format currency correctly for different amounts', () => {
      expect(formatCurrency(500000)).toBe('₹5L')
      expect(formatCurrency(5000000)).toBe('₹50L')
      expect(formatCurrency(15000000)).toBe('₹1.5Cr')
      expect(formatCurrency(50000)).toBe('₹50,000')
    })
  })

  describe('calculatePercentage', () => {
    it('should calculate percentage correctly', () => {
      expect(calculatePercentage(25, 100)).toBe(25)
      expect(calculatePercentage(1, 3)).toBe(33)
      expect(calculatePercentage(0, 100)).toBe(0)
      expect(calculatePercentage(100, 0)).toBe(0)
    })
  })
})