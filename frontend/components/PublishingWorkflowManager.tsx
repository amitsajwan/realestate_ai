'use client'

import { useEffect, useState } from 'react'
import PropertySuccessModal from './PropertySuccessModal'
import PublishingConfirmationModal from './PublishingConfirmationModal'
import QuickPostGenerator from './QuickPostGenerator'

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

    // Reset workflow when modal opens/closes
    useEffect(() => {
        console.log('[PublishingWorkflowManager] useEffect triggered:', { isOpen, propertyData })
        if (isOpen && propertyData) {
            console.log('[PublishingWorkflowManager] Opening workflow with property data:', propertyData)
            setCurrentStep('success')
            setPublishingResults([])
        } else if (!isOpen) {
            console.log('[PublishingWorkflowManager] Closing workflow')
            setCurrentStep('closed')
        }
    }, [isOpen, propertyData])

    const handleCreateSocialPosts = () => {
        setCurrentStep('generator')
    }

    const handleBackToSuccess = () => {
        setCurrentStep('success')
    }

    const handlePublish = async (content: any[]) => {
        // Get agent information to construct proper website URL
        let agentSlug = 'default-agent' // fallback

        try {
            // Try to get agent information from localStorage or API
            const agentData = localStorage.getItem('agent_profile')
            if (agentData) {
                const parsed = JSON.parse(agentData)
                agentSlug = parsed.slug || parsed.agent_name?.toLowerCase().replace(/\s+/g, '-') || 'default-agent'
            } else {
                // Try to get from API if not in localStorage
                const token = localStorage.getItem('auth_token')
                if (token) {
                    // First try the agent public profile endpoint
                    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/agent/dashboard/profile`, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    })
                    if (response.ok) {
                        const agentInfo = await response.json()
                        // The agent dashboard profile endpoint returns the profile directly, not wrapped in success/data
                        if (agentInfo && agentInfo.slug) {
                            agentSlug = agentInfo.slug
                        } else if (agentInfo && agentInfo.agent_name) {
                            agentSlug = agentInfo.agent_name.toLowerCase().replace(/\s+/g, '-')
                        }
                    } else {
                        // Fallback: try to get from user profile
                        const userResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me`, {
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            }
                        })
                        if (userResponse.ok) {
                            const userInfo = await userResponse.json()
                            if (userInfo && userInfo.full_name) {
                                agentSlug = userInfo.full_name.toLowerCase().replace(/\s+/g, '-')
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.log('Could not get agent slug, using fallback:', error)
        }

        // Actually publish the property to platforms
        const results: PublishingResult[] = []

        try {
            const token = localStorage.getItem('auth_token')
            if (!token) {
                throw new Error('No authentication token found')
            }

            // Call the actual publish API
            const publishResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/properties/${propertyData?.id}/publish`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    publishing_channels: ['website', 'facebook'],
                    target_languages: ['en'],
                    facebook_page_mappings: {}
                })
            })

            if (publishResponse.ok) {
                const publishData = await publishResponse.json()

                // Add website result
                results.push({
                    platform: 'website',
                    postId: 'web_' + Date.now(),
                    url: `${window.location.origin}/agent/${agentSlug}/properties/${propertyData?.id}`,
                    status: 'success'
                })

                // Add Facebook result if available
                if (publishData.published_channels?.includes('facebook')) {
                    results.push({
                        platform: 'facebook',
                        postId: 'fb_' + Date.now(),
                        url: 'https://facebook.com/posts/fb_' + Date.now(),
                        status: 'success'
                    })
                }
            } else {
                throw new Error('Failed to publish property')
            }
        } catch (error) {
            console.error('Error publishing property:', error)
            // Add error results
            results.push({
                platform: 'website',
                postId: 'web_' + Date.now(),
                url: `${window.location.origin}/agent/${agentSlug}/properties/${propertyData?.id}`,
                status: 'failed'
            })
        }

        setPublishingResults(results)
        setCurrentStep('confirmation')
    }

    const handleViewPosts = () => {
        // Navigate to property marketing hub section
        window.location.href = '/?section=property-marketing-hub'
        onComplete()
    }

    const handleGoToDashboard = () => {
        // Navigate to main dashboard
        window.location.href = '/dashboard'
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

            {/* Step 2: Quick Post Generator */}
            <QuickPostGenerator
                isOpen={currentStep === 'generator'}
                onClose={handleWorkflowClose}
                propertyData={propertyData}
                onPublish={handlePublish}
                onBack={handleBackToSuccess}
            />

            {/* Step 3: Publishing Confirmation */}
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
