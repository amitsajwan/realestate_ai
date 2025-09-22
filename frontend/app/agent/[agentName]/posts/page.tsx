'use client'

import {
    ChatBubbleLeftIcon,
    CurrencyDollarIcon,
    EyeIcon,
    HeartIcon,
    HomeIcon,
    MapPinIcon,
    ShareIcon
} from '@heroicons/react/24/outline'
import {
    HeartIcon as HeartSolidIcon
} from '@heroicons/react/24/solid'
import { motion } from 'framer-motion'
import Image from 'next/image'
import Link from 'next/link'
import { useEffect, useState } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
    language: string
    channels: string[]
    status: string
    created_at: string
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

interface AgentPostsPageProps {
    params: {
        agentName: string
    }
}

export default function AgentPostsPage({ params }: AgentPostsPageProps) {
    const [posts, setPosts] = useState<Post[]>([])
    const [agent, setAgent] = useState<AgentInfo | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [currentPage, setCurrentPage] = useState(1)
    const [hasMore, setHasMore] = useState(true)
    const [likedPosts, setLikedPosts] = useState<Set<string>>(new Set())

    const agentName = params.agentName.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

    useEffect(() => {
        loadAgentData()
    }, [params.agentName, currentPage])

    const loadAgentData = async () => {
        try {
            setIsLoading(true)
            setError(null)

            // Load agent info
            const agentResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}`)
            if (agentResponse.ok) {
                const agentData = await agentResponse.json()
                setAgent(agentData)
            }

            // Load agent posts
            const postsResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}/posts?page=${currentPage}&limit=10&status=published`)

            if (postsResponse.ok) {
                const postsData = await postsResponse.json()
                if (currentPage === 1) {
                    setPosts(postsData.posts || [])
                } else {
                    setPosts(prev => [...prev, ...(postsData.posts || [])])
                }
                setHasMore(postsData.has_more || false)
            } else {
                throw new Error('Failed to load posts')
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load posts')
        } finally {
            setIsLoading(false)
        }
    }

    const handleLike = (postId: string) => {
        setLikedPosts(prev => {
            const newSet = new Set(prev)
            if (newSet.has(postId)) {
                newSet.delete(postId)
            } else {
                newSet.add(postId)
            }
            return newSet
        })
    }

    const loadMore = () => {
        setCurrentPage(prev => prev + 1)
    }

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(price)
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        const now = new Date()
        const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))

        if (diffInHours < 1) return 'Just now'
        if (diffInHours < 24) return `${diffInHours}h ago`
        if (diffInHours < 48) return 'Yesterday'
        return date.toLocaleDateString()
    }

    if (isLoading && currentPage === 1) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading posts...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-600 mb-4">Error: {error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <Link href={`/agent/${params.agentName}`} className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                                <span className="text-white font-bold text-lg">
                                    {agent?.agent_name?.charAt(0) || 'A'}
                                </span>
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-gray-900">{agent?.agent_name || 'Agent'}</h1>
                                <p className="text-sm text-gray-500">Real Estate Agent</p>
                            </div>
                        </Link>
                        <div className="flex items-center space-x-4">
                            <Link
                                href={`/agent/${params.agentName}/contact`}
                                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Contact
                            </Link>
                        </div>
                    </div>
                </div>
            </header>

            {/* Posts Feed */}
            <div className="max-w-2xl mx-auto py-6 px-4">
                <div className="mb-8 text-center">
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Marketing Updates</h2>
                    <p className="text-gray-600">Stay updated with the latest property news and market insights from {agent?.agent_name || 'our agent'}.</p>
                </div>

                {posts.length === 0 ? (
                    <div className="text-center py-12">
                        <HomeIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No updates yet</h3>
                        <p className="text-gray-500">This agent hasn't shared any marketing updates yet.</p>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {posts.map((post, index) => (
                            <motion.article
                                key={post.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: index * 0.1 }}
                                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
                            >
                                {/* Post Header */}
                                <div className="p-4 border-b border-gray-100">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                            <span className="text-white font-medium text-sm">
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
                                <div className="p-4">
                                    <h2 className="text-lg font-semibold text-gray-900 mb-2">{post.title}</h2>
                                    <p className="text-gray-700 mb-4 whitespace-pre-wrap">{post.content}</p>

                                    {/* Property Details Card */}
                                    {post.property_id && (
                                        <div className="bg-gray-50 rounded-lg p-4 mb-4">
                                            <div className="flex items-start space-x-3">
                                                <div className="flex-1">
                                                    <h3 className="font-semibold text-gray-900 mb-2">
                                                        {post.property_title || 'Property Details'}
                                                    </h3>
                                                    {post.property_description && (
                                                        <p className="text-sm text-gray-600 mb-3">{post.property_description}</p>
                                                    )}

                                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                                        {post.property_price && (
                                                            <div className="flex items-center space-x-2">
                                                                <CurrencyDollarIcon className="w-4 h-4 text-green-600" />
                                                                <span className="font-medium text-green-600">
                                                                    {formatPrice(post.property_price)}
                                                                </span>
                                                            </div>
                                                        )}
                                                        {post.property_location && (
                                                            <div className="flex items-center space-x-2">
                                                                <MapPinIcon className="w-4 h-4 text-gray-500" />
                                                                <span className="text-gray-600">{post.property_location}</span>
                                                            </div>
                                                        )}
                                                        {post.property_bedrooms && (
                                                            <div className="flex items-center space-x-2">
                                                                <HomeIcon className="w-4 h-4 text-gray-500" />
                                                                <span className="text-gray-600">{post.property_bedrooms} bed</span>
                                                            </div>
                                                        )}
                                                        {post.property_bathrooms && (
                                                            <div className="flex items-center space-x-2">
                                                                <HomeIcon className="w-4 h-4 text-gray-500" />
                                                                <span className="text-gray-600">{post.property_bathrooms} bath</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Property Images */}
                                    {post.property_images && post.property_images.length > 0 && (
                                        <div className="mb-4">
                                            <div className="grid grid-cols-1 gap-2">
                                                {post.property_images.slice(0, 3).map((image, imgIndex) => (
                                                    <div key={imgIndex} className="relative aspect-video rounded-lg overflow-hidden">
                                                        <Image
                                                            src={image}
                                                            alt={`Property image ${imgIndex + 1}`}
                                                            fill
                                                            className="object-cover"
                                                            sizes="(max-width: 768px) 100vw, 50vw"
                                                        />
                                                    </div>
                                                ))}
                                                {post.property_images.length > 3 && (
                                                    <div className="text-center py-2">
                                                        <span className="text-sm text-gray-500">
                                                            +{post.property_images.length - 3} more images
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Post Actions */}
                                <div className="px-4 py-3 border-t border-gray-100">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-6">
                                            <button
                                                onClick={() => handleLike(post.id)}
                                                className="flex items-center space-x-2 text-gray-600 hover:text-red-600 transition-colors"
                                            >
                                                {likedPosts.has(post.id) ? (
                                                    <HeartSolidIcon className="w-5 h-5 text-red-600" />
                                                ) : (
                                                    <HeartIcon className="w-5 h-5" />
                                                )}
                                                <span className="text-sm font-medium">
                                                    {post.like_count || 0 + (likedPosts.has(post.id) ? 1 : 0)}
                                                </span>
                                            </button>
                                            <button className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors">
                                                <ChatBubbleLeftIcon className="w-5 h-5" />
                                                <span className="text-sm font-medium">{post.comment_count || 0}</span>
                                            </button>
                                            <button className="flex items-center space-x-2 text-gray-600 hover:text-green-600 transition-colors">
                                                <ShareIcon className="w-5 h-5" />
                                                <span className="text-sm font-medium">{post.share_count || 0}</span>
                                            </button>
                                        </div>
                                        <div className="flex items-center space-x-2 text-gray-500">
                                            <EyeIcon className="w-4 h-4" />
                                            <span className="text-sm">{post.view_count || 0}</span>
                                        </div>
                                    </div>
                                </div>
                            </motion.article>
                        ))}

                        {/* Load More Button */}
                        {hasMore && (
                            <div className="text-center py-6">
                                <button
                                    onClick={loadMore}
                                    disabled={isLoading}
                                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {isLoading ? 'Loading...' : 'Load More Posts'}
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}