'use client'

import { socialPublishingAPI } from '@/lib/social_publishing/api';
import {
    AIDraft,
    Channel,
    GenerateContentRequest,
    PropertyContext,
    PublishingUIState
} from '@/types/social_publishing';
import {
    SparklesIcon
} from '@heroicons/react/24/outline';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import AIContentPanel from './AIContentPanel';
import ChannelSelector from './ChannelSelector';
import LanguageSelector from './LanguageSelector';
import PublishBar from './PublishBar';

interface SocialPublishingWorkflowProps {
    properties: PropertyContext[];
    onRefresh?: () => void;
}

export default function SocialPublishingWorkflow({
    properties,
    onRefresh
}: SocialPublishingWorkflowProps) {

    const [uiState, setUIState] = useState<PublishingUIState>({
        selectedProperty: null,
        selectedLanguages: ['en'],
        selectedChannels: ['facebook'],
        drafts: new Map(),
        loadingStates: new Map(),
        currentLanguage: 'en',
        currentChannel: 'facebook'
    });

    const [isGenerating, setIsGenerating] = useState(false);
    const [isPublishing, setIsPublishing] = useState(false);

    // Load drafts when property changes
    useEffect(() => {
        if (uiState.selectedProperty) {
            loadDrafts(uiState.selectedProperty.id);
        }
    }, [uiState.selectedProperty]);

    const loadDrafts = async (propertyId: string) => {
        try {
            const draftsResponse = await socialPublishingAPI.getDrafts(propertyId);

            const newDrafts = new Map();
            draftsResponse.forEach(response => {
                const channelDrafts = new Map();
                response.drafts.forEach(draft => {
                    channelDrafts.set(draft.channel, draft);
                });
                newDrafts.set(response.language, channelDrafts);
            });

            setUIState(prev => ({
                ...prev,
                drafts: newDrafts
            }));
        } catch (error) {
            console.error('Error loading drafts:', error);
            toast.error('Failed to load drafts');
        }
    };

    const handlePropertySelect = (property: PropertyContext) => {
        setUIState(prev => ({
            ...prev,
            selectedProperty: property
        }));
    };

    const handleLanguageChange = (languages: string[]) => {
        setUIState(prev => ({
            ...prev,
            selectedLanguages: languages
        }));
    };

    const handleLanguageAdded = async (language: string) => {
        if (!uiState.selectedProperty) return;

        setUIState(prev => ({
            ...prev,
            loadingStates: new Map(prev.loadingStates.set(language, true))
        }));

        try {
            const request: GenerateContentRequest = {
                propertyId: uiState.selectedProperty.id,
                language: language,
                channels: uiState.selectedChannels,
                tone: 'friendly',
                length: 'medium',
                agentId: 'current-user' // TODO: Get from auth context
            };

            const response = await socialPublishingAPI.generateContent(request);

            // Update drafts with new content
            const newDrafts = new Map(uiState.drafts);
            const channelDrafts = new Map();

            response.drafts.forEach(draft => {
                channelDrafts.set(draft.channel, draft);
            });

            newDrafts.set(language, channelDrafts);

            setUIState(prev => ({
                ...prev,
                drafts: newDrafts,
                loadingStates: new Map(prev.loadingStates.set(language, false))
            }));

            toast.success(`Content generated for ${language}`);
        } catch (error) {
            console.error('Error generating content:', error);
            toast.error('Failed to generate content');
            setUIState(prev => ({
                ...prev,
                loadingStates: new Map(prev.loadingStates.set(language, false))
            }));
        }
    };

    const handleChannelChange = (channels: Channel[]) => {
        setUIState(prev => ({
            ...prev,
            selectedChannels: channels
        }));
    };

    const handleDraftUpdate = (draft: AIDraft) => {
        const newDrafts = new Map(uiState.drafts);
        const languageDrafts = new Map(newDrafts.get(draft.language) || new Map());
        languageDrafts.set(draft.channel, draft);
        newDrafts.set(draft.language, languageDrafts);

        setUIState(prev => ({
            ...prev,
            drafts: newDrafts
        }));
    };

    const handleRegenerate = async () => {
        if (!uiState.selectedProperty) return;

        setIsGenerating(true);
        try {
            await handleLanguageAdded(uiState.currentLanguage);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleImprove = async (type: string) => {
        // TODO: Implement content improvement
        toast.success(`Improving content: ${type}`);
    };

    const handleMarkReady = async () => {
        const currentDraft = getCurrentDraft();
        if (!currentDraft) return;

        try {
            await socialPublishingAPI.updateDraft(currentDraft.id!, {
                status: 'ready'
            });

            handleDraftUpdate({ ...currentDraft, status: 'ready' });
            toast.success('Content marked as ready');
        } catch (error) {
            console.error('Error marking ready:', error);
            toast.error('Failed to mark content as ready');
        }
    };

    const handlePublish = async () => {
        const readyDrafts = getReadyDrafts();
        if (readyDrafts.length === 0) return;

        setIsPublishing(true);
        try {
            await socialPublishingAPI.publishDrafts({
                draftIds: readyDrafts.map(draft => draft.id!).filter(Boolean)
            });

            toast.success('Content published successfully');
            onRefresh?.();
        } catch (error) {
            console.error('Error publishing:', error);
            toast.error('Failed to publish content');
        } finally {
            setIsPublishing(false);
        }
    };

    const handleSchedule = async (scheduleAt: string) => {
        const readyDrafts = getReadyDrafts();
        if (readyDrafts.length === 0) return;

        try {
            await socialPublishingAPI.publishDrafts({
                draftIds: readyDrafts.map(draft => draft.id!).filter(Boolean),
                scheduleAt
            });

            toast.success('Content scheduled successfully');
        } catch (error) {
            console.error('Error scheduling:', error);
            toast.error('Failed to schedule content');
        }
    };

    const handleExport = () => {
        toast.success('Content exported to clipboard');
    };

    const getCurrentDraft = (): AIDraft | null => {
        const languageDrafts = uiState.drafts.get(uiState.currentLanguage);
        if (!languageDrafts) return null;
        return languageDrafts.get(uiState.currentChannel) || null;
    };

    const getReadyDrafts = (): AIDraft[] => {
        const readyDrafts: AIDraft[] = [];
        uiState.drafts.forEach((languageDrafts) => {
            languageDrafts.forEach((draft) => {
                if (draft.status === 'ready') {
                    readyDrafts.push(draft);
                }
            });
        });
        return readyDrafts;
    };

    const getDraftStatusCounts = () => {
        const counts = { draft: 0, generated: 0, edited: 0, ready: 0, publishing: 0, published: 0, failed: 0 };
        uiState.drafts.forEach((languageDrafts) => {
            languageDrafts.forEach((draft) => {
                counts[draft.status]++;
            });
        });
        return counts;
    };

    const statusCounts = getDraftStatusCounts();
    const readyDrafts = getReadyDrafts();

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-primary mb-2">
                        Social Media Publishing
                    </h1>
                    <p className="text-secondary">
                        Generate AI-powered content and publish to Facebook and Instagram
                    </p>
                </div>

                {/* Property Selection */}
                <div className="mb-8">
                    <h2 className="text-xl font-semibold text-primary mb-4">Select Property</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {properties.map((property) => (
                            <div
                                key={property.id}
                                onClick={() => handlePropertySelect(property)}
                                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${uiState.selectedProperty?.id === property.id
                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                                    }`}
                            >
                                <h3 className="font-semibold text-primary mb-2">{property.title}</h3>
                                <p className="text-sm text-secondary mb-2">{property.location}</p>
                                <p className="text-lg font-bold text-primary">₹{property.price.toLocaleString()}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {uiState.selectedProperty && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Left Column - Language & Channel Selection */}
                        <div className="space-y-8">
                            <LanguageSelector
                                selectedLanguages={uiState.selectedLanguages}
                                onLanguageChange={handleLanguageChange}
                                onLanguageAdded={handleLanguageAdded}
                                loadingStates={uiState.loadingStates}
                            />

                            <ChannelSelector
                                selectedChannels={uiState.selectedChannels}
                                onChannelChange={handleChannelChange}
                            />
                        </div>

                        {/* Middle Column - Content Editor */}
                        <div className="lg:col-span-2">
                            {uiState.selectedLanguages.length > 0 && uiState.selectedChannels.length > 0 ? (
                                <div className="space-y-6">
                                    {/* Language/Channel Tabs */}
                                    <div className="flex space-x-2 mb-6">
                                        {uiState.selectedLanguages.map((language) => (
                                            <div key={language} className="flex space-x-1">
                                                {uiState.selectedChannels.map((channel) => (
                                                    <button
                                                        key={`${language}-${channel}`}
                                                        onClick={() => setUIState(prev => ({
                                                            ...prev,
                                                            currentLanguage: language,
                                                            currentChannel: channel
                                                        }))}
                                                        className={`px-3 py-2 text-sm font-medium rounded-lg ${uiState.currentLanguage === language && uiState.currentChannel === channel
                                                            ? 'bg-blue-500 text-white'
                                                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                                                            }`}
                                                    >
                                                        {language} - {channel}
                                                    </button>
                                                ))}
                                            </div>
                                        ))}
                                    </div>

                                    {/* AI Content Panel */}
                                    <AIContentPanel
                                        property={uiState.selectedProperty}
                                        language={uiState.currentLanguage}
                                        channel={uiState.currentChannel}
                                        draft={getCurrentDraft()}
                                        onDraftUpdate={handleDraftUpdate}
                                        onRegenerate={handleRegenerate}
                                        onImprove={handleImprove}
                                        onMarkReady={handleMarkReady}
                                        isLoading={isGenerating}
                                    />
                                </div>
                            ) : (
                                <div className="text-center py-12">
                                    <SparklesIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-primary mb-2">
                                        Select Languages and Channels
                                    </h3>
                                    <p className="text-secondary">
                                        Choose at least one language and one channel to start generating content
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Status Summary */}
                {uiState.selectedProperty && (
                    <div className="mt-8 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
                        <h3 className="font-semibold text-primary mb-3">Content Status</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {Object.entries(statusCounts).map(([status, count]) => (
                                <div key={status} className="text-center">
                                    <div className="text-2xl font-bold text-primary">{count}</div>
                                    <div className="text-sm text-secondary capitalize">{status}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Publish Bar */}
            <PublishBar
                readyDrafts={readyDrafts}
                onPublish={handlePublish}
                onSchedule={handleSchedule}
                onExport={handleExport}
                isPublishing={isPublishing}
            />
        </div>
    );
}
