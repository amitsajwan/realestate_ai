import React from 'react';
import UnifiedPostCard, { type Post } from '../UI/UnifiedPostCard';

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
    return (
        <UnifiedPostCard
            post={post}
            variant="management"
            viewMode={viewMode}
            onEdit={onEdit}
            onDelete={onDelete}
            onPublish={onPublish}
            showActions={true}
        />
    );
};

export default PostCard;