'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'

interface Property {
  id: string
  title: string
  description: string
  price: number
  property_type: string
  bedrooms: number
  bathrooms: number
  area: number
  location: string
  images: string[]
  features: string[]
  created_at: string
  view_count: number
  inquiry_count: number
}

interface AgentInfo {
  id: string
  agent_name: string
  slug: string
  photo: string
  phone: string
  email: string
  office_address: string
}

interface PropertyDetailPageProps {
  params: {
    agentName: string
    propertyId: string
  }
}

export default function PropertyDetailPage({ params }: PropertyDetailPageProps) {
  const [property, setProperty] = useState<Property | null>(null)
  const [agent, setAgent] = useState<AgentInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPropertyData()
  }, [params.agentName, params.propertyId])

  const loadPropertyData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Load property details
      const propertyResponse = await fetch(`/api/v1/agent-public/${params.agentName}/properties/${params.propertyId}`)
      if (!propertyResponse.ok) {
        throw new Error('Property not found')
      }
      const propertyData = await propertyResponse.json()
      setProperty(propertyData)

      // Load agent info
      const agentResponse = await fetch(`/api/v1/agent-public/${params.agentName}`)
      if (agentResponse.ok) {
        const agentData = await agentResponse.json()
        setAgent(agentData)
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load property')
    } finally {
      setIsLoading(false)
    }
  }

  const formatPrice = (price: number) => {
    if (price >= 10000000) {
      return `₹${(price / 10000000).toFixed(1)}Cr`
    } else if (price >= 100000) {
      return `₹${(price / 100000).toFixed(1)}L`
    } else {
      return `₹${price.toLocaleString()}`
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading property details...</p>
        </div>
      </div>
    )
  }

  if (error || !property) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Property Not Found</h1>
          <p className="text-gray-600 mb-6">{error || 'The property you\'re looking for doesn\'t exist or is not public.'}</p>
          <div className="space-x-4">
            <Link 
              href={`/agent/${params.agentName}/properties`}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              View All Properties
            </Link>
            <Link 
              href={`/agent/${params.agentName}`}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Agent Profile
            </Link>
          </div>
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
            <div>
              <Link href="/" className="text-xl font-bold text-blue-600">
                PropertyAI
              </Link>
              <nav className="flex items-center space-x-2 text-sm text-gray-600 mt-1">
                <Link href={`/agent/${params.agentName}`} className="hover:text-gray-900">
                  {agent?.agent_name}
                </Link>
                <span>›</span>
                <Link href={`/agent/${params.agentName}/properties`} className="hover:text-gray-900">
                  Properties
                </Link>
                <span>›</span>
                <span className="text-gray-900">{property.title}</span>
              </nav>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Property Images */}
            <div className="bg-white rounded-lg shadow-sm overflow-hidden mb-6">
              {property.images && property.images.length > 0 ? (
                <img
                  src={property.images[0]}
                  alt={property.title}
                  className="w-full h-96 object-cover"
                />
              ) : (
                <div className="w-full h-96 bg-gray-200 flex items-center justify-center">
                  <div className="text-gray-400">No Image Available</div>
                </div>
              )}
            </div>

            {/* Property Details */}
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">{property.title}</h1>
                  <div className="flex items-center text-gray-600 mb-4">
                    <span>{property.location}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-blue-600 mb-1">
                    {formatPrice(property.price)}
                  </div>
                  <div className="text-sm text-gray-500">{property.property_type}</div>
                </div>
              </div>

              {/* Property Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {property.bedrooms > 0 && (
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{property.bedrooms}</div>
                    <div className="text-sm text-gray-600">Bedrooms</div>
                  </div>
                )}
                {property.bathrooms > 0 && (
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{property.bathrooms}</div>
                    <div className="text-sm text-gray-600">Bathrooms</div>
                  </div>
                )}
                {property.area > 0 && (
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{property.area}</div>
                    <div className="text-sm text-gray-600">Sq Ft</div>
                  </div>
                )}
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">{property.view_count}</div>
                  <div className="text-sm text-gray-600">Views</div>
                </div>
              </div>

              {/* Description */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Description</h3>
                <p className="text-gray-700 leading-relaxed">{property.description}</p>
              </div>

              {/* Features */}
              {property.features && property.features.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Features</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {property.features.map((feature, index) => (
                      <div key={index} className="flex items-center">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                        <span className="text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* Agent Contact Card */}
            {agent && (
              <div className="bg-white rounded-lg shadow-sm p-6 mb-6 sticky top-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Agent</h3>
                
                <div className="flex items-center mb-4">
                  {agent.photo ? (
                    <img
                      src={agent.photo}
                      alt={agent.agent_name}
                      className="w-12 h-12 rounded-full object-cover mr-3"
                    />
                  ) : (
                    <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center mr-3">
                      <span className="text-gray-400 text-sm">AG</span>
                    </div>
                  )}
                  <div>
                    <div className="font-medium text-gray-900">{agent.agent_name}</div>
                    <div className="text-sm text-gray-600">Real Estate Agent</div>
                  </div>
                </div>

                <div className="space-y-3 mb-6">
                  {agent.phone && (
                    <div className="flex items-center text-gray-700">
                      <span className="mr-2">📞</span>
                      <a href={`tel:${agent.phone}`} className="hover:text-blue-600">
                        {agent.phone}
                      </a>
                    </div>
                  )}
                  {agent.email && (
                    <div className="flex items-center text-gray-700">
                      <span className="mr-2">✉️</span>
                      <a href={`mailto:${agent.email}`} className="hover:text-blue-600">
                        {agent.email}
                      </a>
                    </div>
                  )}
                  {agent.office_address && (
                    <div className="flex items-start text-gray-700">
                      <span className="mr-2">📍</span>
                      <span className="text-sm">{agent.office_address}</span>
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                    Send Message
                  </button>
                  <Link
                    href={`/agent/${params.agentName}`}
                    className="w-full border border-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-50 transition-colors text-center block"
                  >
                    View Agent Profile
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}