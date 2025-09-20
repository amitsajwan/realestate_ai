'use client'

import { Card, CardBody, CardHeader } from '@/components/UI'
import {
    CalendarIcon,
    ChatBubbleLeftRightIcon,
    EyeIcon,
    HeartIcon,
    ShareIcon,
    SparklesIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import Link from 'next/link'

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

interface PostCardProps {
    post: Post
    agentName: string
    showFullContent?: boolean
}

export function PostCard({ post, agentName, showFullContent = false }: PostCardProps) {
    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        })
    }

    const getChannelIcon = (channel: string) => {
        switch (channel.toLowerCase()) {
            case 'facebook':
                return '📘'
            case 'instagram':
                return '📷'
            case 'linkedin':
                return '💼'
            case 'twitter':
                return '🐦'
            default:
                return '📱'
        }
    }

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'published':
                return 'bg-green-100 text-green-800'
            case 'draft':
                return 'bg-yellow-100 text-yellow-800'
            case 'scheduled':
                return 'bg-blue-100 text-blue-800'
            default:
                return 'bg-gray-100 text-gray-800'
        }
    }

    const truncateContent = (content: string, maxLength: number = 150) => {
        if (content.length <= maxLength) return content
        return content.substring(0, maxLength) + '...'
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="group"
        >
            <Card className="h-full hover:shadow-lg transition-all duration-300 border border-gray-200 hover:border-blue-200">
                <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2">
                                {post.title}
                            </h3>
                            <div className="flex items-center mt-2 space-x-4 text-sm text-gray-500">
                                <div className="flex items-center">
                                    <CalendarIcon className="w-4 h-4 mr-1" />
                                    <span>{formatDate(post.created_at)}</span>
                                </div>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(post.status)}`}>
                                    {post.status}
                                </span>
                            </div>
                        </div>
                        <div className="flex items-center space-x-1 ml-4">
                            {post.channels.map((channel, index) => (
                                <span
                                    key={index}
                                    className="text-lg"
                                    title={`Posted on ${channel}`}
                                >
                                    {getChannelIcon(channel)}
                                </span>
                            ))}
                        </div>
                    </div>
                </CardHeader>

                <CardBody className="pt-0">
                    <div className="space-y-4">
                        {/* Content */}
                        <div>
                            <p className="text-gray-700 leading-relaxed">
                                {showFullContent ? post.content : truncateContent(post.content)}
                            </p>
                            {!showFullContent && post.content.length > 150 && (
                                <Link
                                    href={`/agent/${agentName}/posts/${post.id}`}
                                    className="text-blue-600 hover:text-blue-800 text-sm font-medium mt-2 inline-block"
                                >
                                    Read more →
                                </Link>
                            )}
                        </div>

                        {/* Related Property */}
                        {post.property_id && post.property_title && (
                            <div className="bg-blue-50 rounded-lg p-3">
                                <div className="flex items-center">
                                    <SparklesIcon className="w-5 h-5 text-blue-600 mr-2" />
                                    <div>
                                        <p className="text-sm font-medium text-blue-900">Related Property</p>
                                        <p className="text-sm text-blue-700">{post.property_title}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Engagement Stats */}
                        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                                {post.view_count !== undefined && (
                                    <div className="flex items-center">
                                        <EyeIcon className="w-4 h-4 mr-1" />
                                        <span>{post.view_count}</span>
                                    </div>
                                )}
                                {post.like_count !== undefined && (
                                    <div className="flex items-center">
                                        <HeartIcon className="w-4 h-4 mr-1" />
                                        <span>{post.like_count}</span>
                                    </div>
                                )}
                                {post.share_count !== undefined && (
                                    <div className="flex items-center">
                                        <ShareIcon className="w-4 h-4 mr-1" />
                                        <span>{post.share_count}</span>
                                    </div>
                                )}
                                {post.comment_count !== undefined && (
                                    <div className="flex items-center">
                                        <ChatBubbleLeftRightIcon className="w-4 h-4 mr-1" />
                                        <span>{post.comment_count}</span>
                                    </div>
                                )}
                            </div>

                            {/* Language Badge */}
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                                {post.language.toUpperCase()}
                            </span>
                        </div>
                    </div>
                </CardBody>
            </Card>
        </motion.div>
    )
}
