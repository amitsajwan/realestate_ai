'use client'

import {
    BookmarkIcon,
    ChatBubbleLeftIcon,
    EllipsisHorizontalIcon,
    HeartIcon,
    ShareIcon,
    XMarkIcon
} from '@heroicons/react/24/outline'
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
    { id: 'facebook', name: 'Facebook', icon: '⬜', platformIcon: 'text-[#1877F2]', handle: 'PropertyAI' },
    { id: 'instagram', name: 'Instagram', icon: '📷', platformIcon: 'text-[#E4405F]', handle: 'realestate_ai' },
    { id: 'twitter', name: 'Twitter', icon: '🐦', platformIcon: 'text-[#1DA1F2]', handle: '@realestate_ai' },
    { id: 'linkedin', name: 'LinkedIn', icon: '🟦', platformIcon: 'text-[#0A66C2]', handle: 'RealEstate AI' },
    { id: 'website', name: 'Website', icon: '🌐', platformIcon: 'text-[#4F46E5]', handle: 'Blog' }
]

const PostHeader = ({ platform, selectedPlatform }: { platform: string, selectedPlatform: string }) => {
    const currentPlatform = platforms.find(p => p.id === platform) || platforms[0]
    
    return (
        <div className="flex items-center p-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-medium
                ${selectedPlatform === 'facebook' ? 'bg-blue-600' :
                selectedPlatform === 'instagram' ? 'bg-gradient-to-r from-purple-500 to-pink-500' :
                selectedPlatform === 'twitter' ? 'bg-blue-400' :
                selectedPlatform === 'linkedin' ? 'bg-blue-700' : 'bg-gray-600'}`}
            >
                AI
            </div>
            <div className="ml-3 flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 truncate">{currentPlatform.handle}</h3>
                <p className="text-xs text-gray-500">2 hours ago</p>
            </div>
            <button className="text-gray-400 hover:text-gray-600 flex-shrink-0 p-1">
                <EllipsisHorizontalIcon className="w-5 h-5" />
            </button>
        </div>
    )
}

export default function PostPreviewModal({ post, isOpen, onClose }: PostPreviewModalProps) {
    const [selectedPlatform, setSelectedPlatform] = useState('facebook')
    const [isLiked, setIsLiked] = useState(false)
    const [isBookmarked, setIsBookmarked] = useState(false)

    if (!post) return null

    const renderFacebookPost = () => (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm w-full max-w-[500px] mx-auto">
            <PostHeader platform="facebook" selectedPlatform={selectedPlatform} />

            {/* Content */}
            <div className="px-3 pb-2">
                <p className="text-gray-900 text-sm leading-6 break-words">{post.content}</p>
            </div>

            {/* Media */}
            {post.media_urls && post.media_urls.length > 0 && (
                <div className="px-3 pb-3">
                    <img
                        src={post.media_urls[0]}
                        alt="Post media"
                        className="w-full aspect-[4/3] object-cover rounded-lg bg-gray-50"
                    />
                </div>
            )}

            {/* Engagement */}
            <div className="px-3 pt-1 pb-2 border-t border-gray-100">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-2.5 py-1">
                    <div className="flex items-center">
                        <span className="flex h-4 -space-x-1">
                            <div className="w-4 h-4 rounded-full border-2 border-white bg-blue-500 z-30" />
                            <div className="w-4 h-4 rounded-full border-2 border-white bg-red-500 z-20" />
                            <div className="w-4 h-4 rounded-full border-2 border-white bg-yellow-500 z-10" />
                        </span>
                        <span className="ml-2">142 likes</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <span>24 comments</span>
                        <span>3 shares</span>
                    </div>
                </div>
                <div className="flex items-center border-t border-gray-100">
                    <button
                        onClick={() => setIsLiked(!isLiked)}
                        className="flex-1 flex items-center justify-center space-x-2 py-2 text-sm text-gray-600 hover:bg-gray-50 active:bg-gray-100 rounded-lg transition-colors"
                    >
                        {isLiked ? <HeartSolidIcon className="w-5 h-5 text-red-500" /> : <HeartIcon className="w-5 h-5" />}
                        <span>Like</span>
                    </button>
                    <button className="flex-1 flex items-center justify-center space-x-2 py-2 text-sm text-gray-600 hover:bg-gray-50 active:bg-gray-100 rounded-lg transition-colors">
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
            <PostHeader platform="instagram" selectedPlatform={selectedPlatform} />

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
            <PostHeader platform="twitter" selectedPlatform={selectedPlatform} />

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
            <PostHeader platform="linkedin" selectedPlatform={selectedPlatform} />

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
            <PostHeader platform="website" selectedPlatform={selectedPlatform} />

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
        <AnimatePresence mode="wait">
            {isOpen && (
                <>
                    <div className="fixed inset-0 bg-black bg-opacity-50 z-[60]" onClick={onClose} />
                    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 overflow-y-auto">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-white rounded-xl shadow-xl w-full max-w-[600px] max-h-[calc(100vh-5rem)] overflow-hidden flex flex-col mx-auto"
                        >
                            {/* Header with Close Button */}
                            <div className="relative px-4 py-3 border-b border-gray-200">
                                <button
                                    onClick={onClose}
                                    className="absolute right-2 top-2 p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
                                >
                                    <XMarkIcon className="w-5 h-5" />
                                </button>
                                <h2 className="text-lg font-semibold text-gray-900">Post Preview</h2>
                                <p className="text-sm text-gray-500 mt-0.5">See how your post will look on different platforms</p>
                            </div>

                            {/* Platform Selector */}
                            <div className="px-4 py-2 border-b border-gray-200">
                                <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2">
                                    {platforms.map((platform) => (
                                        <button
                                            key={platform.id}
                                            onClick={() => setSelectedPlatform(platform.id)}
                                            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap min-w-fit ${
                                                selectedPlatform === platform.id
                                                ? 'bg-gray-100 text-gray-900'
                                                : 'text-gray-600 hover:bg-gray-50'
                                            }`}
                                        >
                                            <span className={`text-base ${platform.platformIcon}`}>{platform.icon}</span>
                                            <span>{platform.name}</span>
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
                            <div className="px-4 py-3 border-t border-gray-200 bg-white flex-shrink-0">
                                <div className="flex items-center justify-between">
                                    <div className="text-sm text-gray-600">
                                        Post Status: <span className="text-gray-900">{post.status}</span>
                                        {post.channels.length > 0 && (
                                            <span className="ml-2">
                                                • Channels: <span className="text-gray-900">{post.channels.join(', ')}</span>
                                            </span>
                                        )}
                                    </div>
                                    <button
                                        onClick={onClose}
                                        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
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
