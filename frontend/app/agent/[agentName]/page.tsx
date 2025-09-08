'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  UserIcon, 
  PhoneIcon, 
  EnvelopeIcon, 
  MapPinIcon,
  StarIcon,
  EyeIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'
import Link from 'next/link'

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

interface PropertySummary {
  id: string
  title: string
  price: number
  property_type: string
  location: string
  bedrooms: number
  bathrooms: number
  area: number
  images: string[]
}

interface AgentPublicPageProps {
  params: {
    agentName: string
  }
}

export default function AgentPublicPage({ params }: AgentPublicPageProps) {
  const [agent, setAgent] = useState<AgentProfile | null>(null)
  const [properties, setProperties] = useState<PropertySummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAgentData()
  }, [params.agentName])

  const loadAgentData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Load agent profile
      const agentResponse = await fetch(`http://localhost:8000/api/v1/agent-public/${params.agentName}`)
      if (!agentResponse.ok) {
        throw new Error('Agent not found')
      }
      const agentData = await agentResponse.json()
      console.log('Agent data loaded:', agentData) // Debug log
      setAgent(agentData)

      // Load agent's public properties
      const propertiesResponse = await fetch(`http://localhost:8000/api/v1/agent-public/${params.agentName}/properties?limit=6`)
      if (propertiesResponse.ok) {
        const propertiesData = await propertiesResponse.json()
        setProperties(propertiesData.properties || [])
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
      fetch(`http://localhost:8000/api/v1/agent-public/${agent.slug}/track-contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'contact_button_click' })
      })
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
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-xl font-bold text-blue-600">
              PropertyAI
            </Link>
            <div className="flex items-center space-x-4">
              <Link 
                href={`/agent/${agent.slug}/properties`}
                className="text-gray-600 hover:text-gray-900"
              >
                Properties
              </Link>
              <Link 
                href={`/agent/${agent.slug}/contact`}
                className="text-gray-600 hover:text-gray-900"
              >
                Contact
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Agent Profile Section */}
      <section className="bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-8"
          >
            {/* Agent Info */}
            <div className="lg:col-span-2">
              <div className="flex items-start space-x-6">
                <div className="flex-shrink-0">
                  {agent.photo ? (
                    <img
                      src={agent.photo}
                      alt={agent.agent_name}
                      className="w-24 h-24 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center">
                      <UserIcon className="w-12 h-12 text-gray-400" />
                    </div>
                  )}
                </div>
                <div className="flex-1">
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    {agent.agent_name}
                  </h1>
                  <div className="flex items-center space-x-4 text-sm text-gray-600 mb-4">
                    <div className="flex items-center">
                      <EyeIcon className="w-4 h-4 mr-1" />
                      {agent.view_count} profile views
                    </div>
                    <div className="flex items-center">
                      <ChatBubbleLeftRightIcon className="w-4 h-4 mr-1" />
                      {agent.contact_count} inquiries
                    </div>
                  </div>
                  {agent.bio && (
                    <p className="text-gray-700 leading-relaxed mb-6">
                      {agent.bio}
                    </p>
                  )}
                </div>
              </div>

              {/* Specialties */}
              {agent.specialties.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Specialties</h3>
                  <div className="flex flex-wrap gap-2">
                    {agent.specialties.map((specialty, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                      >
                        {specialty}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience & Languages */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                {agent.experience && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Experience</h3>
                    <p className="text-gray-700">{agent.experience}</p>
                  </div>
                )}
                {agent.languages.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Languages</h3>
                    <p className="text-gray-700">{agent.languages.join(', ')}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Contact Card */}
            <div className="lg:col-span-1">
              <div className="bg-gray-50 rounded-lg p-6 sticky top-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
                
                <div className="space-y-4">
                  {agent.phone && (
                    <div className="flex items-center">
                      <PhoneIcon className="w-5 h-5 text-gray-400 mr-3" />
                      <a 
                        href={`tel:${agent.phone}`}
                        className="text-gray-700 hover:text-blue-600"
                      >
                        {agent.phone}
                      </a>
                    </div>
                  )}
                  
                  {agent.email && (
                    <div className="flex items-center">
                      <EnvelopeIcon className="w-5 h-5 text-gray-400 mr-3" />
                      <a 
                        href={`mailto:${agent.email}`}
                        className="text-gray-700 hover:text-blue-600"
                      >
                        {agent.email}
                      </a>
                    </div>
                  )}
                  
                  {agent.office_address && (
                    <div className="flex items-start">
                      <MapPinIcon className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                      <span className="text-gray-700">{agent.office_address}</span>
                    </div>
                  )}
                </div>

                <div className="mt-6 space-y-3">
                  <Link
                    href={`/agent/${agent.slug}/contact`}
                    onClick={handleContactClick}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-center block"
                  >
                    Send Message
                  </Link>
                  <Link
                    href={`/agent/${agent.slug}/properties`}
                    className="w-full border border-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-50 transition-colors text-center block"
                  >
                    View Properties
                  </Link>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Featured Properties */}
      {properties.length > 0 && (
        <section className="bg-gray-50 py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-900">Featured Properties</h2>
              <Link
                href={`/agent/${agent.slug}/properties`}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                View All Properties →
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {properties.map((property) => (
                <motion.div
                  key={property.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow"
                >
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
                    <p className="text-gray-600 text-sm mb-2">{property.location}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-bold text-blue-600">
                        ₹{property.price.toLocaleString()}
                      </span>
                      <span className="text-sm text-gray-500">
                        {property.property_type}
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-gray-500 mt-2">
                      {property.bedrooms > 0 && (
                        <span className="mr-4">{property.bedrooms} bed</span>
                      )}
                      {property.bathrooms > 0 && (
                        <span className="mr-4">{property.bathrooms} bath</span>
                      )}
                      {property.area > 0 && (
                        <span>{property.area} sq ft</span>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  )
}