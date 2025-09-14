'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'

interface AgentInfo {
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
}

interface ContactForm {
  name: string
  email: string
  phone: string
  message: string
  inquiry_type: string
}

interface AgentContactPageProps {
  params: {
    agentName: string
  }
}

export default function AgentContactPage({ params }: AgentContactPageProps) {
  const [agent, setAgent] = useState<AgentInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [agentName, setAgentName] = useState<string>('')
  
  const [form, setForm] = useState<ContactForm>({
    name: '',
    email: '',
    phone: '',
    message: '',
    inquiry_type: 'general'
  })

  useEffect(() => {
    loadAgentData()
  }, [params.agentName])

  const loadAgentData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch(`http://localhost:8000/api/v1/agent-public/${params.agentName}`)
      if (!response.ok) {
        throw new Error('Agent not found')
      }
      const agentData = await response.json()
      setAgent(agentData)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agent data')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setForm(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const response = await fetch(`http://localhost:8000/api/v1/agent-public/${params.agentName}/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      })

      if (response.ok) {
        setIsSubmitted(true)
        setForm({
          name: '',
          email: '',
          phone: '',
          message: '',
          inquiry_type: 'general'
        })
      } else {
        throw new Error('Failed to send message')
      }
    } catch (err) {
      // Handle error silently for now
    } finally {
      setIsSubmitting(false)
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
          <p className="text-gray-600 mb-6">{error || 'The agent profile you\'re looking for doesn\'t exist or is not public.'}</p>
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

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto">
          <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl">✓</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Message Sent Successfully!</h1>
          <p className="text-gray-600 mb-6">
            Thank you for your message. {agent.agent_name} will get back to you as soon as possible.
          </p>
          <div className="space-x-4">
            <Link 
              href={`/agent/${agent.slug}`}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Back to Agent Profile
            </Link>
            <Link 
              href={`/agent/${agent.slug}/properties`}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              View Properties
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
              <p className="text-sm text-gray-600 mt-1">
                Contact {agent.agent_name}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Link 
                href={`/agent/${agent.slug}`}
                className="text-gray-600 hover:text-gray-900"
              >
                Agent Profile
              </Link>
              <Link 
                href={`/agent/${agent.slug}/properties`}
                className="text-gray-600 hover:text-gray-900"
              >
                Properties
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Contact Form */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-8">
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Get in Touch</h1>
                <p className="text-gray-600">
                  Send a message to {agent.agent_name} and they'll get back to you as soon as possible.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      required
                      value={form.name}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Your full name"
                    />
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      required
                      value={form.email}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="your.email@example.com"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={form.phone}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>
                  <div>
                    <label htmlFor="inquiry_type" className="block text-sm font-medium text-gray-700 mb-2">
                      Inquiry Type
                    </label>
                    <select
                      id="inquiry_type"
                      name="inquiry_type"
                      value={form.inquiry_type}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="general">General Inquiry</option>
                      <option value="property_inquiry">Property Inquiry</option>
                      <option value="valuation">Property Valuation</option>
                      <option value="selling">Selling Property</option>
                      <option value="buying">Buying Property</option>
                      <option value="renting">Rental Inquiry</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
                    Message *
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    required
                    rows={6}
                    value={form.message}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Tell us about your requirements, questions, or how we can help you..."
                  />
                </div>

                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    By submitting this form, you agree to our privacy policy and terms of service.
                  </p>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        Sending...
                      </>
                    ) : (
                      'Send Message'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Agent Info Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
              
              <div className="flex items-center mb-6">
                {agent.photo ? (
                  <img
                    src={agent.photo}
                    alt={agent.agent_name}
                    className="w-16 h-16 rounded-full object-cover mr-4"
                  />
                ) : (
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mr-4">
                    <span className="text-gray-400 text-sm">AG</span>
                  </div>
                )}
                <div>
                  <h4 className="font-semibold text-gray-900">{agent.agent_name}</h4>
                  <p className="text-sm text-gray-600">Real Estate Agent</p>
                </div>
              </div>

              <div className="space-y-4">
                {agent.phone && (
                  <div className="flex items-center">
                    <span className="mr-2">📞</span>
                    <div>
                      <p className="text-sm text-gray-600">Phone</p>
                      <a 
                        href={`tel:${agent.phone}`}
                        className="text-gray-900 hover:text-blue-600 transition-colors"
                      >
                        {agent.phone}
                      </a>
                    </div>
                  </div>
                )}
                
                {agent.email && (
                  <div className="flex items-center">
                    <span className="mr-2">✉️</span>
                    <div>
                      <p className="text-sm text-gray-600">Email</p>
                      <a 
                        href={`mailto:${agent.email}`}
                        className="text-gray-900 hover:text-blue-600 transition-colors"
                      >
                        {agent.email}
                      </a>
                    </div>
                  </div>
                )}
                
                {agent.office_address && (
                  <div className="flex items-start">
                    <span className="mr-2">📍</span>
                    <div>
                      <p className="text-sm text-gray-600">Office</p>
                      <p className="text-gray-900">{agent.office_address}</p>
                    </div>
                  </div>
                )}
              </div>

              {agent.bio && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-2">About</h4>
                  <p className="text-sm text-gray-600 leading-relaxed">{agent.bio}</p>
                </div>
              )}

              {agent.specialties && agent.specialties.length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-2">Specialties</h4>
                  <div className="flex flex-wrap gap-2">
                    {agent.specialties.map((specialty, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                      >
                        {specialty}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-gray-200">
                <Link
                  href={`/agent/${agent.slug}/properties`}
                  className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors text-center block"
                >
                  View Properties
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}