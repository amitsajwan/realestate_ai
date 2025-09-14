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
    <div className="min-h-screen bg-white">
      {/* Professional Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center space-x-3 group">
              <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center group-hover:bg-slate-700 transition-colors">
                <UserIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-slate-900">
                PropertyAI
              </span>
            </Link>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              <Link 
                href={`/agent/${agent.slug}/properties`}
                className="text-slate-600 hover:text-slate-900 font-medium transition-colors text-sm"
              >
                Properties
              </Link>
              <Link 
                href={`/agent/${agent.slug}/contact`}
                className="text-slate-600 hover:text-slate-900 font-medium transition-colors text-sm"
              >
                Contact
              </Link>
              <Link
                href={`/agent/${agent.slug}/contact`}
                onClick={handleContactClick}
                className="bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors text-sm font-medium"
              >
                Get Started
              </Link>
            </nav>
            
            {/* Mobile Menu Button */}
            <button className="md:hidden p-2 text-slate-600 hover:text-slate-900">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-slate-50 py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            {/* Agent Photo */}
            <div className="inline-block relative mb-8">
              {agent.photo ? (
                <img
                  src={agent.photo}
                  alt={agent.agent_name}
                  className="w-24 h-24 md:w-32 md:h-32 rounded-full object-cover border-4 border-white shadow-lg"
                />
              ) : (
                <div className="w-24 h-24 md:w-32 md:h-32 bg-slate-200 rounded-full flex items-center justify-center border-4 border-white shadow-lg">
                  <UserIcon className="w-12 h-12 md:w-16 md:h-16 text-slate-400" />
                </div>
              )}
              <div className="absolute -bottom-1 -right-1 w-6 h-6 md:w-8 md:h-8 bg-green-500 rounded-full border-4 border-white flex items-center justify-center">
                <div className="w-2 h-2 md:w-3 md:w-3 bg-white rounded-full"></div>
              </div>
            </div>
            
            {/* Agent Name */}
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-slate-900 mb-4">
              {agent.agent_name}
            </h1>
            
            {/* Bio */}
            <p className="text-lg md:text-xl text-slate-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              {agent.bio || "Professional Real Estate Agent helping you find your dream property"}
            </p>
            
            {/* Stats */}
            <div className="flex flex-wrap items-center justify-center gap-4 md:gap-8 mb-12">
              <div className="flex items-center bg-white rounded-lg px-4 py-3 shadow-sm">
                <EyeIcon className="w-5 h-5 text-slate-600 mr-2" />
                <span className="text-sm font-medium text-slate-700">{agent.view_count} Views</span>
              </div>
              <div className="flex items-center bg-white rounded-lg px-4 py-3 shadow-sm">
                <ChatBubbleLeftRightIcon className="w-5 h-5 text-slate-600 mr-2" />
                <span className="text-sm font-medium text-slate-700">{agent.contact_count} Clients</span>
              </div>
              <div className="flex items-center bg-white rounded-lg px-4 py-3 shadow-sm">
                <StarIcon className="w-5 h-5 text-yellow-500 mr-2" />
                <span className="text-sm font-medium text-slate-700">5.0 Rating</span>
              </div>
            </div>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href={`/agent/${agent.slug}/contact`}
                onClick={handleContactClick}
                className="bg-slate-900 text-white px-8 py-3 rounded-lg hover:bg-slate-800 transition-colors font-medium text-sm"
              >
                Get In Touch
              </Link>
              <Link
                href={`/agent/${agent.slug}/properties`}
                className="bg-white text-slate-900 px-8 py-3 rounded-lg hover:bg-slate-50 transition-colors font-medium text-sm border border-slate-200"
              >
                View Properties
              </Link>
            </div>
          </div>
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

      {/* Client Testimonials & Reviews */}
      <section className="bg-slate-50 py-16 md:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              What Clients Say
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Real feedback from satisfied clients who found their dream properties
            </p>
          </div>

          {/* Testimonials Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
            {/* Testimonial 1 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <div className="flex items-center mb-4">
                <div className="flex text-yellow-400">
                  {[...Array(5)].map((_, i) => (
                    <StarIcon key={i} className="w-5 h-5 fill-current" />
                  ))}
                </div>
                <span className="ml-2 text-sm text-slate-600">5.0</span>
              </div>
              <p className="text-slate-700 mb-4">
                "Exceptional service! {agent.agent_name} helped us find our perfect home in just 2 weeks. Professional, knowledgeable, and always available."
              </p>
              <div className="flex items-center">
                <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center mr-3">
                  <span className="text-sm font-semibold text-slate-600">SJ</span>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Sarah Johnson</p>
                  <p className="text-sm text-slate-600">Home Buyer</p>
                </div>
              </div>
            </div>

            {/* Testimonial 2 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <div className="flex items-center mb-4">
                <div className="flex text-yellow-400">
                  {[...Array(5)].map((_, i) => (
                    <StarIcon key={i} className="w-5 h-5 fill-current" />
                  ))}
                </div>
                <span className="ml-2 text-sm text-slate-600">5.0</span>
              </div>
              <p className="text-slate-700 mb-4">
                "Outstanding expertise in the local market. {agent.agent_name} guided us through every step and got us an amazing deal on our investment property."
              </p>
              <div className="flex items-center">
                <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center mr-3">
                  <span className="text-sm font-semibold text-slate-600">MR</span>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Michael Rodriguez</p>
                  <p className="text-sm text-slate-600">Investor</p>
                </div>
              </div>
            </div>

            {/* Testimonial 3 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <div className="flex items-center mb-4">
                <div className="flex text-yellow-400">
                  {[...Array(5)].map((_, i) => (
                    <StarIcon key={i} className="w-5 h-5 fill-current" />
                  ))}
                </div>
                <span className="ml-2 text-sm text-slate-600">5.0</span>
              </div>
              <p className="text-slate-700 mb-4">
                "Professional, responsive, and results-driven. {agent.agent_name} sold our house above asking price in just 5 days!"
              </p>
              <div className="flex items-center">
                <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center mr-3">
                  <span className="text-sm font-semibold text-slate-600">AC</span>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Anna Chen</p>
                  <p className="text-sm text-slate-600">Home Seller</p>
                </div>
              </div>
            </div>
          </div>

          {/* Social Proof Stats */}
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl md:text-4xl font-bold text-slate-900 mb-2">50+</div>
                <div className="text-sm text-slate-600">Happy Clients</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-slate-900 mb-2">₹2.5Cr+</div>
                <div className="text-sm text-slate-600">Properties Sold</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-slate-900 mb-2">5.0</div>
                <div className="text-sm text-slate-600">Average Rating</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-slate-900 mb-2">15</div>
                <div className="text-sm text-slate-600">Years Experience</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Properties */}
      {properties.length > 0 && (
        <section className="bg-white py-16 md:py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-12">
              <div>
                <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
                  Featured Properties
                </h2>
                <p className="text-lg text-slate-600">
                  Discover our latest and most popular listings
                </p>
              </div>
              <Link
                href={`/agent/${agent.slug}/properties`}
                className="hidden md:flex items-center text-slate-600 hover:text-slate-900 font-medium"
              >
                View All Properties
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {properties.map((property) => (
                <motion.div
                  key={property.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-lg transition-shadow group"
                >
                  {property.images.length > 0 && (
                    <div className="relative">
                      <img
                        src={property.images[0]}
                        alt={property.title}
                        className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                      <div className="absolute top-4 right-4">
                        <span className="bg-white/90 backdrop-blur-sm text-slate-900 px-3 py-1 rounded-full text-sm font-medium">
                          {property.property_type}
                        </span>
                      </div>
                    </div>
                  )}
                  <div className="p-6">
                    <h3 className="font-semibold text-slate-900 mb-2 line-clamp-2 text-lg">
                      {property.title}
                    </h3>
                    <p className="text-slate-600 text-sm mb-4 flex items-center">
                      <MapPinIcon className="w-4 h-4 mr-1" />
                      {property.location}
                    </p>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-2xl font-bold text-slate-900">
                        ₹{property.price.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-slate-500 space-x-4">
                      {property.bedrooms > 0 && (
                        <span>{property.bedrooms} bed</span>
                      )}
                      {property.bathrooms > 0 && (
                        <span>{property.bathrooms} bath</span>
                      )}
                      {property.area > 0 && (
                        <span>{property.area} sq ft</span>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Mobile View All Button */}
            <div className="mt-8 text-center md:hidden">
              <Link
                href={`/agent/${agent.slug}/properties`}
                className="inline-flex items-center bg-slate-900 text-white px-6 py-3 rounded-lg hover:bg-slate-800 transition-colors font-medium"
              >
                View All Properties
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Social Engagement Section */}
      <section className="bg-slate-50 py-16 md:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              Connect & Engage
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Follow our journey, share your experience, and stay updated with the latest properties
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Recent Activity */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-semibold text-slate-900 mb-4">Recent Activity</h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-slate-700">Property sold in Bandra West</p>
                    <p className="text-xs text-slate-500">2 hours ago</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-slate-700">New listing added</p>
                    <p className="text-xs text-slate-500">1 day ago</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                    <StarIcon className="w-4 h-4 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-700">Received 5-star review</p>
                    <p className="text-xs text-slate-500">3 days ago</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Social Media */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-semibold text-slate-900 mb-4">Follow Us</h3>
              <div className="space-y-4">
                <a href="#" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-50 transition-colors">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">Twitter</p>
                    <p className="text-sm text-slate-600">@propertyai_agent</p>
                  </div>
                </a>
                <a href="#" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-50 transition-colors">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">LinkedIn</p>
                    <p className="text-sm text-slate-600">propertyai-agent</p>
                  </div>
                </a>
                <a href="#" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-50 transition-colors">
                  <div className="w-8 h-8 bg-pink-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-pink-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.174-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.357-.629-2.746-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24.009 12.017 24.009c6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641.001.012.001z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">Instagram</p>
                    <p className="text-sm text-slate-600">@propertyai_agent</p>
                  </div>
                </a>
              </div>
            </div>

            {/* Quick Contact */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-semibold text-slate-900 mb-4">Quick Contact</h3>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <PhoneIcon className="w-5 h-5 text-slate-600" />
                  <a href={`tel:${agent.phone}`} className="text-slate-700 hover:text-slate-900 font-medium">
                    {agent.phone}
                  </a>
                </div>
                <div className="flex items-center space-x-3">
                  <EnvelopeIcon className="w-5 h-5 text-slate-600" />
                  <a href={`mailto:${agent.email}`} className="text-slate-700 hover:text-slate-900 font-medium">
                    {agent.email}
                  </a>
                </div>
                <div className="pt-4">
                  <Link
                    href={`/agent/${agent.slug}/contact`}
                    onClick={handleContactClick}
                    className="w-full bg-slate-900 text-white py-3 px-4 rounded-lg hover:bg-slate-800 transition-colors text-center block font-medium"
                  >
                    Send Message
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Professional Footer */}
      <footer className="bg-slate-900 text-white py-12 md:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Company Info */}
            <div className="md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                  <UserIcon className="w-5 h-5 text-slate-900" />
                </div>
                <span className="text-xl font-bold">PropertyAI</span>
              </div>
              <p className="text-slate-300 mb-6 max-w-md">
                Professional real estate services powered by AI. Helping you find your dream property with cutting-edge technology and personalized service.
              </p>
              <div className="flex space-x-4">
                <a href="#" className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center hover:bg-slate-700 transition-colors">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
                  </svg>
                </a>
                <a href="#" className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center hover:bg-slate-700 transition-colors">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                </a>
                <a href="#" className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center hover:bg-slate-700 transition-colors">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.174-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.357-.629-2.746-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24.009 12.017 24.009c6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641.001.012.001z"/>
                  </svg>
                </a>
              </div>
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
              <ul className="space-y-3">
                <li><Link href={`/agent/${agent.slug}/properties`} className="text-slate-300 hover:text-white transition-colors">Properties</Link></li>
                <li><Link href={`/agent/${agent.slug}/contact`} className="text-slate-300 hover:text-white transition-colors">Contact</Link></li>
                <li><a href="#" className="text-slate-300 hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="text-slate-300 hover:text-white transition-colors">Services</a></li>
                <li><a href="#" className="text-slate-300 hover:text-white transition-colors">Testimonials</a></li>
              </ul>
            </div>

            {/* Contact Info */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Contact Info</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <PhoneIcon className="w-5 h-5 text-slate-400" />
                  <span className="text-slate-300">{agent.phone}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <EnvelopeIcon className="w-5 h-5 text-slate-400" />
                  <span className="text-slate-300">{agent.email}</span>
                </div>
                <div className="flex items-start space-x-3">
                  <MapPinIcon className="w-5 h-5 text-slate-400 mt-0.5" />
                  <span className="text-slate-300">{agent.office_address}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-slate-800 mt-8 pt-8 text-center">
            <p className="text-slate-400 text-sm">
              © 2024 PropertyAI. All rights reserved. | Professional Real Estate Services
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}