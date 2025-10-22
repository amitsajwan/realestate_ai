'use client'

import { api } from '@/lib/api'
import {
    BuildingOfficeIcon,
    ChatBubbleLeftIcon,
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
    const [selectedImage, setSelectedImage] = useState<{ url: string; index: number; total: number } | null>(null)

    useEffect(() => {
        loadPosts()
    }, [])

    // Add a refresh mechanism that can be called from parent components
    const refreshPosts = () => {
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
            const response = await api.enhancedPosts.get()
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

    const handleImageClick = (url: string, index: number, total: number) => {
        setSelectedImage({ url, index, total })
    }

    const closeImageModal = () => {
        setSelectedImage(null)
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        )
    }

    return (
        <div className="posts-management-mobile space-y-4 md:space-y-6">
            {/* Header */}
            <div className="posts-header-mobile flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex-1">
                    <h2 className="posts-title-mobile text-xl md:text-2xl font-bold text-gray-900">Posts Management</h2>
                    <p className="posts-description-mobile text-sm md:text-base text-gray-600 mt-1">Manage your published content, drafts, and scheduled posts</p>
                </div>
                <div className="posts-actions-mobile flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
                    <button
                        onClick={loadPosts}
                        className="bg-gray-600 text-white px-4 py-3 rounded-lg hover:bg-gray-700 flex items-center justify-center space-x-2 text-sm font-medium min-h-[44px]"
                        title="Refresh posts"
                        aria-label="Refresh posts"
                    >
                        <span>Refresh</span>
                    </button>
                    <button
                        onClick={onCreatePost}
                        className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center space-x-2 text-sm font-medium min-h-[44px]"
                        title="Create New Post"
                        aria-label="Create New Post"
                    >
                        <PlusIcon className="w-5 h-5" />
                        <span className="hidden sm:inline">Create New Post</span>
                        <span className="sm:hidden">Create</span>
                    </button>
                </div>
            </div>

            {/* Filters and Search */}
            <div className="bg-white p-3 md:p-4 rounded-lg border border-gray-200">
                <div className="posts-filters-mobile grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                    {/* Search */}
                    <div className="relative sm:col-span-2 lg:col-span-1">
                        <label htmlFor="search-posts" className="sr-only">Search posts</label>
                        <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                            id="search-posts"
                            type="text"
                            placeholder="Search posts..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base min-h-[44px]"
                            title="Search posts"
                            aria-label="Search posts"
                        />
                    </div>

                    {/* Status Filter */}
                    <div>
                        <label htmlFor="status-filter" className="sr-only">Filter by status</label>
                        <select
                            id="status-filter"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base min-h-[44px] bg-white"
                            title="Filter by status"
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
                        <label htmlFor="channel-filter" className="sr-only">Filter by channel</label>
                        <select
                            id="channel-filter"
                            value={channelFilter}
                            onChange={(e) => setChannelFilter(e.target.value)}
                            className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base min-h-[44px] bg-white"
                            title="Filter by channel"
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
                        <label htmlFor="sort-posts" className="sr-only">Sort posts</label>
                        <select
                            id="sort-posts"
                            value={`${sortBy}-${sortOrder}`}
                            onChange={(e) => {
                                const [field, order] = e.target.value.split('-')
                                setSortBy(field as any)
                                setSortOrder(order as any)
                            }}
                            className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base min-h-[44px] bg-white"
                            title="Sort posts"
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
            </div>

            {/* Posts List */}
            <div className="space-y-3 md:space-y-4 max-w-4xl mx-auto">
                {sortedPosts.length === 0 ? (
                    <div className="text-center py-8 md:py-12 px-4">
                        <DocumentTextIcon className="w-12 h-12 md:w-16 md:h-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg md:text-xl font-medium text-gray-900 mb-2">No posts found</h3>
                        <p className="text-sm md:text-base text-gray-600 mb-6 max-w-md mx-auto">
                            {searchTerm || statusFilter !== 'all' || channelFilter !== 'all'
                                ? 'Try adjusting your filters to see more posts.'
                                : 'Create your first post to get started.'}
                        </p>
                        {!searchTerm && statusFilter === 'all' && channelFilter === 'all' && (
                            <button
                                onClick={onCreatePost}
                                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 text-sm font-medium min-h-[44px]"
                                title="Create Your First Post"
                                aria-label="Create Your First Post"
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
                            className="agent-post-card bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
                            style={{ pointerEvents: 'auto' }}
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

                                {/* Property Images - Mobile Optimized */}
                                {post.media_urls && post.media_urls.length > 0 ? (
                                    <div className="agent-post-images mb-4 space-y-2">
                                        {post.media_urls.slice(0, 4).map((url, index) => (
                                            <div key={url} className="relative cursor-pointer" onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                handleImageClick(url, index, post.media_urls?.length || 0);
                                            }}>
                                                <img
                                                    src={url}
                                                    alt={`Property image ${index + 1}`}
                                                    className="w-full h-auto rounded-lg object-cover hover:opacity-95 transition-opacity"
                                                    style={{
                                                        maxHeight: (post.media_urls?.length || 0) === 1 ? '400px' :
                                                            (post.media_urls?.length || 0) === 2 ? '300px' : '250px'
                                                    }}
                                                    onError={(e) => {
                                                        console.error('Failed to load image:', url);
                                                        e.currentTarget.style.display = 'none';
                                                        const placeholder = e.currentTarget.parentElement?.querySelector('.image-placeholder');
                                                        if (placeholder) {
                                                            (placeholder as HTMLElement).style.display = 'flex';
                                                        }
                                                    }}
                                                />
                                                {/* Fallback placeholder */}
                                                <div className="image-placeholder absolute inset-0 bg-gray-200 flex items-center justify-center text-gray-500 rounded-lg" style={{ display: 'none' }}>
                                                    <div className="text-center">
                                                        <BuildingOfficeIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                                                        <p className="text-sm">Image {index + 1}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                        {(post.media_urls?.length || 0) > 4 && (
                                            <div className="relative cursor-pointer" onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                handleImageClick(post.media_urls![4], 4, post.media_urls?.length || 0);
                                            }}>
                                                <div className="w-full h-48 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600 hover:bg-gray-200 transition-colors">
                                                    <div className="text-center">
                                                        <BuildingOfficeIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                                                        <p className="font-medium">+{(post.media_urls?.length || 0) - 4} more photos</p>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="bg-gradient-to-r from-blue-100 to-purple-100 rounded-lg h-48 flex items-center justify-center mb-4">
                                        <div className="text-center">
                                            <BuildingOfficeIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                                            <p className="text-gray-500 text-sm">No Images</p>
                                        </div>
                                    </div>
                                )}

                                {/* Facebook-Style Engagement */}
                                <div className="agent-engagement">
                                    {/* Like/Comment/Share Stats */}
                                    <div className="agent-engagement-stats">
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
                                    <div className="agent-engagement-actions">
                                        <button className="agent-engagement-button">
                                            <span className="text-lg mr-2">👍</span>
                                            <span className="font-medium">Like</span>
                                        </button>
                                        <button className="agent-engagement-button">
                                            <ChatBubbleLeftIcon className="w-5 h-5 mr-2" />
                                            <span className="font-medium">Comment</span>
                                        </button>
                                        <button className="agent-engagement-button">
                                            <ShareIcon className="w-5 h-5 mr-2" />
                                            <span className="font-medium">Share</span>
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Admin Actions - Mobile Optimized */}
                            <div className="bg-gray-50 px-4 py-3 border-t border-gray-100">
                                <div className="flex items-center justify-between">
                                    <div className="text-xs text-gray-500">
                                        Created {new Date(post.createdAt).toLocaleDateString()}
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <button
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                // TODO: Implement edit functionality
                                            }}
                                            className="p-2 text-gray-400 hover:text-blue-600 transition-colors rounded-lg hover:bg-blue-50"
                                            aria-label="Edit post"
                                            title="Edit post"
                                            type="button"
                                        >
                                            <PencilIcon className="w-4 h-4" />
                                            <span className="sr-only">Edit post</span>
                                        </button>

                                        {post.status === 'draft' && (
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    e.stopPropagation();
                                                    handlePublishPost(post.id);
                                                }}
                                                className="p-2 text-gray-400 hover:text-green-600 transition-colors rounded-lg hover:bg-green-50"
                                                aria-label="Publish post"
                                                title="Publish post"
                                                type="button"
                                            >
                                                <ShareIcon className="w-4 h-4" />
                                                <span className="sr-only">Publish post</span>
                                            </button>
                                        )}

                                        {post.status === 'published' && (
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    e.stopPropagation();
                                                    handlePromotePost(post.id);
                                                }}
                                                className="p-2 text-gray-400 hover:text-purple-600 transition-colors rounded-lg hover:bg-purple-50"
                                                aria-label="Promote post"
                                                title="Promote post"
                                                type="button"
                                            >
                                                <RocketLaunchIcon className="w-4 h-4" />
                                                <span className="sr-only">Promote post</span>
                                            </button>
                                        )}

                                        <button
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                handleDeletePost(post.id);
                                            }}
                                            className="p-2 text-gray-400 hover:text-red-600 transition-colors rounded-lg hover:bg-red-50"
                                            aria-label="Delete post"
                                            title="Delete post"
                                            type="button"
                                        >
                                            <TrashIcon className="w-4 h-4" />
                                            <span className="sr-only">Delete post</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))
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
