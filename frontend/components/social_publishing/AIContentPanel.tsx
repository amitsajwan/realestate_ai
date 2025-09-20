'use client'

import { Button } from '@/components/ui';
import { AIContentPanelProps, AIDraft, CharLimits } from '@/types/social_publishing';
import {
    CheckCircleIcon,
    ClockIcon,
    ExclamationTriangleIcon,
    SparklesIcon
} from '@heroicons/react/24/outline';
import { useState } from 'react';
import ContentEditor from './ContentEditor';
import PreviewPanel from './PreviewPanel';

export default function AIContentPanel({
    property,
    language,
    channel,
    draft,
    onDraftUpdate,
    onRegenerate,
    onImprove,
    onMarkReady,
    isLoading
}: AIContentPanelProps) {

    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // Character limits based on channel
    const getCharLimits = (): CharLimits => {
        if (channel === 'instagram') {
            return {
                maxChars: 2200,
                maxHashtags: 30,
                warningThreshold: 80
            };
        } else {
            return {
                maxChars: 5000,
                maxHashtags: 30,
                warningThreshold: 80
            };
        }
    };

    const limits = getCharLimits();

    const handleDraftUpdate = async (updates: Partial<AIDraft>) => {
        if (!draft) return;

        const updatedDraft = { ...draft, ...updates };
        onDraftUpdate(updatedDraft);

        // Auto-save after 2 seconds
        setIsSaving(true);
        setTimeout(() => {
            setIsSaving(false);
        }, 2000);
    };

    const handleMarkReady = async () => {
        if (!draft) return;

        const updatedDraft = { ...draft, status: 'ready' as const };
        onDraftUpdate(updatedDraft);
        onMarkReady();
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'draft': return 'bg-gray-100 text-gray-800';
            case 'generated': return 'bg-blue-100 text-blue-800';
            case 'edited': return 'bg-yellow-100 text-yellow-800';
            case 'ready': return 'bg-green-100 text-green-800';
            case 'publishing': return 'bg-purple-100 text-purple-800';
            case 'published': return 'bg-green-100 text-green-800';
            case 'failed': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'ready': return <CheckCircleIcon className="w-4 h-4" />;
            case 'publishing': return <ClockIcon className="w-4 h-4" />;
            case 'failed': return <ExclamationTriangleIcon className="w-4 h-4" />;
            default: return <SparklesIcon className="w-4 h-4" />;
        }
    };

    if (isLoading) {
        return (
            <div className="space-y-6">
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
                    <h3 className="text-lg font-semibold text-primary mb-2">
                        Generating AI Content
                    </h3>
                    <p className="text-secondary">
                        Creating {channel} content in {language}...
                    </p>
                </div>
            </div>
        );
    }

    if (!draft) {
        return (
            <div className="text-center py-12">
                <SparklesIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-primary mb-2">
                    No Content Generated
                </h3>
                <p className="text-secondary mb-4">
                    Click "Generate Content" to create AI-powered social media posts
                </p>
                <Button onClick={onRegenerate} variant="primary">
                    Generate Content
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-primary">
                        {channel === 'facebook' ? 'Facebook' : 'Instagram'} Content
                    </h3>
                    <p className="text-sm text-secondary">
                        Language: {language} • Status: {draft.status}
                    </p>
                </div>

                <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(draft.status)}`}>
                        {getStatusIcon(draft.status)}
                        <span className="ml-1 capitalize">{draft.status}</span>
                    </span>

                    {isSaving && (
                        <span className="text-xs text-gray-500">Saving...</span>
                    )}
                </div>
            </div>

            {/* Content Tabs */}
            <div className="border-b border-gray-200 dark:border-gray-600">
                <nav className="-mb-px flex space-x-8">
                    <button
                        onClick={() => setIsEditing(true)}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${isEditing
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                    >
                        Edit Content
                    </button>
                    <button
                        onClick={() => setIsEditing(false)}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${!isEditing
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                    >
                        Preview
                    </button>
                </nav>
            </div>

            {/* Content */}
            {isEditing ? (
                <ContentEditor
                    draft={draft}
                    onUpdate={handleDraftUpdate}
                    limits={limits}
                />
            ) : (
                <PreviewPanel
                    draft={draft}
                    channel={channel}
                />
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-600">
                <div className="flex space-x-2">
                    <Button
                        variant="outline"
                        onClick={onRegenerate}
                        disabled={isLoading}
                    >
                        <SparklesIcon className="w-4 h-4 mr-2" />
                        Regenerate
                    </Button>

                    <Button
                        variant="outline"
                        onClick={() => onImprove('tone_luxury')}
                        disabled={isLoading}
                    >
                        Improve Tone
                    </Button>
                </div>

                <div className="flex space-x-2">
                    <Button
                        variant="outline"
                        onClick={() => setIsEditing(!isEditing)}
                    >
                        {isEditing ? 'Preview' : 'Edit'}
                    </Button>

                    {draft.status !== 'ready' && (
                        <Button
                            variant="primary"
                            onClick={handleMarkReady}
                            disabled={isLoading}
                        >
                            <CheckCircleIcon className="w-4 h-4 mr-2" />
                            Mark Ready
                        </Button>
                    )}
                </div>
            </div>

            {/* Status Messages */}
            {draft.status === 'ready' && (
                <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div className="flex items-center space-x-2">
                        <CheckCircleIcon className="w-5 h-5 text-green-500" />
                        <p className="text-sm text-green-700 dark:text-green-300">
                            This content is ready for publishing!
                        </p>
                    </div>
                </div>
            )}

            {draft.status === 'failed' && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <div className="flex items-center space-x-2">
                        <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                        <p className="text-sm text-red-700 dark:text-red-300">
                            Content generation failed. Please try regenerating.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
