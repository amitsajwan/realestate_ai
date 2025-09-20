'use client'

import React, { memo, useMemo } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import {
  CalendarIcon,
  ChatBubbleLeftRightIcon,
  EyeIcon,
  HeartIcon,
  ShareIcon,
  SparklesIcon,
  PencilIcon,
  TrashIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline'
import { Card, CardBody, CardHeader } from './index'
import ChannelBadge from './ChannelBadge'
import StatusBadge from './StatusBadge'

export interface Post {
  id: string
  title: string
  content: string
  property_id?: string
  property_title?: string
  language: string
  channels: string[]
  status: string
  created_at: string
  updated_at?: string
  view_count?: number
  like_count?: number
  share_count?: number
  comment_count?: number
  agent_id?: string
  published_at?: string
}

interface UnifiedPostCardProps {
  post: Post
  variant?: 'public' | 'management'
  viewMode?: 'grid' | 'list'
  agentName?: string
  showFullContent?: boolean
  onEdit?: (post: Post) => void
  onDelete?: (postId: string) => void
  onPublish?: (postId: string, channels: string[]) => void
  showActions?: boolean
  className?: string
}

const UnifiedPostCard: React.FC<UnifiedPostCardProps> = memo(({
  post,
  variant = 'public',
  viewMode = 'grid',
  agentName,
  showFullContent = false,
  onEdit,
  onDelete,
  onPublish,
  showActions = false,
  className = ''
}) => {
  // Memoize formatted date
  const formattedDate = useMemo(() => {
    return new Date(post.created_at).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      ...(variant === 'management' && { hour: '2-digit', minute: '2-digit' })
    })
  }, [post.created_at, variant])

  // Memoize content truncation
  const displayContent = useMemo(() => {
    if (showFullContent || viewMode === 'list') return post.content
    const maxLength = viewMode === 'grid' ? 150 : 200
    return post.content.length > maxLength 
      ? post.content.substring(0, maxLength) + '...' 
      : post.content
  }, [post.content, showFullContent, viewMode])

  // Memoize channel icons
  const getChannelIcon = useMemo(() => (channel: string) => {
    const icons: Record<string, string> = {
      facebook: '📘',
      instagram: '📷',
      twitter: '🐦',
      linkedin: '💼',
      website: '🌐'
    }
    return icons[channel.toLowerCase()] || '📱'
  }, [])

  // Memoize stats
  const stats = useMemo(() => [
    { icon: EyeIcon, value: post.view_count || 0, label: 'views' },
    { icon: HeartIcon, value: post.like_count || 0, label: 'likes' },
    { icon: ShareIcon, value: post.share_count || 0, label: 'shares' },
    { icon: ChatBubbleLeftRightIcon, value: post.comment_count || 0, label: 'comments' }
  ], [post.view_count, post.like_count, post.share_count, post.comment_count])

  if (variant === 'public') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={className}
      >
        <Card className="h-full hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
          <CardHeader className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <SparklesIcon className="w-5 h-5 text-purple-500" />
                <span className="text-sm font-medium text-gray-600">
                  {getChannelIcon(post.channels[0])} {post.channels[0]}
                </span>
              </div>
              <time className="text-xs text-gray-500">{formattedDate}</time>
            </div>
            
            <Link href={`/agent/${agentName}/posts/${post.id}`}>
              <h3 className="text-lg font-bold text-gray-900 hover:text-blue-600 transition-colors line-clamp-2">
                {post.title}
              </h3>
            </Link>
            
            {post.property_title && (
              <p className="text-sm text-gray-600 mt-2 flex items-center">
                <GlobeAltIcon className="w-4 h-4 mr-1" />
                {post.property_title}
              </p>
            )}
          </CardHeader>
          
          <CardBody className="p-4 pt-0">
            <p className="text-gray-700 text-sm mb-4 line-clamp-3">
              {displayContent}
            </p>
            
            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-2 text-center border-t pt-4">
              {stats.map((stat, idx) => (
                <div key={idx} className="group cursor-pointer">
                  <div className="flex flex-col items-center space-y-1 group-hover:text-blue-600 transition-colors">
                    <stat.icon className="w-4 h-4 text-gray-400 group-hover:text-blue-600" />
                    <span className="text-sm font-semibold">{stat.value}</span>
                    <span className="text-xs text-gray-500">{stat.label}</span>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Language Badge */}
            <div className="mt-4 flex items-center justify-between">
              <span className="text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded-full">
                {post.language}
              </span>
              <Link
                href={`/agent/${agentName}/posts/${post.id}`}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Read More →
              </Link>
            </div>
          </CardBody>
        </Card>
      </motion.div>
    )
  }

  // Management variant
  return (
    <div className={`${viewMode === 'list' ? 'mb-4' : ''} ${className}`}>
      <Card className={`
        ${viewMode === 'list' ? 'flex flex-row' : 'h-full'}
        hover:shadow-lg transition-all duration-200
      `}>
        <div className={`${viewMode === 'list' ? 'flex-1 flex' : ''}`}>
          <CardBody className={`${viewMode === 'list' ? 'flex-1 p-4' : 'p-6'}`}>
            <div className="flex justify-between items-start mb-3">
              <h3 className="text-lg font-semibold text-gray-800 flex-1 mr-2">
                {post.title}
              </h3>
              <StatusBadge status={post.status} />
            </div>

            <p className={`text-gray-600 mb-4 ${viewMode === 'grid' ? 'line-clamp-3' : ''}`}>
              {displayContent}
            </p>

            <div className="flex flex-wrap gap-2 mb-4">
              {post.channels.map((channel) => (
                <ChannelBadge key={channel} channel={channel} />
              ))}
            </div>

            <div className="flex justify-between items-center text-sm text-gray-500">
              <span>{formattedDate}</span>
              {post.property_title && (
                <span className="flex items-center">
                  <GlobeAltIcon className="w-4 h-4 mr-1" />
                  {post.property_title}
                </span>
              )}
            </div>

            {/* Action Buttons */}
            {showActions && (
              <div className="mt-4 flex gap-2">
                {onEdit && (
                  <button
                    onClick={() => onEdit(post)}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
                  >
                    <PencilIcon className="w-4 h-4" />
                    Edit
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={() => onDelete(post.id)}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" />
                    Delete
                  </button>
                )}
                {onPublish && post.status === 'draft' && (
                  <button
                    onClick={() => onPublish(post.id, post.channels)}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors"
                  >
                    <GlobeAltIcon className="w-4 h-4" />
                    Publish
                  </button>
                )}
              </div>
            )}
          </CardBody>
        </div>
      </Card>
    </div>
  )
})

UnifiedPostCard.displayName = 'UnifiedPostCard'

export default UnifiedPostCard