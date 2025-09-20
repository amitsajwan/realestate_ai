'use client'

import {
    ArrowLeftIcon,
    ChatBubbleLeftRightIcon,
    DocumentTextIcon,
    HeartIcon,
    ShareIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useEffect, useState } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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

interface AgentInfo {
    id: string
    agent_name: string
    slug: string
    photo: string
    phone: string
    email: string
    office_address: string
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

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading Post</h2>
                    <p className="text-gray-600">Loading the latest insights...</p>
                </div>
            </div>
        )
    }

    if (error || !post) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
                <div className="text-center max-w-md mx-auto">
                    <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <DocumentTextIcon className="w-10 h-10 text-red-500" />
                    </div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-4">Post Not Found</h1>
                    <p className="text-gray-600 mb-8">{error || 'The post you\'re looking for doesn\'t exist or is not public.'}</p>
                    <div className="space-x-4">
                        <Link
                            href={`/agent/${params.agentName}/posts`}
                            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            View All Posts
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
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <Link
                                href={`/agent/${params.agentName}/posts`}
                                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
                            >
                                <ArrowLeftIcon className="w-5 h-5 mr-2" />
                                Back to Posts
                            </Link>
                            <div className="text-gray-300">|</div>
                            <Link href="/" className="text-xl font-bold text-blue-600">
                                PropertyAI
                            </Link>
                        </div>
                        <div className="flex items-center space-x-4">
                            <Link
                                href={`/agent/${params.agentName}`}
                                className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                            >
                                Agent Profile
                            </Link>
                            <Link
                                href={`/agent/${params.agentName}/properties`}
                                className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                            >
                                Properties
                            </Link>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Content */}
                    <div className="lg:col-span-2">
                        <article className="bg-white rounded-2xl shadow-lg overflow-hidden">
                            {/* Post Header */}
                            <div className="p-8 border-b border-gray-100">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <h1 className="text-3xl font-bold text-gray-900 mb-4">
                                            {post.title}
                                        </h1>
                                        <div className="flex items-center space-x-4 text-sm text-gray-500 mb-4">
                                            <div className="flex items-center">
                                                <DocumentTextIcon className="w-4 h-4 mr-1" />
                                                <span>{formatDate(post.created_at)}</span>
                                            </div>
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${post.status === 'published'
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-yellow-100 text-yellow-800'
                                                }`}>
                                                {post.status}
                                            </span>
                                            <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                                                {post.language.toUpperCase()}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Social Media Channels */}
                                {post.channels.length > 0 && (
                                    <div className="flex items-center space-x-2">
                                        <span className="text-sm text-gray-600">Posted on:</span>
                                        {post.channels.map((channel, index) => (
                                            <span
                                                key={index}
                                                className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                                            >
                                                {channel.charAt(0).toUpperCase() + channel.slice(1)}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Post Content */}
                            <div className="p-8">
                                <div className="prose prose-lg max-w-none">
                                    <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                                        {post.content}
                                    </div>
                                </div>

                                {/* Related Property */}
                                {post.property_id && post.property_title && (
                                    <div className="mt-8 p-6 bg-blue-50 rounded-xl">
                                        <div className="flex items-center mb-3">
                                            <DocumentTextIcon className="w-6 h-6 text-blue-600 mr-2" />
                                            <h3 className="text-lg font-semibold text-blue-900">Related Property</h3>
                                        </div>
                                        <p className="text-blue-800 font-medium">{post.property_title}</p>
                                        <Link
                                            href={`/agent/${params.agentName}/properties/${post.property_id}`}
                                            className="inline-flex items-center mt-3 text-blue-600 hover:text-blue-800 font-medium"
                                        >
                                            View Property Details →
                                        </Link>
                                    </div>
                                )}

                                {/* Engagement Stats */}
                                <div className="mt-8 pt-6 border-t border-gray-100">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-6 text-sm text-gray-500">
                                            {post.view_count !== undefined && (
                                                <div className="flex items-center">
                                                    <DocumentTextIcon className="w-4 h-4 mr-1" />
                                                    <span>{post.view_count} views</span>
                                                </div>
                                            )}
                                            {post.like_count !== undefined && (
                                                <div className="flex items-center">
                                                    <HeartIcon className="w-4 h-4 mr-1" />
                                                    <span>{post.like_count} likes</span>
                                                </div>
                                            )}
                                            {post.share_count !== undefined && (
                                                <div className="flex items-center">
                                                    <ShareIcon className="w-4 h-4 mr-1" />
                                                    <span>{post.share_count} shares</span>
                                                </div>
                                            )}
                                            {post.comment_count !== undefined && (
                                                <div className="flex items-center">
                                                    <ChatBubbleLeftRightIcon className="w-4 h-4 mr-1" />
                                                    <span>{post.comment_count} comments</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </article>
                    </div>

                    {/* Sidebar */}
                    <div className="lg:col-span-1">
                        {/* Agent Contact Card */}
                        {agent && (
                            <div className="bg-white rounded-2xl shadow-lg p-6 mb-6 sticky top-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">About the Author</h3>

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
                                </div>

                                <div className="space-y-3">
                                    <Link
                                        href={`/agent/${params.agentName}`}
                                        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-center block"
                                    >
                                        View Profile
                                    </Link>
                                    <Link
                                        href={`/agent/${params.agentName}/properties`}
                                        className="w-full border border-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-50 transition-colors text-center block"
                                    >
                                        View Properties
                                    </Link>
                                </div>
                            </div>
                        )}

                        {/* More Posts */}
                        <div className="bg-white rounded-2xl shadow-lg p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">More Posts</h3>
                            <p className="text-gray-600 text-sm mb-4">
                                Discover more insights and property updates from {agent?.agent_name || 'this agent'}.
                            </p>
                            <Link
                                href={`/agent/${params.agentName}/posts`}
                                className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
                            >
                                View All Posts →
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
