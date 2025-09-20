'use client'

import { AIDraft, DraftStatus, PropertyContext } from '@/types/social_publishing'
import {
    ArrowLeftIcon,
    ArrowRightIcon,
    CheckCircleIcon,
    EyeIcon,
    PencilIcon,
    SparklesIcon
} from '@heroicons/react/24/outline'
import { motion, PanInfo } from 'framer-motion'
import { useState } from 'react'

interface ContentReviewMobileProps {
    property: PropertyContext
    generatedContent: Map<string, AIDraft>
    onDraftUpdate: (language: string, draft: AIDraft) => void
    onMarkReady: (language: string) => void
    onPublish: () => void
    readyDrafts: AIDraft[]
}

const LANGUAGE_NAMES = {
    'en': 'English',
    'hi': 'Hindi',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'ta': 'Tamil',
    'te': 'Telugu',
    'bn': 'Bengali',
    'pa': 'Punjabi',
    'kn': 'Kannada',
    'ml': 'Malayalam'
}

const LANGUAGE_FLAGS = {
    'en': '🇺🇸',
    'hi': '🇮🇳',
    'mr': '🇮🇳',
    'gu': '🇮🇳',
    'ta': '🇮🇳',
    'te': '🇮🇳',
    'bn': '🇮🇳',
    'pa': '🇮🇳',
    'kn': '🇮🇳',
    'ml': '🇮🇳'
}

export default function ContentReviewMobile({
    property,
    generatedContent,
    onDraftUpdate,
    onMarkReady,
    onPublish,
    readyDrafts
}: ContentReviewMobileProps) {

    const [currentLanguageIndex, setCurrentLanguageIndex] = useState(0)
    const [editingField, setEditingField] = useState<'title' | 'body' | 'hashtags' | null>(null)
    const [editValue, setEditValue] = useState('')

    const languages = Array.from(generatedContent.keys())
    const currentLanguage = languages[currentLanguageIndex]
    const currentDraft = generatedContent.get(currentLanguage)

    const handleSwipe = (direction: 'left' | 'right') => {
        if (direction === 'left' && currentLanguageIndex < languages.length - 1) {
            setCurrentLanguageIndex(currentLanguageIndex + 1)
        } else if (direction === 'right' && currentLanguageIndex > 0) {
            setCurrentLanguageIndex(currentLanguageIndex - 1)
        }
    }

    const handlePanEnd = (event: any, info: PanInfo) => {
        const threshold = 50
        if (info.offset.x > threshold) {
            handleSwipe('right')
        } else if (info.offset.x < -threshold) {
            handleSwipe('left')
        }
    }

    const handleStartEdit = (field: 'title' | 'body' | 'hashtags') => {
        if (currentDraft) {
            setEditingField(field)
            if (field === 'hashtags') {
                setEditValue(currentDraft.hashtags.join(' '))
            } else {
                setEditValue(currentDraft[field] as string)
            }
        }
    }

    const handleSaveEdit = () => {
        if (editingField && currentDraft && currentLanguage) {
            const updatedDraft = { ...currentDraft }

            if (editingField === 'hashtags') {
                updatedDraft.hashtags = editValue.split(' ').filter(tag => tag.trim()).map(tag =>
                    tag.startsWith('#') ? tag : `#${tag}`
                )
            } else {
                updatedDraft[editingField] = editValue
            }

            updatedDraft.status = 'edited'
            onDraftUpdate(currentLanguage, updatedDraft)
            setEditingField(null)
            setEditValue('')
        }
    }

    const handleCancelEdit = () => {
        setEditingField(null)
        setEditValue('')
    }

    const getStatusColor = (status: DraftStatus) => {
        switch (status) {
            case 'generated': return 'bg-blue-100 text-blue-800'
            case 'edited': return 'bg-yellow-100 text-yellow-800'
            case 'ready': return 'bg-green-100 text-green-800'
            default: return 'bg-gray-100 text-gray-800'
        }
    }

    const getStatusIcon = (status: DraftStatus) => {
        switch (status) {
            case 'ready': return <CheckCircleIcon className="w-4 h-4" />
            default: return <SparklesIcon className="w-4 h-4" />
        }
    }

    if (languages.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-96 px-4">
                <SparklesIcon className="w-16 h-16 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Content Generated</h3>
                <p className="text-gray-500 text-center">Go back and generate some content first</p>
            </div>
        )
    }

    return (
        <div className="flex flex-col h-full bg-gray-50">
            {/* Language Switcher */}
            <div className="bg-white border-b border-gray-200 px-4 py-3">
                <div className="flex items-center justify-between">
                    <button
                        onClick={() => handleSwipe('right')}
                        disabled={currentLanguageIndex === 0}
                        className="p-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <ArrowLeftIcon className="w-5 h-5 text-gray-600" />
                    </button>

                    <div className="flex items-center space-x-2">
                        <span className="text-2xl">{LANGUAGE_FLAGS[currentLanguage as keyof typeof LANGUAGE_FLAGS]}</span>
                        <span className="font-semibold text-gray-900">
                            {LANGUAGE_NAMES[currentLanguage as keyof typeof LANGUAGE_NAMES]}
                        </span>
                    </div>

                    <button
                        onClick={() => handleSwipe('left')}
                        disabled={currentLanguageIndex === languages.length - 1}
                        className="p-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <ArrowRightIcon className="w-5 h-5 text-gray-600" />
                    </button>
                </div>

                {/* Language Dots */}
                <div className="flex justify-center space-x-2 mt-3">
                    {languages.map((_, index) => (
                        <button
                            key={index}
                            onClick={() => setCurrentLanguageIndex(index)}
                            className={`w-2 h-2 rounded-full transition-colors ${index === currentLanguageIndex ? 'bg-blue-500' : 'bg-gray-300'
                                }`}
                        />
                    ))}
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto">
                <motion.div
                    key={currentLanguage}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                    drag="x"
                    dragConstraints={{ left: 0, right: 0 }}
                    onPanEnd={handlePanEnd}
                    className="h-full"
                >
                    <div className="p-4 space-y-4">
                        {/* Status Header */}
                        {currentDraft && (
                            <div className="bg-white rounded-xl p-4 border border-gray-200">
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center space-x-2">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(currentDraft.status)}`}>
                                            {getStatusIcon(currentDraft.status)}
                                            <span className="ml-1 capitalize">{currentDraft.status}</span>
                                        </span>
                                    </div>

                                    <div className="flex items-center space-x-2">
                                        <span className="text-xs text-gray-500">
                                            Tap edit icons to modify content
                                        </span>
                                    </div>
                                </div>

                                {/* Content Preview */}
                                <div className="space-y-3">
                                    {/* Title */}
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <h4 className="font-semibold text-gray-900">Title</h4>
                                            <button
                                                onClick={() => handleStartEdit('title')}
                                                className="p-1 text-gray-400 hover:text-blue-600"
                                            >
                                                <PencilIcon className="w-4 h-4" />
                                            </button>
                                        </div>
                                        {editingField === 'title' ? (
                                            <div className="space-y-2">
                                                <input
                                                    type="text"
                                                    value={editValue}
                                                    onChange={(e) => setEditValue(e.target.value)}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
                                                />
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={handleSaveEdit}
                                                        className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
                                                    >
                                                        Save
                                                    </button>
                                                    <button
                                                        onClick={handleCancelEdit}
                                                        className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <p className="text-gray-700">{currentDraft.title}</p>
                                        )}
                                    </div>

                                    {/* Content Body */}
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <h4 className="font-semibold text-gray-900">Content</h4>
                                            <button
                                                onClick={() => handleStartEdit('body')}
                                                className="p-1 text-gray-400 hover:text-blue-600"
                                            >
                                                <PencilIcon className="w-4 h-4" />
                                            </button>
                                        </div>
                                        {editingField === 'body' ? (
                                            <div className="space-y-2">
                                                <textarea
                                                    value={editValue}
                                                    onChange={(e) => setEditValue(e.target.value)}
                                                    rows={4}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
                                                />
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={handleSaveEdit}
                                                        className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
                                                    >
                                                        Save
                                                    </button>
                                                    <button
                                                        onClick={handleCancelEdit}
                                                        className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="bg-gray-50 rounded-lg p-3">
                                                <p className="text-gray-700 whitespace-pre-wrap">{currentDraft.body}</p>
                                            </div>
                                        )}
                                    </div>

                                    {/* Hashtags */}
                                    {currentDraft.hashtags.length > 0 && (
                                        <div>
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="font-semibold text-gray-900">Hashtags</h4>
                                                <button
                                                    onClick={() => handleStartEdit('hashtags')}
                                                    className="p-1 text-gray-400 hover:text-blue-600"
                                                >
                                                    <PencilIcon className="w-4 h-4" />
                                                </button>
                                            </div>
                                            {editingField === 'hashtags' ? (
                                                <div className="space-y-2">
                                                    <input
                                                        type="text"
                                                        value={editValue}
                                                        onChange={(e) => setEditValue(e.target.value)}
                                                        placeholder="#realestate #property #investment"
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
                                                    />
                                                    <div className="flex space-x-2">
                                                        <button
                                                            onClick={handleSaveEdit}
                                                            className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
                                                        >
                                                            Save
                                                        </button>
                                                        <button
                                                            onClick={handleCancelEdit}
                                                            className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm"
                                                        >
                                                            Cancel
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="flex flex-wrap gap-1">
                                                    {currentDraft.hashtags.map((hashtag, index) => (
                                                        <span
                                                            key={index}
                                                            className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-blue-50 text-blue-700"
                                                        >
                                                            {hashtag}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Platform Preview */}
                        {currentDraft && (
                            <div className="bg-white rounded-xl p-4 border border-gray-200">
                                <div className="flex items-center space-x-2 mb-3">
                                    <EyeIcon className="w-5 h-5 text-gray-600" />
                                    <h4 className="font-semibold text-gray-900">Preview</h4>
                                </div>

                                {/* Mock Social Media Post */}
                                <div className={`border rounded-lg p-4 ${currentDraft.channel === 'facebook' ? 'border-blue-200 bg-blue-50' : 'border-pink-200 bg-pink-50'
                                    }`}>
                                    <div className="flex items-center space-x-3 mb-3">
                                        <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                                            <span className="text-lg">🏠</span>
                                        </div>
                                        <div>
                                            <p className="font-semibold text-gray-900">PropertyAI</p>
                                            <p className="text-xs text-gray-600">2 hours ago</p>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <h5 className="font-semibold text-gray-900">{currentDraft.title}</h5>
                                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{currentDraft.body}</p>
                                        {currentDraft.hashtags.length > 0 && (
                                            <div className="flex flex-wrap gap-1 mt-2">
                                                {currentDraft.hashtags.slice(0, 5).map((hashtag, index) => (
                                                    <span key={index} className="text-blue-600 text-sm">{hashtag}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>

            {/* Bottom Actions */}
            <div className="bg-white border-t border-gray-200 p-4">
                {currentDraft && currentDraft.status !== 'ready' && (
                    <button
                        onClick={() => onMarkReady(currentLanguage)}
                        className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 active:scale-95 transition-all"
                    >
                        <div className="flex items-center justify-center space-x-2">
                            <CheckCircleIcon className="w-5 h-5" />
                            <span>Mark as Ready</span>
                        </div>
                    </button>
                )}

                {currentDraft && currentDraft.status === 'ready' && (
                    <div className="text-center">
                        <div className="flex items-center justify-center space-x-2 text-green-600 mb-2">
                            <CheckCircleIcon className="w-5 h-5" />
                            <span className="font-medium">Ready for Publishing</span>
                        </div>
                        <p className="text-sm text-gray-600">
                            This content is ready to be published
                        </p>
                    </div>
                )}
            </div>

        </div>
    )
}
