'use client'

import {
    ArrowLeftIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
    EnvelopeIcon,
    HeartIcon,
    HomeIcon,
    MapPinIcon,
    PhoneIcon,
    ShareIcon
} from '@heroicons/react/24/outline'
import {
    HeartIcon as HeartSolidIcon
} from '@heroicons/react/24/solid'
import { motion } from 'framer-motion'
import Image from 'next/image'
import Link from 'next/link'
import { useEffect, useState } from 'react'

import { API_BASE_URL } from '@/lib/config/api'

interface Property {
    id: string
    title: string
    description: string
    price: number
    location: string
    address: string
    bedrooms: number
    bathrooms: number
    area_sqft: number
    property_type: string
    images: string[]
    features: string[]
    amenities: string[]
    status: string
    created_at: string
    updated_at: string
    year_built?: number
    parking_spaces?: number
    garden_area?: number
    balcony_area?: number
    furnished: boolean
    pet_friendly: boolean
    security_features: string[]
    nearby_amenities: string[]
    property_tax?: number
    maintenance_fee?: number
    hoa_fee?: number
    utilities_included: string[]
    availability_date?: string
    listing_type: string
    agent_id: string
    agent_name?: string
    agent_phone?: string
    agent_email?: string
    agent_photo?: string
}

interface AgentInfo {
    id: string
    agent_name: string
    slug: string
    photo: string
    phone: string
    email: string
    office_address: string
    bio?: string
    specialties?: string[]
    experience?: string
    languages?: string[]
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
    const [favorited, setFavorited] = useState(false)
    const [selectedImageIndex, setSelectedImageIndex] = useState(0)
    const [showContactForm, setShowContactForm] = useState(false)
    const [contactForm, setContactForm] = useState({
        name: '',
        email: '',
        phone: '',
        message: '',
        inquiry_type: 'property_inquiry'
    })

    useEffect(() => {
        loadPropertyData()
    }, [params.agentName, params.propertyId])

    const loadPropertyData = async () => {
        try {
            setIsLoading(true)
            setError(null)

            // Load agent info
            const agentResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}`)
            if (agentResponse.ok) {
                const agentData = await agentResponse.json()
                setAgent(agentData)
            }

            // Load specific property
            const propertyResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}/properties/${params.propertyId}`)

            if (propertyResponse.ok) {
                const propertyData = await propertyResponse.json()
                setProperty(propertyData)
            } else {
                throw new Error('Property not found')
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load property')
        } finally {
            setIsLoading(false)
        }
    }

    const handleFavorite = () => {
        setFavorited(!favorited)
    }

    const handleContactSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}/contact`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...contactForm,
                    property_id: params.propertyId,
                    property_title: property?.title
                })
            })

            if (response.ok) {
                setShowContactForm(false)
                setContactForm({
                    name: '',
                    email: '',
                    phone: '',
                    message: '',
                    inquiry_type: 'property_inquiry'
                })
                alert('Your message has been sent successfully!')
            }
        } catch (err) {
            alert('Failed to send message. Please try again.')
        }
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
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
    }

    const nextImage = () => {
        if (property?.images) {
            setSelectedImageIndex((prev) =>
                prev < property.images.length - 1 ? prev + 1 : 0
            )
        }
    }

    const prevImage = () => {
        if (property?.images) {
            setSelectedImageIndex((prev) =>
                prev > 0 ? prev - 1 : property.images.length - 1
            )
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading property...</p>
                </div>
            </div>
        )
    }

    if (error || !property) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-600 mb-4">Error: {error || 'Property not found'}</p>
                    <Link
                        href={`/agent/${params.agentName}/properties`}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Back to Properties
                    </Link>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <Link
                                href={`/agent/${params.agentName}/properties`}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <ArrowLeftIcon className="w-5 h-5 text-gray-600" />
                            </Link>
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                                    <span className="text-white font-bold text-lg">
                                        {agent?.agent_name?.charAt(0) || 'A'}
                                    </span>
                                </div>
                                <div>
                                    <h1 className="text-xl font-bold text-gray-900">{agent?.agent_name || 'Agent'}</h1>
                                    <p className="text-sm text-gray-500">Real Estate Agent</p>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={handleFavorite}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                {favorited ? (
                                    <HeartSolidIcon className="w-6 h-6 text-red-500" />
                                ) : (
                                    <HeartIcon className="w-6 h-6 text-gray-600" />
                                )}
                            </button>
                            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                <ShareIcon className="w-6 h-6 text-gray-600" />
                            </button>
                            <button
                                onClick={() => setShowContactForm(true)}
                                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Contact Agent
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Property Content */}
                    <div className="lg:col-span-2">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
                        >
                            {/* Image Gallery */}
                            {property.images && property.images.length > 0 && (
                                <div className="relative">
                                    <div className="aspect-video relative">
                                        <Image
                                            src={property.images[selectedImageIndex]}
                                            alt={`${property.title} - Image ${selectedImageIndex + 1}`}
                                            fill
                                            className="object-cover"
                                            sizes="(max-width: 768px) 100vw, 66vw"
                                        />

                                        {/* Navigation Arrows */}
                                        {property.images.length > 1 && (
                                            <>
                                                <button
                                                    onClick={prevImage}
                                                    className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
                                                >
                                                    <ChevronLeftIcon className="w-6 h-6" />
                                                </button>
                                                <button
                                                    onClick={nextImage}
                                                    className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
                                                >
                                                    <ChevronRightIcon className="w-6 h-6" />
                                                </button>
                                            </>
                                        )}

                                        {/* Image Counter */}
                                        {property.images.length > 1 && (
                                            <div className="absolute bottom-4 right-4 bg-black/70 text-white text-sm px-3 py-1 rounded-full">
                                                {selectedImageIndex + 1} / {property.images.length}
                                            </div>
                                        )}
                                    </div>

                                    {/* Thumbnail Grid */}
                                    {property.images.length > 1 && (
                                        <div className="p-4 border-t border-gray-100">
                                            <div className="grid grid-cols-6 gap-2">
                                                {property.images.map((image, index) => (
                                                    <button
                                                        key={index}
                                                        onClick={() => setSelectedImageIndex(index)}
                                                        className={`relative aspect-video rounded-lg overflow-hidden border-2 ${selectedImageIndex === index
                                                            ? 'border-blue-600'
                                                            : 'border-gray-200 hover:border-gray-300'
                                                            }`}
                                                    >
                                                        <Image
                                                            src={image}
                                                            alt={`Thumbnail ${index + 1}`}
                                                            fill
                                                            className="object-cover"
                                                            sizes="(max-width: 768px) 16vw, 11vw"
                                                        />
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Property Header */}
                            <div className="p-6 border-b border-gray-100">
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h1 className="text-3xl font-bold text-gray-900 mb-2">{property.title}</h1>
                                        <div className="flex items-center text-gray-600 mb-2">
                                            <MapPinIcon className="w-5 h-5 mr-2" />
                                            <span className="text-lg">{property.location}</span>
                                        </div>
                                        <p className="text-gray-500">{property.address}</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-bold text-green-600 mb-1">
                                            {property.price ? formatPrice(property.price) : 'Price on request'}
                                        </div>
                                        <span className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${property.status === 'active'
                                            ? 'bg-green-100 text-green-800'
                                            : property.status === 'pending'
                                                ? 'bg-yellow-100 text-yellow-800'
                                                : 'bg-red-100 text-red-800'
                                            }`}>
                                            {property.status === 'active' ? 'Available' :
                                                property.status === 'pending' ? 'Pending' : 'Sold'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Property Details */}
                            <div className="p-6">
                                <h2 className="text-2xl font-bold text-gray-900 mb-6">Property Details</h2>

                                {/* Key Features */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
                                    <div className="text-center">
                                        <HomeIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                                        <div className="text-2xl font-bold text-gray-900">{property.bedrooms || 'N/A'}</div>
                                        <div className="text-sm text-gray-600">Bedrooms</div>
                                    </div>
                                    <div className="text-center">
                                        <HomeIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                                        <div className="text-2xl font-bold text-gray-900">{property.bathrooms || 'N/A'}</div>
                                        <div className="text-sm text-gray-600">Bathrooms</div>
                                    </div>
                                    <div className="text-center">
                                        <HomeIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                                        <div className="text-2xl font-bold text-gray-900">{property.area_sqft ? property.area_sqft.toLocaleString() : 'N/A'}</div>
                                        <div className="text-sm text-gray-600">Sq Ft</div>
                                    </div>
                                    <div className="text-center">
                                        <HomeIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                                        <div className="text-2xl font-bold text-gray-900">{property.property_type || 'Property'}</div>
                                        <div className="text-sm text-gray-600">Type</div>
                                    </div>
                                </div>

                                {/* Description */}
                                <div className="mb-8">
                                    <h3 className="text-xl font-semibold text-gray-900 mb-4">Description</h3>
                                    <p className="text-gray-700 leading-relaxed">{property.description || 'No description available'}</p>
                                </div>

                                {/* Features & Amenities */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {property.features && property.features.length > 0 && (
                                        <div>
                                            <h3 className="text-xl font-semibold text-gray-900 mb-4">Features</h3>
                                            <div className="flex flex-wrap gap-2">
                                                {property.features.map((feature, index) => (
                                                    <span
                                                        key={index}
                                                        className="bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full"
                                                    >
                                                        {feature}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {property.amenities && property.amenities.length > 0 && (
                                        <div>
                                            <h3 className="text-xl font-semibold text-gray-900 mb-4">Amenities</h3>
                                            <div className="flex flex-wrap gap-2">
                                                {property.amenities.map((amenity, index) => (
                                                    <span
                                                        key={index}
                                                        className="bg-green-100 text-green-800 text-sm px-3 py-1 rounded-full"
                                                    >
                                                        {amenity}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Additional Details */}
                                <div className="mt-8 pt-8 border-t border-gray-200">
                                    <h3 className="text-xl font-semibold text-gray-900 mb-4">Additional Information</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                        {property.year_built && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Year Built:</span>
                                                <span className="font-medium">{property.year_built}</span>
                                            </div>
                                        )}
                                        {property.parking_spaces && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Parking Spaces:</span>
                                                <span className="font-medium">{property.parking_spaces}</span>
                                            </div>
                                        )}
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Furnished:</span>
                                            <span className="font-medium">{property.furnished ? 'Yes' : 'No'}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Pet Friendly:</span>
                                            <span className="font-medium">{property.pet_friendly ? 'Yes' : 'No'}</span>
                                        </div>
                                        {property.property_tax && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Property Tax:</span>
                                                <span className="font-medium">{formatPrice(property.property_tax)}/year</span>
                                            </div>
                                        )}
                                        {property.hoa_fee && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">HOA Fee:</span>
                                                <span className="font-medium">{formatPrice(property.hoa_fee)}/month</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>

                    {/* Agent Contact Sidebar */}
                    <div className="lg:col-span-1">
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-24"
                        >
                            <h2 className="text-xl font-bold text-gray-900 mb-6">Contact Agent</h2>

                            {/* Agent Info */}
                            <div className="flex items-center space-x-3 mb-6">
                                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                    <span className="text-white font-medium text-lg">
                                        {agent?.agent_name?.charAt(0) || 'A'}
                                    </span>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-gray-900">{agent?.agent_name || 'Agent'}</h3>
                                    <p className="text-sm text-gray-500">Real Estate Agent</p>
                                </div>
                            </div>

                            {/* Contact Methods */}
                            <div className="space-y-3 mb-6">
                                {agent?.phone && (
                                    <a
                                        href={`tel:${agent.phone}`}
                                        className="flex items-center space-x-3 text-gray-700 hover:text-blue-600 transition-colors p-3 rounded-lg hover:bg-gray-50"
                                    >
                                        <PhoneIcon className="w-5 h-5" />
                                        <span>{agent.phone}</span>
                                    </a>
                                )}
                                {agent?.email && (
                                    <a
                                        href={`mailto:${agent.email}`}
                                        className="flex items-center space-x-3 text-gray-700 hover:text-blue-600 transition-colors p-3 rounded-lg hover:bg-gray-50"
                                    >
                                        <EnvelopeIcon className="w-5 h-5" />
                                        <span>{agent.email}</span>
                                    </a>
                                )}
                            </div>

                            {/* Quick Contact Buttons */}
                            <div className="space-y-3">
                                <button
                                    onClick={() => setShowContactForm(true)}
                                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                                >
                                    Schedule Viewing
                                </button>
                                <button
                                    onClick={() => setShowContactForm(true)}
                                    className="w-full border border-gray-300 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                                >
                                    Get More Information
                                </button>
                            </div>

                            {/* Property Stats */}
                            <div className="mt-8 pt-6 border-t border-gray-200">
                                <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                                    <span>Listed:</span>
                                    <span>{formatDate(property.created_at)}</span>
                                </div>
                                <div className="flex items-center justify-between text-sm text-gray-600">
                                    <span>Last Updated:</span>
                                    <span>{formatDate(property.updated_at)}</span>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>

            {/* Contact Form Modal */}
            {showContactForm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-white rounded-xl max-w-md w-full p-6"
                    >
                        <h3 className="text-xl font-bold text-gray-900 mb-4">Contact Agent</h3>
                        <form onSubmit={handleContactSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                <input
                                    type="text"
                                    required
                                    value={contactForm.name}
                                    onChange={(e) => setContactForm(prev => ({ ...prev, name: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                <input
                                    type="email"
                                    required
                                    value={contactForm.email}
                                    onChange={(e) => setContactForm(prev => ({ ...prev, email: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                                <input
                                    type="tel"
                                    value={contactForm.phone}
                                    onChange={(e) => setContactForm(prev => ({ ...prev, phone: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                                <textarea
                                    rows={4}
                                    value={contactForm.message}
                                    onChange={(e) => setContactForm(prev => ({ ...prev, message: e.target.value }))}
                                    placeholder="I'm interested in this property..."
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div className="flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => setShowContactForm(false)}
                                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                                >
                                    Send Message
                                </button>
                            </div>
                        </form>
                    </motion.div>
                </div>
            )}
        </div>
    )
}
