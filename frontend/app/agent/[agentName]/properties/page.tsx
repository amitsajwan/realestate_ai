'use client'

import {
    FunnelIcon,
    HeartIcon,
    HomeIcon,
    MagnifyingGlassIcon,
    MapPinIcon,
    ShareIcon
} from '@heroicons/react/24/outline'
import {
    HeartIcon as HeartSolidIcon
} from '@heroicons/react/24/solid'
import { motion } from 'framer-motion'
import Image from 'next/image'
import Link from 'next/link'
import { useEffect, useState } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Property {
    id: string
    title: string
    description: string
    price: number
    location: string
    address: string
    bedrooms: number
    bathrooms: number
    area_sqft: number
    property_type: string
    images: string[]
    features: string[]
    amenities: string[]
    status: string
    created_at: string
    agent_id: string
    agent_name?: string
    agent_phone?: string
    agent_email?: string
}

interface AgentInfo {
    id: string
    agent_name: string
    slug: string
    photo: string
    phone: string
    email: string
    office_address: string
    bio?: string
}

interface PropertyFilters {
    location: string
    min_price: number | null
    max_price: number | null
    property_type: string
    min_bedrooms: number | null
    min_bathrooms: number | null
    min_area: number | null
    max_area: number | null
    status: string
}

interface AgentPropertiesPageProps {
    params: {
        agentName: string
    }
}

export default function AgentPropertiesPage({ params }: AgentPropertiesPageProps) {
    const [properties, setProperties] = useState<Property[]>([])
    const [agent, setAgent] = useState<AgentInfo | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [currentPage, setCurrentPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [showFilters, setShowFilters] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [favorites, setFavorites] = useState<Set<string>>(new Set())
    const [filters, setFilters] = useState<PropertyFilters>({
        location: '',
        min_price: null,
        max_price: null,
        property_type: '',
        min_bedrooms: null,
        min_bathrooms: null,
        min_area: null,
        max_area: null,
        status: 'active'
    })

    const agentName = params.agentName.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

    useEffect(() => {
        loadProperties()
        loadAgentData()
    }, [currentPage, filters, searchQuery])

    const loadAgentData = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}`)
            if (response.ok) {
                const agentData = await response.json()
                setAgent(agentData)
            }
        } catch (err) {
            console.error('Error loading agent data:', err)
        }
    }

    const loadProperties = async () => {
        try {
            setIsLoading(true)
            setError(null)

            const queryParams = new URLSearchParams({
                page: currentPage.toString(),
                limit: '12'
            })

            // Add filters to query params
            if (searchQuery) queryParams.append('search', searchQuery)
            if (filters.location) queryParams.append('location', filters.location)
            if (filters.property_type) queryParams.append('property_type', filters.property_type)
            if (filters.min_price) queryParams.append('min_price', filters.min_price.toString())
            if (filters.max_price) queryParams.append('max_price', filters.max_price.toString())
            if (filters.min_bedrooms) queryParams.append('min_bedrooms', filters.min_bedrooms.toString())
            if (filters.min_bathrooms) queryParams.append('min_bathrooms', filters.min_bathrooms.toString())
            if (filters.min_area) queryParams.append('min_area', filters.min_area.toString())
            if (filters.max_area) queryParams.append('max_area', filters.max_area.toString())
            if (filters.status) queryParams.append('status', filters.status)

            const response = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}/properties?${queryParams}`)

            if (!response.ok) {
                throw new Error('Failed to load properties')
            }

            const data = await response.json()
            setProperties(data.properties || [])
            setTotalPages(data.total_pages || 1)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
        }
    }

    const handleFilterChange = (key: keyof PropertyFilters, value: any) => {
        setFilters(prev => ({ ...prev, [key]: value }))
        setCurrentPage(1)
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
            status: 'active'
        })
        setSearchQuery('')
        setCurrentPage(1)
    }

    const handleFavorite = (propertyId: string) => {
        setFavorites(prev => {
            const newSet = new Set(prev)
            if (newSet.has(propertyId)) {
                newSet.delete(propertyId)
            } else {
                newSet.add(propertyId)
            }
            return newSet
        })
    }

    const formatPrice = (price: number) => {
        if (price == null || price === 0) return 'Contact for price'
        
        if (price >= 10000000) {
            return `₹${(price / 10000000).toFixed(1)}Cr`
        } else if (price >= 100000) {
            return `₹${(price / 100000).toFixed(0)}L`
        } else {
            return `₹${price.toLocaleString()}`
        }
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        const now = new Date()
        const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

        if (diffInDays === 0) return 'Today'
        if (diffInDays === 1) return 'Yesterday'
        if (diffInDays < 7) return `${diffInDays} days ago`
        return date.toLocaleDateString()
    }

    const filteredProperties = properties.filter(property => {
        if (searchQuery) {
            const query = searchQuery.toLowerCase()
            return (
                property.title.toLowerCase().includes(query) ||
                property.location.toLowerCase().includes(query) ||
                property.description.toLowerCase().includes(query)
            )
        }
        return true
    })

    if (isLoading && currentPage === 1) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading properties...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-600 mb-4">Error: {error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <Link href={`/agent/${params.agentName}`} className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                                    <span className="text-white font-bold text-lg">
                                        {agent?.agent_name?.charAt(0) || 'A'}
                                    </span>
                                </div>
                                <div>
                                    <h1 className="text-xl font-bold text-gray-900">{agent?.agent_name || 'Agent'}</h1>
                                    <p className="text-sm text-gray-500">Real Estate Agent</p>
                                </div>
                            </Link>
                        </div>
                        <div className="flex items-center space-x-4">
                            <Link
                                href={`/agent/${params.agentName}/contact`}
                                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Contact Agent
                            </Link>
                        </div>
                    </div>
                </div>
            </header>

            {/* Search and Filters */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 py-6">
                    <div className="flex flex-col lg:flex-row gap-4">
                        {/* Search Bar */}
                        <div className="flex-1 relative">
                            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search properties by location, features, or keywords..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        {/* Filter Toggle */}
                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className="flex items-center space-x-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                            <FunnelIcon className="w-5 h-5 text-gray-500" />
                            <span className="text-gray-700">Filters</span>
                        </button>
                    </div>

                    {/* Advanced Filters */}
                    {showFilters && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-6 p-6 bg-gray-50 rounded-lg"
                        >
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                {/* Location */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                                    <input
                                        type="text"
                                        placeholder="City, neighborhood..."
                                        value={filters.location}
                                        onChange={(e) => handleFilterChange('location', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                {/* Property Type */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Property Type</label>
                                    <select
                                        value={filters.property_type}
                                        onChange={(e) => handleFilterChange('property_type', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="">All Types</option>
                                        <option value="house">House</option>
                                        <option value="apartment">Apartment</option>
                                        <option value="condo">Condo</option>
                                        <option value="townhouse">Townhouse</option>
                                        <option value="commercial">Commercial</option>
                                    </select>
                                </div>

                                {/* Price Range */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Min Price</label>
                                    <input
                                        type="number"
                                        placeholder="Min price"
                                        value={filters.min_price || ''}
                                        onChange={(e) => handleFilterChange('min_price', e.target.value ? Number(e.target.value) : null)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Max Price</label>
                                    <input
                                        type="number"
                                        placeholder="Max price"
                                        value={filters.max_price || ''}
                                        onChange={(e) => handleFilterChange('max_price', e.target.value ? Number(e.target.value) : null)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                {/* Bedrooms */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Min Bedrooms</label>
                                    <select
                                        value={filters.min_bedrooms || ''}
                                        onChange={(e) => handleFilterChange('min_bedrooms', e.target.value ? Number(e.target.value) : null)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="">Any</option>
                                        <option value="1">1+</option>
                                        <option value="2">2+</option>
                                        <option value="3">3+</option>
                                        <option value="4">4+</option>
                                        <option value="5">5+</option>
                                    </select>
                                </div>

                                {/* Bathrooms */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Min Bathrooms</label>
                                    <select
                                        value={filters.min_bathrooms || ''}
                                        onChange={(e) => handleFilterChange('min_bathrooms', e.target.value ? Number(e.target.value) : null)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="">Any</option>
                                        <option value="1">1+</option>
                                        <option value="1.5">1.5+</option>
                                        <option value="2">2+</option>
                                        <option value="2.5">2.5+</option>
                                        <option value="3">3+</option>
                                    </select>
                                </div>

                                {/* Status */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                                    <select
                                        value={filters.status}
                                        onChange={(e) => handleFilterChange('status', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="active">Available</option>
                                        <option value="pending">Pending</option>
                                        <option value="sold">Sold</option>
                                    </select>
                                </div>
                            </div>

                            <div className="flex justify-end mt-4">
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
            </div>

            {/* Properties Grid */}
            <div className="max-w-7xl mx-auto px-4 py-8">
                {filteredProperties.length === 0 ? (
                    <div className="text-center py-12">
                        <HomeIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No properties found</h3>
                        <p className="text-gray-500">Try adjusting your search criteria or filters.</p>
                    </div>
                ) : (
                    <>
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-2xl font-bold text-gray-900">
                                {filteredProperties.length} Properties Found
                            </h2>
                            <div className="flex items-center space-x-2 text-sm text-gray-500">
                                <span>Page {currentPage} of {totalPages}</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredProperties.map((property, index) => (
                                <motion.div
                                    key={property.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.3, delay: index * 0.1 }}
                                    className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
                                >
                                    {/* Property Image */}
                                    <div className="relative aspect-video">
                                        {property.images && property.images.length > 0 ? (
                                            <Image
                                                src={property.images[0]}
                                                alt={property.title}
                                                fill
                                                className="object-cover"
                                                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                                            />
                                        ) : (
                                            <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                                                <HomeIcon className="w-12 h-12 text-gray-400" />
                                            </div>
                                        )}

                                        {/* Status Badge */}
                                        <div className="absolute top-3 left-3">
                                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${property.status === 'active'
                                                ? 'bg-green-100 text-green-800'
                                                : property.status === 'pending'
                                                    ? 'bg-yellow-100 text-yellow-800'
                                                    : 'bg-red-100 text-red-800'
                                                }`}>
                                                {property.status === 'active' ? 'Available' :
                                                    property.status === 'pending' ? 'Pending' : 'Sold'}
                                            </span>
                                        </div>

                                        {/* Favorite Button */}
                                        <button
                                            onClick={() => handleFavorite(property.id)}
                                            className="absolute top-3 right-3 p-2 bg-white/90 rounded-full hover:bg-white transition-colors"
                                        >
                                            {favorites.has(property.id) ? (
                                                <HeartSolidIcon className="w-5 h-5 text-red-500" />
                                            ) : (
                                                <HeartIcon className="w-5 h-5 text-gray-600" />
                                            )}
                                        </button>

                                        {/* Image Count */}
                                        {property.images && property.images.length > 1 && (
                                            <div className="absolute bottom-3 right-3 bg-black/70 text-white text-xs px-2 py-1 rounded-full">
                                                +{property.images.length - 1} more
                                            </div>
                                        )}
                                    </div>

                                    {/* Property Details */}
                                    <div className="p-6">
                                        {/* Price */}
                                        <div className="text-2xl font-bold text-green-600 mb-2">
                                            {property.price ? formatPrice(property.price) : 'Price on request'}
                                        </div>

                                        {/* Title */}
                                        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-1">
                                            {property.title}
                                        </h3>

                                        {/* Location */}
                                        <div className="flex items-center text-gray-600 mb-4">
                                            <MapPinIcon className="w-4 h-4 mr-1" />
                                            <span className="text-sm">{property.location}</span>
                                        </div>

                                        {/* Key Details */}
                                        <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
                                            <div className="flex items-center space-x-4">
                                                <div className="flex items-center">
                                                    <HomeIcon className="w-4 h-4 mr-1" />
                                                    <span>{property.bedrooms || 'N/A'} bed</span>
                                                </div>
                                                <div className="flex items-center">
                                                    <HomeIcon className="w-4 h-4 mr-1" />
                                                    <span>{property.bathrooms || 'N/A'} bath</span>
                                                </div>
                                                <div className="flex items-center">
                                                    <HomeIcon className="w-4 h-4 mr-1" />
                                                    <span>{property.area_sqft ? property.area_sqft.toLocaleString() : 'N/A'} sq ft</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Property Type */}
                                        <div className="mb-4">
                                            <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                                                {property.property_type || 'Property'}
                                            </span>
                                        </div>

                                        {/* Description */}
                                        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                                            {property.description || 'No description available'}
                                        </p>

                                        {/* Agent Info */}
                                        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                                            <div className="flex items-center space-x-2">
                                                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                                    <span className="text-white text-xs font-medium">
                                                        {agent?.agent_name?.charAt(0) || 'A'}
                                                    </span>
                                                </div>
                                                <div>
                                                    <p className="text-sm font-medium text-gray-900">
                                                        {agent?.agent_name || 'Agent'}
                                                    </p>
                                                    <p className="text-xs text-gray-500">
                                                        {formatDate(property.created_at)}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center space-x-2">
                                                <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                                                    <ShareIcon className="w-4 h-4" />
                                                </button>
                                                <Link
                                                    href={`/agent/${params.agentName}/properties/${property.id}`}
                                                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                                                >
                                                    View Details
                                                </Link>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="flex justify-center mt-8">
                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                        disabled={currentPage === 1}
                                        className="px-3 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Previous
                                    </button>
                                    <span className="px-4 py-2 bg-blue-600 text-white rounded-lg">
                                        {currentPage}
                                    </span>
                                    <button
                                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                        disabled={currentPage === totalPages}
                                        className="px-3 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Next
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
