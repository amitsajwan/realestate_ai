'use client'

import { BookmarkIcon, ChatBubbleLeftIcon, HeartIcon, ShareIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { BookmarkIcon as BookmarkSolidIcon, HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'

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

interface PostPreviewModalProps {
    post: Post | null
    isOpen: boolean
    onClose: () => void
}

const platforms = [
    { id: 'facebook', name: 'Facebook', color: 'bg-blue-600', icon: '📘' },
    { id: 'instagram', name: 'Instagram', color: 'bg-gradient-to-r from-purple-500 to-pink-500', icon: '📷' },
    { id: 'twitter', name: 'Twitter', color: 'bg-blue-400', icon: '🐦' },
    { id: 'linkedin', name: 'LinkedIn', color: 'bg-blue-700', icon: '💼' },
    { id: 'website', name: 'Website', color: 'bg-gray-600', icon: '🌐' }
]

export default function PostPreviewModal({ post, isOpen, onClose }: PostPreviewModalProps) {
    const [selectedPlatform, setSelectedPlatform] = useState('facebook')
    const [isLiked, setIsLiked] = useState(false)
    const [isBookmarked, setIsBookmarked] = useState(false)

    if (!post) return null

    const renderFacebookPost = () => (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm w-full">
            {/* Header */}
            <div className="flex items-center p-4">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                    AI
                </div>
                <div className="ml-3 flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 truncate">RealEstate AI</h3>
                    <p className="text-sm text-gray-500">2 hours ago</p>
                </div>
                <button className="text-gray-400 hover:text-gray-600 flex-shrink-0">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                    </svg>
                </button>
            </div>

            {/* Content */}
            <div className="px-4 pb-2">
                <p className="text-gray-900 mb-3 break-words">{post.content}</p>
            </div>

            {/* Media */}
            {post.media_urls && post.media_urls.length > 0 && (
                <div className="px-4 pb-4">
                    <img
                        src={post.media_urls[0]}
                        alt="Post media"
                        className="w-full h-64 object-cover rounded-lg"
                    />
                </div>
            )}

            {/* Engagement */}
            <div className="px-4 py-2 border-t border-gray-100">
                <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
                    <span>👍 12 likes</span>
                    <span>💬 3 comments</span>
                    <span>📤 1 share</span>
                </div>
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => setIsLiked(!isLiked)}
                        className="flex items-center space-x-1 text-gray-500 hover:text-blue-600"
                    >
                        {isLiked ? <HeartSolidIcon className="w-5 h-5 text-red-500" /> : <HeartIcon className="w-5 h-5" />}
                        <span>Like</span>
                    </button>
                    <button className="flex items-center space-x-1 text-gray-500 hover:text-green-600">
                        <ChatBubbleLeftIcon className="w-5 h-5" />
                        <span>Comment</span>
                    </button>
                    <button className="flex items-center space-x-1 text-gray-500 hover:text-blue-600">
                        <ShareIcon className="w-5 h-5" />
                        <span>Share</span>
                    </button>
                </div>
            </div>
        </div>
    )

    const renderInstagramPost = () => (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm w-full max-w-sm mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-4">
                <div className="flex items-center min-w-0 flex-1">
                    <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                        AI
                    </div>
                    <div className="ml-3 min-w-0">
                        <h3 className="font-semibold text-gray-900 text-sm truncate">realestate_ai</h3>
                    </div>
                </div>
                <button className="text-gray-400 hover:text-gray-600 flex-shrink-0">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                    </svg>
                </button>
            </div>

            {/* Media */}
            {post.media_urls && post.media_urls.length > 0 ? (
                <img
                    src={post.media_urls[0]}
                    alt="Post media"
                    className="w-full h-80 object-cover"
                />
            ) : (
                <div className="w-full h-80 bg-gray-100 flex items-center justify-center">
                    <span className="text-gray-400">📝 Text Post</span>
                </div>
            )}

            {/* Engagement */}
            <div className="p-4">
                <div className="flex items-center space-x-4 mb-3">
                    <button
                        onClick={() => setIsLiked(!isLiked)}
                        className="text-gray-500 hover:text-red-500"
                    >
                        {isLiked ? <HeartSolidIcon className="w-6 h-6 text-red-500" /> : <HeartIcon className="w-6 h-6" />}
                    </button>
                    <button className="text-gray-500 hover:text-gray-700">
                        <ChatBubbleLeftIcon className="w-6 h-6" />
                    </button>
                    <button className="text-gray-500 hover:text-gray-700">
                        <ShareIcon className="w-6 h-6" />
                    </button>
                    <button
                        onClick={() => setIsBookmarked(!isBookmarked)}
                        className="ml-auto text-gray-500 hover:text-gray-700"
                    >
                        {isBookmarked ? <BookmarkSolidIcon className="w-6 h-6" /> : <BookmarkIcon className="w-6 h-6" />}
                    </button>
                </div>
                <p className="text-sm text-gray-900 mb-2 break-words">
                    <span className="font-semibold">realestate_ai</span> {post.content}
                </p>
                <p className="text-sm text-gray-500">View all 12 comments</p>
            </div>
        </div>
    )

    const renderTwitterPost = () => (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm w-full max-w-md mx-auto">
            {/* Header */}
            <div className="flex items-start p-4">
                <div className="w-10 h-10 bg-blue-400 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                    AI
                </div>
                <div className="ml-3 flex-1 min-w-0">
                    <div className="flex items-center flex-wrap">
                        <h3 className="font-semibold text-gray-900 truncate">RealEstate AI</h3>
                        <span className="ml-2 text-gray-500 truncate">@realestate_ai</span>
                        <span className="ml-2 text-gray-500">·</span>
                        <span className="ml-2 text-gray-500">2h</span>
                    </div>
                </div>
                <button className="text-gray-400 hover:text-gray-600 flex-shrink-0">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                    </svg>
                </button>
            </div>

            {/* Content */}
            <div className="px-4 pb-4">
                <p className="text-gray-900 mb-3 break-words">{post.content}</p>

                {/* Media */}
                {post.media_urls && post.media_urls.length > 0 && (
                    <div className="mb-3">
                        <img
                            src={post.media_urls[0]}
                            alt="Post media"
                            className="w-full h-48 object-cover rounded-lg"
                        />
                    </div>
                )}

                {/* Engagement */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                    <button className="flex items-center space-x-1 hover:text-blue-500">
                        <ChatBubbleLeftIcon className="w-4 h-4" />
                        <span>12</span>
                    </button>
                    <button className="flex items-center space-x-1 hover:text-green-500">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M8 12l-4-4 4-4 1.5 1.5L7 7h6a4 4 0 014 4v1a4 4 0 01-4 4H7l2.5 2.5L8 12z" />
                        </svg>
                        <span>8</span>
                    </button>
                    <button
                        onClick={() => setIsLiked(!isLiked)}
                        className="flex items-center space-x-1 hover:text-red-500"
                    >
                        {isLiked ? <HeartSolidIcon className="w-4 h-4 text-red-500" /> : <HeartIcon className="w-4 h-4" />}
                        <span>24</span>
                    </button>
                    <button className="flex items-center space-x-1 hover:text-blue-500">
                        <ShareIcon className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    )

    const renderLinkedInPost = () => (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm w-full max-w-md mx-auto">
            {/* Header */}
            <div className="flex items-center p-4">
                <div className="w-10 h-10 bg-blue-700 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                    AI
                </div>
                <div className="ml-3 flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 truncate">RealEstate AI</h3>
                    <p className="text-sm text-gray-500 truncate">Real Estate Professional · 2h</p>
                </div>
                <button className="text-gray-400 hover:text-gray-600 flex-shrink-0">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                    </svg>
                </button>
            </div>

            {/* Content */}
            <div className="px-4 pb-4">
                <p className="text-gray-900 mb-3 break-words">{post.content}</p>

                {/* Media */}
                {post.media_urls && post.media_urls.length > 0 && (
                    <div className="mb-3">
                        <img
                            src={post.media_urls[0]}
                            alt="Post media"
                            className="w-full h-48 object-cover rounded-lg"
                        />
                    </div>
                )}

                {/* Engagement */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>👍 8 reactions</span>
                    <span>💬 3 comments</span>
                    <span>📤 1 repost</span>
                </div>
            </div>
        </div>
    )

    const renderWebsitePost = () => (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm w-full max-w-md mx-auto">
            {/* Header */}
            <div className="p-4 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900 truncate">{post.title}</h3>
                <p className="text-sm text-gray-500 mt-1">Posted 2 hours ago</p>
            </div>

            {/* Content */}
            <div className="p-4">
                <p className="text-gray-900 mb-4 break-words">{post.content}</p>

                {/* Media */}
                {post.media_urls && post.media_urls.length > 0 && (
                    <div className="mb-4">
                        <img
                            src={post.media_urls[0]}
                            alt="Post media"
                            className="w-full h-48 object-cover rounded-lg"
                        />
                    </div>
                )}

                {/* Engagement */}
                <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t border-gray-100">
                    <span>👁️ 45 views</span>
                    <span>👍 8 likes</span>
                    <span>💬 3 comments</span>
                </div>
            </div>
        </div>
    )

    const renderPostPreview = () => {
        switch (selectedPlatform) {
            case 'facebook':
                return renderFacebookPost()
            case 'instagram':
                return renderInstagramPost()
            case 'twitter':
                return renderTwitterPost()
            case 'linkedin':
                return renderLinkedInPost()
            case 'website':
                return renderWebsitePost()
            default:
                return renderFacebookPost()
        }
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={onClose} />
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 overflow-y-auto">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] sm:max-h-[95vh] overflow-hidden flex flex-col mx-2 sm:mx-4"
                            style={{
                                maxWidth: 'calc(100vw - 1rem)',
                                maxHeight: 'calc(100vh - 2rem)'
                            }}
                        >
                            {/* Header */}
                            <div className="flex items-center justify-between p-6 border-b border-gray-200">
                                <div>
                                    <h2 className="text-xl font-semibold text-gray-900">Post Preview</h2>
                                    <p className="text-sm text-gray-500">See how your post will look on different platforms</p>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <XMarkIcon className="w-6 h-6" />
                                </button>
                            </div>

                            {/* Platform Selector */}
                            <div className="p-6 border-b border-gray-200">
                                <div className="flex flex-wrap gap-2">
                                    {platforms.map((platform) => (
                                        <button
                                            key={platform.id}
                                            onClick={() => setSelectedPlatform(platform.id)}
                                            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${selectedPlatform === platform.id
                                                ? 'bg-blue-100 text-blue-700 border border-blue-200'
                                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                                }`}
                                        >
                                            <span className="text-lg flex-shrink-0">{platform.icon}</span>
                                            <span className="truncate">{platform.name}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Post Preview */}
                            <div className="p-4 sm:p-6 bg-gray-50 flex-1 overflow-y-auto">
                                <div className="flex justify-center min-h-0">
                                    <div className="w-full max-w-md mx-auto">
                                        {renderPostPreview()}
                                    </div>
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="p-6 border-t border-gray-200 bg-gray-50 flex-shrink-0">
                                <div className="flex items-center justify-between flex-wrap gap-4">
                                    <div className="text-sm text-gray-500 min-w-0 flex-1">
                                        <span className="font-medium">Post Status:</span> {post.status}
                                        {post.channels.length > 0 && (
                                            <span className="ml-2">
                                                • <span className="font-medium">Channels:</span> <span className="truncate">{post.channels.join(', ')}</span>
                                            </span>
                                        )}
                                    </div>
                                    <button
                                        onClick={onClose}
                                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex-shrink-0"
                                    >
                                        Close Preview
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </>
            )}
        </AnimatePresence>
    )
}
