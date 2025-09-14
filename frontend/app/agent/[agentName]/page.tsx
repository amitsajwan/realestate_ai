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
      const agentResponse = await fetch(`http://localhost:8000/api/v1/agent/public/agent-public/${params.agentName}`)
      if (!agentResponse.ok) {
        throw new Error('Agent not found')
      }
      const agentData = await agentResponse.json()
      console.log('Agent data loaded:', agentData) // Debug log
      setAgent(agentData)

      // Load agent's public properties
      const propertiesResponse = await fetch(`http://localhost:8000/api/v1/agent/public/agent-public/${params.agentName}/properties?limit=6`)
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
      fetch(`http://localhost:8000/api/v1/agent/public/agent-public/${agent.slug}/track-contact`, {
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Modern Header */}
      <header className="bg-white/95 backdrop-blur-lg shadow-lg border-b border-gray-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3 group">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform">
                <UserIcon className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                PropertyAI
              </span>
            </Link>
            <nav className="hidden md:flex items-center space-x-8">
              <Link 
                href={`/agent/${agent.slug}/properties`}
                className="text-gray-600 hover:text-blue-600 font-medium transition-colors relative group"
              >
                Properties
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-600 group-hover:w-full transition-all duration-300"></span>
              </Link>
              <Link 
                href={`/agent/${agent.slug}/contact`}
                className="text-gray-600 hover:text-blue-600 font-medium transition-colors relative group"
              >
                Contact
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-600 group-hover:w-full transition-all duration-300"></span>
              </Link>
              <Link
                href={`/agent/${agent.slug}/contact`}
                onClick={handleContactClick}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2 rounded-full hover:shadow-lg hover:scale-105 transition-all duration-200 font-medium"
              >
                Get Started
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-indigo-600/10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <div className="inline-flex items-center justify-center w-32 h-32 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full shadow-2xl mb-8 relative">
              {agent.photo ? (
                <img
                  src={agent.photo}
                  alt={agent.agent_name}
                  className="w-28 h-28 rounded-full object-cover border-4 border-white"
                />
              ) : (
                <div className="w-28 h-28 bg-white/20 rounded-full flex items-center justify-center">
                  <UserIcon className="w-16 h-16 text-white" />
                </div>
              )}
              <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-green-500 rounded-full border-4 border-white flex items-center justify-center">
                <div className="w-3 h-3 bg-white rounded-full"></div>
              </div>
            </div>
            
            <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-purple-900 bg-clip-text text-transparent mb-4">
              {agent.agent_name}
            </h1>
            
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              {agent.bio || "Professional Real Estate Agent helping you find your dream property"}
            </p>
            
            <div className="flex flex-wrap items-center justify-center gap-6 mb-12">
              <div className="flex items-center bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 shadow-lg">
                <EyeIcon className="w-5 h-5 text-blue-600 mr-2" />
                <span className="font-semibold text-gray-700">{agent.view_count} Profile Views</span>
              </div>
              <div className="flex items-center bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 shadow-lg">
                <ChatBubbleLeftRightIcon className="w-5 h-5 text-green-600 mr-2" />
                <span className="font-semibold text-gray-700">{agent.contact_count} Happy Clients</span>
              </div>
              <div className="flex items-center bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 shadow-lg">
                <StarIcon className="w-5 h-5 text-yellow-500 mr-2" />
                <span className="font-semibold text-gray-700">5.0 ⭐ Rating</span>
              </div>
            </div>
            
            <div className="flex flex-wrap justify-center gap-4">
              <Link
                href={`/agent/${agent.slug}/contact`}
                onClick={handleContactClick}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-full hover:shadow-xl hover:scale-105 transition-all duration-200 font-semibold text-lg"
              >
                Get In Touch
              </Link>
              <Link
                href={`/agent/${agent.slug}/properties`}
                className="bg-white text-gray-700 px-8 py-4 rounded-full hover:shadow-xl hover:scale-105 transition-all duration-200 font-semibold text-lg border-2 border-gray-200"
              >
                View Properties
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Agent Details Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-12"
          >
            {/* Agent Info */}
            <div className="lg:col-span-2 space-y-8">

              {/* Specialties */}
              {agent.specialties.length > 0 && (
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                    <SparklesIcon className="w-6 h-6 text-blue-600 mr-3" />
                    Specialties
                  </h3>
                  <div className="flex flex-wrap gap-3">
                    {agent.specialties.map((specialty, index) => (
                      <motion.span
                        key={index}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1 }}
                        className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full text-sm font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
                      >
                        {specialty}
                      </motion.span>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience & Languages */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {agent.experience && (
                  <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
                    <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                      <StarIcon className="w-6 h-6 text-yellow-500 mr-3" />
                      Experience
                    </h3>
                    <p className="text-gray-700 text-lg leading-relaxed">{agent.experience}</p>
                  </div>
                )}
                {agent.languages.length > 0 && (
                  <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
                    <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                      <ChatBubbleLeftRightIcon className="w-6 h-6 text-green-500 mr-3" />
                      Languages
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {agent.languages.map((language, index) => (
                        <span
                          key={index}
                          className="px-4 py-2 bg-green-100 text-green-800 rounded-lg text-sm font-medium"
                        >
                          {language}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Contact Card */}
            <div className="lg:col-span-1">
              <div className="bg-gradient-to-br from-white to-gray-50 rounded-3xl p-8 shadow-2xl border border-gray-100 sticky top-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-8 text-center">Get In Touch</h3>
                
                <div className="space-y-6">
                  {agent.phone && (
                    <motion.div 
                      className="flex items-center bg-white rounded-xl p-4 shadow-md hover:shadow-lg transition-all duration-200"
                      whileHover={{ scale: 1.02 }}
                    >
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                        <PhoneIcon className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Phone</p>
                        <a 
                          href={`tel:${agent.phone}`}
                          className="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                        >
                          {agent.phone}
                        </a>
                      </div>
                    </motion.div>
                  )}
                  
                  {agent.email && (
                    <motion.div 
                      className="flex items-center bg-white rounded-xl p-4 shadow-md hover:shadow-lg transition-all duration-200"
                      whileHover={{ scale: 1.02 }}
                    >
                      <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mr-4">
                        <EnvelopeIcon className="w-6 h-6 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Email</p>
                        <a 
                          href={`mailto:${agent.email}`}
                          className="text-lg font-semibold text-gray-900 hover:text-purple-600 transition-colors"
                        >
                          {agent.email}
                        </a>
                      </div>
                    </motion.div>
                  )}
                  
                  {agent.office_address && (
                    <motion.div 
                      className="flex items-start bg-white rounded-xl p-4 shadow-md hover:shadow-lg transition-all duration-200"
                      whileHover={{ scale: 1.02 }}
                    >
                      <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mr-4 mt-1">
                        <MapPinIcon className="w-6 h-6 text-green-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Office</p>
                        <span className="text-lg font-semibold text-gray-900">{agent.office_address}</span>
                      </div>
                    </motion.div>
                  )}
                </div>

                <div className="mt-8 space-y-4">
                  <Link
                    href={`/agent/${agent.slug}/contact`}
                    onClick={handleContactClick}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 rounded-xl hover:shadow-xl hover:scale-105 transition-all duration-200 text-center block font-semibold text-lg"
                  >
                    Send Message
                  </Link>
                  <Link
                    href={`/agent/${agent.slug}/properties`}
                    className="w-full border-2 border-gray-200 text-gray-700 py-4 px-6 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 text-center block font-semibold text-lg"
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