'use client'

import { API_BASE_URL } from '@/lib/config/api'
import { apiService } from '@/lib/api/centralized-client'
import { generatePropertyUrl, getAgentSlug } from '@/lib/utils/slug'
import { useEffect, useState } from 'react'
import PropertySuccessModal from './PropertySuccessModal'
import PublishingConfirmationModal from './PublishingConfirmationModal'
import UnifiedPostingHub from './UnifiedPostingHub'

interface PropertyData {
    id: string
    title: string
    location: string
    price: number
    bedrooms: number
    bathrooms: number
    propertyType: string
    area?: number
    description?: string
    images?: string[]
    status?: string
    publishing_status?: string
}

interface PublishingResult {
    platform: 'website' | 'facebook' | 'instagram'
    postId: string
    url: string
    status: 'success' | 'failed'
    error?: string
}

interface PublishingWorkflowManagerProps {
    propertyData: PropertyData | null
    isOpen: boolean
    onClose: () => void
    onComplete: () => void
}

type WorkflowStep = 'success' | 'generator' | 'confirmation' | 'closed'

export default function PublishingWorkflowManager({
    propertyData,
    isOpen,
    onClose,
    onComplete
}: PublishingWorkflowManagerProps) {
    const [currentStep, setCurrentStep] = useState<WorkflowStep>('closed')
    const [publishingResults, setPublishingResults] = useState<PublishingResult[]>([])

    useEffect(() => {
        if (isOpen && propertyData) {
            setCurrentStep('success')
            setPublishingResults([])
        } else {
            setCurrentStep('closed')
        }
    }, [isOpen, propertyData])

    const handleCreateSocialPosts = () => {
        setCurrentStep('generator')
    }

    const handleBackToSuccess = () => {
        setCurrentStep('success')
    }

    const handlePublish = async (content: any) => {
        const results: PublishingResult[] = []
        const selectedLanguage = 'en'
        
        try {
            console.log('AI content generated:', content)

            // Save the generated content using the centralized API
            if (content && Array.isArray(content)) {
                for (const contentItem of content) {
                    const postData = {
                        property_id: propertyData?.id,
                        title: contentItem.title || '',
                        content: contentItem.content || '',
                        language: contentItem.language || selectedLanguage,
                        channels: [contentItem.platform],
                        ai_generated: true,
                        ai_prompt: 'AI generated content for publishing',
                        hashtags: contentItem.hashtags || [],
                        status: 'published'
                    }

                    await apiService.createPost(postData)
                    console.log(`Saved content for ${contentItem.platform}/${contentItem.language}`)
                }
            }

            // Add website result
            results.push({
                platform: 'website',
                postId: 'web_' + Date.now(),
                url: generatePropertyUrl(propertyData?.id || '', getAgentSlug({}) || 'default', undefined, propertyData?.publishing_status || propertyData?.status),
                status: 'success'
            })

            // Add Facebook result
            results.push({
                platform: 'facebook',
                postId: 'fb_' + Date.now(),
                url: generatePropertyUrl(propertyData?.id || '', getAgentSlug({}) || 'default', 'facebook', propertyData?.publishing_status || propertyData?.status),
                status: 'success'
            })

            // Add Instagram result
            results.push({
                platform: 'instagram',
                postId: 'ig_' + Date.now(),
                url: generatePropertyUrl(propertyData?.id || '', getAgentSlug({}) || 'default', 'instagram', propertyData?.publishing_status || propertyData?.status),
                status: 'success'
            })

            setPublishingResults(results)
            setCurrentStep('confirmation')

            // Auto-close after 3 seconds
            setTimeout(() => {
                onComplete()
            }, 3000)
        } catch (error) {
            console.error('Error publishing content:', error)
            // Add error results
            const errorResults: PublishingResult[] = [
                {
                    platform: 'website',
                    postId: '',
                    url: '',
                    status: 'failed',
                    error: error instanceof Error ? error.message : 'Unknown error'
                },
                {
                    platform: 'facebook',
                    postId: '',
                    url: '',
                    status: 'failed',
                    error: error instanceof Error ? error.message : 'Unknown error'
                },
                {
                    platform: 'instagram',
                    postId: '',
                    url: '',
                    status: 'failed',
                    error: error instanceof Error ? error.message : 'Unknown error'
                }
            ]
            setPublishingResults(errorResults)
            setCurrentStep('confirmation')
        }
    }

    const handleViewPosts = () => {
        // Navigate to property marketing hub section
        window.location.href = '/?section=ai-content'
        onComplete()
    }

    const handleGoToDashboard = () => {
        // Navigate to main dashboard
        window.location.href = '/'
        onComplete()
    }

    const handleWorkflowClose = () => {
        setCurrentStep('closed')
        onClose()
    }

    if (!propertyData || !isOpen) {
        return null
    }

    return (
        <>
            {/* Step 1: Property Success Modal */}
            <PropertySuccessModal
                isOpen={currentStep === 'success'}
                onClose={handleWorkflowClose}
                propertyData={propertyData}
                onCreateSocialPosts={handleCreateSocialPosts}
                onGoToDashboard={handleGoToDashboard}
            />

            {/* Step 2: Unified Posting Hub */}
            <UnifiedPostingHub
                mode="quick-post"
                isOpen={currentStep === 'generator'}
                onClose={handleWorkflowClose}
                propertyData={propertyData}
                onPublish={(content, language) => {
                    handlePublish(content)
                }}
            />

            {/* Step 3: Publishing Confirmation Modal */}
            <PublishingConfirmationModal
                isOpen={currentStep === 'confirmation'}
                onClose={handleWorkflowClose}
                publishingResults={publishingResults}
                propertyData={propertyData}
                onViewPosts={handleViewPosts}
            />
        </>
    )
}