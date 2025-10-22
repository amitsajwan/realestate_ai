'use client'

import { api } from '@/lib/api'
import {
    AdjustmentsHorizontalIcon,
    BuildingOfficeIcon,
    ChatBubbleLeftIcon,
    ChevronDownIcon,
    DocumentTextIcon,
    GlobeAltIcon,
    MagnifyingGlassIcon,
    PencilIcon,
    PlusIcon,
    RocketLaunchIcon,
    ShareIcon,
    TrashIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
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
    media_urls?: string[]
    analytics?: {
        views: number
        likes: number
        shares: number
        comments: number
    }
}

interface MobilePostsManagementProps {
    onCreatePost: () => void
}

const statusColors = {
    draft: 'bg-amber-100 text-amber-800 border-amber-200',
    published: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    scheduled: 'bg-blue-100 text-blue-800 border-blue-200',
    promoted: 'bg-purple-100 text-purple-800 border-purple-200'
}

const channelIcons = {
    website: GlobeAltIcon,
    facebook: ShareIcon,
    instagram: ShareIcon,
    twitter: ShareIcon,
    linkedin: ShareIcon
}

export default function MobilePostsManagement({ onCreatePost }: MobilePostsManagementProps) {
    const [posts, setPosts] = useState<Post[]>([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [channelFilter, setChannelFilter] = useState<string>('all')
    const [sortBy, setSortBy] = useState<'date' | 'title' | 'status'>('date')
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
    const [showFilters, setShowFilters] = useState(false)
    const [selectedImage, setSelectedImage] = useState<{ url: string; index: number; total: number } | null>(null)

    useEffect(() => {
        loadPosts()
    }, [])

    const loadPosts = async () => {
        try {
            setLoading(true)
            console.log('[MobilePostsManagement] Fetching posts...')
            const response = await api.enhancedPosts.get()
            console.log('[MobilePostsManagement] Posts response:', response)
            setPosts(response || [])
        } catch (error) {
            console.error('Error loading posts:', error)
            toast.error('Failed to load posts')
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

    const handleImageClick = (url: string, index: number, total: number) => {
        setSelectedImage({ url, index, total })
    }

    const closeImageModal = () => {
        setSelectedImage(null)
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading posts...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Mobile Header */}
            <div className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
                <div className="px-4 py-4 max-w-2xl mx-auto">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">Posts</h1>
                            <p className="text-sm text-gray-600">Manage your content</p>
                        </div>
                        <button
                            onClick={onCreatePost}
                            className="bg-blue-600 text-white p-3 rounded-full shadow-lg"
                            aria-label="Create new post"
                        >
                            <PlusIcon className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Mobile Search */}
                    <div className="relative mb-3">
                        <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search posts..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                            aria-label="Search posts"
                        />
                    </div>

                    {/* Mobile Filter Toggle */}
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className="w-full flex items-center justify-between p-3 bg-gray-100 rounded-xl text-gray-700"
                        aria-label="Toggle filters"
                    >
                        <span className="flex items-center space-x-2">
                            <AdjustmentsHorizontalIcon className="w-5 h-5" />
                            <span>Filters</span>
                        </span>
                        <ChevronDownIcon className={`w-5 h-5 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
                    </button>
                </div>

                {/* Mobile Filters Panel */}
                <AnimatePresence>
                    {showFilters && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden bg-white border-t border-gray-100"
                        >
                            <div className="px-4 py-4 space-y-4">
                                {/* Status Filter */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                                    <select
                                        value={statusFilter}
                                        onChange={(e) => setStatusFilter(e.target.value)}
                                        className="w-full p-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                                        aria-label="Filter by status"
                                    >
                                        <option value="all">All Status</option>
                                        <option value="draft">Draft</option>
                                        <option value="published">Published</option>
                                        <option value="scheduled">Scheduled</option>
                                        <option value="promoted">Promoted</option>
                                    </select>
                                </div>

                                {/* Channel Filter */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Channel</label>
                                    <select
                                        value={channelFilter}
                                        onChange={(e) => setChannelFilter(e.target.value)}
                                        className="w-full p-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                                        aria-label="Filter by channel"
                                    >
                                        <option value="all">All Channels</option>
                                        <option value="facebook">Facebook</option>
                                        <option value="instagram">Instagram</option>
                                        <option value="twitter">Twitter</option>
                                        <option value="linkedin">LinkedIn</option>
                                        <option value="website">Website</option>
                                    </select>
                                </div>

                                {/* Sort */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Sort by</label>
                                    <select
                                        value={`${sortBy}-${sortOrder}`}
                                        onChange={(e) => {
                                            const [field, order] = e.target.value.split('-')
                                            setSortBy(field as any)
                                            setSortOrder(order as any)
                                        }}
                                        className="w-full p-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                                        aria-label="Sort posts"
                                    >
                                        <option value="date-desc">Newest First</option>
                                        <option value="date-asc">Oldest First</option>
                                        <option value="title-asc">Title A-Z</option>
                                        <option value="title-desc">Title Z-A</option>
                                        <option value="status-asc">Status</option>
                                    </select>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Mobile Posts List */}
            <div className="px-4 py-6 max-w-2xl mx-auto">
                {sortedPosts.length === 0 ? (
                    <div className="text-center py-16">
                        <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No posts found</h3>
                        <p className="text-gray-600 mb-6 max-w-sm mx-auto">
                            {searchTerm || statusFilter !== 'all' || channelFilter !== 'all'
                                ? 'Try adjusting your filters to see more posts.'
                                : 'Create your first post to get started.'}
                        </p>
                        {!searchTerm && statusFilter === 'all' && channelFilter === 'all' && (
                            <button
                                onClick={onCreatePost}
                                className="bg-blue-600 text-white px-6 py-3 rounded-xl font-medium"
                                aria-label="Create your first post"
                            >
                                Create Your First Post
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="space-y-4">
                        {sortedPosts.map((post) => (
                            <motion.div
                                key={post.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="agent-post-card"
                            >
                                {/* Facebook-Style Post Header */}
                                <div className="agent-post-header">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                                                <span className="text-white font-semibold text-lg">RE</span>
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-gray-900 text-base">Real Estate Agent</h3>
                                                <div className="flex items-center space-x-2">
                                                    <p className="text-sm text-gray-600">
                                                        {post.promotedAt
                                                            ? new Date(post.promotedAt).toLocaleDateString()
                                                            : post.publishedAt
                                                                ? new Date(post.publishedAt).toLocaleDateString()
                                                                : post.scheduledAt
                                                                    ? new Date(post.scheduledAt).toLocaleDateString()
                                                                    : 'Draft'
                                                        }
                                                    </p>
                                                    <span className="text-gray-400">•</span>
                                                    <div className="flex items-center space-x-1">
                                                        <GlobeAltIcon className="w-4 h-4 text-gray-500" />
                                                        <span className="text-sm text-gray-600">Public</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[post.status]}`}>
                                                {post.status}
                                            </span>
                                            <button className="p-1 hover:bg-gray-100 rounded-full">
                                                <span className="text-gray-500 text-xl">⋯</span>
                                            </button>
                                        </div>
                                    </div>

                                    {/* Post Content - Facebook Style */}
                                    <div className="agent-post-content">
                                        <p className="text-gray-900 text-base leading-relaxed">{post.content}</p>
                                    </div>

                                    {/* Property Images - Facebook Style Vertical Stack */}
                                    {post.media_urls && post.media_urls.length > 0 && (
                                        <div className="mb-4 space-y-2">
                                            {post.media_urls.slice(0, 4).map((url, index) => (
                                                <div key={url} className="relative cursor-pointer" onClick={() => handleImageClick(url, index, post.media_urls?.length || 0)}>
                                                    <img
                                                        src={url}
                                                        alt={`Property image ${index + 1}`}
                                                        className="w-full h-auto rounded-lg object-cover"
                                                        style={{
                                                            maxHeight: (post.media_urls?.length || 0) === 1 ? '400px' :
                                                                (post.media_urls?.length || 0) === 2 ? '250px' : '200px'
                                                        }}
                                                        onError={(e) => {
                                                            e.currentTarget.style.display = 'none';
                                                            const placeholder = e.currentTarget.parentElement?.querySelector('.image-placeholder');
                                                            if (placeholder) {
                                                                (placeholder as HTMLElement).style.display = 'flex';
                                                            }
                                                        }}
                                                    />
                                                    <div className="image-placeholder absolute inset-0 bg-gray-200 flex items-center justify-center text-gray-500 rounded-lg" style={{ display: 'none' }}>
                                                        <div className="text-center">
                                                            <BuildingOfficeIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                                                            <p className="text-sm">Image {index + 1}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                            {(post.media_urls?.length || 0) > 4 && (
                                                <div className="relative cursor-pointer" onClick={() => handleImageClick(post.media_urls![4], 4, post.media_urls?.length || 0)}>
                                                    <div className="w-full h-48 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600">
                                                        <div className="text-center">
                                                            <BuildingOfficeIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                                                            <p className="font-medium">+{(post.media_urls?.length || 0) - 4} more photos</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Facebook-Style Engagement */}
                                    <div className="agent-engagement">
                                        {/* Like/Comment/Share Stats */}
                                        <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                                            <div className="flex items-center space-x-4">
                                                <span className="flex items-center space-x-1">
                                                    <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                                                        <span className="text-white text-xs">👍</span>
                                                    </div>
                                                    <span>{post.analytics?.likes || 12}</span>
                                                </span>
                                                <span className="flex items-center space-x-1">
                                                    <span>{post.analytics?.shares || 3} shares</span>
                                                </span>
                                            </div>
                                            <span className="flex items-center space-x-1">
                                                <span>{post.analytics?.views || 45} comments</span>
                                            </span>
                                        </div>

                                        {/* Facebook-Style Action Buttons */}
                                        <div className="flex items-center border-t border-gray-200 pt-2">
                                            <button className="flex-1 flex items-center justify-center py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                                                <span className="text-lg mr-2">👍</span>
                                                <span className="font-medium">Like</span>
                                            </button>
                                            <button className="flex-1 flex items-center justify-center py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                                                <ChatBubbleLeftIcon className="w-5 h-5 mr-2" />
                                                <span className="font-medium">Comment</span>
                                            </button>
                                            <button className="flex-1 flex items-center justify-center py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                                                <ShareIcon className="w-5 h-5 mr-2" />
                                                <span className="font-medium">Share</span>
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                {/* Admin Actions - Hidden by default */}
                                <div className="bg-gray-50 px-4 py-2 border-t border-gray-100">
                                    <div className="flex items-center justify-between">
                                        <div className="text-xs text-gray-500">
                                            Created {new Date(post.createdAt).toLocaleDateString()}
                                        </div>
                                        <div className="flex items-center space-x-1">
                                            <button
                                                onClick={() => {/* TODO: Implement edit */ }}
                                                className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                                                aria-label="Edit post"
                                            >
                                                <PencilIcon className="w-4 h-4" />
                                            </button>

                                            {post.status === 'draft' && (
                                                <button
                                                    onClick={() => handlePublishPost(post.id)}
                                                    className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                                                    aria-label="Publish post"
                                                >
                                                    <ShareIcon className="w-4 h-4" />
                                                </button>
                                            )}

                                            {post.status === 'published' && (
                                                <button
                                                    onClick={() => handlePromotePost(post.id)}
                                                    className="p-1 text-gray-400 hover:text-purple-600 transition-colors"
                                                    aria-label="Promote post"
                                                >
                                                    <RocketLaunchIcon className="w-4 h-4" />
                                                </button>
                                            )}

                                            <button
                                                onClick={() => handleDeletePost(post.id)}
                                                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                                                aria-label="Delete post"
                                            >
                                                <TrashIcon className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>

            {/* Image Modal */}
            <AnimatePresence>
                {selectedImage && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
                        onClick={closeImageModal}
                    >
                        <motion.div
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.8, opacity: 0 }}
                            className="relative max-w-4xl max-h-full w-full h-full flex items-center justify-center"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Close button */}
                            <button
                                onClick={closeImageModal}
                                className="absolute top-4 right-4 z-10 bg-black bg-opacity-50 text-white rounded-full p-2 hover:bg-opacity-70 transition-all"
                                aria-label="Close image"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>

                            {/* Image */}
                            <img
                                src={selectedImage.url}
                                alt="Property image"
                                className="max-w-full max-h-full object-contain rounded-lg"
                                onError={(e) => {
                                    e.currentTarget.style.display = 'none';
                                }}
                            />

                            {/* Image counter */}
                            {selectedImage.total > 1 && (
                                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm">
                                    {selectedImage.index + 1} of {selectedImage.total}
                                </div>
                            )}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
