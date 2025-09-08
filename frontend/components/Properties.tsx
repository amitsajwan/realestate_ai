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
  ListBulletIcon,
  ArrowPathIcon
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
  onRefresh?: () => void
}

export default function Properties({ 
  onAddProperty, 
  properties: propProperties = [], 
  setProperties: propSetProperties,
  onRefresh
}: PropertiesProps) {
  // State management
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
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

  // Utility functions
  const formatPrice = (price: number): string => {
    if (price >= 10000000) {
      return `₹${(price / 10000000).toFixed(1)}Cr`
    } else if (price >= 100000) {
      return `₹${(price / 100000).toFixed(0)}L`
    } else {
      return `₹${price.toLocaleString()}`
    }
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'for-sale':
        return 'bg-emerald-500/95 text-white border-emerald-400/60 shadow-emerald-500/25'
      case 'for-rent':
        return 'bg-blue-500/95 text-white border-blue-400/60 shadow-blue-500/25'
      case 'sold':
        return 'bg-gray-500/95 text-white border-gray-400/60 shadow-gray-500/25'
      default:
        return 'bg-amber-500/95 text-white border-amber-400/60 shadow-amber-500/25'
    }
  }

  const toggleFavorite = (propertyId: string) => {
    setFavorites(prev => 
      prev.includes(propertyId) 
        ? prev.filter(id => id !== propertyId)
        : [...prev, propertyId]
    )
  }

  const handleShare = async (property: Property) => {
    const shareData = {
      title: property.title,
      text: `Check out this property: ${property.title}`,
      url: `${window.location.origin}/properties/${property.id}`
    }

    try {
      if (navigator.share) {
        await navigator.share(shareData)
      } else {
        // no-op; fallback handled below
      }
      // Always copy link to clipboard as a convenient fallback
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(shareData.url)
      }
      toast.success(navigator.share ? 'Property shared successfully!' : 'Property link copied to clipboard!')
    } catch (error) {
      console.error('Error sharing property:', error)
      toast.error('Failed to share property')
    }
  }

  const handleEdit = (property: Property) => {
    // TODO: Implement edit functionality
    toast('Edit functionality coming soon!')
  }

  const handleDeleteProperty = (property: Property) => {
    setPropertyToDelete(property.id)
    setShowDeleteModal(true)
  }

  const confirmDelete = async () => {
    if (!propertyToDelete) return

    try {
      setLoading(true)
      // Call API to delete property
      // await apiService.deleteProperty(propertyToDelete)
      console.log('Deleting property:', propertyToDelete)
      
      // Update local state
      const updatedProperties = properties.filter(p => p.id !== propertyToDelete)
      setProperties(updatedProperties)
      
      toast('Property deleted successfully!')
      setShowDeleteModal(false)
      setPropertyToDelete(null)
    } catch (error) {
      console.error('Error deleting property:', error)
      toast('Failed to delete property')
    } finally {
      setLoading(false)
    }
  }

  // Filter and sort properties
  const filteredProperties = properties
    .filter(property => {
      const matchesSearch = property.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           property.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           (property.description && property.description.toLowerCase().includes(searchTerm.toLowerCase()))
      const matchesStatus = statusFilter === 'all' || property.status === statusFilter
      const matchesType = typeFilter === 'all' || property.type === typeFilter
      const matchesBedrooms = bedroomFilter === 'all' || property.bedrooms.toString() === bedroomFilter
      
      return matchesSearch && matchesStatus && matchesType && matchesBedrooms
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
        case 'dateAdded':
        default:
          aValue = new Date(a.dateAdded).getTime()
          bValue = new Date(b.dateAdded).getTime()
          break
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

  const clearFilters = () => {
    setSearchTerm('')
    setStatusFilter('all')
    setTypeFilter('all')
    setBedroomFilter('all')
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
            Properties
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your property listings • {properties.length} properties
          </p>
        </div>
        <div className="flex gap-3">
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 px-4 py-3 rounded-xl font-semibold flex items-center space-x-2 transition-all duration-200"
              title="Refresh Properties"
            >
              <ArrowPathIcon className="w-5 h-5" />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          )}
          <button
            onClick={onAddProperty}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-semibold flex items-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
          >
            <PlusIcon className="w-5 h-5" />
            <span>Add Property</span>
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by title, location, or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              />
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2 px-4 py-3 border border-gray-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-600 transition-colors"
            >
              <FunnelIcon className="w-5 h-5" />
              <span>Filters</span>
            </button>

            {/* View Mode Toggle */}
            <div className="flex border border-gray-200 dark:border-slate-600 rounded-xl overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-3 transition-colors ${
                  viewMode === 'grid' 
                    ? 'bg-white dark:bg-slate-700 text-blue-600' 
                    : 'bg-gray-50 dark:bg-slate-600 text-gray-500 dark:text-gray-400'
                }`}
              >
                <Squares2X2Icon className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-3 transition-colors ${
                  viewMode === 'list' 
                    ? 'bg-white dark:bg-slate-700 text-blue-600' 
                    : 'bg-gray-50 dark:bg-slate-600 text-gray-500 dark:text-gray-400'
                }`}
              >
                <ListBulletIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Filter Options */}
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 pt-4 border-t border-gray-200 dark:border-slate-700"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  Type
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Types</option>
                  <option value="Apartment">Apartment</option>
                  <option value="House">House</option>
                  <option value="Villa">Villa</option>
                  <option value="Commercial">Commercial</option>
                </select>
              </div>

              {/* Bedroom Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Bedrooms
                </label>
                <select
                  value={bedroomFilter}
                  onChange={(e) => setBedroomFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Bedrooms</option>
                  <option value="1">1 Bedroom</option>
                  <option value="2">2 Bedrooms</option>
                  <option value="3">3 Bedrooms</option>
                  <option value="4">4+ Bedrooms</option>
                </select>
              </div>

              {/* Sort */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Sort By
                </label>
                <select
                  value={`${sortBy}-${sortOrder}`}
                  onChange={(e) => {
                    const [newSortBy, newSortOrder] = e.target.value.split('-')
                    setSortBy(newSortBy)
                    setSortOrder(newSortOrder as 'asc' | 'desc')
                  }}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="dateAdded-desc">Newest First</option>
                  <option value="dateAdded-asc">Oldest First</option>
                  <option value="price-desc">Price: High to Low</option>
                  <option value="price-asc">Price: Low to High</option>
                  <option value="title-asc">Title: A to Z</option>
                  <option value="title-desc">Title: Z to A</option>
                </select>
              </div>
            </div>

            {/* Clear Filters */}
            <div className="mt-4 flex justify-end">
              <button
                onClick={clearFilters}
                className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              >
                Clear All Filters
              </button>
            </div>
          </motion.div>
        )}
      </div>

      {/* Properties Grid */}
      <div className={`grid gap-6 ${
        viewMode === 'grid' 
          ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' 
          : 'grid-cols-1'
      }`}>
        {filteredProperties.map((property, index) => (
          <motion.div
            key={property.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className={`bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 overflow-hidden hover:shadow-xl dark:hover:shadow-slate-900/20 transition-all duration-300 group ${
              viewMode === 'list' ? 'flex flex-col sm:flex-row' : ''
            }`}
          >
            {/* Property Image */}
            <div className={`relative overflow-hidden ${
               viewMode === 'list' ? 'h-48 sm:h-32 sm:w-48 flex-shrink-0' : 'h-48'
             }`}>
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

              {/* Status Badge */}
              <div className="absolute top-3 left-3">
                <span className={`px-3 py-1.5 rounded-full text-xs font-bold backdrop-blur-sm border shadow-lg ${getStatusColor(property.status)}`}>
                  {property.status === 'for-sale' ? 'FOR SALE' :
                   property.status === 'for-rent' ? 'FOR RENT' :
                   property.status === 'sold' ? 'SOLD' :
                   'UNKNOWN'}
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

            {/* Property Details */}
            <div className="p-5 sm:p-6">
              <div className="mb-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 line-clamp-2">
                  {property.title}
                </h3>
                <div className="flex items-center text-gray-500 dark:text-gray-400 text-sm">
                  <MapPinIcon className="w-4 h-4 mr-1.5 flex-shrink-0" />
                  <span className="truncate">{property.address}</span>
                </div>
              </div>

              {/* Property Specs */}
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

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedProperty(property)}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-4 py-2.5 rounded-lg font-semibold transition-all duration-200 text-sm shadow-md hover:shadow-lg"
                >
                  View Details
                </button>
                <button
                  onClick={() => handleEdit(property)}
                  className="p-2.5 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 rounded-lg transition-all duration-200"
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
            <BuildingOfficeIcon className="w-12 h-12 text-blue-600 dark:text-blue-400" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
            {searchTerm || statusFilter !== 'all' || typeFilter !== 'all' || bedroomFilter !== 'all' 
              ? 'No properties match your filters' 
              : 'No properties yet'
            }
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
            {searchTerm || statusFilter !== 'all' || typeFilter !== 'all' || bedroomFilter !== 'all'
              ? 'Try adjusting your search criteria or filters to find more properties.'
              : 'Get started by adding your first property listing to showcase your real estate portfolio.'
            }
          </p>
          {(!searchTerm && statusFilter === 'all' && typeFilter === 'all' && bedroomFilter === 'all') && (
            <button
              onClick={onAddProperty}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-xl font-semibold flex items-center space-x-2 mx-auto transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
            >
              <PlusIcon className="w-5 h-5" />
              <span>Add Your First Property</span>
            </button>
          )}
        </motion.div>
      )}

      {/* Property Details Modal */}
      {selectedProperty && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
          >
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-slate-700">
              <div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedProperty.title}</h3>
                <p className="text-gray-600 dark:text-gray-400 mt-1">{selectedProperty.address}</p>
              </div>
              <button
                onClick={() => setSelectedProperty(null)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-6 h-6 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            
            <div className="overflow-y-auto max-h-[calc(90vh-140px)]">
              {/* Property Image */}
              <div className="relative h-80 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Image
                  src={selectedProperty.image || '/placeholder-property.jpg'}
                  alt={selectedProperty.title}
                  fill
                  className="object-cover"
                />
              </div>

              {/* Property Details */}
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Property Details</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Price:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{formatPrice(selectedProperty.price)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Type:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{selectedProperty.type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Status:</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(selectedProperty.status)}`}>
                          {selectedProperty.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Specifications</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Bedrooms:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{selectedProperty.bedrooms}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Bathrooms:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{selectedProperty.bathrooms}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Area:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{selectedProperty.area} sq ft</span>
                      </div>
                    </div>
                  </div>
                </div>

                {selectedProperty.description && (
                  <div className="mt-6">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Description</h4>
                    <p className="text-gray-600 dark:text-gray-400">{selectedProperty.description}</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => {
                      setSelectedProperty(null)
                      handleEdit(selectedProperty)
                    }}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                  >
                    Edit Property
                  </button>
                  <button
                    onClick={() => {
                      setSelectedProperty(null)
                      handleDeleteProperty(selectedProperty)
                    }}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                  >
                    Delete Property
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6"
          >
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Delete Property</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to delete this property? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 px-4 py-2 border border-gray-200 dark:border-slate-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {loading ? 'Deleting...' : 'Delete Property'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
