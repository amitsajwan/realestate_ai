'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  DocumentTextIcon,
  GlobeAltIcon,
  ShareIcon,
  CheckCircleIcon,
  ClockIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  LanguageIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'
import { apiService } from '@/lib/api'
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

interface PublishingStatus {
  property_id: string
  publishing_status: string
  published_at?: string
  published_channels: string[]
  language_status: Record<string, string>
  facebook_posts: Record<string, string>
  analytics_data: Record<string, any>
}

interface LanguagePreference {
  language_code: string
  is_primary: boolean
  facebook_page_id?: string
}

interface ModernPublishingWorkflowProps {
  properties: Property[]
  onRefresh: () => void
}

const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'mr', name: 'Marathi', flag: '🇮🇳' },
  { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
  { code: 'gu', name: 'Gujarati', flag: '🇮🇳' },
  { code: 'ta', name: 'Tamil', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali', flag: '🇮🇳' },
  { code: 'pa', name: 'Punjabi', flag: '🇮🇳' },
  { code: 'kn', name: 'Kannada', flag: '🇮🇳' },
  { code: 'ml', name: 'Malayalam', flag: '🇮🇳' }
]

const SUPPORTED_CHANNELS = [
  { id: 'website', name: 'Website', icon: '🌐', description: 'Public agent website' },
  { id: 'facebook', name: 'Facebook', icon: '📘', description: 'Facebook page posts' },
  { id: 'instagram', name: 'Instagram', icon: '📷', description: 'Instagram posts (coming soon)' },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', description: 'LinkedIn posts (coming soon)' }
]

export default function ModernPublishingWorkflow({ properties, onRefresh }: ModernPublishingWorkflowProps) {
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)
  const [publishingStatus, setPublishingStatus] = useState<PublishingStatus | null>(null)
  const [languagePreferences, setLanguagePreferences] = useState<LanguagePreference[]>([])
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(['en'])
  const [selectedChannels, setSelectedChannels] = useState<string[]>(['website'])
  const [facebookPageMappings, setFacebookPageMappings] = useState<Record<string, string>>({})
  const [isPublishing, setIsPublishing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Load language preferences on component mount
  useEffect(() => {
    loadLanguagePreferences()
  }, [])

  const loadLanguagePreferences = async () => {
    try {
      setIsLoading(true)
      // This would be implemented when we have the user context
      // const response = await apiService.get('/publishing/agents/{agent_id}/language-preferences')
      // setLanguagePreferences(response.data.preferences)
      
      // For now, set default preferences
      setLanguagePreferences([
        { language_code: 'en', is_primary: true, facebook_page_id: 'facebook_page_english' },
        { language_code: 'mr', is_primary: false, facebook_page_id: 'facebook_page_marathi' },
        { language_code: 'hi', is_primary: false, facebook_page_id: 'facebook_page_hindi' }
      ])
    } catch (error) {
      console.error('Error loading language preferences:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadPublishingStatus = async (propertyId: string) => {
    try {
      setIsLoading(true)
      const response = await apiService.get(`/publishing/properties/${propertyId}/status`)
      setPublishingStatus(response.data)
    } catch (error) {
      console.error('Error loading publishing status:', error)
      toast.error('Failed to load publishing status')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePropertySelect = (property: Property) => {
    setSelectedProperty(property)
    loadPublishingStatus(property.id)
  }

  const handlePublish = async () => {
    if (!selectedProperty) return

    try {
      setIsPublishing(true)
      
      const publishingRequest = {
        property_id: selectedProperty.id,
        target_languages: selectedLanguages,
        publishing_channels: selectedChannels,
        facebook_page_mappings: facebookPageMappings,
        auto_translate: true
      }

      const response = await apiService.post(
        `/publishing/properties/${selectedProperty.id}/publish`,
        publishingRequest
      )

      if (response.status === 200) {
        toast.success('Property published successfully!')
        setPublishingStatus(response.data)
        onRefresh()
      }
    } catch (error) {
      console.error('Error publishing property:', error)
      toast.error('Failed to publish property')
    } finally {
      setIsPublishing(false)
    }
  }

  const handleUnpublish = async () => {
    if (!selectedProperty) return

    try {
      setIsPublishing(true)
      
      const response = await apiService.post(
        `/publishing/properties/${selectedProperty.id}/unpublish`,
        {}
      )

      if (response.status === 200) {
        toast.success('Property unpublished successfully!')
        setPublishingStatus(response.data)
        onRefresh()
      }
    } catch (error) {
      console.error('Error unpublishing property:', error)
      toast.error('Failed to unpublish property')
    } finally {
      setIsPublishing(false)
    }
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

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Modern Publishing Workflow
        </h1>
        <p className="text-gray-600">
          Manage your property listings with our modern Draft → Publish → Promote workflow
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Properties List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Your Properties
            </h2>
            <div className="space-y-3">
              {properties.map((property) => (
                <motion.div
                  key={property.id}
                  whileHover={{ scale: 1.02 }}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedProperty?.id === property.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handlePropertySelect(property)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 text-sm">
                        {property.title}
                      </h3>
                      <p className="text-gray-600 text-xs mt-1">
                        ₹{property.price.toLocaleString()}
                      </p>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs flex items-center gap-1 ${getStatusColor(property.publishing_status)}`}>
                      {getStatusIcon(property.publishing_status)}
                      {property.publishing_status}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* Publishing Controls */}
        <div className="lg:col-span-2">
          {selectedProperty ? (
            <div className="space-y-6">
              {/* Property Details */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Property Details
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Title</label>
                    <p className="text-gray-900">{selectedProperty.title}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Price</label>
                    <p className="text-gray-900">₹{selectedProperty.price.toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Location</label>
                    <p className="text-gray-900">{selectedProperty.location}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Status</label>
                    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${getStatusColor(selectedProperty.publishing_status)}`}>
                      {getStatusIcon(selectedProperty.publishing_status)}
                      {selectedProperty.publishing_status}
                    </div>
                  </div>
                </div>
              </div>

              {/* Publishing Status */}
              {publishingStatus && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    Publishing Status
                  </h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Status</label>
                      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${getStatusColor(publishingStatus.publishing_status)}`}>
                        {getStatusIcon(publishingStatus.publishing_status)}
                        {publishingStatus.publishing_status}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Published At</label>
                      <p className="text-gray-900">
                        {publishingStatus.published_at 
                          ? new Date(publishingStatus.published_at).toLocaleString()
                          : 'Not published'
                        }
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Channels</label>
                      <div className="flex flex-wrap gap-1">
                        {publishingStatus.published_channels.map((channel) => (
                          <span key={channel} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                            {channel}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Languages</label>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(publishingStatus.language_status).map(([lang, status]) => (
                          <span key={lang} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            {lang}: {status}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Publishing Controls */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Publishing Controls
                </h2>
                
                {/* Language Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Languages
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {SUPPORTED_LANGUAGES.map((lang) => (
                      <label key={lang.code} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={selectedLanguages.includes(lang.code)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedLanguages([...selectedLanguages, lang.code])
                            } else {
                              setSelectedLanguages(selectedLanguages.filter(l => l !== lang.code))
                            }
                          }}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm text-gray-700">
                          {lang.flag} {lang.name}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Channel Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Publishing Channels
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {SUPPORTED_CHANNELS.map((channel) => (
                      <label key={channel.id} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={selectedChannels.includes(channel.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedChannels([...selectedChannels, channel.id])
                            } else {
                              setSelectedChannels(selectedChannels.filter(c => c !== channel.id))
                            }
                          }}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm text-gray-700">
                          {channel.icon} {channel.name}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                  {selectedProperty.publishing_status === 'draft' ? (
                    <button
                      onClick={handlePublish}
                      disabled={isPublishing || selectedLanguages.length === 0 || selectedChannels.length === 0}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <SparklesIcon className="w-4 h-4" />
                      {isPublishing ? 'Publishing...' : 'Publish Property'}
                    </button>
                  ) : (
                    <button
                      onClick={handleUnpublish}
                      disabled={isPublishing}
                      className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <TrashIcon className="w-4 h-4" />
                      {isPublishing ? 'Unpublishing...' : 'Unpublish Property'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select a Property
              </h3>
              <p className="text-gray-600">
                Choose a property from the list to manage its publishing status
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}