import React, { useState } from 'react';
import { Post } from '../../types/post';
import ChannelBadge from '../UI/ChannelBadge';
import StatusBadge from '../UI/StatusBadge';
import PostActionsMenu from './PostActionsMenu';

interface PostCardProps {
    post: Post;
    viewMode: 'grid' | 'list';
    onEdit: (post: Post) => void;
    onDelete: (postId: string) => void;
    onPublish: (postId: string, channels: string[]) => void;
}

export const PostCard: React.FC<PostCardProps> = ({
    post,
    viewMode,
    onEdit,
    onDelete,
    onPublish
}) => {
    const [showActions, setShowActions] = useState(false);
    const [isPublishing, setIsPublishing] = useState(false);

    const handlePublish = async (channels: string[]) => {
        setIsPublishing(true);
        try {
            await onPublish(post.id, channels);
        } catch (error) {
            console.error('Failed to publish post:', error);
        } finally {
            setIsPublishing(false);
        }
    };

    const formatDate = (date: string) => {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const truncateContent = (content: string, maxLength: number = 150) => {
        if (content.length <= maxLength) return content;
        return content.substring(0, maxLength) + '...';
    };

    const getLanguageFlag = (language: string) => {
        const flags: { [key: string]: string } = {
            'en': '🇺🇸',
            'hi': '🇮🇳',
            'ta': '🇮🇳',
            'te': '🇮🇳',
            'bn': '🇮🇳',
            'gu': '🇮🇳',
            'kn': '🇮🇳',
            'ml': '🇮🇳',
            'mr': '🇮🇳',
            'pa': '🇮🇳',
            'ur': '🇮🇳'
        };
        return flags[language] || '🌐';
    };

    if (viewMode === 'list') {
        return (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-900 truncate">
                                {post.title}
                            </h3>
                            <StatusBadge status={post.status} />
                            <span className="text-sm text-gray-500">
                                {getLanguageFlag(post.language)} {post.language.toUpperCase()}
                            </span>
                            {post.ai_generated && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                    AI Generated
                                </span>
                            )}
                        </div>

                        <p className="text-gray-600 mb-3 line-clamp-2">
                            {truncateContent(post.content, 200)}
                        </p>

                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>Created: {formatDate(post.created_at)}</span>
                            {post.updated_at !== post.created_at && (
                                <span>Updated: {formatDate(post.updated_at)}</span>
                            )}
                            <span>Version: {post.version}</span>
                        </div>

                        {post.channels.length > 0 && (
                            <div className="flex items-center space-x-2 mt-3">
                                <span className="text-sm text-gray-500">Channels:</span>
                                {post.channels.map((channel) => (
                                    <ChannelBadge key={channel} channel={channel} />
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="flex items-center space-x-2 ml-4">
                        <PostActionsMenu
                            post={post}
                            onEdit={() => onEdit(post)}
                            onDelete={() => onDelete(post.id)}
                            onPublish={handlePublish}
                            isPublishing={isPublishing}
                        />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                        {post.title}
                    </h3>
                    <div className="flex items-center space-x-2 mb-3">
                        <StatusBadge status={post.status} />
                        <span className="text-sm text-gray-500">
                            {getLanguageFlag(post.language)} {post.language.toUpperCase()}
                        </span>
                    </div>
                </div>

                <div className="relative">
                    <PostActionsMenu
                        post={post}
                        onEdit={() => onEdit(post)}
                        onDelete={() => onDelete(post.id)}
                        onPublish={handlePublish}
                        isPublishing={isPublishing}
                    />
                </div>
            </div>

            <p className="text-gray-600 mb-4 line-clamp-3">
                {truncateContent(post.content)}
            </p>

            {post.channels.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                    {post.channels.map((channel) => (
                        <ChannelBadge key={channel} channel={channel} />
                    ))}
                </div>
            )}

            <div className="flex items-center justify-between text-sm text-gray-500">
                <div className="flex items-center space-x-3">
                    <span>{formatDate(post.created_at)}</span>
                    {post.updated_at !== post.created_at && (
                        <span>v{post.version}</span>
                    )}
                </div>

                {post.ai_generated && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        AI
                    </span>
                )}
            </div>

            {post.analytics && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-500">Views:</span>
                            <span className="font-medium">{post.analytics.views}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">Likes:</span>
                            <span className="font-medium">{post.analytics.likes}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">Shares:</span>
                            <span className="font-medium">{post.analytics.shares}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">Engagement:</span>
                            <span className="font-medium">{post.analytics.engagement_rate}%</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PostCard;
