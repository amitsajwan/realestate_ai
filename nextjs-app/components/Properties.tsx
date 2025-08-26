'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
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
  XMarkIcon
} from '@heroicons/react/24/outline'
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
  const [priceRange, setPriceRange] = useState<{ min: number; max: number }>({ min: 0, max: 1000000 })
  const [bedroomFilter, setBedroomFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('dateAdded')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [propertyToDelete, setPropertyToDelete] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
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
      case 'active': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'sold': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const handleEditProperty = (property: Property) => {
    setSelectedProperty(property)
    // You can implement edit modal or navigate to edit page here
    console.log('Edit property:', property)
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
    console.log('View property:', property)
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Properties</h1>
          <p className="text-gray-300">Manage your property listings</p>
        </div>
        <button
          onClick={onAddProperty}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium flex items-center space-x-2 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          <span>Add Property</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search properties..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="pending">Pending</option>
            <option value="sold">Sold</option>
          </select>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="House">House</option>
            <option value="Condo">Condo</option>
            <option value="Apartment">Apartment</option>
            <option value="Townhouse">Townhouse</option>
          </select>

          <select
            value={bedroomFilter}
            onChange={(e) => setBedroomFilter(e.target.value)}
            className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Bedrooms</option>
            <option value="1">1 Bedroom</option>
            <option value="2">2 Bedrooms</option>
            <option value="3">3 Bedrooms</option>
            <option value="4">4+ Bedrooms</option>
          </select>

          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [sort, order] = e.target.value.split('-')
              setSortBy(sort)
              setSortOrder(order as 'asc' | 'desc')
            }}
            className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
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

        {/* Price Range Filter */}
        <div className="mb-6">
          <label className="block text-white text-sm font-medium mb-2">
            Price Range: ${priceRange.min.toLocaleString()} - ${priceRange.max.toLocaleString()}
          </label>
          <div className="flex items-center space-x-4">
            <input
              type="range"
              min="0"
              max="1000000"
              step="10000"
              value={priceRange.min}
              onChange={(e) => setPriceRange(prev => ({ ...prev, min: parseInt(e.target.value) }))}
              className="flex-1 h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
            />
            <input
              type="range"
              min="0"
              max="1000000"
              step="10000"
              value={priceRange.max}
              onChange={(e) => setPriceRange(prev => ({ ...prev, max: parseInt(e.target.value) }))}
              className="flex-1 h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Properties Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProperties.map((property, index) => (
          <motion.div
            key={property.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            className="bg-white/10 backdrop-blur-lg rounded-xl overflow-hidden border border-white/20 hover:border-white/40 transition-all duration-300"
          >
            {/* Property Image */}
            <div className="relative h-48 bg-gray-700">
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
              <div className="absolute top-4 left-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(property.status)}`}>
                  {property.status.charAt(0).toUpperCase() + property.status.slice(1)}
                </span>
              </div>
              <div className="absolute bottom-4 left-4 text-white">
                <div className="flex items-center space-x-1 text-sm">
                  <span className="bg-black/50 px-2 py-1 rounded text-xs">
                    {property.status.replace('-', ' ').toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {/* Property Details */}
            <div className="p-6">
              <h3 className="text-xl font-semibold text-white mb-2 line-clamp-2">
                {property.title}
              </h3>
              
              <div className="flex items-center text-gray-300 mb-3">
                <MapPinIcon className="w-4 h-4 mr-1" />
                <span className="text-sm">{property.address}</span>
              </div>
              
              <div className="flex items-center text-blue-400 mb-4">
                <CurrencyRupeeIcon className="w-5 h-5 mr-1" />
                <span className="text-2xl font-bold">{formatPrice(property.price)}</span>
              </div>
              
              <div className="flex justify-between text-sm text-gray-300 mb-4">
                <span>{property.bedrooms} BHK</span>
                <span>{property.bathrooms} Bath</span>
                <span>{property.area} sq ft</span>
              </div>
              
              <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                {property.description}
              </p>
              
              {/* Actions */}
              <div className="flex space-x-2">
                <button 
                  onClick={() => handleViewProperty(property)}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center space-x-1"
                >
                  <EyeIcon className="w-4 h-4" />
                  <span>View</span>
                </button>
                <button 
                  onClick={() => handleEditProperty(property)}
                  className="bg-white/10 hover:bg-white/20 text-white py-2 px-3 rounded-lg transition-colors"
                >
                  <PencilIcon className="w-4 h-4" />
                </button>
                <button 
                  onClick={() => handleDeleteProperty(property.id)}
                  className="bg-red-600/20 hover:bg-red-600/30 text-red-400 py-2 px-3 rounded-lg transition-colors"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Empty State */}
      {filteredProperties.length === 0 && (
        <div className="text-center py-12">
          <BuildingOfficeIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No properties found</h3>
          <p className="text-gray-400 mb-6">Try adjusting your search or filters</p>
          <button
            onClick={onAddProperty}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium inline-flex items-center space-x-2 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            <span>Add Your First Property</span>
          </button>
        </div>
      )}

      {/* Property Details Modal */}
       {selectedProperty && (
         <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
           <motion.div
             initial={{ opacity: 0, scale: 0.95 }}
             animate={{ opacity: 1, scale: 1 }}
             exit={{ opacity: 0, scale: 0.95 }}
             className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
           >
             <div className="flex justify-between items-center mb-4">
               <h3 className="text-xl font-semibold text-white">{selectedProperty.title}</h3>
               <button
                 onClick={() => setSelectedProperty(null)}
                 className="text-gray-400 hover:text-white transition-colors"
               >
                 <XMarkIcon className="w-6 h-6" />
               </button>
             </div>
             
             <div className="space-y-4">
               <div className="w-full h-64 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                 <BuildingOfficeIcon className="w-16 h-16 text-white/50" />
               </div>
               
               <div className="grid grid-cols-2 gap-4">
                 <div>
                   <p className="text-gray-400 text-sm">Address</p>
                   <p className="text-white">{selectedProperty.address}</p>
                 </div>
                 <div>
                   <p className="text-gray-400 text-sm">Price</p>
                   <p className="text-white font-semibold">
                     ${selectedProperty.status === 'for-rent'
                       ? `${selectedProperty.price.toLocaleString()}/month`
                       : selectedProperty.price.toLocaleString()}
                   </p>
                 </div>
                 <div>
                   <p className="text-gray-400 text-sm">Type</p>
                   <p className="text-white">{selectedProperty.type}</p>
                 </div>
                 <div>
                   <p className="text-gray-400 text-sm">Status</p>
                   <p className="text-white">{selectedProperty.status}</p>
                 </div>
                 <div>
                   <p className="text-gray-400 text-sm">Bedrooms</p>
                   <p className="text-white">{selectedProperty.bedrooms}</p>
                 </div>
                 <div>
                   <p className="text-gray-400 text-sm">Bathrooms</p>
                   <p className="text-white">{selectedProperty.bathrooms}</p>
                 </div>
                 <div>
                   <p className="text-gray-400 text-sm">Area</p>
                   <p className="text-white">{selectedProperty.area} sq ft</p>
                 </div>
                 <div>
                   <p className="text-gray-400 text-sm">Date Added</p>
                   <p className="text-white">{selectedProperty.dateAdded}</p>
                 </div>
               </div>
               
               {selectedProperty.description && (
                 <div>
                   <p className="text-gray-400 text-sm mb-2">Description</p>
                   <p className="text-white">{selectedProperty.description}</p>
                 </div>
               )}
               
               <div className="flex space-x-3 pt-4">
                 <button
                   onClick={() => {
                     setSelectedProperty(null)
                     handleEditProperty(selectedProperty)
                   }}
                   className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors"
                 >
                   Edit Property
                 </button>
                 <button
                   onClick={() => {
                     setSelectedProperty(null)
                     handleDeleteProperty(selectedProperty.id)
                   }}
                   className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg transition-colors"
                 >
                   Delete
                 </button>
               </div>
             </div>
           </motion.div>
         </div>
       )}

       {/* Delete Confirmation Modal */}
       {showDeleteModal && (
         <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
           <motion.div
             initial={{ opacity: 0, scale: 0.95 }}
             animate={{ opacity: 1, scale: 1 }}
             exit={{ opacity: 0, scale: 0.95 }}
             className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 max-w-md w-full mx-4"
           >
             <div className="flex justify-between items-center mb-4">
               <h3 className="text-xl font-semibold text-white">Delete Property</h3>
               <button
                 onClick={() => setShowDeleteModal(false)}
                 className="text-gray-400 hover:text-white transition-colors"
               >
                 <XMarkIcon className="w-6 h-6" />
               </button>
             </div>
             <p className="text-gray-300 mb-6">
               Are you sure you want to delete this property? This action cannot be undone.
             </p>
             <div className="flex space-x-3">
               <button
                 onClick={() => setShowDeleteModal(false)}
                 className="flex-1 bg-white/10 hover:bg-white/20 text-white py-2 px-4 rounded-lg transition-colors"
               >
                 Cancel
               </button>
               <button
                 onClick={confirmDelete}
                 className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg transition-colors"
               >
                 Delete
               </button>
             </div>
           </motion.div>
         </div>
       )}
    </div>
  )
}