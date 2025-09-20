'use client'

import { PostCard } from '@/components/PostCard'
import { Button, Card, CardBody, CardHeader } from '@/components/UI'
import {
    ChatBubbleLeftRightIcon,
    CheckIcon,
    DocumentTextIcon,
    EnvelopeIcon,
    EyeIcon,
    HomeIcon,
    MapPinIcon,
    PhoneIcon,
    SparklesIcon,
    StarIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useCachedData } from '@/lib/cache'

interface Post {
    id: string
    title: string
    content: string
    property_id?: string
    property_title?: string
    language: string
    channels: string[]
    status: string
    created_at: string
    view_count?: number
    like_count?: number
    share_count?: number
    comment_count?: number
}

interface AgentProfileProps {
    agent: {
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
    properties: any[]
    onContactClick: () => void
}

export function AgentProfile({ agent, properties, onContactClick }: AgentProfileProps) {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    // Use cached data hook for posts
    const { 
        data: postsData, 
        isLoading: isLoadingPosts, 
        error: postsError 
    } = useCachedData(
        async () => {
            const response = await fetch(
                `${API_BASE_URL}/api/v1/agent/public/${agent.slug}/posts?limit=6&status=published`
            )
            if (!response.ok) {
                throw new Error(`Failed to load posts: ${response.status}`)
            }
            return response.json()
        },
        {
            method: 'GET',
            path: `/api/v1/agent/public/${agent.slug}/posts`,
            params: { limit: 6, status: 'published' }
        },
        { ttl: 2 * 60 * 1000 } // Cache for 2 minutes
    )
    
    const posts = postsData?.posts || postsData || []

    const testimonials = [
        {
            id: 1,
            name: "Sarah Johnson",
            role: "Home Buyer",
            photo: "/api/placeholder/40/40",
            rating: 5,
            text: `Exceptional service! ${agent.agent_name} helped us find our perfect home in just 2 weeks. Professional, knowledgeable, and always available.`
        },
        {
            id: 2,
            name: "Michael Rodriguez",
            role: "Investor",
            photo: "/api/placeholder/40/40",
            rating: 5,
            text: `Outstanding expertise in the local market. ${agent.agent_name} guided us through every step and got us an amazing deal on our investment property.`
        },
        {
            id: 3,
            name: "Anna Chen",
            role: "Home Seller",
            photo: "/api/placeholder/40/40",
            rating: 5,
            text: `Professional, responsive, and results-driven. ${agent.agent_name} sold our house above asking price in just 5 days!`
        }
    ]

    return (
        <div className="min-h-screen bg-white">
            {/* Enhanced Hero Section */}
            <section className="bg-gradient-to-br from-blue-50 to-purple-50 py-20">
                <div className="container mx-auto px-4">
                    <div className="text-center">
                        {/* Trust Indicators */}
                        <div className="inline-flex items-center bg-green-50 text-green-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
                            <CheckIcon className="w-4 h-4 mr-2" />
                            Verified Agent • 15+ Years Experience
                        </div>

                        {/* Agent Photo with Status */}
                        <div className="inline-block relative mb-8">
                            {agent.photo ? (
                                <img
                                    src={agent.photo}
                                    alt={agent.agent_name}
                                    className="w-32 h-32 rounded-full object-cover border-4 border-white shadow-xl"
                                />
                            ) : (
                                <div className="w-32 h-32 bg-gray-200 rounded-full flex items-center justify-center border-4 border-white shadow-xl">
                                    <HomeIcon className="w-16 h-16 text-gray-400" />
                                </div>
                            )}
                            <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-green-500 rounded-full border-4 border-white flex items-center justify-center">
                                <div className="w-3 h-3 bg-white rounded-full"></div>
                            </div>
                        </div>

                        {/* Agent Name & Bio */}
                        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                            {agent.agent_name}
                        </h1>
                        <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
                            {agent.bio || "Professional Real Estate Agent helping you find your dream property"}
                        </p>

                        {/* Enhanced Stats */}
                        <div className="flex flex-wrap items-center justify-center gap-6 mb-8">
                            <div className="flex items-center bg-white rounded-lg px-6 py-3 shadow-sm">
                                <EyeIcon className="w-5 h-5 text-gray-600 mr-2" />
                                <span className="font-semibold text-gray-900">{agent.view_count} Views</span>
                            </div>
                            <div className="flex items-center bg-white rounded-lg px-6 py-3 shadow-sm">
                                <ChatBubbleLeftRightIcon className="w-5 h-5 text-gray-600 mr-2" />
                                <span className="font-semibold text-gray-900">{agent.contact_count} Clients</span>
                            </div>
                            <div className="flex items-center bg-white rounded-lg px-6 py-3 shadow-sm">
                                <StarIcon className="w-5 h-5 text-yellow-500 mr-2" />
                                <span className="font-semibold text-gray-900">5.0 Rating</span>
                            </div>
                        </div>

                        {/* Enhanced CTAs */}
                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <Button
                                size="lg"
                                className="px-8 py-4"
                                onClick={onContactClick}
                            >
                                Book Free Consultation
                            </Button>
                            <Button
                                size="lg"
                                variant="outline"
                                className="px-8 py-4"
                            >
                                Download Market Report
                            </Button>
                        </div>

                        <p className="text-gray-600 text-sm mt-4">
                            ⏰ Limited time offer • No obligation • 100% Free
                        </p>
                    </div>
                </div>
            </section>

            {/* Agent Details Section */}
            <section className="py-20 bg-white">
                <div className="container mx-auto px-4">
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
                                <Card className="hover:shadow-lg transition-shadow">
                                    <CardHeader>
                                        <h3 className="text-2xl font-bold text-gray-900 flex items-center">
                                            <SparklesIcon className="w-6 h-6 text-blue-600 mr-3" />
                                            Specialties
                                        </h3>
                                    </CardHeader>
                                    <CardBody>
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
                                    </CardBody>
                                </Card>
                            )}

                            {/* Experience & Languages */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {agent.experience && (
                                    <Card className="hover:shadow-lg transition-shadow">
                                        <CardHeader>
                                            <h3 className="text-xl font-bold text-gray-900 flex items-center">
                                                <StarIcon className="w-6 h-6 text-yellow-500 mr-3" />
                                                Experience
                                            </h3>
                                        </CardHeader>
                                        <CardBody>
                                            <p className="text-gray-700 text-lg leading-relaxed">{agent.experience}</p>
                                        </CardBody>
                                    </Card>
                                )}

                                {agent.languages.length > 0 && (
                                    <Card className="hover:shadow-lg transition-shadow">
                                        <CardHeader>
                                            <h3 className="text-xl font-bold text-gray-900 flex items-center">
                                                <ChatBubbleLeftRightIcon className="w-6 h-6 text-green-500 mr-3" />
                                                Languages
                                            </h3>
                                        </CardHeader>
                                        <CardBody>
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
                                        </CardBody>
                                    </Card>
                                )}
                            </div>
                        </div>

                        {/* Contact Card */}
                        <div className="lg:col-span-1">
                            <Card className="sticky top-6 shadow-xl">
                                <CardHeader>
                                    <h3 className="text-2xl font-bold text-gray-900 text-center">Get In Touch</h3>
                                </CardHeader>
                                <CardBody>
                                    <div className="space-y-6">
                                        {agent.phone && (
                                            <motion.div
                                                className="flex items-center bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors"
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
                                                className="flex items-center bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors"
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
                                                className="flex items-start bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors"
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
                                        <Button
                                            size="lg"
                                            className="w-full"
                                            onClick={onContactClick}
                                        >
                                            Send Message
                                        </Button>
                                        <Button
                                            size="lg"
                                            variant="outline"
                                            className="w-full"
                                        >
                                            View Properties
                                        </Button>
                                    </div>
                                </CardBody>
                            </Card>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Client Testimonials */}
            <section className="bg-gray-50 py-16 md:py-20">
                <div className="container mx-auto px-4">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                            What Clients Say
                        </h2>
                        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                            Real feedback from satisfied clients who found their dream properties
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {testimonials.map((testimonial) => (
                            <Card key={testimonial.id} className="hover:shadow-lg transition-shadow">
                                <CardBody>
                                    <div className="flex items-center mb-4">
                                        <div className="flex text-yellow-400">
                                            {[...Array(testimonial.rating)].map((_, i) => (
                                                <StarIcon key={i} className="w-5 h-5 fill-current" />
                                            ))}
                                        </div>
                                        <span className="ml-2 text-sm text-gray-600">{testimonial.rating}.0</span>
                                    </div>
                                    <p className="text-gray-700 mb-4 italic">"{testimonial.text}"</p>
                                    <div className="flex items-center">
                                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center mr-3">
                                            <span className="text-sm font-semibold text-gray-600">
                                                {testimonial.name.split(' ').map(n => n[0]).join('')}
                                            </span>
                                        </div>
                                        <div>
                                            <p className="font-semibold text-gray-900">{testimonial.name}</p>
                                            <p className="text-sm text-gray-600">{testimonial.role}</p>
                                        </div>
                                    </div>
                                </CardBody>
                            </Card>
                        ))}
                    </div>

                    {/* Social Proof Stats */}
                    <Card className="mt-12">
                        <CardBody>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                                <div>
                                    <div className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">50+</div>
                                    <div className="text-sm text-gray-600">Happy Clients</div>
                                </div>
                                <div>
                                    <div className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">₹2.5Cr+</div>
                                    <div className="text-sm text-gray-600">Properties Sold</div>
                                </div>
                                <div>
                                    <div className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">5.0</div>
                                    <div className="text-sm text-gray-600">Average Rating</div>
                                </div>
                                <div>
                                    <div className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">15</div>
                                    <div className="text-sm text-gray-600">Years Experience</div>
                                </div>
                            </div>
                        </CardBody>
                    </Card>
                </div>
            </section>

            {/* Recent Posts/Blog Section */}
            <section className="py-16 md:py-20 bg-white">
                <div className="container mx-auto px-4">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4 flex items-center justify-center">
                            <DocumentTextIcon className="w-8 h-8 mr-3 text-blue-600" />
                            Latest Insights & Properties
                        </h2>
                        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                            Stay updated with the latest market insights, property updates, and real estate tips from {agent.agent_name}
                        </p>
                    </div>

                    {isLoadingPosts ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                            <span className="ml-3 text-gray-600">Loading posts...</span>
                        </div>
                    ) : postsError ? (
                        <div className="text-center py-12">
                            <div className="text-gray-500 mb-4">{postsError}</div>
                            <button
                                onClick={loadAgentPosts}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Try Again
                            </button>
                        </div>
                    ) : posts.length > 0 ? (
                        <>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {posts.map((post) => (
                                    <PostCard
                                        key={post.id}
                                        post={post}
                                        agentName={agent.slug}
                                    />
                                ))}
                            </div>

                            {posts.length >= 6 && (
                                <div className="text-center mt-12">
                                    <Link
                                        href={`/agent/${agent.slug}/posts`}
                                        className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                    >
                                        <DocumentTextIcon className="w-5 h-5 mr-2" />
                                        View All Posts
                                    </Link>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="text-center py-12">
                            <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Posts Yet</h3>
                            <p className="text-gray-600">
                                {agent.agent_name} hasn't published any posts yet. Check back soon for updates!
                            </p>
                        </div>
                    )}
                </div>
            </section>
        </div>
    )
}
