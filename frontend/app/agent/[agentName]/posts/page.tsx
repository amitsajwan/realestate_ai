'use client'

import { PostCard } from '@/components/PostCard'
import {
    DocumentTextIcon,
    FunnelIcon,
    MagnifyingGlassIcon,
    PlusIcon
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
    const [totalPages, setTotalPages] = useState(1)
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedLanguage, setSelectedLanguage] = useState('')
    const [selectedChannel, setSelectedChannel] = useState('')

    const agentName = params.agentName.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

    useEffect(() => {
        loadAgentData()
    }, [params.agentName, currentPage, searchQuery, selectedLanguage, selectedChannel])

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

            // Load agent posts with filters
            const queryParams = new URLSearchParams({
                page: currentPage.toString(),
                limit: '12'
            })

            if (searchQuery) queryParams.append('search', searchQuery)
            if (selectedLanguage) queryParams.append('language', selectedLanguage)
            if (selectedChannel) queryParams.append('channel', selectedChannel)

            const postsResponse = await fetch(`${API_BASE_URL}/api/v1/agent/public/${params.agentName}/posts?${queryParams}`)

            if (postsResponse.ok) {
                const postsData = await postsResponse.json()
                setPosts(postsData.posts || postsData || [])
                setTotalPages(postsData.total_pages || 1)
            } else {
                console.warn('Failed to load agent posts:', postsResponse.status)
                setPosts([])
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load posts')
        } finally {
            setIsLoading(false)
        }
    }

    const clearFilters = () => {
        setSearchQuery('')
        setSelectedLanguage('')
        setSelectedChannel('')
        setCurrentPage(1)
    }

    const languages = [
        { code: 'en', name: 'English' },
        { code: 'hi', name: 'Hindi' },
        { code: 'ta', name: 'Tamil' },
        { code: 'te', name: 'Telugu' },
        { code: 'bn', name: 'Bengali' },
        { code: 'gu', name: 'Gujarati' },
        { code: 'kn', name: 'Kannada' },
        { code: 'ml', name: 'Malayalam' },
        { code: 'mr', name: 'Marathi' },
        { code: 'pa', name: 'Punjabi' },
        { code: 'ur', name: 'Urdu' }
    ]

    const channels = [
        { code: 'facebook', name: 'Facebook' },
        { code: 'instagram', name: 'Instagram' },
        { code: 'linkedin', name: 'LinkedIn' },
        { code: 'twitter', name: 'Twitter' }
    ]

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading Posts</h2>
                    <p className="text-gray-600">Finding the latest insights from {agentName}...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
                <div className="text-center max-w-md mx-auto">
                    <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <DocumentTextIcon className="w-10 h-10 text-red-500" />
                    </div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-4">Oops! Something went wrong</h1>
                    <p className="text-gray-600 mb-8">{error}</p>
                    <button
                        onClick={loadAgentData}
                        className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
            {/* Hero Header */}
            <header className="relative bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 text-white overflow-hidden">
                <div className="absolute inset-0 bg-black/20"></div>
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600/30 to-purple-600/30"></div>
                <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                    <div className="flex items-center justify-between">
                        <div>
                            <Link href="/" className="text-4xl font-bold text-white hover:text-blue-200 transition-colors">
                                PropertyAI
                            </Link>
                            <p className="text-blue-100 mt-3 text-xl">
                                Latest Insights by {agentName}
                            </p>
                            <div className="flex items-center mt-4 space-x-6">
                                <div className="flex items-center text-blue-200">
                                    <DocumentTextIcon className="w-5 h-5 mr-2" />
                                    <span>Real Estate Insights</span>
                                </div>
                                <div className="flex items-center text-blue-200">
                                    <PlusIcon className="w-5 h-5 mr-2" />
                                    <span>Market Updates</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center space-x-6">
                            <Link
                                href={`/agent/${params.agentName}`}
                                className="text-white/90 hover:text-white font-medium transition-colors"
                            >
                                Agent Profile
                            </Link>
                            <Link
                                href={`/agent/${params.agentName}/properties`}
                                className="bg-white/20 backdrop-blur-sm text-white px-8 py-3 rounded-full hover:bg-white/30 transition-all duration-300 font-medium shadow-lg hover:shadow-xl"
                            >
                                View Properties
                            </Link>
                        </div>
                    </div>
                </div>
                {/* Decorative elements */}
                <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-white/10 to-transparent rounded-full -translate-y-48 translate-x-48"></div>
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-tr from-white/5 to-transparent rounded-full translate-y-32 -translate-x-32"></div>
            </header>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Search and Filters */}
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8 mb-12">
                    <div className="flex flex-col lg:flex-row gap-6">
                        {/* Search Bar */}
                        <div className="flex-1">
                            <div className="relative group">
                                <MagnifyingGlassIcon className="w-6 h-6 absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                                <input
                                    type="text"
                                    placeholder="Search posts by title or content..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 text-lg bg-white/50 backdrop-blur-sm"
                                />
                            </div>
                        </div>

                        {/* Language Filter */}
                        <select
                            value={selectedLanguage}
                            onChange={(e) => setSelectedLanguage(e.target.value)}
                            className="px-6 py-4 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 text-lg bg-white/50 backdrop-blur-sm"
                        >
                            <option value="">All Languages</option>
                            {languages.map((lang) => (
                                <option key={lang.code} value={lang.code}>
                                    {lang.name}
                                </option>
                            ))}
                        </select>

                        {/* Channel Filter */}
                        <select
                            value={selectedChannel}
                            onChange={(e) => setSelectedChannel(e.target.value)}
                            className="px-6 py-4 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 text-lg bg-white/50 backdrop-blur-sm"
                        >
                            <option value="">All Channels</option>
                            {channels.map((channel) => (
                                <option key={channel.code} value={channel.code}>
                                    {channel.name}
                                </option>
                            ))}
                        </select>

                        {/* Clear Filters */}
                        <button
                            onClick={clearFilters}
                            className="flex items-center px-6 py-4 bg-gradient-to-r from-gray-600 to-gray-700 text-white rounded-xl hover:from-gray-700 hover:to-gray-800 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                        >
                            <FunnelIcon className="w-5 h-5 mr-2" />
                            Clear
                        </button>
                    </div>
                </div>

                {/* Results Count */}
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        <h2 className="text-3xl font-bold text-gray-900">
                            Latest Posts
                        </h2>
                        <p className="text-gray-600 text-lg">
                            {posts.length} {posts.length === 1 ? 'post' : 'posts'} found
                        </p>
                    </div>
                </div>

                {/* Posts Grid */}
                {posts.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {posts.map((post) => (
                            <PostCard
                                key={post.id}
                                post={post}
                                agentName={params.agentName}
                                showFullContent={false}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20">
                        <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto mb-8">
                            <DocumentTextIcon className="w-12 h-12 text-blue-400" />
                        </div>
                        <h3 className="text-3xl font-bold text-gray-900 mb-4">No Posts Found</h3>
                        <p className="text-gray-600 mb-8 text-lg max-w-md mx-auto">
                            We couldn't find any posts matching your criteria. Try adjusting your search or clear the filters.
                        </p>
                        <button
                            onClick={clearFilters}
                            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                        >
                            Clear All Filters
                        </button>
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="mt-16 flex justify-center">
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                disabled={currentPage === 1}
                                className="px-6 py-3 border-2 border-gray-200 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 hover:border-gray-300 transition-all duration-300 font-medium"
                            >
                                Previous
                            </button>

                            <div className="flex items-center space-x-2">
                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                    const page = i + 1
                                    return (
                                        <button
                                            key={page}
                                            onClick={() => setCurrentPage(page)}
                                            className={`w-12 h-12 rounded-xl font-medium transition-all duration-300 ${currentPage === page
                                                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                                                : 'text-gray-600 hover:bg-gray-100'
                                                }`}
                                        >
                                            {page}
                                        </button>
                                    )
                                })}
                            </div>

                            <button
                                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                disabled={currentPage === totalPages}
                                className="px-6 py-3 border-2 border-gray-200 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 hover:border-gray-300 transition-all duration-300 font-medium"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
