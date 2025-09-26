'use client'

import AgentNavigation from '@/components/AgentNavigation'
import { initializeBrandTheme } from '@/lib/theme'
import {
  BuildingOfficeIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  EyeIcon,
  HeartIcon,
  HomeIcon,
  MapPinIcon,
  PhoneIcon,
  ShareIcon
} from '@heroicons/react/24/outline'
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid'
import { motion } from 'framer-motion'
import Image from 'next/image'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { toast } from 'react-hot-toast'

import { API_BASE_URL } from '@/lib/config/api'

interface AgentProfile {
  id: string
  agent_name: string
  slug: string
  bio: string
  photo: string
  phone: string
  email: string
  office_address: string
  specialties: string[]
  experience: string
  languages: string[]
  view_count: number
  contact_count: number
}

interface PropertyPost {
  id: string
  title: string
  content: string
  property_id?: string
  property_title?: string
  property_description?: string
  property_price?: number
  property_location?: string
  property_bedrooms?: number
  property_bathrooms?: number
  property_area?: number
  property_type?: string
  property_images?: string[]
  language: string
  channels: string[]
  status: string
  created_at: string
  view_count?: number
  like_count?: number
  share_count?: number
  comment_count?: number
}

interface AgentPublicPageProps {
  params: {
    agentName: string
  }
}

export default function AgentPublicPage({ params }: AgentPublicPageProps) {
  const [agent, setAgent] = useState<AgentProfile | null>(null)
  const [propertyPosts, setPropertyPosts] = useState<PropertyPost[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [favorites, setFavorites] = useState<Set<string>>(new Set())

  useEffect(() => {
    // Initialize brand theme
    initializeBrandTheme()
    loadAgentData()
  }, [params.agentName])

  const loadAgentData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Load agent profile
      const agentResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}`)
      if (!agentResponse.ok) {
        throw new Error('Agent not found')
      }
      const agentData = await agentResponse.json()
      console.log('Agent data loaded:', agentData) // Debug log
      setAgent(agentData)

      // Apply branding if available
      if (agentData.branding_data && agentData.branding_data.brand_theme) {
        console.log('Applying agent branding:', agentData.branding_data.brand_theme)
        const { applyBrandTheme } = await import('@/lib/theme')
        applyBrandTheme(agentData.branding_data.brand_theme, false) // Don't persist, just apply for this session
      }

      // Use properties directly from agent data (they include images)
      if (agentData.properties && agentData.properties.length > 0) {
        // Transform properties to match PropertyPost interface for display
        const transformedProperties = agentData.properties.map((property: any) => ({
          id: property.id,
          title: property.title,
          content: property.description,
          property_id: property.id,
          property_title: property.title,
          property_description: property.description,
          property_price: property.price,
          property_location: property.location,
          property_bedrooms: property.bedrooms,
          property_bathrooms: property.bathrooms,
          property_area: property.area,
          property_type: property.property_type,
          property_images: property.images, // This is the key field with images!
          language: 'en',
          channels: ['website'],
          status: 'published',
          created_at: property.created_at,
          view_count: property.view_count || 0,
          like_count: 0,
          share_count: 0,
          comment_count: 0
        }))
        setPropertyPosts(transformedProperties)
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agent data')
      toast.error('Failed to load agent profile')
    } finally {
      setIsLoading(false)
    }
  }

  const handleContactClick = () => {
    // Track contact button click
    if (agent) {
      fetch(`${API_BASE_URL}/api/v1/agent/public/${agent.slug}/track-contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'contact_button_click' })
      })
    }
  }

  const handleFavorite = (postId: string) => {
    setFavorites(prev => {
      const newSet = new Set(prev)
      if (newSet.has(postId)) {
        newSet.delete(postId)
      } else {
        newSet.add(postId)
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
    try {
      // Handle backend date format with microseconds
      let cleanDateString = dateString

      // If the date string has microseconds but no timezone, add UTC timezone
      if (dateString.includes('.') && !dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
        // Remove microseconds and add Z for proper ISO parsing
        const parts = dateString.split('.')
        if (parts.length === 2) {
          // Keep only the first 6 digits of microseconds (milliseconds)
          const microseconds = parts[1].substring(0, 6)
          cleanDateString = parts[0] + '.' + microseconds + 'Z'
        }
      }

      const date = new Date(cleanDateString)

      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.error('Invalid date:', dateString, 'cleaned:', cleanDateString)
        return 'Invalid Date'
      }

      const now = new Date()
      const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

      if (diffInDays === 0) return 'Today'
      if (diffInDays === 1) return 'Yesterday'
      if (diffInDays < 7) return `${diffInDays} days ago`
      return date.toLocaleDateString()
    } catch (error) {
      console.error('Date formatting error:', error, 'for date:', dateString)
      return 'Invalid Date'
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading agent profile...</p>
        </div>
      </div>
    )
  }

  if (error || !agent) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Agent Not Found</h1>
          <p className="text-gray-600 mb-6">The agent profile you're looking for doesn't exist or is not public.</p>
          <Link
            href="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* New Agent Navigation */}
      <AgentNavigation agent={agent || { agent_name: 'Agent', slug: params.agentName }} />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row items-center justify-between">
            <div className="lg:w-2/3 mb-8 lg:mb-0">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <div className="flex items-center space-x-4 mb-6">
                  <div className="w-20 h-20 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-2xl">
                      {agent?.agent_name?.charAt(0) || 'A'}
                    </span>
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                      {agent?.agent_name || 'Real Estate Agent'}
                    </h1>
                    <p className="text-xl text-gray-600">Your Trusted Real Estate Professional</p>
                  </div>
                </div>

                <p className="text-lg text-gray-700 mb-8 max-w-2xl">
                  {agent?.bio || 'Dedicated to helping you find your perfect property. Browse my latest listings and get in touch to start your real estate journey.'}
                </p>

                <div className="flex flex-col sm:flex-row gap-4">
                  <Link
                    href={`/agent/${params.agentName}/properties`}
                    className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium text-center"
                  >
                    <BuildingOfficeIcon className="w-5 h-5 inline mr-2" />
                    View Properties
                  </Link>
                  <Link
                    href={`/agent/${params.agentName}/posts`}
                    className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium text-center"
                  >
                    <DocumentTextIcon className="w-5 h-5 inline mr-2" />
                    Read Posts
                  </Link>
                  <Link
                    href={`/agent/${params.agentName}/contact`}
                    onClick={handleContactClick}
                    className="bg-white text-blue-600 border-2 border-blue-600 px-8 py-3 rounded-lg hover:bg-blue-50 transition-colors font-medium text-center"
                  >
                    <PhoneIcon className="w-5 h-5 inline mr-2" />
                    Contact Me
                  </Link>
                </div>
              </motion.div>
            </div>

            {/* Agent Stats */}
            <div className="lg:w-1/3">
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="bg-white rounded-xl shadow-lg p-6"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Statistics</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Profile Views</span>
                    <span className="font-semibold text-blue-600">{agent?.view_count || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Client Contacts</span>
                    <span className="font-semibold text-blue-600">{agent?.contact_count || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Active Listings</span>
                    <span className="font-semibold text-blue-600">{propertyPosts.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Experience</span>
                    <span className="font-semibold text-blue-600">{agent?.experience || 'Professional'}</span>
                  </div>
                </div>
              </motion.div>

              {/* Quick Links */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className="bg-white rounded-xl shadow-lg p-6 mt-6"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Access</h3>
                <div className="space-y-3">
                  <Link
                    href={`/agent/${params.agentName}/properties`}
                    className="flex items-center space-x-3 p-3 rounded-lg hover:bg-blue-50 transition-colors group"
                  >
                    <BuildingOfficeIcon className="w-5 h-5 text-blue-600 group-hover:text-blue-700" />
                    <div>
                      <p className="font-medium text-gray-900">Browse Properties</p>
                      <p className="text-sm text-gray-500">View all available listings</p>
                    </div>
                  </Link>
                  <Link
                    href={`/agent/${params.agentName}/posts`}
                    className="flex items-center space-x-3 p-3 rounded-lg hover:bg-green-50 transition-colors group"
                  >
                    <DocumentTextIcon className="w-5 h-5 text-green-600 group-hover:text-green-700" />
                    <div>
                      <p className="font-medium text-gray-900">Read Latest Posts</p>
                      <p className="text-sm text-gray-500">Stay updated with market insights</p>
                    </div>
                  </Link>
                  <Link
                    href={`/agent/${params.agentName}/contact`}
                    className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors group"
                  >
                    <PhoneIcon className="w-5 h-5 text-gray-600 group-hover:text-gray-700" />
                    <div>
                      <p className="font-medium text-gray-900">Get In Touch</p>
                      <p className="text-sm text-gray-500">Contact for inquiries</p>
                    </div>
                  </Link>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Property Listings Section */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Featured Properties</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Discover exceptional properties curated by {agent?.agent_name || 'our agent'}. Each listing represents quality, value, and opportunity.
            </p>
          </div>

          {propertyPosts.length === 0 ? (
            <div className="text-center py-16">
              <HomeIcon className="w-20 h-20 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-gray-900 mb-2">No Properties Available</h3>
              <p className="text-gray-500 mb-6">This agent hasn't posted any properties yet.</p>
              <Link
                href={`/agent/${params.agentName}/contact`}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Contact for Upcoming Listings
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {propertyPosts.map((post, index) => (
                <motion.div
                  key={post.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl hover:scale-105 transition-all duration-300 cursor-pointer"
                  onClick={() => window.location.href = `/agent/${params.agentName}/properties/${post.property_id}`}
                  title="Click to view full property details"
                >
                  {/* Property Images */}
                  <div className="relative aspect-video">
                    {post.property_images && post.property_images.length > 0 ? (
                      <Image
                        src={post.property_images[0]}
                        alt={post.property_title || post.title}
                        fill
                        className="object-cover"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                      />
                    ) : (
                      <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                        <HomeIcon className="w-16 h-16 text-gray-400" />
                      </div>
                    )}

                    {/* Favorite Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleFavorite(post.id)
                      }}
                      className="absolute top-3 right-3 p-2 bg-white/90 rounded-full hover:bg-white transition-colors"
                    >
                      {favorites.has(post.id) ? (
                        <HeartSolidIcon className="w-5 h-5 text-red-500" />
                      ) : (
                        <HeartIcon className="w-5 h-5 text-gray-600" />
                      )}
                    </button>

                    {/* Image Count */}
                    {post.property_images && post.property_images.length > 1 && (
                      <div className="absolute bottom-3 right-3 bg-black/70 text-white text-xs px-2 py-1 rounded-full">
                        +{post.property_images.length - 1} more
                      </div>
                    )}
                  </div>

                  {/* Property Details */}
                  <div className="p-6">
                    {/* Price */}
                    <div className="text-2xl font-bold text-green-600 mb-3">
                      {post.property_price ? formatPrice(post.property_price) : 'Price on request'}
                    </div>

                    {/* Title */}
                    <h3 className="text-xl font-semibold text-gray-900 mb-2 line-clamp-1">
                      {post.property_title || post.title}
                    </h3>

                    {/* Location */}
                    <div className="flex items-center text-gray-600 mb-4">
                      <MapPinIcon className="w-4 h-4 mr-2" />
                      <span className="text-sm">{post.property_location || 'Location available on request'}</span>
                    </div>

                    {/* Property Features */}
                    <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
                      <div className="flex items-center space-x-4">
                        {post.property_bedrooms && (
                          <div className="flex items-center">
                            <HomeIcon className="w-4 h-4 mr-1" />
                            <span>{post.property_bedrooms} bed</span>
                          </div>
                        )}
                        {post.property_bathrooms && (
                          <div className="flex items-center">
                            <HomeIcon className="w-4 h-4 mr-1" />
                            <span>{post.property_bathrooms} bath</span>
                          </div>
                        )}
                        {post.property_area && (
                          <div className="flex items-center">
                            <HomeIcon className="w-4 h-4 mr-1" />
                            <span>{post.property_area.toLocaleString()} sq ft</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Property Type */}
                    {post.property_type && (
                      <div className="mb-4">
                        <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                          {post.property_type}
                        </span>
                      </div>
                    )}

                    {/* Marketing Content */}
                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {post.content || post.property_description || 'Contact agent for more details'}
                    </p>

                    {/* Post Stats & Actions */}
                    <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <div className="flex items-center">
                          <EyeIcon className="w-4 h-4 mr-1" />
                          <span>{post.view_count || 0}</span>
                        </div>
                        <div className="flex items-center">
                          <HeartIcon className="w-4 h-4 mr-1" />
                          <span>{post.like_count || 0}</span>
                        </div>
                        <span>{formatDate(post.created_at)}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={(e) => e.stopPropagation()}
                          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <ShareIcon className="w-4 h-4" />
                        </button>
                        <Link
                          href={`/agent/${params.agentName}/contact?property=${post.property_id}`}
                          onClick={(e) => {
                            e.stopPropagation()
                            handleContactClick()
                          }}
                          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                        >
                          Inquire
                        </Link>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {/* View All Properties Link */}
          {propertyPosts.length > 0 && (
            <div className="text-center mt-12">
              <Link
                href={`/agent/${params.agentName}/properties`}
                className="inline-flex items-center px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-medium"
              >
                View All Properties
                <svg className="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Latest Posts Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Latest Market Insights</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Stay informed with the latest real estate trends, market updates, and property insights from {agent?.agent_name || 'our expert agent'}.
            </p>
          </div>

          {/* Posts will be loaded here */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Placeholder for posts - will be populated by AgentProfile component */}
            <div className="text-center py-16 col-span-full">
              <DocumentTextIcon className="w-20 h-20 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-gray-900 mb-2">Posts Loading...</h3>
              <p className="text-gray-500 mb-6">Latest market insights will appear here.</p>
              <Link
                href={`/agent/${params.agentName}/posts`}
                className="inline-flex items-center px-6 py-3 border border-green-600 text-green-600 rounded-lg hover:bg-green-50 transition-colors font-medium"
              >
                View All Posts
                <svg className="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Contact CTA Section */}
      <section className="bg-blue-600 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to Find Your Dream Property?
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Get in touch with {agent?.agent_name || 'our agent'} today for personalized assistance
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href={`/agent/${params.agentName}/contact`}
                onClick={handleContactClick}
                className="bg-white text-blue-600 px-8 py-3 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                <PhoneIcon className="w-5 h-5 inline mr-2" />
                Contact Now
              </Link>
              {agent?.email && (
                <a
                  href={`mailto:${agent.email}`}
                  className="bg-blue-700 text-white px-8 py-3 rounded-lg hover:bg-blue-800 transition-colors font-medium"
                >
                  <EnvelopeIcon className="w-5 h-5 inline mr-2" />
                  Send Email
                </a>
              )}
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}