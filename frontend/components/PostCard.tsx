'use client'

// Re-export the unified PostCard component for backward compatibility
import UnifiedPostCard, { type Post } from '@/components/UI/UnifiedPostCard'

interface PostCardProps {
    post: Post
    agentName: string
    showFullContent?: boolean
}

export function PostCard({ post, agentName, showFullContent = false }: PostCardProps) {
    return (
        <UnifiedPostCard
            post={post}
            variant="public"
            agentName={agentName}
            showFullContent={showFullContent}
        />
    )
}

// Re-export the Post type for backward compatibility
export type { Post }