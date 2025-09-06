'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Image from 'next/image'
import {
  BuildingOfficeIcon,
  MapPinIcon,
  CurrencyRupeeIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
  HeartIcon,
  ShareIcon,
  AdjustmentsHorizontalIcon,
  Squares2X2Icon,
  ListBulletIcon
} from '@heroicons/react/24/outline'
import {
  HeartIcon as HeartSolidIcon
} from '@heroicons/react/24/solid'
import { apiService } from '@/lib/api'
import toast from 'react-hot-toast'

interface Property {
  id: string
  title: string
  description?: string
  price: number
  address: string
  bedrooms: number
  bathrooms: number
  area: number
  type: string
  status: 'for-sale' | 'for-rent' | 'sold'
  dateAdded: string
  image?: string
}

interface PropertiesProps {
  onAddProperty?: () => void
  properties?: Property[]
  setProperties?: (properties: Property[]) => void
}

export default function Properties({ onAddProperty, properties: propProperties = [], setProperties: propSetProperties }: PropertiesProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterType, setFilterType] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [priceRange, setPriceRange] = useState<{ min: number; max: number }>({ min: 0, max: 1000000 })
  const [bedroomFilter, setBedroomFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('dateAdded')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [propertyToDelete, setPropertyToDelete] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [favorites, setFavorites] = useState<string[]>([])

  // Use passed properties or fallback to empty array
  const properties = propProperties
  const setProperties = propSetProperties || (() => {})

  // Filter and sort properties
  const filteredProperties = properties
    .filter(property => {
      const matchesSearch = property.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           property.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           (property.description && property.description.toLowerCase().includes(searchTerm.toLowerCase()))
      const matchesStatus = filterStatus === 'all' || property.status === filterStatus
      const matchesType = filterType === 'all' || property.type === filterType
      const matchesPrice = property.price >= priceRange.min && property.price <= priceRange.max
      const matchesBedrooms = bedroomFilter === 'all' || property.bedrooms.toString() === bedroomFilter

      return matchesSearch && matchesStatus && matchesType && matchesPrice && matchesBedrooms
    })
    .sort((a, b) => {
      let aValue: any, bValue: any

      switch (sortBy) {
        case 'price':
          aValue = a.price
          bValue = b.price
          break
        case 'title':
          aValue = a.title.toLowerCase()
          bValue = b.title.toLowerCase()
          break
        case 'area':
          aValue = a.area
          bValue = b.area
          break
        case 'bedrooms':
          aValue = a.bedrooms
          bValue = b.bedrooms
          break
        case 'dateAdded':
        default:
          aValue = new Date(a.dateAdded)
          bValue = new Date(b.dateAdded)
          break
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
      }
    })

  const formatPrice = (price: number) => {
    if (price >= 10000000) {
      return `₹${(price / 10000000).toFixed(1)}Cr`
    } else if (price >= 100000) {
      return `₹${(price / 100000).toFixed(1)}L`
    }
    return `₹${price.toLocaleString()}`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'for-sale': return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300'
      case 'for-rent': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
      case 'sold': return 'bg-gray-100 text-gray-800 dark:bg-gray-800/30 dark:text-gray-300'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800/30 dark:text-gray-300'
    }
  }

  const toggleFavorite = (propertyId: string) => {
    setFavorites(prev => {
      if (prev.includes(propertyId)) {
        return prev.filter(id => id !== propertyId)
      } else {
        return [...prev, propertyId]
      }
    })
  }

  const handleEditProperty = (property: Property) => {
    setSelectedProperty(property)
    // You can implement edit modal or navigate to edit page here
  }

  const handleShare = async (property: Property) => {
    try {
      const shareData = {
        title: property.title,
        text: `Check out this property: ${property.title}`,
        url: window.location.href
      }

      if (navigator.share) {
        await navigator.share(shareData)
        toast.success('Property shared successfully!')
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(`${shareData.title} - ${shareData.url}`)
        toast.success('Property link copied to clipboard!')
      }
    } catch (error) {
      console.error('Share error:', error)
      toast.error('Failed to share property')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
            Properties
          </h1>
          <p className="text-gray-600 dark:text-gray-300 text-base">
            Manage your property listings • {filteredProperties.length} properties
          </p>
        </div>
        <button
          onClick={onAddProperty}
          className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-medium flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] hover-lift click-shrink"
        >
          <PlusIcon className="w-5 h-5" />
          <span className="hidden sm:inline">Add Property</span>
          <span className="sm:hidden">Add</span>
        </button>
      </div>

      {/* Search and Controls */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700">
        <div className="p-6">
          {/* Search Bar */}
          <div className="relative mb-4">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by title, location, or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
            />
          </div>

          {/* Controls Row */}
          <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 hover-glow click-shrink ${
                  showFilters
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    : 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600'
                }`}
              >
                <AdjustmentsHorizontalIcon className="w-4 h-4" />
                <span className="text-sm">Filters</span>
              </button>

              <div className="flex items-center bg-gray-100 dark:bg-slate-700 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-md transition-all duration-200 hover-scale click-shrink ${
                    viewMode === 'grid'
                      ? 'bg-white dark:bg-slate-600 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Squares2X2Icon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-all duration-200 hover-scale click-shrink ${
                    viewMode === 'list'
                      ? 'bg-white dark:bg-slate-600 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <ListBulletIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Filters Panel */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="border-t border-gray-200 dark:border-slate-600 pt-6 mt-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {/* Status Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Status
                      </label>
                      <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="all">All Status</option>
                        <option value="for-sale">For Sale</option>
                        <option value="for-rent">For Rent</option>
                        <option value="sold">Sold</option>
                      </select>
                    </div>

                    {/* Type Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Property Type
                      </label>
                      <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="all">All Types</option>
                        <option value="apartment">Apartment</option>
                        <option value="house">House</option>
                        <option value="villa">Villa</option>
                        <option value="office">Office</option>
                      </select>
                    </div>

                    {/* Bedrooms Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Bedrooms
                      </label>
                      <select
                        value={bedroomFilter}
                        onChange={(e) => setBedroomFilter(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="all">Any</option>
                        <option value="1">1 Bedroom</option>
                        <option value="2">2 Bedrooms</option>
                        <option value="3">3 Bedrooms</option>
                        <option value="4">4+ Bedrooms</option>
                      </select>
                    </div>

                    {/* Quick Actions */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Quick Actions
                      </label>
                      <button
                        onClick={() => {
                          setSearchTerm('')
                          setFilterStatus('all')
                          setFilterType('all')
                          setBedroomFilter('all')
                          setPriceRange({ min: 0, max: 1000000 })
                        }}
                        className="w-full px-3 py-2 bg-gray-100 dark:bg-slate-600 hover:bg-gray-200 dark:hover:bg-slate-500 text-gray-700 dark:text-gray-300 rounded-lg font-medium transition-colors text-sm"
                      >
                        Clear All Filters
                      </button>
                    </div>
                  </div>

                  {/* Price Range */}
                  <div className="bg-gray-50 dark:bg-slate-700/50 rounded-xl p-4 mt-6">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      Price Range: ₹{priceRange.min.toLocaleString()} - ₹{priceRange.max.toLocaleString()}
                    </label>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-4">
                        <div className="flex-1">
                          <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Min Price</label>
                          <input
                            type="range"
                            min="0"
                            max="1000000"
                            step="10000"
                            value={priceRange.min}
                            onChange={(e) => setPriceRange(prev => ({ ...prev, min: parseInt(e.target.value) }))}
                            className="w-full h-2 bg-gray-200 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer slider"
                          />
                        </div>
                        <div className="flex-1">
                          <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Max Price</label>
                          <input
                            type="range"
                            min="0"
                            max="1000000"
                            step="10000"
                            value={priceRange.max}
                            onChange={(e) => setPriceRange(prev => ({ ...prev, max: parseInt(e.target.value) }))}
                            className="w-full h-2 bg-gray-200 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer slider"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Properties Display */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : 'space-y-4'}>
        {filteredProperties.map((property, index) => (
          <motion.div
            key={property.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className={`bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 overflow-hidden hover:shadow-xl dark:hover:shadow-slate-900/20 transition-all duration-300 group card-hover hover-glow hover:-translate-y-1 ${
              viewMode === 'list' ? 'flex flex-col sm:flex-row' : ''
            }`}
          >
            {/* Property Image with Enhanced Design */}
            <div className={`relative overflow-hidden ${
              viewMode === 'list' ? 'h-48 sm:h-32 sm:w-48 flex-shrink-0' : 'h-48'
            }`}>
              {/* Property Image */}
              <div className="h-full bg-gradient-to-br from-blue-500 to-purple-600 relative">
                {property.image ? (
                  <Image
                    src={property.image}
                    alt={property.title}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <BuildingOfficeIcon className="w-16 h-16 text-white/50" />
                  </div>
                )}
              </div>

              {/* Enhanced Status Badge with Semantic Colors */}
              <div className="absolute top-3 left-3">
                <span className={`px-3 py-1.5 rounded-full text-xs font-bold backdrop-blur-sm border shadow-lg ${
                  property.status === 'for-sale'
                    ? 'bg-emerald-500/95 text-white border-emerald-400/60 shadow-emerald-500/25'
                    : property.status === 'for-rent'
                    ? 'bg-blue-500/95 text-white border-blue-400/60 shadow-blue-500/25'
                    : property.status === 'sold'
                    ? 'bg-gray-500/95 text-white border-gray-400/60 shadow-gray-500/25'
                    : 'bg-amber-500/95 text-white border-amber-400/60 shadow-amber-500/25'
                }`}>
                  {property.status === 'for-sale' ? 'FOR SALE' :
                   property.status === 'for-rent' ? 'FOR RENT' :
                   property.status === 'sold' ? 'SOLD' :
                   property.status.toUpperCase()}
                </span>
              </div>

              {/* Quick Actions */}
              <div className="absolute top-3 right-3 flex gap-2">
                <button
                  onClick={() => toggleFavorite(property.id)}
                  className={`p-2 rounded-full backdrop-blur-sm border transition-all duration-200 ${
                    favorites.includes(property.id)
                      ? 'bg-red-500/90 text-white border-red-400/50'
                      : 'bg-white/10 text-white border-white/20 hover:bg-white/20'
                  }`}
                >
                  <HeartSolidIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleShare(property)}
                  className="p-2 rounded-full bg-white/10 text-white border border-white/20 backdrop-blur-sm hover:bg-white/20 transition-all duration-200"
                >
                  <ShareIcon className="w-4 h-4" />
                </button>
              </div>

              {/* Price Overlay */}
              <div className="absolute bottom-3 left-3">
                <div className="bg-black/60 backdrop-blur-sm rounded-lg px-3 py-1.5">
                  <div className="text-white font-bold text-lg">
                    {formatPrice(property.price)}
                  </div>
                </div>
              </div>
            </div>

            {/* Property Details with Enhanced Layout */}
            <div className="p-5 sm:p-6">
              {/* Property Title and Location */}
              <div className="mb-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-200">
                  {property.title}
                </h3>
                <div className="flex items-center text-gray-500 dark:text-gray-400 text-sm">
                  <MapPinIcon className="w-4 h-4 mr-1.5 flex-shrink-0" />
                  <span className="truncate">{property.address}</span>
                </div>
              </div>

              {/* Enhanced Property Specs */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-300">
                  <div className="flex items-center bg-gray-50 dark:bg-slate-700 px-2 py-1 rounded-md">
                    <span className="mr-1">🛏️</span>
                    <span className="font-medium">{property.bedrooms}</span>
                  </div>
                  <div className="flex items-center bg-gray-50 dark:bg-slate-700 px-2 py-1 rounded-md">
                    <span className="mr-1">🚿</span>
                    <span className="font-medium">{property.bathrooms}</span>
                  </div>
                  <div className="flex items-center bg-gray-50 dark:bg-slate-700 px-2 py-1 rounded-md">
                    <span className="mr-1">📐</span>
                    <span className="font-medium">{property.area}</span>
                  </div>
                </div>
              </div>

              {/* Property Type Badge */}
              <div className="mb-4">
                <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-sm">
                  {property.type.charAt(0).toUpperCase() + property.type.slice(1)}
                </span>
              </div>

              {/* Enhanced Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedProperty(property)}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-4 py-2.5 rounded-lg font-semibold transition-all duration-200 text-sm shadow-md hover:shadow-lg hover-lift click-shrink"
                >
                  View Details
                </button>
                <button
                  onClick={() => handleEditProperty(property)}
                  className="p-2.5 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 rounded-lg transition-all duration-200 hover-lift click-shrink"
                  title="Edit Property"
                >
                  <PencilIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Empty State */}
      {filteredProperties.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16"
        >
          <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-2xl flex items-center justify-center">
            <svg className="w-12 h-12 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
            {searchTerm || filterStatus !== 'all' || filterType !== 'all' || bedroomFilter !== 'all'
              ? 'No properties match your filters'
              : 'No properties found'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
            {searchTerm || filterStatus !== 'all' || filterType !== 'all' || bedroomFilter !== 'all'
              ? 'Try adjusting your search criteria or filters to find more properties.'
              : 'Get started by adding your first property listing.'}
          </p>
          <button
            onClick={onAddProperty}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] inline-flex items-center space-x-2"
          >
            <PlusIcon className="w-5 h-5" />
            <span>Add Your First Property</span>
          </button>
        </motion.div>
      )}
    </div>
  )
}
