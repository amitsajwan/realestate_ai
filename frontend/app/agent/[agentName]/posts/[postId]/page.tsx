'use client'

import {
    ArrowLeftIcon,
    ChatBubbleLeftIcon,
    EnvelopeIcon,
    EyeIcon,
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

interface Post {
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
    property_features?: string[]
    property_amenities?: string[]
    language: string
    channels: string[]
    status: string
    created_at: string
    updated_at: string
    view_count?: number
    like_count?: number
    share_count?: number
    comment_count?: number
    agent_name?: string
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
}

interface PostDetailPageProps {
    params: {
        agentName: string
        postId: string
    }
}

export default function PostDetailPage({ params }: PostDetailPageProps) {
    const [post, setPost] = useState<Post | null>(null)
    const [agent, setAgent] = useState<AgentInfo | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [liked, setLiked] = useState(false)
    const [selectedImageIndex, setSelectedImageIndex] = useState(0)

    useEffect(() => {
        loadPostData()
    }, [params.agentName, params.postId])

    const loadPostData = async () => {
        try {
            setIsLoading(true)
            setError(null)

            // Load agent info
            const agentResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}`)
            if (agentResponse.ok) {
                const agentData = await agentResponse.json()
                setAgent(agentData)
            }

            // Load specific post
            const postResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}/posts/${params.postId}`)

            if (postResponse.ok) {
                const postData = await postResponse.json()
                setPost(postData)
            } else {
                throw new Error('Post not found')
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load post')
        } finally {
            setIsLoading(false)
        }
    }

    const handleLike = () => {
        setLiked(!liked)
    }

    const formatPrice = (price: number) => {
        if (price == null || price === 0) return 'Contact for price';

        if (price >= 10000000) {
            return `₹${(price / 10000000).toFixed(1)}Cr`;
        } else if (price >= 100000) {
            return `₹${(price / 100000).toFixed(0)}L`;
        } else {
            return `₹${price.toLocaleString()}`;
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

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading post...</p>
                </div>
            </div>
        )
    }

    if (error || !post) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-600 mb-4">Error: {error || 'Post not found'}</p>
                    <Link
                        href={`/agent/${params.agentName}/posts`}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Back to Posts
                    </Link>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <Link
                                href={`/agent/${params.agentName}/posts`}
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
                        <Link
                            href={`/agent/${params.agentName}/contact`}
                            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Contact Agent
                        </Link>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto py-6 px-4">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Post Content */}
                    <div className="lg:col-span-2">
                        <motion.article
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
                        >
                            {/* Post Header */}
                            <div className="p-6 border-b border-gray-100">
                                <div className="flex items-center space-x-3">
                                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                        <span className="text-white font-medium text-lg">
                                            {agent?.agent_name?.charAt(0) || 'A'}
                                        </span>
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-semibold text-gray-900">{agent?.agent_name || 'Agent'}</h3>
                                        <p className="text-sm text-gray-500">{formatDate(post.created_at)}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Post Content */}
                            <div className="p-6">
                                <h1 className="text-2xl font-bold text-gray-900 mb-4">{post.title}</h1>
                                <div className="prose max-w-none">
                                    <p className="text-gray-700 text-lg leading-relaxed whitespace-pre-wrap">{post.content}</p>
                                </div>
                            </div>

                            {/* Property Images Gallery */}
                            {post.property_images && post.property_images.length > 0 && (
                                <div className="p-6 border-t border-gray-100">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Property Images</h3>
                                    <div className="space-y-4">
                                        {/* Main Image */}
                                        <div className="relative aspect-video rounded-lg overflow-hidden">
                                            <Image
                                                src={post.property_images[selectedImageIndex]}
                                                alt={`Property image ${selectedImageIndex + 1}`}
                                                fill
                                                className="object-cover"
                                                sizes="(max-width: 768px) 100vw, 66vw"
                                            />
                                        </div>

                                        {/* Thumbnail Grid */}
                                        {post.property_images.length > 1 && (
                                            <div className="grid grid-cols-4 gap-2">
                                                {post.property_images.map((image, index) => (
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
                                                            alt={`Property thumbnail ${index + 1}`}
                                                            fill
                                                            className="object-cover"
                                                            sizes="(max-width: 768px) 25vw, 16vw"
                                                        />
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Post Actions */}
                            <div className="px-6 py-4 border-t border-gray-100">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-6">
                                        <button
                                            onClick={handleLike}
                                            className="flex items-center space-x-2 text-gray-600 hover:text-red-600 transition-colors"
                                        >
                                            {liked ? (
                                                <HeartSolidIcon className="w-6 h-6 text-red-600" />
                                            ) : (
                                                <HeartIcon className="w-6 h-6" />
                                            )}
                                            <span className="font-medium">
                                                {post.like_count || 0 + (liked ? 1 : 0)}
                                            </span>
                                        </button>
                                        <button className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors">
                                            <ChatBubbleLeftIcon className="w-6 h-6" />
                                            <span className="font-medium">{post.comment_count || 0}</span>
                                        </button>
                                        <button className="flex items-center space-x-2 text-gray-600 hover:text-green-600 transition-colors">
                                            <ShareIcon className="w-6 h-6" />
                                            <span className="font-medium">{post.share_count || 0}</span>
                                        </button>
                                    </div>
                                    <div className="flex items-center space-x-2 text-gray-500">
                                        <EyeIcon className="w-5 h-5" />
                                        <span>{post.view_count || 0}</span>
                                    </div>
                                </div>
                            </div>
                        </motion.article>
                    </div>

                    {/* Property Details Sidebar */}
                    {post.property_id && (
                        <div className="lg:col-span-1">
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-24"
                            >
                                <h2 className="text-xl font-bold text-gray-900 mb-6">Property Details</h2>

                                {/* Price */}
                                {post.property_price && (
                                    <div className="mb-6">
                                        <div className="text-3xl font-bold text-green-600">
                                            {formatPrice(post.property_price)}
                                        </div>
                                        <div className="text-sm text-gray-500">Asking Price</div>
                                    </div>
                                )}

                                {/* Basic Info */}
                                <div className="space-y-4 mb-6">
                                    {post.property_type && (
                                        <div className="flex items-center space-x-3">
                                            <HomeIcon className="w-5 h-5 text-gray-500" />
                                            <span className="text-gray-700">{post.property_type}</span>
                                        </div>
                                    )}
                                    {post.property_location && (
                                        <div className="flex items-center space-x-3">
                                            <MapPinIcon className="w-5 h-5 text-gray-500" />
                                            <span className="text-gray-700">{post.property_location}</span>
                                        </div>
                                    )}
                                    {post.property_bedrooms && (
                                        <div className="flex items-center space-x-3">
                                            <HomeIcon className="w-5 h-5 text-gray-500" />
                                            <span className="text-gray-700">{post.property_bedrooms} Bedrooms</span>
                                        </div>
                                    )}
                                    {post.property_bathrooms && (
                                        <div className="flex items-center space-x-3">
                                            <HomeIcon className="w-5 h-5 text-gray-500" />
                                            <span className="text-gray-700">{post.property_bathrooms} Bathrooms</span>
                                        </div>
                                    )}
                                    {post.property_area && (
                                        <div className="flex items-center space-x-3">
                                            <HomeIcon className="w-5 h-5 text-gray-500" />
                                            <span className="text-gray-700">{post.property_area.toLocaleString()} sq ft</span>
                                        </div>
                                    )}
                                </div>

                                {/* Description */}
                                {post.property_description && (
                                    <div className="mb-6">
                                        <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                                        <p className="text-gray-700 text-sm leading-relaxed">{post.property_description}</p>
                                    </div>
                                )}

                                {/* Features */}
                                {post.property_features && post.property_features.length > 0 && (
                                    <div className="mb-6">
                                        <h3 className="font-semibold text-gray-900 mb-3">Features</h3>
                                        <div className="flex flex-wrap gap-2">
                                            {post.property_features.map((feature, index) => (
                                                <span
                                                    key={index}
                                                    className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                                                >
                                                    {feature}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Amenities */}
                                {post.property_amenities && post.property_amenities.length > 0 && (
                                    <div className="mb-6">
                                        <h3 className="font-semibold text-gray-900 mb-3">Amenities</h3>
                                        <div className="flex flex-wrap gap-2">
                                            {post.property_amenities.map((amenity, index) => (
                                                <span
                                                    key={index}
                                                    className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full"
                                                >
                                                    {amenity}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Contact Agent */}
                                <div className="border-t border-gray-200 pt-6">
                                    <h3 className="font-semibold text-gray-900 mb-4">Contact Agent</h3>
                                    <div className="space-y-3">
                                        {agent?.phone && (
                                            <a
                                                href={`tel:${agent.phone}`}
                                                className="flex items-center space-x-3 text-gray-700 hover:text-blue-600 transition-colors"
                                            >
                                                <PhoneIcon className="w-5 h-5" />
                                                <span>{agent.phone}</span>
                                            </a>
                                        )}
                                        {agent?.email && (
                                            <a
                                                href={`mailto:${agent.email}`}
                                                className="flex items-center space-x-3 text-gray-700 hover:text-blue-600 transition-colors"
                                            >
                                                <EnvelopeIcon className="w-5 h-5" />
                                                <span>{agent.email}</span>
                                            </a>
                                        )}
                                        <Link
                                            href={`/agent/${params.agentName}/contact`}
                                            className="w-full bg-blue-600 text-white text-center py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors block"
                                        >
                                            Get More Information
                                        </Link>
                                    </div>
                                </div>
                            </motion.div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}