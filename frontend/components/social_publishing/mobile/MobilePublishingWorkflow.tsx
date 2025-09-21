'use client'

import { authManager } from '@/lib/auth'
import { socialPublishingAPI } from '@/lib/social_publishing/api'
import { AIDraft, Channel, DraftStatus, PropertyContext } from '@/types/social_publishing'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import toast from 'react-hot-toast'

// Import mobile components
import ContentReviewMobile from './ContentReviewMobile'
import PropertySelectorMobile from './PropertySelectorMobile'
import PublishingBottomSheet from './PublishingBottomSheet'
import QuickSetupPanel from './QuickSetupPanel'

// Import icons
import {
    ArrowLeftIcon,
    SparklesIcon
} from '@heroicons/react/24/outline'

interface MobilePublishingWorkflowProps {
    properties: PropertyContext[]
    onRefresh?: () => void
}

type WorkflowStep = 'property' | 'setup' | 'generate' | 'review' | 'publish'

interface MobilePublishingState {
    currentStep: WorkflowStep
    selectedProperty: PropertyContext | null
    quickSetup: {
        platforms: Channel[]
        languages: string[]
        style: 'friendly' | 'luxury' | 'investor'
    }
    generatedContent: Map<string, AIDraft> // language -> draft
    isGenerating: boolean
    readyDrafts: AIDraft[]
}

const LANGUAGE_OPTIONS = [
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
    { code: 'mr', name: 'Marathi', flag: '🇮🇳' },
    { code: 'gu', name: 'Gujarati', flag: '🇮🇳' },
    { code: 'ta', name: 'Tamil', flag: '🇮🇳' },
    { code: 'te', name: 'Telugu', flag: '🇮🇳' },
    { code: 'bn', name: 'Bengali', flag: '🇮🇳' },
    { code: 'pa', name: 'Punjabi', flag: '🇮🇳' },
    { code: 'kn', name: 'Kannada', flag: '🇮🇳' },
    { code: 'ml', name: 'Malayalam', flag: '🇮🇳' }
]

const PLATFORM_OPTIONS = [
    {
        code: 'facebook' as Channel,
        name: 'Facebook',
        icon: '📘',
        description: 'Professional posts for business pages'
    },
    {
        code: 'instagram' as Channel,
        name: 'Instagram',
        icon: '📷',
        description: 'Visual stories for engagement'
    },
    {
        code: 'website' as Channel,
        name: 'Website',
        icon: '🌐',
        description: 'Blog posts for your website'
    }
]

const STYLE_OPTIONS = [
    { code: 'friendly' as const, name: 'Friendly', description: 'Approachable and trustworthy' },
    { code: 'luxury' as const, name: 'Luxury', description: 'Premium and sophisticated' },
    { code: 'investor' as const, name: 'Investor', description: 'Professional and data-driven' }
]

export default function MobilePublishingWorkflow({
    properties,
    onRefresh
}: MobilePublishingWorkflowProps) {

    const [state, setState] = useState<MobilePublishingState>({
        currentStep: 'property',
        selectedProperty: null,
        quickSetup: {
            platforms: ['facebook'],
            languages: ['en'],
            style: 'friendly'
        },
        generatedContent: new Map(),
        isGenerating: false,
        readyDrafts: []
    })

    // Step navigation
    const goToStep = (step: WorkflowStep) => {
        setState(prev => ({ ...prev, currentStep: step }))
    }

    const goBack = () => {
        const stepOrder: WorkflowStep[] = ['property', 'setup', 'generate', 'review', 'publish']
        const currentIndex = stepOrder.indexOf(state.currentStep)
        if (currentIndex > 0) {
            goToStep(stepOrder[currentIndex - 1])
        }
    }

    // Property selection
    const handlePropertySelect = async (property: PropertyContext) => {
        setState(prev => ({
            ...prev,
            selectedProperty: property,
            currentStep: 'setup'
        }))

        // Load existing drafts for this property
        try {
            const draftsResponse = await socialPublishingAPI.getDrafts(property.id)

            const existingContent = new Map<string, AIDraft>()
            draftsResponse.forEach(response => {
                if (response.drafts.length > 0) {
                    // Use the first draft for each language
                    existingContent.set(response.language, response.drafts[0])
                }
            })

            if (existingContent.size > 0) {
                setState(prev => ({
                    ...prev,
                    generatedContent: existingContent
                }))
                toast.success(`Loaded ${existingContent.size} existing draft(s)`)
            }
        } catch (error) {
            console.error('Error loading existing drafts:', error)
            // Don't show error toast as this is optional
        }
    }

    // Quick setup handlers
    const handlePlatformToggle = (platform: Channel) => {
        setState(prev => ({
            ...prev,
            quickSetup: {
                ...prev.quickSetup,
                platforms: prev.quickSetup.platforms.includes(platform)
                    ? prev.quickSetup.platforms.filter(p => p !== platform)
                    : [...prev.quickSetup.platforms, platform]
            }
        }))
    }

    const handleLanguageToggle = (language: string) => {
        setState(prev => ({
            ...prev,
            quickSetup: {
                ...prev.quickSetup,
                languages: prev.quickSetup.languages.includes(language)
                    ? prev.quickSetup.languages.filter(l => l !== language)
                    : [...prev.quickSetup.languages, language]
            }
        }))
    }

    const handleStyleChange = (style: 'friendly' | 'luxury' | 'investor') => {
        setState(prev => ({
            ...prev,
            quickSetup: {
                ...prev.quickSetup,
                style
            }
        }))
    }

    const handleGenerateContent = async () => {
        if (!state.selectedProperty) return

        // Check if user is authenticated
        const authState = authManager.getState()
        if (!authState.isAuthenticated || !authState.user?.id) {
            toast.error('Please log in to generate content')
            return
        }

        setState(prev => ({ ...prev, isGenerating: true, currentStep: 'generate' }))

        try {
            const newContent = new Map<string, AIDraft>()

            // Check if we already have content for these languages
            const existingLanguages = Array.from(state.generatedContent.keys())
            const languagesToGenerate = state.quickSetup.languages.filter(lang => !existingLanguages.includes(lang))

            // Only generate content for languages we don't already have
            for (const language of languagesToGenerate) {
                const request = {
                    propertyId: state.selectedProperty.id,
                    language,
                    channels: state.quickSetup.platforms,
                    tone: state.quickSetup.style,
                    length: 'medium',
                    agentId: authState.user.id
                }

                const response = await socialPublishingAPI.generateContent(request)

                // Store the first draft for this language (assuming one platform for simplicity)
                if (response.drafts.length > 0) {
                    const draft = response.drafts[0]
                    console.log('Generated draft:', draft)
                    console.log('Draft ID:', draft.id)

                    // Automatically mark generated drafts as ready for immediate publishing
                    // Update the draft status in the backend first
                    let readyDraft = { ...draft, status: 'ready' as DraftStatus }
                    if (draft.id) {
                        try {
                            console.log('Updating draft status to ready for ID:', draft.id)
                            readyDraft = await socialPublishingAPI.updateDraft(draft.id, { status: 'ready' })
                            console.log('Successfully updated draft status in backend')
                        } catch (error) {
                            console.error('Failed to mark draft as ready in backend:', error)
                            // Continue with frontend state update even if backend fails
                        }
                    } else {
                        console.error('Draft has no ID, cannot update backend status')
                    }

                    newContent.set(language, readyDraft)
                }
            }

            // Merge with existing content
            const mergedContent = new Map([...state.generatedContent, ...newContent])

            // Update readyDrafts array with newly generated ready drafts
            const newReadyDrafts = Array.from(newContent.values()).filter(draft => draft.status === 'ready')
            const updatedReadyDrafts = [...state.readyDrafts, ...newReadyDrafts]

            setState(prev => ({
                ...prev,
                generatedContent: mergedContent,
                readyDrafts: updatedReadyDrafts,
                isGenerating: false,
                currentStep: 'review'
            }))

            if (languagesToGenerate.length > 0) {
                toast.success(`Content generated for ${languagesToGenerate.length} language(s)!`)
            } else {
                toast.success('Using existing content!')
            }
        } catch (error) {
            console.error('Error generating content:', error)
            toast.error('Failed to generate content')
            setState(prev => ({ ...prev, isGenerating: false }))
        }
    }

    const handleDraftUpdate = (language: string, draft: AIDraft) => {
        setState(prev => {
            const newContent = new Map(prev.generatedContent)
            newContent.set(language, draft)
            return {
                ...prev,
                generatedContent: newContent
            }
        })
    }

    const handleMarkReady = async (language: string) => {
        const draft = state.generatedContent.get(language)
        if (!draft?.id) return

        try {
            const updatedDraft = await socialPublishingAPI.updateDraft(draft.id, { status: 'ready' })

            setState(prev => {
                const newContent = new Map(prev.generatedContent)
                newContent.set(language, updatedDraft)
                return {
                    ...prev,
                    generatedContent: newContent,
                    readyDrafts: [...prev.readyDrafts.filter(d => d.id !== draft.id), updatedDraft]
                }
            })

            toast.success('Content marked as ready!')
        } catch (error) {
            console.error('Error marking ready:', error)
            toast.error('Failed to mark content as ready')
        }
    }

    const handlePublish = async () => {
        const readyDrafts = state.readyDrafts.filter(d => d.status === 'ready')
        console.log('Ready drafts for publishing:', readyDrafts)
        console.log('Draft IDs being sent:', readyDrafts.map(d => d.id!).filter(Boolean))

        if (readyDrafts.length === 0) {
            console.log('No ready drafts found for publishing')
            return
        }

        try {
            await socialPublishingAPI.publishDrafts({
                draftIds: readyDrafts.map(d => d.id!).filter(Boolean)
            })

            toast.success('Content published successfully!')
            onRefresh?.()
            goToStep('property') // Reset workflow
        } catch (error) {
            console.error('Error publishing:', error)
            toast.error('Failed to publish content')
        }
    }

    const getStepTitle = () => {
        switch (state.currentStep) {
            case 'property': return 'Select Property'
            case 'setup': return 'Quick Setup'
            case 'generate': return 'Generating Content'
            case 'review': return 'Review & Publish'
            case 'publish': return 'Publishing'
            default: return 'Social Publishing'
        }
    }

    const canProceedFromSetup = () => {
        return state.quickSetup.platforms.length > 0 &&
            state.quickSetup.languages.length > 0
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Mobile Header */}
            <div className="sticky top-0 z-50 bg-white border-b border-gray-200 px-4 py-3">
                <div className="flex items-center justify-between">
                    {state.currentStep !== 'property' && (
                        <button
                            onClick={goBack}
                            className="p-2 -ml-2 text-gray-600 hover:text-gray-900"
                        >
                            <ArrowLeftIcon className="w-5 h-5" />
                        </button>
                    )}

                    <h1 className="text-lg font-semibold text-gray-900 flex-1 text-center">
                        {getStepTitle()}
                    </h1>

                    <div className="w-9" /> {/* Spacer for centering */}
                </div>
            </div>

            {/* Progress Indicator */}
            <div className="px-4 py-3 bg-gray-100">
                <div className="flex items-center justify-center space-x-2">
                    {['property', 'setup', 'generate', 'review'].map((step, index) => (
                        <div key={step} className="flex items-center">
                            <div
                                className={`w-2 h-2 rounded-full ${['property', 'setup', 'generate', 'review'].indexOf(state.currentStep) >= index
                                    ? 'bg-blue-500'
                                    : 'bg-gray-300'
                                    }`}
                            />
                            {index < 3 && <div className="w-4 h-px bg-gray-300 mx-1" />}
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden">
                <AnimatePresence mode="wait">
                    {state.currentStep === 'property' && (
                        <motion.div
                            key="property"
                            initial={{ x: -300, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ x: -300, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <PropertySelectorMobile
                                properties={properties}
                                onPropertySelect={handlePropertySelect}
                            />
                        </motion.div>
                    )}

                    {state.currentStep === 'setup' && (
                        <motion.div
                            key="setup"
                            initial={{ x: 300, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ x: 300, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <QuickSetupPanel
                                platforms={state.quickSetup.platforms}
                                languages={state.quickSetup.languages}
                                style={state.quickSetup.style}
                                onPlatformToggle={handlePlatformToggle}
                                onLanguageToggle={handleLanguageToggle}
                                onStyleChange={handleStyleChange}
                                onGenerate={handleGenerateContent}
                                canProceed={canProceedFromSetup()}
                                platformOptions={PLATFORM_OPTIONS}
                                languageOptions={LANGUAGE_OPTIONS}
                                styleOptions={STYLE_OPTIONS}
                            />
                        </motion.div>
                    )}

                    {state.currentStep === 'generate' && (
                        <motion.div
                            key="generate"
                            initial={{ x: 300, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ x: 300, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="h-full"
                        >
                            <div className="flex flex-col items-center justify-center h-96 px-4">
                                <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mb-6"></div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                    Generating Content
                                </h3>
                                <p className="text-gray-600 text-center">
                                    Creating {state.quickSetup.platforms.length} posts in {state.quickSetup.languages.length} languages...
                                </p>
                                <div className="mt-6 space-y-2">
                                    {state.quickSetup.languages.map((lang, index) => (
                                        <div key={lang} className="flex items-center space-x-2">
                                            <SparklesIcon className="w-4 h-4 text-blue-500" />
                                            <span className="text-sm text-gray-600">
                                                {LANGUAGE_OPTIONS.find(l => l.code === lang)?.name} content
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {state.currentStep === 'review' && (
                        <motion.div
                            key="review"
                            initial={{ x: 300, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ x: 300, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="h-full"
                        >
                            <ContentReviewMobile
                                property={state.selectedProperty!}
                                generatedContent={state.generatedContent}
                                onDraftUpdate={handleDraftUpdate}
                                onMarkReady={handleMarkReady}
                                onPublish={handlePublish}
                                readyDrafts={state.readyDrafts}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Bottom Publishing Sheet */}
            {state.readyDrafts.length > 0 && (
                <PublishingBottomSheet
                    readyDrafts={state.readyDrafts}
                    onPublish={handlePublish}
                    onSchedule={(scheduleAt) => {
                        // TODO: Implement scheduling
                        toast.success('Scheduling not implemented yet')
                    }}
                />
            )}
        </div>
    )
}
