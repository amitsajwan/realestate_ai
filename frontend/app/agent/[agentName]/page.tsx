'use client'

import { AgentProfile } from '@/components/AgentProfile'
import { initializeBrandTheme } from '@/lib/theme'
import {
  UserIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { toast } from 'react-hot-toast'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

      // Load agent's public properties
      const propertiesResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}/properties?limit=6`)
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
      fetch(`${API_BASE_URL}/api/v1/agent/public/${agent.slug}/track-contact`, {
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
        <div className="container mx-auto px-4">
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
                href={`/agent/${agent.slug}/posts`}
                className="text-slate-600 hover:text-slate-900 font-medium transition-colors text-sm"
              >
                Posts
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
                className="bg-brand-primary text-white px-4 py-2 rounded-lg hover:opacity-90 transition-colors text-sm font-medium"
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

      {/* Main Content */}
      <AgentProfile
        agent={agent}
        properties={properties}
        onContactClick={handleContactClick}
      />
    </div>
  )
}