'use client'

import {
  ChatBubbleLeftRightIcon,
  EyeIcon,
  GlobeAltIcon,
  HeartIcon,
  PencilIcon,
  ShareIcon,
  SparklesIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import Image from 'next/image'
import Link from 'next/link'
import React, { memo, useMemo, useState } from 'react'
import { Post } from '../../types/post'
import ChannelBadge from './ChannelBadge'
import ImageModal from './ImageModal'
import { Card, CardContent, CardHeader } from './index'
import StatusBadge from './StatusBadge'

// Re-export for convenience
export type { Post }

// Image Gallery Component
const ImageGallery: React.FC<{ mediaUrls: string[] }> = ({ mediaUrls }) => {
  const [showImageModal, setShowImageModal] = useState(false)
  const [initialImageIndex, setInitialImageIndex] = useState(0)

  if (!mediaUrls || mediaUrls.length === 0) {
    console.log('No media URLs provided to ImageGallery')
    return null
  }

  const displayImages = mediaUrls.slice(0, 3)
  const remainingCount = mediaUrls.length - 3

  const handleImageClick = (index: number) => {
    setInitialImageIndex(index)
    setShowImageModal(true)
  }

  return (
    <>
      <div className="mt-2 sm:mt-3 mb-3 sm:mb-4">
        <div className="grid gap-1 sm:gap-2 touch-manipulation" style={{
          gridTemplateColumns: mediaUrls.length === 1 ? '1fr' :
            mediaUrls.length === 2 ? 'repeat(2, 1fr)' :
              'repeat(3, 1fr)'
        }}>
          {displayImages.map((url, index) => (
            <div 
              key={url} 
              className="relative aspect-square rounded-lg overflow-hidden bg-gray-100 touch-manipulation"
              onClick={() => handleImageClick(index)}
            >
              <div className="absolute inset-0 bg-black opacity-0 hover:opacity-10 active:opacity-20 transition-opacity z-10" />
              <Image
                src={url}
                alt={`Post image ${index + 1}`}
                fill
                className="object-cover transition-transform duration-200 cursor-pointer"
                sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
                onLoad={() => console.log('Image loaded successfully:', url)}
                onError={(e) => {
                  console.error('Failed to load image:', url)
                  e.currentTarget.style.display = 'none'
                  const placeholder = e.currentTarget.parentElement?.querySelector('.image-placeholder')
                  if (placeholder) {
                    (placeholder as HTMLElement).style.display = 'flex'
                  }
                }}
              />
              {/* Image count indicator */}
              <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded-full">
                {index + 1}/{mediaUrls.length}
              </div>
              {/* Fallback placeholder */}
              <div className="image-placeholder absolute inset-0 bg-gray-200 flex items-center justify-center text-gray-500 text-sm" style={{ display: 'none' }}>
                Image {index + 1}
              </div>
              {index === 2 && remainingCount > 0 && (
                <div 
                  className="absolute inset-0 bg-black bg-opacity-60 flex flex-col items-center justify-center text-white cursor-pointer active:bg-opacity-70"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleImageClick(0)
                  }}
                >
                  <span className="text-2xl font-bold">+{remainingCount}</span>
                  <span className="text-sm">more photos</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Image Modal */}
      <ImageModal
        images={mediaUrls} 
        initialIndex={initialImageIndex}
        isOpen={showImageModal} 
        onClose={() => setShowImageModal(false)} 
      />
    </>
  )
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
  // Memoize formatted date - improved logic
  const formattedDate = useMemo(() => {
    try {
      let dateString = post.created_at || post.published_at

      if (!dateString) {
        return 'Recently created'
      }

      // Handle various date formats more robustly
      if (dateString.includes('T')) {
        // ISO format - clean up timezone issues
        dateString = dateString.replace(/\+00:00$/, 'Z')
        if (!dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
          dateString += 'Z'
        }
      } else if (dateString.includes(' ')) {
        // Space-separated format - convert to ISO
        dateString = dateString.replace(' ', 'T') + 'Z'
      }

      const date = new Date(dateString)

      if (isNaN(date.getTime())) {
        console.warn('Invalid date string:', dateString)
        return 'Recently created'
      }

      // Check if date is reasonable (not too far in future or past)
      const now = new Date()
      const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
      const oneYearFromNow = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate())

      if (date < oneYearAgo || date > oneYearFromNow) {
        return 'Recently created'
      }

      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        ...(variant === 'management' && {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        })
      })
    } catch (error) {
      console.error('Date formatting error:', error)
      return 'Recently created'
    }
  }, [post.created_at, post.published_at, variant])

  // Memoize content truncation
  const displayContent = useMemo(() => {
    if (showFullContent || viewMode === 'list') return post.content
    // Increase character limit for mobile to show more content
    const maxLength = viewMode === 'grid' ? 300 : 400
    
    if (post.content.length <= maxLength) return post.content
    
    // Find the last complete word before maxLength
    const truncated = post.content.substring(0, maxLength)
    const lastSpace = truncated.lastIndexOf(' ')
    
    // Find the last complete emoji before maxLength (emoji regex)
    const lastEmoji = truncated.match(/[\u{1F300}-\u{1F9FF}](?=[\u{1F300}-\u{1F9FF}]*$)/u)
    const lastEmojiIndex = lastEmoji ? truncated.lastIndexOf(lastEmoji[0]) : -1
    
    // Use the later of word or emoji boundary
    const breakPoint = Math.max(lastSpace, lastEmojiIndex)
    return breakPoint > 0 
      ? truncated.substring(0, breakPoint) + '...'
      : truncated + '...'
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
    { icon: EyeIcon, value: post.analytics?.views || 0, label: 'views' },
    { icon: HeartIcon, value: post.analytics?.likes || 0, label: 'likes' },
    { icon: ShareIcon, value: post.analytics?.shares || 0, label: 'shares' },
    { icon: ChatBubbleLeftRightIcon, value: post.analytics?.comments || 0, label: 'comments' }
  ], [post.analytics?.views, post.analytics?.likes, post.analytics?.shares, post.analytics?.comments])

  if (variant === 'public') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={className}
      >
        <Card className="h-full hover:shadow-sm transition-all duration-300 w-full max-w-[400px] sm:max-w-[450px] mx-auto bg-white">
          <CardHeader className="p-2.5 sm:p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center">
                  <SparklesIcon className="w-4 h-4 text-blue-600" />
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-gray-900">
                    RealEstate AI
                  </span>
                  <time className="text-xs text-gray-500">{formattedDate}</time>
                </div>
              </div>
              <div className="flex items-center">
                <span className="text-sm text-gray-600">
                  {getChannelIcon(post.channels[0])}
                </span>
              </div>
            </div>

            <Link href={`/agent/${agentName}/posts/${post.id}`}>
              <h3 className="text-base sm:text-lg font-bold text-gray-900 hover:text-blue-600 transition-colors line-clamp-2">
                {post.title}
              </h3>
            </Link>

            {post.property_title && (
              <p className="text-xs sm:text-sm text-gray-600 mt-2 flex items-center">
                <GlobeAltIcon className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                <span className="line-clamp-1">{post.property_title}</span>
              </p>
            )}
          </CardHeader>

          <CardContent className="p-2.5 sm:p-3">
            <p className="text-gray-800 text-sm leading-5 mb-2.5">
              {displayContent}
            </p>

            {/* Image Gallery */}
            {(() => {
              console.log('Post data for image display (management variant):', {
                hasMediaUrls: !!post.media_urls,
                mediaUrlsLength: post.media_urls?.length || 0,
                mediaUrls: post.media_urls
              })
              return post.media_urls && post.media_urls.length > 0 && (
                <ImageGallery mediaUrls={post.media_urls} />
              )
            })()}

            {/* Stats */}
            <div className="mt-2 border-t border-gray-100">
              <div className="grid grid-cols-4 gap-1 text-center pt-1">
                {stats.map((stat, idx) => (
                  <div key={idx} className="group cursor-pointer touch-manipulation">
                    <div className="flex flex-col items-center py-2 px-1 group-hover:bg-gray-50 active:bg-gray-100 transition-colors rounded">
                      <stat.icon className="w-4 h-4 text-gray-500 group-hover:text-blue-600 group-active:text-blue-700 mb-0.5" />
                      <span className="text-xs font-medium text-gray-700">{stat.value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  // Management variant
  return (
    <div className={`${viewMode === 'list' ? 'mb-4' : ''} ${className}`}>
      <Card className={`
        ${viewMode === 'list' ? 'flex flex-row' : 'h-full'}
        hover:shadow-lg transition-all duration-200 max-w-[400px] sm:max-w-[450px] mx-auto
      `}>
        <div className={`${viewMode === 'list' ? 'flex-1 flex' : ''}`}>
          <CardContent className={`${viewMode === 'list' ? 'flex-1 p-3' : 'p-3 sm:p-4'}`}>
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-base sm:text-lg font-semibold text-gray-800 flex-1 mr-2">
                {post.title}
              </h3>
              <StatusBadge status={post.status} />
            </div>

            <p className={`text-gray-600 text-sm leading-5 mb-3 ${viewMode === 'grid' ? 'line-clamp-3' : ''}`}>
              {displayContent}
            </p>

            {/* Image Gallery */}
            {(() => {
              console.log('Post data for image display (management variant):', {
                hasMediaUrls: !!post.media_urls,
                mediaUrlsLength: post.media_urls?.length || 0,
                mediaUrls: post.media_urls
              })
              return post.media_urls && post.media_urls.length > 0 && (
                <ImageGallery mediaUrls={post.media_urls} />
              )
            })()}

            <div className="flex flex-wrap gap-1.5 mb-3">
              {post.channels.map((channel) => (
                <ChannelBadge key={channel} channel={channel} />
              ))}
            </div>

            <div className={`${viewMode === 'list' ? 'flex' : 'flex flex-col sm:flex-row'} justify-between items-start sm:items-center space-y-2 sm:space-y-0 text-xs sm:text-sm text-gray-500`}>
              <span className="inline-block">{formattedDate}</span>
              {post.property_title && (
                <span className="flex items-center">
                  <GlobeAltIcon className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                  <span className="line-clamp-1">{post.property_title}</span>
                </span>
              )}
            </div>

            {/* Action Buttons */}
            {showActions && (
              <div className="mt-3 flex flex-wrap gap-2">
                {onEdit && (
                  <button
                    onClick={() => onEdit(post)}
                    className="flex items-center gap-1.5 px-4 py-2.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 active:bg-blue-200 transition-colors min-w-[88px] min-h-[40px] justify-center touch-manipulation"
                  >
                    <PencilIcon className="w-4 h-4" />
                    Edit
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={() => onDelete(post.id)}
                    className="flex items-center gap-1.5 px-4 py-2.5 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100 active:bg-red-200 transition-colors min-w-[88px] min-h-[40px] justify-center touch-manipulation"
                  >
                    <TrashIcon className="w-4 h-4" />
                    Delete
                  </button>
                )}
                {onPublish && post.status === 'draft' && (
                  <button
                    onClick={() => onPublish(post.id, post.channels)}
                    className="flex items-center gap-1.5 px-4 py-2.5 text-sm bg-green-50 text-green-600 rounded-lg hover:bg-green-100 active:bg-green-200 transition-colors min-w-[88px] min-h-[40px] justify-center touch-manipulation"
                  >
                    <GlobeAltIcon className="w-4 h-4" />
                    Publish
                  </button>
                )}
              </div>
            )}
          </CardContent>
        </div>
      </Card>
    </div>
  )
})

UnifiedPostCard.displayName = 'UnifiedPostCard'

export default UnifiedPostCard