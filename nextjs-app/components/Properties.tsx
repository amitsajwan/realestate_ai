'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
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
  console.debug('[Properties] Edit property:', property)
  }

  const handleDeleteProperty = (propertyId: string) => {
    setPropertyToDelete(propertyId)
    setShowDeleteModal(true)
  }

  const confirmDelete = () => {
    if (propertyToDelete) {
      setProperties(properties.filter(p => p.id !== propertyToDelete))
      setPropertyToDelete(null)
      setShowDeleteModal(false)
    }
  }

  const handleViewProperty = (property: Property) => {
    // Navigate to property details or show property modal
    setSelectedProperty(property)
  console.debug('[Properties] View property:', property)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-1">
            Properties
          </h1>
          <p className="text-gray-600 dark:text-gray-300 text-sm sm:text-base">
            Manage your property listings • {filteredProperties.length} properties
          </p>
        </div>
        <button
          onClick={onAddProperty}
          className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl font-medium flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] hover-lift click-shrink"
        >
          <PlusIcon className="w-5 h-5" />
          <span className="hidden sm:inline">Add Property</span>
          <span className="sm:hidden">Add</span>
        </button>
      </div>

      {/* Search and Controls */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700">
        <div className="p-4 sm:p-6">
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
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  <Squares2X2Icon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-all duration-200 hover-scale click-shrink ${
                    viewMode === 'list'
                      ? 'bg-white dark:bg-slate-600 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  <ListBulletIcon className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sort, order] = e.target.value.split('-')
                  setSortBy(sort)
                  setSortOrder(order as 'asc' | 'desc')
                }}
                className="bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="dateAdded-desc">Newest First</option>
                <option value="dateAdded-asc">Oldest First</option>
                <option value="price-desc">Price: High to Low</option>
                <option value="price-asc">Price: Low to High</option>
                <option value="title-asc">Name: A to Z</option>
                <option value="title-desc">Name: Z to A</option>
                <option value="area-desc">Area: Largest First</option>
                <option value="area-asc">Area: Smallest First</option>
              </select>
            </div>
          </div>

          {/* Collapsible Filters */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="overflow-hidden border-t border-gray-200 dark:border-slate-600 mt-4 pt-4"
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                  {/* Status Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Status
                    </label>
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
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
                      className="w-full px-3 py-2 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    >
                      <option value="all">All Types</option>
                      <option value="House">House</option>
                      <option value="Apartment">Apartment</option>
                      <option value="Condo">Condo</option>
                      <option value="Townhouse">Townhouse</option>
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
                      className="w-full px-3 py-2 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    >
                      <option value="all">All Bedrooms</option>
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
                <div className="bg-gray-50 dark:bg-slate-700/50 rounded-xl p-4">
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
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Properties Display */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6' : 'space-y-4'}>
        {filteredProperties.map((property, index) => (
          <motion.div
            key={property.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className={`bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 overflow-hidden hover:shadow-lg dark:hover:shadow-slate-900/20 transition-all duration-300 group card-hover hover-glow ${
              viewMode === 'list' ? 'flex flex-col sm:flex-row' : ''
            }`}
          >
            {/* Property Image */}
            <div className={`relative overflow-hidden ${
               viewMode === 'list' ? 'h-48 sm:h-32 sm:w-48 flex-shrink-0' : 'h-48'
             }`}>
               <img
                 src={property.image}
                 alt={property.title}
                 className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
               />
               <div className="absolute top-3 left-3 flex items-center gap-2">
                 <span className={`px-2.5 py-1 rounded-full text-xs font-semibold backdrop-blur-sm ${
                   getStatusColor(property.status)
                 }`}>
                   {property.status === 'for-sale' ? 'For Sale' : 
                    property.status === 'for-rent' ? 'For Rent' : 
                    property.status.charAt(0).toUpperCase() + property.status.slice(1)}
                 </span>
               </div>
               <div className="absolute top-3 right-3">
                 <button
                   onClick={() => toggleFavorite(property.id)}
                   className="p-2 rounded-full bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm hover:bg-white dark:hover:bg-slate-800 transition-all duration-200 group/heart hover-scale click-shrink"
                 >
                   {favorites.indexOf(property.id) !== -1 ? (
                     <HeartSolidIcon className="w-4 h-4 text-red-500" />
                   ) : (
                     <HeartIcon className="w-4 h-4 text-gray-600 dark:text-gray-400 group-hover/heart:text-red-500" />
                   )}
                 </button>
               </div>
               <div className="absolute bottom-3 right-3">
                 <button className="p-2 rounded-full bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm hover:bg-white dark:hover:bg-slate-800 transition-all duration-200 hover-scale click-shrink">
                   <ShareIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                 </button>
               </div>
             </div>

            {/* Property Details */}
            <div className={`p-4 sm:p-5 flex-1 ${
              viewMode === 'list' ? 'flex flex-col justify-between' : ''
            }`}>
              <div>
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-1">
                    {property.title}
                  </h3>
                  <span className="text-xl font-bold text-blue-600 dark:text-blue-400 ml-2 flex-shrink-0">
                    {formatPrice(property.price)}
                  </span>
                </div>
                
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 flex items-center">
                   <svg className="w-4 h-4 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                   </svg>
                   <span className="line-clamp-1">{property.address}</span>
                 </p>

                 <div className="flex items-center gap-4 text-gray-600 dark:text-gray-400 text-sm mb-3">
                   <div className="flex items-center gap-1">
                     <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                     </svg>
                     <span>{property.bedrooms} bed</span>
                   </div>
                   <div className="flex items-center gap-1">
                     <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10v11M20 10v11" />
                     </svg>
                     <span>{property.bathrooms} bath</span>
                   </div>
                   <div className="flex items-center gap-1">
                     <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                     </svg>
                     <span>{property.area} sqft</span>
                   </div>
                 </div>

                {viewMode === 'grid' && (
                  <p className="text-gray-500 dark:text-gray-400 text-sm mb-4 line-clamp-2">
                    {property.description}
                  </p>
                )}
              </div>

              {/* Action Buttons */}
               <div className={`flex gap-2 mt-4 ${
                 viewMode === 'list' ? 'sm:flex-col sm:w-32 sm:flex-shrink-0' : ''
               }`}>
                 <button
                   onClick={() => setSelectedProperty(property)}
                   className="flex-1 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white py-2 px-3 rounded-lg font-medium transition-all duration-200 text-sm hover:shadow-md hover-lift click-shrink"
                 >
                   View Details
                 </button>
                 <button
                   onClick={() => handleViewProperty(property)}
                   className="flex-1 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 py-2 px-3 rounded-lg font-medium transition-all duration-200 text-sm hover-lift click-shrink"
                 >
                   Edit
                 </button>
                 <button
                   onClick={() => {
                     setPropertyToDelete(property.id);
                     setShowDeleteModal(true);
                   }}
                   className="bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 py-2 px-3 rounded-lg font-medium transition-all duration-200 text-sm"
                 >
                   <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                   </svg>
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
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-xl font-semibold flex items-center space-x-2 mx-auto transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] hover-lift click-shrink"
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
                 <img
                   src={selectedProperty.image}
                   alt={selectedProperty.title}
                   className="w-full h-full object-cover"
                   onError={(e) => {
                     e.currentTarget.style.display = 'none'
                     const nextElement = e.currentTarget.nextElementSibling as HTMLElement;
                     if (nextElement) nextElement.style.display = 'flex';
                   }}
                 />
                 <div className="w-full h-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center" style={{display: 'none'}}>
                   <svg className="w-20 h-20 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                   </svg>
                 </div>
                 <div className="absolute top-4 left-4">
                   <span className={`px-3 py-1.5 rounded-full text-sm font-semibold backdrop-blur-sm ${getStatusColor(selectedProperty.status)}`}>
                     {selectedProperty.status === 'for-sale' ? 'For Sale' : 
                      selectedProperty.status === 'for-rent' ? 'For Rent' : 
                      selectedProperty.status.charAt(0).toUpperCase() + selectedProperty.status.slice(1)}
                   </span>
                 </div>
                 <div className="absolute top-4 right-4">
                   <span className="text-2xl font-bold text-white bg-black/30 backdrop-blur-sm px-4 py-2 rounded-lg">
                     {formatPrice(selectedProperty.price)}
                   </span>
                 </div>
               </div>
               
               <div className="p-6">
                 {/* Property Stats */}
                 <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                   <div className="bg-gray-50 dark:bg-slate-700 rounded-xl p-4 text-center">
                     <div className="text-2xl font-bold text-gray-900 dark:text-white">{selectedProperty.bedrooms}</div>
                     <div className="text-sm text-gray-600 dark:text-gray-400">Bedrooms</div>
                   </div>
                   <div className="bg-gray-50 dark:bg-slate-700 rounded-xl p-4 text-center">
                     <div className="text-2xl font-bold text-gray-900 dark:text-white">{selectedProperty.bathrooms}</div>
                     <div className="text-sm text-gray-600 dark:text-gray-400">Bathrooms</div>
                   </div>
                   <div className="bg-gray-50 dark:bg-slate-700 rounded-xl p-4 text-center">
                     <div className="text-2xl font-bold text-gray-900 dark:text-white">{selectedProperty.area}</div>
                     <div className="text-sm text-gray-600 dark:text-gray-400">Sq Ft</div>
                   </div>
                   <div className="bg-gray-50 dark:bg-slate-700 rounded-xl p-4 text-center">
                     <div className="text-lg font-bold text-gray-900 dark:text-white">{selectedProperty.type}</div>
                     <div className="text-sm text-gray-600 dark:text-gray-400">Type</div>
                   </div>
                 </div>
                 
                 {/* Description */}
                 {selectedProperty.description && (
                   <div className="mb-6">
                     <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Description</h4>
                     <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{selectedProperty.description}</p>
                   </div>
                 )}
                 
                 {/* Property Details */}
                 <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
                   <div>
                     <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Property Details</h4>
                     <div className="space-y-3">
                       <div className="flex justify-between">
                         <span className="text-gray-600 dark:text-gray-400">Property Type:</span>
                         <span className="text-gray-900 dark:text-white font-medium">{selectedProperty.type}</span>
                       </div>
                       <div className="flex justify-between">
                         <span className="text-gray-600 dark:text-gray-400">Status:</span>
                         <span className="text-gray-900 dark:text-white font-medium">
                           {selectedProperty.status === 'for-sale' ? 'For Sale' : 
                            selectedProperty.status === 'for-rent' ? 'For Rent' : 
                            selectedProperty.status.charAt(0).toUpperCase() + selectedProperty.status.slice(1)}
                         </span>
                       </div>
                       <div className="flex justify-between">
                         <span className="text-gray-600 dark:text-gray-400">Date Added:</span>
                         <span className="text-gray-900 dark:text-white font-medium">{new Date(selectedProperty.dateAdded).toLocaleDateString()}</span>
                       </div>
                     </div>
                   </div>
                   
                   <div>
                     <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Location</h4>
                     <div className="space-y-3">
                       <div className="flex items-start gap-2">
                         <MapPinIcon className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                         <span className="text-gray-600 dark:text-gray-400">{selectedProperty.address}</span>
                       </div>
                     </div>
                   </div>
                 </div>
               </div>
             </div>
             
             {/* Modal Footer */}
             <div className="flex flex-col sm:flex-row gap-3 p-6 border-t border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-700/50">
               <button
                 onClick={() => {
                   setSelectedProperty(null)
                   handleEditProperty(selectedProperty)
                 }}
                 className="flex-1 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white py-3 px-6 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center gap-2"
               >
                 <PencilIcon className="w-5 h-5" />
                 Edit Property
               </button>
               <button
                 onClick={() => {
                   setSelectedProperty(null)
                   handleDeleteProperty(selectedProperty.id)
                 }}
                 className="bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700 text-white py-3 px-6 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center gap-2"
               >
                 <TrashIcon className="w-5 h-5" />
                 Delete
               </button>
               <button
                 onClick={() => setSelectedProperty(null)}
                 className="bg-gray-200 dark:bg-slate-600 hover:bg-gray-300 dark:hover:bg-slate-500 text-gray-700 dark:text-gray-300 py-3 px-6 rounded-xl font-semibold transition-all duration-200"
               >
                 Close
               </button>
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
             className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full"
           >
             <div className="p-6">
               <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-red-100 dark:bg-red-900/20 rounded-full">
                 <TrashIcon className="w-8 h-8 text-red-600 dark:text-red-400" />
               </div>
               <h3 className="text-xl font-bold text-gray-900 dark:text-white text-center mb-2">Delete Property</h3>
               <p className="text-gray-600 dark:text-gray-400 text-center mb-6">
                 Are you sure you want to delete this property? This action cannot be undone and all associated data will be permanently removed.
               </p>
               <div className="flex flex-col sm:flex-row gap-3">
                 <button
                   onClick={() => setShowDeleteModal(false)}
                   className="flex-1 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 py-3 px-4 rounded-xl font-semibold transition-all duration-200"
                 >
                   Cancel
                 </button>
                 <button
                   onClick={confirmDelete}
                   className="flex-1 bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700 text-white py-3 px-4 rounded-xl font-semibold transition-all duration-200"
                 >
                   Delete Property
                 </button>
               </div>
             </div>
           </motion.div>
         </div>
       )}
    </div>
  )
}