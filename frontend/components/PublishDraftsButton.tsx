'use client'

import { unifiedAuthService } from '@/lib/auth/unified-auth'
import { Loader2, Send } from 'lucide-react'
import { useState } from 'react'
import { Button } from './UI/Button'

interface PublishDraftsButtonProps {
    draftIds: string[]
    onPublishSuccess?: () => void
    disabled?: boolean
    className?: string
}

export default function PublishDraftsButton({
    draftIds,
    onPublishSuccess,
    disabled = false,
    className = ""
}: PublishDraftsButtonProps) {
    const [isPublishing, setIsPublishing] = useState(false)

    const handlePublish = async () => {
        if (draftIds.length === 0) {
            alert('No drafts selected for publishing')
            return
        }

        setIsPublishing(true)

        try {
            const response = await unifiedAuthService.authenticatedRequest(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/content/publish-drafts`, {
                method: 'POST',
                body: JSON.stringify(draftIds)
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Failed to publish drafts')
            }

            const result = await response.json()

            if (result.published_count > 0) {
                alert(`Successfully published ${result.published_count} posts!`)
                onPublishSuccess?.()
            } else {
                alert('No drafts were published')
            }

            if (result.failed_count > 0) {
                alert(`${result.failed_count} drafts failed to publish`)
            }

        } catch (error) {
            console.error('Error publishing drafts:', error)
            alert(error instanceof Error ? error.message : 'Failed to publish drafts')
        } finally {
            setIsPublishing(false)
        }
    }

    return (
        <Button
            onClick={handlePublish}
            disabled={disabled || isPublishing || draftIds.length === 0}
            className={`${className}`}
            variant="primary"
        >
            {isPublishing ? (
                <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Publishing...
                </>
            ) : (
                <>
                    <Send className="w-4 h-4 mr-2" />
                    Publish Selected ({draftIds.length})
                </>
            )}
        </Button>
    )
}
