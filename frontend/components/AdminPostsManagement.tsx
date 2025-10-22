'use client'

import { api } from '@/lib/api'
import {
    ArrowDownTrayIcon,
    Bars3Icon,
    ChevronDownIcon,
    DocumentTextIcon,
    MagnifyingGlassIcon,
    PlusIcon,
    RocketLaunchIcon,
    ShareIcon,
    VideoCameraIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import PostEditModal from './PostEditModal'
import PostPreviewModal from './PostPreviewModal'

interface Post {
    id: string
    title: string
    content: string
    status: 'draft' | 'published' | 'scheduled' | 'promoted'
    channels: string[]
    media_urls?: string[]
    publishedAt?: string
    scheduledAt?: string
    promotedAt?: string
    createdAt: string
    analytics?: {
        views: number
        likes: number
        shares: number
        reach: number
    }
    propertyTitle?: string
}

interface AdminPostsManagementProps {
    onCreatePost: () => void
}

const statusColors = {
    draft: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    published: 'bg-green-100 text-green-800 border-green-200',
    scheduled: 'bg-blue-100 text-blue-800 border-blue-200',
    promoted: 'bg-purple-100 text-purple-800 border-purple-200'
}

const channelIcons = {
    facebook: ShareIcon,
    instagram: ShareIcon,
    twitter: ShareIcon,
    linkedin: ShareIcon,
    website: ShareIcon
}

export default function AdminPostsManagement({ onCreatePost }: AdminPostsManagementProps) {
    const [posts, setPosts] = useState<Post[]>([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [channelFilter, setChannelFilter] = useState<string>('all')
    const [postTypeFilter, setPostTypeFilter] = useState<string>('all')
    const [selectedPosts, setSelectedPosts] = useState<Set<string>>(new Set())
    const [sortBy, setSortBy] = useState<'date' | 'title' | 'status' | 'reach' | 'views'>('date')
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
    const [showColumns, setShowColumns] = useState(true)
    const [activeTab, setActiveTab] = useState<'published' | 'scheduled' | 'drafts' | 'expiring' | 'expired'>('drafts')
    const [editingPost, setEditingPost] = useState<Post | null>(null)
    const [showEditModal, setShowEditModal] = useState(false)
    const [previewPost, setPreviewPost] = useState<Post | null>(null)
    const [showPreviewModal, setShowPreviewModal] = useState(false)
    const mountedRef = useRef(true)
    const loadingRef = useRef(false)
    const componentId = useRef(Math.random().toString(36).substr(2, 9))
    const postsRef = useRef<Post[]>([])

    // Global check to prevent multiple instances
    const globalLoadingKey = 'AdminPostsManagement_loading'
    const globalPostsKey = 'AdminPostsManagement_posts'
    const isGlobalLoading = typeof window !== 'undefined' && (window as any)[globalLoadingKey]
    const globalPosts = typeof window !== 'undefined' && (window as any)[globalPostsKey]

    useEffect(() => {
        console.log(`[AdminPostsManagement-${componentId.current}] Component mounted`)

        // Check if we have global posts first
        if (globalPosts && globalPosts.length > 0) {
            console.log(`[AdminPostsManagement-${componentId.current}] Loading from global storage:`, globalPosts.length, 'posts')
            setPosts(globalPosts)
            postsRef.current = globalPosts
            setLoading(false) // Set loading to false when loading from global storage
        } else {
            loadPosts()
        }

        return () => {
            console.log(`[AdminPostsManagement-${componentId.current}] Component unmounting`)
            mountedRef.current = false
        }
    }, []) // Empty dependency array to run only once

    // Monitor posts state changes
    useEffect(() => {
        console.log(`[AdminPostsManagement-${componentId.current}] Posts state changed: ${posts.length} posts, ref: ${postsRef.current.length} posts`)
        if (posts.length > 0) {
            console.log(`[AdminPostsManagement-${componentId.current}] First post:`, posts[0])
            setLoading(false) // Ensure loading is false when we have posts
        } else if (postsRef.current.length > 0) {
            console.log(`[AdminPostsManagement-${componentId.current}] Using ref posts:`, postsRef.current[0])
            setLoading(false) // Ensure loading is false when we have posts in ref
        }
    }, [posts])

    const loadPosts = async () => {
        if (loadingRef.current || isGlobalLoading) {
            console.log(`[AdminPostsManagement-${componentId.current}] Already loading globally or locally, skipping duplicate API call`)
            return
        }

        loadingRef.current = true
        if (typeof window !== 'undefined') {
            (window as any)[globalLoadingKey] = true
        }
        try {
            setLoading(true)
            console.log(`[AdminPostsManagement-${componentId.current}] Loading posts...`)
            const response = await api.enhancedPosts.get()
            console.log('[AdminPostsManagement] API response:', response)
            console.log('[AdminPostsManagement] Response type:', typeof response)
            console.log('[AdminPostsManagement] Response length:', Array.isArray(response) ? response.length : 'Not an array')

            // Handle different response formats
            let postsData = []
            if (Array.isArray(response)) {
                postsData = response
            } else if (response && Array.isArray(response.data)) {
                postsData = response.data
            } else if (response && response.posts && Array.isArray(response.posts)) {
                postsData = response.posts
            }

            console.log('[AdminPostsManagement] Processed posts data:', postsData)

            // Store immediately regardless of mount status
            if (typeof window !== 'undefined') {
                (window as any)[globalPostsKey] = postsData
                console.log('[AdminPostsManagement] Global posts updated with', postsData.length, 'posts')
            }

            // Store in ref immediately
            postsRef.current = postsData
            console.log('[AdminPostsManagement] Posts ref updated with', postsRef.current.length, 'posts')

            // Force a re-render by updating state
            if (mountedRef.current) {
                setPosts(postsData)
                console.log('[AdminPostsManagement] Posts state updated with', postsData.length, 'posts')
            }

            console.log('[AdminPostsManagement] First post sample:', postsData[0])

            // Force component to re-render
            setTimeout(() => {
                console.log('[AdminPostsManagement] Forcing re-render with posts:', postsData.length)
                setPosts(postsData)
                setLoading(false) // Ensure loading is set to false after data is loaded
            }, 100)
        } catch (error) {
            console.error('Error loading posts:', error)
            toast.error('Failed to load posts')
        } finally {
            setLoading(false)
            loadingRef.current = false
            if (typeof window !== 'undefined') {
                (window as any)[globalLoadingKey] = false
            }
        }
    }

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

    const handleEditPost = (postId: string) => {
        const post = posts.find(p => p.id === postId)
        if (post) {
            setEditingPost(post)
            setShowEditModal(true)
        }
    }

    const handlePreviewPost = (postId: string) => {
        // Try multiple data sources to find the post
        let post = currentPosts.find((p: any) => p.id === postId)
        if (!post) {
            post = postsRef.current.find((p: any) => p.id === postId)
        }
        if (!post) {
            post = posts.find((p: any) => p.id === postId)
        }

        if (post) {
            setPreviewPost(post)
            setShowPreviewModal(true)
        }
    }

    const handleSavePost = (updatedPost: Post) => {
        setPosts(posts.map(post =>
            post.id === updatedPost.id ? updatedPost : post
        ))
        setEditingPost(null)
        setShowEditModal(false)
    }

    const handleDeletePostFromModal = (postId: string) => {
        setPosts(posts.filter(post => post.id !== postId))
        setEditingPost(null)
        setShowEditModal(false)
    }

    const handleBulkDelete = async () => {
        if (selectedPosts.size === 0) return
        if (!confirm(`Are you sure you want to delete ${selectedPosts.size} posts?`)) return

        try {
            for (const postId of selectedPosts) {
                await api.enhancedPosts.delete(postId)
            }
            setPosts(posts.filter(post => !selectedPosts.has(post.id)))
            setSelectedPosts(new Set())
            toast.success(`${selectedPosts.size} posts deleted successfully`)
        } catch (error) {
            console.error('Error deleting posts:', error)
            toast.error('Failed to delete posts')
        }
    }

    const handleBulkPublish = async () => {
        if (selectedPosts.size === 0) return

        try {
            for (const postId of selectedPosts) {
                await api.enhancedPosts.publish(postId, ['facebook', 'instagram'])
            }
            setPosts(posts.map(post =>
                selectedPosts.has(post.id)
                    ? { ...post, status: 'published' as const, publishedAt: new Date().toISOString() }
                    : post
            ))
            setSelectedPosts(new Set())
            toast.success(`${selectedPosts.size} posts published successfully`)
        } catch (error) {
            console.error('Error publishing posts:', error)
            toast.error('Failed to publish posts')
        }
    }

    const togglePostSelection = (postId: string) => {
        const newSelected = new Set(selectedPosts)
        if (newSelected.has(postId)) {
            newSelected.delete(postId)
        } else {
            newSelected.add(postId)
        }
        setSelectedPosts(newSelected)
    }

    const selectAllPosts = () => {
        if (selectedPosts.size === filteredPosts.length) {
            setSelectedPosts(new Set())
        } else {
            setSelectedPosts(new Set(filteredPosts.map((post: Post) => post.id)))
        }
    }

    // Use posts from state, or fallback to ref, or fallback to global storage
    const currentPosts = posts.length > 0 ? posts :
        postsRef.current.length > 0 ? postsRef.current :
            globalPosts || []

    // Ensure loading is false when we have posts from any source
    if (currentPosts.length > 0 && loading) {
        setLoading(false)
    }


    const filteredPosts = currentPosts.filter((post: Post) => {
        const matchesSearch = post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            post.content.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === 'all' || post.status === statusFilter
        const matchesChannel = channelFilter === 'all' || post.channels.includes(channelFilter)
        const matchesType = postTypeFilter === 'all' ||
            (postTypeFilter === 'text' && !post.media_urls?.length) ||
            (postTypeFilter === 'media' && post.media_urls?.length)

        // Filter by active tab
        const matchesTab = activeTab === 'published' ? post.status === 'published' :
            activeTab === 'scheduled' ? post.status === 'scheduled' :
                activeTab === 'drafts' ? post.status === 'draft' :
                    activeTab === 'expiring' ? false : // TODO: Implement expiring logic
                        activeTab === 'expired' ? false : // TODO: Implement expired logic
                            true

        const result = matchesSearch && matchesStatus && matchesChannel && matchesType && matchesTab

        // Debug logging for first few posts
        if (posts.indexOf(post) < 3) {
            console.log(`[AdminPostsManagement] Post ${post.id} filtering:`, {
                title: post.title,
                status: post.status,
                activeTab,
                matchesTab,
                matchesSearch,
                matchesStatus,
                matchesChannel,
                matchesType,
                result
            })
        }

        return result
    })

    // If no posts are showing, let's show all posts regardless of tab
    const displayPosts = filteredPosts.length > 0 ? filteredPosts : currentPosts

    const sortedPosts = [...displayPosts].sort((a, b) => {
        let comparison = 0
        switch (sortBy) {
            case 'date':
                comparison = new Date(a.publishedAt || a.createdAt).getTime() - new Date(b.publishedAt || b.createdAt).getTime()
                break
            case 'title':
                comparison = a.title.localeCompare(b.title)
                break
            case 'status':
                comparison = a.status.localeCompare(b.status)
                break
            case 'reach':
                comparison = (a.analytics?.reach || 0) - (b.analytics?.reach || 0)
                break
            case 'views':
                comparison = (a.analytics?.views || 0) - (b.analytics?.views || 0)
                break
        }
        return sortOrder === 'asc' ? comparison : -comparison
    })

    if (loading) {
        return (
            <div className="flex items-center justify-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Admin Header */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Content</h1>
                            <p className="text-gray-600">Schedule, publish and manage posts and stories, and more.</p>
                        </div>
                        <div className="flex items-center space-x-3">
                            <button className="flex items-center space-x-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                                <ArrowDownTrayIcon className="w-4 h-4" />
                                <span>Export Data</span>
                                <ChevronDownIcon className="w-4 h-4" />
                            </button>
                            <button className="flex items-center space-x-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                                <VideoCameraIcon className="w-4 h-4" />
                                <span>Create reel</span>
                            </button>
                            <button
                                onClick={onCreatePost}
                                className="flex items-center space-x-2 px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                            >
                                <PlusIcon className="w-4 h-4" />
                                <span>Create post</span>
                                <ChevronDownIcon className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <nav className="flex space-x-8">
                        {[
                            { id: 'published', label: 'Published', count: posts.filter(p => p.status === 'published').length },
                            { id: 'scheduled', label: 'Scheduled', count: posts.filter(p => p.status === 'scheduled').length },
                            { id: 'drafts', label: 'Drafts', count: posts.filter(p => p.status === 'draft').length },
                            { id: 'expiring', label: 'Expiring', count: 0 },
                            { id: 'expired', label: 'Expired', count: 0 }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === tab.id
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                {tab.label}
                                {tab.count > 0 && (
                                    <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                                        {tab.count}
                                    </span>
                                )}
                            </button>
                        ))}
                    </nav>
                </div>
            </div>

            {/* Filters and Search */}
            <div className="bg-white border-b border-gray-200 py-3 sm:py-4">
                <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8">
                    <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-4">
                        {/* Search - Full width on mobile */}
                        <div className="w-full sm:flex-1 sm:min-w-64 order-1">
                            <div className="relative">
                                <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search posts..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        {/* Filters Row */}
                        <div className="flex flex-wrap items-center gap-2 sm:gap-4 order-2">
                            {/* Post Type Filter */}
                            <select
                                value={postTypeFilter}
                                onChange={(e) => setPostTypeFilter(e.target.value)}
                                className="px-2 py-2 border border-gray-300 rounded-lg text-sm min-w-0 flex-1 sm:flex-none"
                            >
                                <option value="all">Type</option>
                                <option value="text">Text</option>
                                <option value="media">Media</option>
                            </select>

                            {/* Status Filter */}
                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                className="px-2 py-2 border border-gray-300 rounded-lg text-sm min-w-0 flex-1 sm:flex-none"
                            >
                                <option value="all">Status</option>
                                <option value="draft">Draft</option>
                                <option value="published">Published</option>
                                <option value="scheduled">Scheduled</option>
                                <option value="promoted">Promoted</option>
                            </select>

                            <button className="px-2 py-2 text-gray-600 hover:text-gray-800 text-sm">Clear</button>

                            {/* Columns Toggle */}
                            <button
                                onClick={() => setShowColumns(!showColumns)}
                                className="flex items-center space-x-1 px-2 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                            >
                                <Bars3Icon className="w-4 h-4" />
                                <span className="hidden sm:inline">Columns</span>
                            </button>
                        </div>

                        {/* Date Range - Hidden on mobile */}
                        <div className="hidden lg:block order-3">
                            <select className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
                                <option>Last 90 days</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Bulk Actions */}
            {selectedPosts.size > 0 && (
                <div className="bg-blue-50 border-b border-blue-200 py-3">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-blue-800">
                                {selectedPosts.size} post{selectedPosts.size !== 1 ? 's' : ''} selected
                            </span>
                            <div className="flex items-center space-x-3">
                                <button
                                    onClick={handleBulkPublish}
                                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                                >
                                    Publish Selected
                                </button>
                                <button
                                    onClick={handleBulkDelete}
                                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                                >
                                    Delete Selected
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Posts Table */}
            <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 sm:py-6">
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-3 sm:px-6 py-3 text-left">
                                        <input
                                            type="checkbox"
                                            checked={selectedPosts.size === filteredPosts.length && filteredPosts.length > 0}
                                            onChange={selectAllPosts}
                                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                    </th>
                                    <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <span className="hidden sm:inline">Title</span>
                                        <span className="sm:hidden">Post</span>
                                    </th>
                                    {showColumns && (
                                        <>
                                            <th className="hidden md:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Date
                                            </th>
                                            <th className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Status
                                            </th>
                                            <th className="hidden lg:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Reach
                                            </th>
                                            <th className="hidden lg:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Views
                                            </th>
                                        </>
                                    )}
                                    <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <span className="hidden sm:inline">Actions</span>
                                        <span className="sm:hidden">⋯</span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {sortedPosts.map((post) => (
                                    <motion.tr
                                        key={post.id}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="hover:bg-gray-50 cursor-pointer transition-colors"
                                        onClick={(e) => {
                                            // Don't trigger if clicking on checkbox or action buttons
                                            if (e.target instanceof HTMLInputElement ||
                                                (e.target as HTMLElement).closest('button') ||
                                                (e.target as HTMLElement).closest('[data-no-click]')) {
                                                return;
                                            }
                                            handlePreviewPost(post.id);
                                        }}
                                    >
                                        <td className="px-3 sm:px-6 py-4">
                                            <input
                                                type="checkbox"
                                                checked={selectedPosts.has(post.id)}
                                                onChange={() => togglePostSelection(post.id)}
                                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                            />
                                        </td>
                                        <td className="px-3 sm:px-6 py-4">
                                            <div className="flex items-start space-x-3">
                                                {/* Post Thumbnail */}
                                                <div className="flex-shrink-0">
                                                    {post.media_urls && post.media_urls.length > 0 ? (
                                                        <img
                                                            src={post.media_urls[0]}
                                                            alt="Post thumbnail"
                                                            className="w-10 h-10 sm:w-12 sm:h-12 rounded object-cover"
                                                        />
                                                    ) : (
                                                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gray-100 rounded flex items-center justify-center">
                                                            <DocumentTextIcon className="w-5 h-5 sm:w-6 sm:h-6 text-gray-400" />
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Post Info */}
                                                <div className="min-w-0 flex-1">
                                                    {/* Mobile: Stack vertically, Desktop: Horizontal */}
                                                    <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-2 mb-1">
                                                        <div className="flex items-center space-x-1 mb-1 sm:mb-0">
                                                            <ShareIcon className="w-3 h-3 sm:w-4 sm:h-4 text-blue-500" />
                                                            {post.media_urls && post.media_urls.length > 0 ? (
                                                                <span className="text-xs text-gray-500">Media</span>
                                                            ) : (
                                                                <span className="text-xs text-gray-500">Text</span>
                                                            )}
                                                        </div>
                                                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 w-fit">
                                                            AI Demo
                                                        </span>
                                                    </div>
                                                    {/* Post Title - Better responsive handling */}
                                                    <p
                                                        className="text-sm font-medium text-gray-900 break-words leading-tight"
                                                        title="Click anywhere on the row to preview post"
                                                    >
                                                        {post.title}
                                                    </p>
                                                </div>
                                            </div>
                                        </td>

                                        {showColumns && (
                                            <>
                                                <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {post.publishedAt
                                                        ? new Date(post.publishedAt).toLocaleDateString('en-GB', {
                                                            day: 'numeric',
                                                            month: 'short',
                                                            hour: '2-digit',
                                                            minute: '2-digit'
                                                        })
                                                        : post.scheduledAt
                                                            ? new Date(post.scheduledAt).toLocaleDateString('en-GB', {
                                                                day: 'numeric',
                                                                month: 'short',
                                                                hour: '2-digit',
                                                                minute: '2-digit'
                                                            })
                                                            : '-'
                                                    }
                                                </td>
                                                <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center">
                                                        {post.status === 'published' && <RocketLaunchIcon className="w-4 h-4 text-green-500 mr-1" />}
                                                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${statusColors[post.status as 'draft' | 'published' | 'scheduled' | 'promoted']}`}>
                                                            {post.status}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="hidden lg:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {post.analytics?.reach || 0}
                                                </td>
                                                <td className="hidden lg:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {post.analytics?.views || 0}
                                                </td>
                                            </>
                                        )}

                                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <div className="flex items-center justify-end space-x-1 sm:space-x-2">
                                                {post.status === 'published' && (
                                                    <button
                                                        onClick={() => handlePromotePost(post.id)}
                                                        className="hidden sm:inline-flex px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                                                        data-no-click
                                                    >
                                                        Boost
                                                    </button>
                                                )}
                                                <div data-no-click>
                                                    <AdminActionsDropdown
                                                        post={post}
                                                        onEdit={handleEditPost}
                                                        onPublish={handlePublishPost}
                                                        onPromote={handlePromotePost}
                                                        onDelete={handleDeletePost}
                                                    />
                                                </div>
                                            </div>
                                        </td>
                                    </motion.tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Edit Post Modal */}
            <PostEditModal
                post={editingPost}
                isOpen={showEditModal}
                onClose={() => {
                    setShowEditModal(false)
                    setEditingPost(null)
                }}
                onSave={handleSavePost}
                onDelete={handleDeletePostFromModal}
            />

            {/* Post Preview Modal */}
            <PostPreviewModal
                post={previewPost}
                isOpen={showPreviewModal}
                onClose={() => {
                    setShowPreviewModal(false)
                    setPreviewPost(null)
                }}
            />
        </div>
    )
}

// Admin Actions Dropdown Component
interface AdminActionsDropdownProps {
    post: Post
    onEdit: (postId: string) => void
    onPublish: (postId: string) => void
    onPromote: (postId: string) => void
    onDelete: (postId: string) => void
}

function AdminActionsDropdown({ post, onEdit, onPublish, onPromote, onDelete }: AdminActionsDropdownProps) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-1 text-gray-400 hover:text-gray-600"
            >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                </svg>
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <div
                            className="fixed inset-0 z-10"
                            onClick={() => setIsOpen(false)}
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="absolute right-0 z-20 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1"
                        >
                            <button
                                onClick={() => {
                                    onEdit(post.id)
                                    setIsOpen(false)
                                }}
                                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center justify-between"
                            >
                                <span>Manage post</span>
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                            </button>
                            <button
                                onClick={() => {
                                    // TODO: Implement add to story
                                    setIsOpen(false)
                                }}
                                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                            >
                                Add post to story
                            </button>
                            <button
                                onClick={() => {
                                    navigator.clipboard.writeText(post.id)
                                    toast.success('Post ID copied to clipboard')
                                    setIsOpen(false)
                                }}
                                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                            >
                                Copy Post ID
                            </button>
                            {post.status === 'draft' && (
                                <button
                                    onClick={() => {
                                        onPublish(post.id)
                                        setIsOpen(false)
                                    }}
                                    className="w-full px-4 py-2 text-left text-sm text-green-700 hover:bg-green-50"
                                >
                                    Publish Now
                                </button>
                            )}
                            <button
                                onClick={() => {
                                    onDelete(post.id)
                                    setIsOpen(false)
                                }}
                                className="w-full px-4 py-2 text-left text-sm text-red-700 hover:bg-red-50"
                            >
                                Delete Post
                            </button>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    )
}
