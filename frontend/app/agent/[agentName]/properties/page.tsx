'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  MapPinIcon,
  HomeIcon,
  CurrencyRupeeIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import { PropertyType } from '@/types/property'

interface Property {
  id: string
  title: string
  description: string
  price: number
  property_type: string
  bedrooms: number
  bathrooms: number
  area: number
  location: string
  images: string[]
  features: string[]
  created_at: string
}

interface SearchFilters {
  location: string
  min_price: number | null
  max_price: number | null
  property_type: string
  min_bedrooms: number | null
  min_bathrooms: number | null
  min_area: number | null
  max_area: number | null
  features: string[]
  sort_by: string
  sort_order: string
}

interface AgentPropertiesPageProps {
  params: Promise<{
    agentName: string
  }>
}

export default function AgentPropertiesPage({ params }: AgentPropertiesPageProps) {
  const [properties, setProperties] = useState<Property[]>([])
  const [filteredProperties, setFilteredProperties] = useState<Property[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [agentName, setAgentName] = useState('')

  const [filters, setFilters] = useState<SearchFilters>({
    location: '',
    min_price: null,
    max_price: null,
    property_type: '',
    min_bedrooms: null,
    min_bathrooms: null,
    min_area: null,
    max_area: null,
    features: [],
    sort_by: 'created_at',
    sort_order: 'desc'
  })

  useEffect(() => {
    const initializeParams = async () => {
      const resolvedParams = await params
      setAgentName(resolvedParams.agentName)
      loadProperties(resolvedParams.agentName)
    }
    initializeParams()
  }, [params])

  useEffect(() => {
    if (agentName) {
      loadProperties(agentName)
    }
  }, [agentName, currentPage])

  useEffect(() => {
    applyFilters()
  }, [properties, filters])

  const loadProperties = async (agentName: string) => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch(
        `/api/v1/agent-public/${agentName}/properties?page=${currentPage}&limit=12`
      )
      
      if (!response.ok) {
        throw new Error('Failed to load properties')
      }

      const data = await response.json()
      setProperties(data.properties || [])
      setTotalPages(data.total_pages || 1)
      setAgentName(data.agent_name || '')

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load properties')
    } finally {
      setIsLoading(false)
    }
  }

  const applyFilters = () => {
    let filtered = [...properties]

    // Location filter
    if (filters.location) {
      filtered = filtered.filter(property =>
        property.location.toLowerCase().includes(filters.location.toLowerCase())
      )
    }

    // Price filters
    if (filters.min_price !== null) {
      filtered = filtered.filter(property => property.price >= filters.min_price!)
    }
    if (filters.max_price !== null) {
      filtered = filtered.filter(property => property.price <= filters.max_price!)
    }

    // Property type filter
    if (filters.property_type) {
      filtered = filtered.filter(property => property.property_type === filters.property_type)
    }

    // Bedrooms filter
    if (filters.min_bedrooms !== null) {
      filtered = filtered.filter(property => property.bedrooms >= filters.min_bedrooms!)
    }

    // Bathrooms filter
    if (filters.min_bathrooms !== null) {
      filtered = filtered.filter(property => property.bathrooms >= filters.min_bathrooms!)
    }

    // Area filters
    if (filters.min_area !== null) {
      filtered = filtered.filter(property => property.area >= filters.min_area!)
    }
    if (filters.max_area !== null) {
      filtered = filtered.filter(property => property.area <= filters.max_area!)
    }

    // Features filter
    if (filters.features.length > 0) {
      filtered = filtered.filter(property =>
        filters.features.every(feature =>
          property.features.some(propFeature =>
            propFeature.toLowerCase().includes(feature.toLowerCase())
          )
        )
      )
    }

    // Sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any

      switch (filters.sort_by) {
        case 'price':
          aValue = a.price
          bValue = b.price
          break
        case 'area':
          aValue = a.area
          bValue = b.area
          break
        case 'bedrooms':
          aValue = a.bedrooms
          bValue = b.bedrooms
          break
        default:
          aValue = new Date(a.created_at).getTime()
          bValue = new Date(b.created_at).getTime()
      }

      if (filters.sort_order === 'asc') {
        return aValue - bValue
      } else {
        return bValue - aValue
      }
    })

    setFilteredProperties(filtered)
  }

  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const clearFilters = () => {
    setFilters({
      location: '',
      min_price: null,
      max_price: null,
      property_type: '',
      min_bedrooms: null,
      min_bathrooms: null,
      min_area: null,
      max_area: null,
      features: [],
      sort_by: 'created_at',
      sort_order: 'desc'
    })
  }

  const formatPrice = (price: number) => {
    if (price >= 10000000) {
      return `₹${(price / 10000000).toFixed(1)}Cr`
    } else if (price >= 100000) {
      return `₹${(price / 100000).toFixed(1)}L`
    } else {
      return `₹${price.toLocaleString()}`
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading properties...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Properties</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => loadProperties(agentName)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/" className="text-xl font-bold text-blue-600">
                PropertyAI
              </Link>
              <p className="text-sm text-gray-600 mt-1">
                Properties by {agentName}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Link 
                href={`/agent/${agentName}`}
                className="text-gray-600 hover:text-gray-900"
              >
                Agent Profile
              </Link>
              <Link 
                href={`/agent/${agentName}/contact`}
                className="text-gray-600 hover:text-gray-900"
              >
                Contact
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search Bar */}
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by location..."
                  value={filters.location}
                  onChange={(e) => handleFilterChange('location', e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <FunnelIcon className="w-5 h-5 mr-2" />
              Filters
            </button>

            {/* Sort */}
            <select
              value={`${filters.sort_by}-${filters.sort_order}`}
              onChange={(e) => {
                const [sort_by, sort_order] = e.target.value.split('-')
                handleFilterChange('sort_by', sort_by)
                handleFilterChange('sort_order', sort_order)
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="created_at-desc">Newest First</option>
              <option value="created_at-asc">Oldest First</option>
              <option value="price-asc">Price: Low to High</option>
              <option value="price-desc">Price: High to Low</option>
              <option value="area-desc">Area: Large to Small</option>
              <option value="area-asc">Area: Small to Large</option>
            </select>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 pt-6 border-t border-gray-200"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Price Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min Price
                  </label>
                  <input
                    type="number"
                    placeholder="Min price"
                    value={filters.min_price || ''}
                    onChange={(e) => handleFilterChange('min_price', e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Price
                  </label>
                  <input
                    type="number"
                    placeholder="Max price"
                    value={filters.max_price || ''}
                    onChange={(e) => handleFilterChange('max_price', e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Property Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Property Type
                  </label>
                  <select
                    value={filters.property_type}
                    onChange={(e) => handleFilterChange('property_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">All Types</option>
                    <option value="Apartment">Apartment</option>
                    <option value="House">House</option>
                    <option value="Villa">Villa</option>
                    <option value="Commercial">Commercial</option>
                    <option value="Land">Land</option>
                    <option value="Office">Office</option>
                  </select>
                </div>

                {/* Bedrooms */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min Bedrooms
                  </label>
                  <select
                    value={filters.min_bedrooms || ''}
                    onChange={(e) => handleFilterChange('min_bedrooms', e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Any</option>
                    <option value="1">1+</option>
                    <option value="2">2+</option>
                    <option value="3">3+</option>
                    <option value="4">4+</option>
                    <option value="5">5+</option>
                  </select>
                </div>
              </div>

              <div className="mt-4 flex justify-end">
                <button
                  onClick={clearFilters}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Clear Filters
                </button>
              </div>
            </motion.div>
          )}
        </div>

        {/* Results Count */}
        <div className="mb-6">
          <p className="text-gray-600">
            Showing {filteredProperties.length} of {properties.length} properties
          </p>
        </div>

        {/* Properties Grid */}
        {filteredProperties.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProperties.map((property) => (
              <motion.div
                key={property.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow"
              >
                <Link href={`/agent/${agentName}/properties/${property.id}`}>
                  {property.images.length > 0 && (
                    <div className="aspect-w-16 aspect-h-9">
                      <img
                        src={property.images[0]}
                        alt={property.title}
                        className="w-full h-48 object-cover"
                      />
                    </div>
                  )}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                      {property.title}
                    </h3>
                    <div className="flex items-center text-gray-600 text-sm mb-2">
                      <MapPinIcon className="w-4 h-4 mr-1" />
                      {property.location}
                    </div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xl font-bold text-blue-600">
                        {formatPrice(property.price)}
                      </span>
                      <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {property.property_type}
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      {property.bedrooms > 0 && (
                        <span className="mr-4 flex items-center">
                          <HomeIcon className="w-4 h-4 mr-1" />
                          {property.bedrooms} bed
                        </span>
                      )}
                      {property.bathrooms > 0 && (
                        <span className="mr-4">{property.bathrooms} bath</span>
                      )}
                      {property.area > 0 && (
                        <span>{property.area} sq ft</span>
                      )}
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <HomeIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Properties Found</h3>
            <p className="text-gray-600 mb-6">
              Try adjusting your search criteria or clear the filters to see all properties.
            </p>
            <button
              onClick={clearFilters}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-8 flex justify-center">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-gray-700">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}