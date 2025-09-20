'use client'

import { MobilePublishingWorkflow } from '@/components/social_publishing/mobile'
import { apiService } from '@/lib/api'
import { propertiesAPI } from '@/lib/properties'
import { PropertyContext } from '@/types/social_publishing'
import {
  ChartBarIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  PlusIcon,
  ShareIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'

interface Property {
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

interface PropertyManagementProps {
  onAddProperty?: () => void
}

export default function PropertyManagement({ onAddProperty }: PropertyManagementProps) {
  const [properties, setProperties] = useState<Property[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'list' | 'mobile-publishing'>('list')
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)

  console.log('[PropertyManagement] Component rendered with properties:', properties.length, properties)

  useEffect(() => {
    loadProperties()
  }, [])

  const loadProperties = async () => {
    try {
      setIsLoading(true)
      console.log('[PropertyManagement] Starting to load properties...')

      const response = await propertiesAPI.getProperties()
      console.log('[PropertyManagement] API response:', response)
      console.log('[PropertyManagement] Response type:', typeof response)
      console.log('[PropertyManagement] Is array:', Array.isArray(response))

      // Handle both direct array response and wrapped response
      const propertiesData = Array.isArray(response) ? response : (response?.data || [])
      console.log('[PropertyManagement] Properties data extracted:', propertiesData)
      console.log('[PropertyManagement] Properties data type:', typeof propertiesData)
      console.log('[PropertyManagement] Properties data length:', propertiesData?.length)

      if (propertiesData && propertiesData.length > 0) {
        console.log('[PropertyManagement] Setting properties state with:', propertiesData.length, 'properties')

        // Normalize incoming property objects to match this component's Property interface
        const normalized: Property[] = propertiesData.map((p: any) => ({
          id: p.id || p._id || String(p.property_id || ''),
          title: p.title || p.name || 'Untitled Property',
          description: p.description || p.desc || '',
          price: Number(p.price) || 0,
          location: p.location || p.address || '',
          bedrooms: Number(p.bedrooms) || 0,
          bathrooms: Number(p.bathrooms) || 0,
          area_sqft: Number(p.area_sqft || p.area || 0),
          property_type: p.property_type || p.type || 'Unknown',
          features: p.features || [],
          amenities: p.amenities || '',
          publishing_status: p.publishing_status || 'draft',
          published_at: p.published_at,
          target_languages: p.target_languages || [],
          publishing_channels: p.publishing_channels || [],
          facebook_page_mappings: p.facebook_page_mappings || {},
          created_at: p.created_at || p.createdAt || new Date().toISOString(),
          updated_at: p.updated_at || p.updatedAt || new Date().toISOString()
        }))

        setProperties(normalized)
        console.log('[PropertyManagement] Properties state set successfully')
      } else {
        console.log('[PropertyManagement] No properties found, setting empty array')
        setProperties([])
      }
    } catch (error) {
      console.error('[PropertyManagement] Error loading properties:', error)
      toast.error('Failed to load properties')
      setProperties([])
    } finally {
      console.log('[PropertyManagement] Setting loading to false')
      setIsLoading(false)
    }
  }

  const handleDeleteProperty = async (propertyId: string) => {
    if (!confirm('Are you sure you want to delete this property?')) return

    try {
      await apiService.deleteProperty(propertyId)
      toast.success('Property deleted successfully')
      loadProperties()
    } catch (error) {
      console.error('Error deleting property:', error)
      toast.error('Failed to delete property')
    }
  }

  // Transform Property data to PropertyContext format for Social Publishing
  const transformPropertiesForSocialPublishing = (properties: Property[]): PropertyContext[] => {
    return properties.map(property => ({
      id: property.id,
      title: property.title,
      description: property.description,
      price: property.price,
      location: property.location,
      propertyType: property.property_type,
      bedrooms: property.bedrooms,
      bathrooms: property.bathrooms,
      areaSqft: property.area_sqft,
      amenities: property.amenities ? property.amenities.split(',').map(a => a.trim()) : [],
      features: property.features || [],
      images: [] // Add image handling if needed
    }))
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800'
      case 'published': return 'bg-green-100 text-green-800'
      case 'archived': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft': return <DocumentTextIcon className="w-4 h-4" />
      case 'published': return <CheckCircleIcon className="w-4 h-4" />
      case 'archived': return <TrashIcon className="w-4 h-4" />
      default: return <DocumentTextIcon className="w-4 h-4" />
    }
  }

  const getStatusCounts = () => {
    const counts = {
      draft: 0,
      published: 0,
      archived: 0,
      total: properties.length
    }

    properties.forEach(property => {
      counts[property.publishing_status as keyof typeof counts]++
    })

    return counts
  }

  const statusCounts = getStatusCounts()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Property Management
            </h1>
            <p className="text-gray-600">
              Manage your property listings with modern publishing workflow
            </p>
          </div>
          <button
            onClick={onAddProperty}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <PlusIcon className="w-5 h-5" />
            Add Property
          </button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-gray-100 rounded-lg">
              <DocumentTextIcon className="w-6 h-6 text-gray-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Draft</p>
              <p className="text-2xl font-bold text-gray-900">{statusCounts.draft}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircleIcon className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Published</p>
              <p className="text-2xl font-bold text-gray-900">{statusCounts.published}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <TrashIcon className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Archived</p>
              <p className="text-2xl font-bold text-gray-900">{statusCounts.archived}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total</p>
              <p className="text-2xl font-bold text-gray-900">{statusCounts.total}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('list')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'list'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              Property List
            </button>
            <button
              onClick={() => setActiveTab('mobile-publishing')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'mobile-publishing'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              📱 Social Publishing
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'list' ? (
          <motion.div
            key="list"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {/* Properties List */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              {properties.length === 0 ? (
                <div className="p-12 text-center">
                  <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Properties Found
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Get started by adding your first property listing
                  </p>
                  <button
                    onClick={onAddProperty}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 mx-auto"
                  >
                    <PlusIcon className="w-5 h-5" />
                    Add Property
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Property
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Price
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Published
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {properties.map((property) => (
                        <tr key={property.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {property.title}
                              </div>
                              <div className="text-sm text-gray-500">
                                {property.location}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              ₹{property.price.toLocaleString()}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${getStatusColor(property.publishing_status)}`}>
                              {getStatusIcon(property.publishing_status)}
                              {property.publishing_status}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {property.published_at
                              ? new Date(property.published_at).toLocaleDateString()
                              : 'Not published'
                            }
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => {
                                  setSelectedProperty(property)
                                  setActiveTab('mobile-publishing')
                                }}
                                className="text-blue-600 hover:text-blue-900"
                                title="Open Social Media Publishing"
                              >
                                <ShareIcon className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteProperty(property.id)}
                                className="text-red-600 hover:text-red-900"
                              >
                                <TrashIcon className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="mobile-publishing"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            <MobilePublishingWorkflow
              properties={transformPropertiesForSocialPublishing(properties)}
              onRefresh={loadProperties}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}