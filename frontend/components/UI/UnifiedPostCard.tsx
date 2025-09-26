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
import React, { memo, useMemo } from 'react'
import { Post } from '../../types/post'
import ChannelBadge from './ChannelBadge'
import { Card, CardBody, CardHeader } from './index'
import StatusBadge from './StatusBadge'

// Re-export for convenience
export type { Post }

// Image Gallery Component
const ImageGallery: React.FC<{ mediaUrls: string[] }> = ({ mediaUrls }) => {
  if (!mediaUrls || mediaUrls.length === 0) {
    console.log('No media URLs provided to ImageGallery');
    return null;
  }
  
  console.log('ImageGallery rendering with URLs:', mediaUrls);
  
  const displayImages = mediaUrls.slice(0, 3);
  const remainingCount = mediaUrls.length - 3;
  
  return (
    <div className="mt-3 mb-4">
      <div className="grid gap-2" style={{
        gridTemplateColumns: mediaUrls.length === 1 ? '1fr' : 
                            mediaUrls.length === 2 ? 'repeat(2, 1fr)' : 
                            'repeat(3, 1fr)'
      }}>
        {displayImages.map((url, index) => (
          <div key={url} className="relative aspect-square rounded-lg overflow-hidden bg-gray-100">
            <Image
              src={url}
              alt={`Post image ${index + 1}`}
              fill
              className="object-cover hover:scale-105 transition-transform cursor-pointer"
              sizes="(max-width: 768px) 50vw, 33vw"
              onLoad={() => console.log('Image loaded successfully:', url)}
              onError={(e) => {
                console.error('Failed to load image:', url);
                // Show a placeholder instead of hiding
                e.currentTarget.style.display = 'none';
                const placeholder = e.currentTarget.parentElement?.querySelector('.image-placeholder');
                if (placeholder) {
                  (placeholder as HTMLElement).style.display = 'flex';
                }
              }}
            />
            {/* Fallback placeholder */}
            <div className="image-placeholder absolute inset-0 bg-gray-200 flex items-center justify-center text-gray-500 text-sm" style={{display: 'none'}}>
              Image {index + 1}
            </div>
            {index === 2 && remainingCount > 0 && (
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center text-white font-semibold">
                +{remainingCount}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

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
      let dateString = post.created_at || post.published_at;
      
      if (!dateString) {
        return 'Recently created';
      }
      
      // Handle various date formats more robustly
      if (dateString.includes('T')) {
        // ISO format - clean up timezone issues
        dateString = dateString.replace(/\+00:00$/, 'Z');
        if (!dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
          dateString += 'Z';
        }
      } else if (dateString.includes(' ')) {
        // Space-separated format - convert to ISO
        dateString = dateString.replace(' ', 'T') + 'Z';
      }
      
      const date = new Date(dateString);
      
      if (isNaN(date.getTime())) {
        console.warn('Invalid date string:', dateString);
        return 'Recently created';
      }
      
      // Check if date is reasonable (not too far in future or past)
      const now = new Date();
      const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
      const oneYearFromNow = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate());
      
      if (date < oneYearAgo || date > oneYearFromNow) {
        return 'Recently created';
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
      });
    } catch (error) {
      console.error('Date formatting error:', error);
      return 'Recently created';
    }
  }, [post.created_at, post.published_at, variant])

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

            {/* Image Gallery */}
            {(() => {
              console.log('Post data for image display (public variant):', {
                hasMediaUrls: !!post.media_urls,
                mediaUrlsLength: post.media_urls?.length || 0,
                mediaUrls: post.media_urls
              });
              return post.media_urls && post.media_urls.length > 0 && (
                <ImageGallery mediaUrls={post.media_urls} />
              );
            })()}

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

            {/* Image Gallery */}
            {(() => {
              console.log('Post data for image display (management variant):', {
                hasMediaUrls: !!post.media_urls,
                mediaUrlsLength: post.media_urls?.length || 0,
                mediaUrls: post.media_urls
              });
              return post.media_urls && post.media_urls.length > 0 && (
                <ImageGallery mediaUrls={post.media_urls} />
              );
            })()}

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