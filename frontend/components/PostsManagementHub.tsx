'use client'

import { api } from '@/lib/api'
import {
    BuildingOfficeIcon,
    ChartBarIcon,
    DocumentTextIcon,
    EyeIcon,
    GlobeAltIcon,
    MagnifyingGlassIcon,
    PencilIcon,
    PlusIcon,
    RocketLaunchIcon,
    ShareIcon,
    TrashIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'

interface Post {
    id: string
    title: string
    content: string
    status: 'draft' | 'published' | 'scheduled' | 'promoted'
    channels: string[]
    createdAt: string
    publishedAt?: string
    scheduledAt?: string
    promotedAt?: string
    propertyId?: string
    propertyTitle?: string
    analytics?: {
        views: number
        likes: number
        shares: number
        comments: number
    }
}

interface PostsManagementHubProps {
    onCreatePost: () => void
}

const statusColors = {
    draft: 'bg-yellow-100 text-yellow-800',
    published: 'bg-green-100 text-green-800',
    scheduled: 'bg-blue-100 text-blue-800',
    promoted: 'bg-purple-100 text-purple-800'
}

const channelIcons = {
    website: GlobeAltIcon,
    facebook: ShareIcon,
    instagram: ShareIcon,
    twitter: ShareIcon,
    linkedin: ShareIcon
}

export default function PostsManagementHub({ onCreatePost }: PostsManagementHubProps) {
    const [posts, setPosts] = useState<Post[]>([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [channelFilter, setChannelFilter] = useState<string>('all')
    const [sortBy, setSortBy] = useState<'date' | 'title' | 'status'>('date')
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

    useEffect(() => {
        loadPosts()
    }, [])

    // Add a refresh mechanism that can be called from parent components
    const refreshPosts = () => {
        console.log('[PostsManagementHub] Refreshing posts...')
        loadPosts()
    }

    // Expose refreshPosts to parent components via window object for now
    useEffect(() => {
        (window as any).refreshPostsManagementHub = refreshPosts
        return () => {
            delete (window as any).refreshPostsManagementHub
        }
    }, [])

    const loadPosts = async () => {
        try {
            setLoading(true)
            console.log('[PostsManagementHub] Fetching posts...')
            const response = await api.enhancedPosts.get()
            console.log('[PostsManagementHub] Posts response:', response)
            console.log('[PostsManagementHub] Number of posts:', response?.length || 0)
            setPosts(response || [])
        } catch (error) {
            console.error('Error loading posts:', error)
            toast.error('Failed to load posts')
            // Fallback to empty array if API fails
            setPosts([])
        } finally {
            setLoading(false)
        }
    }

    const filteredPosts = posts.filter(post => {
        const matchesSearch = post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            post.content.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === 'all' || post.status === statusFilter
        const matchesChannel = channelFilter === 'all' || post.channels.includes(channelFilter)

        return matchesSearch && matchesStatus && matchesChannel
    })

    const sortedPosts = [...filteredPosts].sort((a, b) => {
        let comparison = 0
        switch (sortBy) {
            case 'date':
                comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
                break
            case 'title':
                comparison = a.title.localeCompare(b.title)
                break
            case 'status':
                comparison = a.status.localeCompare(b.status)
                break
        }
        return sortOrder === 'asc' ? comparison : -comparison
    })

    const handleDeletePost = async (postId: string) => {
        if (!confirm('Are you sure you want to delete this post?')) return

        try {
            await api.enhancedPosts.delete(postId)
            setPosts(posts.filter(post => post.id !== postId))
            toast.success('Post deleted successfully')
        } catch (error) {
            console.error('Error deleting post:', error)
            toast.error('Failed to delete post')
        }
    }

    const handlePublishPost = async (postId: string) => {
        try {
            await api.enhancedPosts.publish(postId, ['facebook', 'instagram'])
            setPosts(posts.map(post =>
                post.id === postId
                    ? { ...post, status: 'published' as const, publishedAt: new Date().toISOString() }
                    : post
            ))
            toast.success('Post published successfully')
        } catch (error) {
            console.error('Error publishing post:', error)
            toast.error('Failed to publish post')
        }
    }

    const handlePromotePost = async (postId: string) => {
        try {
            // TODO: Implement promote API call when backend supports it
            // await api.enhancedPosts.promote(postId, ['facebook', 'instagram'])
            setPosts(posts.map(post =>
                post.id === postId
                    ? { ...post, status: 'promoted' as const, promotedAt: new Date().toISOString() }
                    : post
            ))
            toast.success('Post promoted successfully')
        } catch (error) {
            console.error('Error promoting post:', error)
            toast.error('Failed to promote post')
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Posts Management</h2>
                    <p className="text-gray-600">Manage your published content, drafts, and scheduled posts</p>
                </div>
                <div className="flex items-center space-x-3">
                    <button
                        onClick={loadPosts}
                        className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center space-x-2"
                    >
                        <span>Refresh</span>
                    </button>
                    <button
                        onClick={onCreatePost}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
                    >
                        <PlusIcon className="w-5 h-5" />
                        <span>Create New Post</span>
                    </button>
                </div>
            </div>

            {/* Filters and Search */}
            <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Search */}
                    <div className="relative">
                        <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search posts..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    {/* Status Filter */}
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <option value="all">All Status</option>
                        <option value="draft">Draft</option>
                        <option value="published">Published</option>
                        <option value="scheduled">Scheduled</option>
                        <option value="promoted">Promoted</option>
                    </select>

                    {/* Channel Filter */}
                    <select
                        value={channelFilter}
                        onChange={(e) => setChannelFilter(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <option value="all">All Channels</option>
                        <option value="facebook">Facebook</option>
                        <option value="instagram">Instagram</option>
                        <option value="twitter">Twitter</option>
                        <option value="linkedin">LinkedIn</option>
                        <option value="website">Website</option>
                    </select>

                    {/* Sort */}
                    <select
                        value={`${sortBy}-${sortOrder}`}
                        onChange={(e) => {
                            const [field, order] = e.target.value.split('-')
                            setSortBy(field as any)
                            setSortOrder(order as any)
                        }}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <option value="date-desc">Newest First</option>
                        <option value="date-asc">Oldest First</option>
                        <option value="title-asc">Title A-Z</option>
                        <option value="title-desc">Title Z-A</option>
                        <option value="status-asc">Status</option>
                    </select>
                </div>
            </div>

            {/* Posts List */}
            <div className="space-y-4">
                {sortedPosts.length === 0 ? (
                    <div className="text-center py-12">
                        <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No posts found</h3>
                        <p className="text-gray-600 mb-4">
                            {searchTerm || statusFilter !== 'all' || channelFilter !== 'all'
                                ? 'Try adjusting your filters to see more posts.'
                                : 'Create your first post to get started.'}
                        </p>
                        {!searchTerm && statusFilter === 'all' && channelFilter === 'all' && (
                            <button
                                onClick={onCreatePost}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                            >
                                Create Your First Post
                            </button>
                        )}
                    </div>
                ) : (
                    sortedPosts.map((post) => (
                        <motion.div
                            key={post.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
                        >
                            {/* Post Header */}
                            <div className="p-4 border-b border-gray-100">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                                            <span className="text-white font-semibold text-sm">RE</span>
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-gray-900">Real Estate Agent</h3>
                                            <p className="text-sm text-gray-500">
                                                {post.promotedAt
                                                    ? `Promoted ${new Date(post.promotedAt).toLocaleDateString()}`
                                                    : post.publishedAt
                                                        ? `Published ${new Date(post.publishedAt).toLocaleDateString()}`
                                                        : post.scheduledAt
                                                            ? `Scheduled for ${new Date(post.scheduledAt).toLocaleDateString()}`
                                                            : 'Draft'
                                                }
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[post.status]}`}>
                                            {post.status}
                                        </span>
                                        <div className="flex items-center space-x-1">
                                            {post.channels.map((channel) => {
                                                const Icon = channelIcons[channel as keyof typeof channelIcons]
                                                return (
                                                    <div key={channel} className="p-1 bg-gray-100 rounded">
                                                        {Icon && <Icon className="w-4 h-4 text-gray-600" />}
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Post Content - Social Media Style */}
                            <div className="p-4">
                                <h4 className="text-lg font-semibold text-gray-900 mb-2">{post.title}</h4>
                                <p className="text-gray-700 mb-4 leading-relaxed">{post.content}</p>

                                {/* Property Image Placeholder */}
                                <div className="bg-gradient-to-r from-blue-100 to-purple-100 rounded-lg h-48 flex items-center justify-center mb-4">
                                    <div className="text-center">
                                        <BuildingOfficeIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                                        <p className="text-gray-500 text-sm">Property Image</p>
                                    </div>
                                </div>

                                {/* Social Media Engagement */}
                                {post.analytics && (
                                    <div className="flex items-center justify-between text-sm text-gray-500 border-t border-gray-100 pt-3">
                                        <div className="flex items-center space-x-4">
                                            <span className="flex items-center space-x-1">
                                                <EyeIcon className="w-4 h-4" />
                                                <span>{post.analytics.views}</span>
                                            </span>
                                            <span className="flex items-center space-x-1">
                                                <ChartBarIcon className="w-4 h-4" />
                                                <span>{post.analytics.likes}</span>
                                            </span>
                                            <span className="flex items-center space-x-1">
                                                <ShareIcon className="w-4 h-4" />
                                                <span>{post.analytics.shares}</span>
                                            </span>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <button className="p-1 hover:bg-gray-100 rounded">
                                                <ChartBarIcon className="w-4 h-4" />
                                            </button>
                                            <button className="p-1 hover:bg-gray-100 rounded">
                                                <ShareIcon className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Management Actions */}
                            <div className="bg-gray-50 px-4 py-3 border-t border-gray-100">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                                        <span>Created {new Date(post.createdAt).toLocaleDateString()}</span>
                                        {post.propertyTitle && (
                                            <span>• {post.propertyTitle}</span>
                                        )}
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <button
                                            onClick={() => {/* TODO: Implement edit */ }}
                                            className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                                            title="Edit post"
                                        >
                                            <PencilIcon className="w-4 h-4" />
                                        </button>

                                        {/* Show Publish button only for draft posts */}
                                        {post.status === 'draft' && (
                                            <button
                                                onClick={() => handlePublishPost(post.id)}
                                                className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                                                title="Publish post"
                                            >
                                                <ShareIcon className="w-4 h-4" />
                                            </button>
                                        )}

                                        {/* Show Promote button only for published posts */}
                                        {post.status === 'published' && (
                                            <button
                                                onClick={() => handlePromotePost(post.id)}
                                                className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
                                                title="Promote post"
                                            >
                                                <RocketLaunchIcon className="w-4 h-4" />
                                            </button>
                                        )}

                                        <button
                                            onClick={() => handleDeletePost(post.id)}
                                            className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                                            title="Delete post"
                                        >
                                            <TrashIcon className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    )
}
