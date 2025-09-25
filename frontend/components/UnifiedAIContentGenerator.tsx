"use client";

import { authManager } from '@/lib/auth';
import { ArrowPathIcon, LanguageIcon, SparklesIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useEffect, useState } from 'react';
import { STANDARD_LANGUAGES, getLanguageName } from '../lib/languageConfig';

// Types
interface PropertyData {
    id: string;
    title: string;
    location: string;
    price: string | number;
    property_type?: string;
    features?: string[];
    bedrooms?: number;
    bathrooms?: number;
    area?: number;
    description?: string;
    amenities?: string;
}

interface GeneratedContent {
    title: string;
    body: string;
    hashtags: string[];
    metadata?: {
        platform: string;
        language: string;
        tone: string;
        length: string;
    };
}

interface PlatformContent {
    title: string;
    body: string;
    hashtags: string[];
    metadata: Record<string, any>;
}

interface UnifiedAIContentGeneratorProps {
    context: 'publishing' | 'standalone' | 'property_creation';
    propertyData?: PropertyData;
    onContentGenerated: (content: Record<string, Record<string, PlatformContent>>) => void;
    onClose?: () => void;
    preselectedLanguage?: string;
    preselectedPlatforms?: string[];
    isOpen?: boolean;
}

const PLATFORMS = [
    { id: 'website', name: 'Website', icon: '🌐' },
    { id: 'facebook', name: 'Facebook', icon: '📘' },
    { id: 'instagram', name: 'Instagram', icon: '📷' },
    { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
    { id: 'whatsapp', name: 'WhatsApp', icon: '💬' },
    { id: 'email', name: 'Email', icon: '📧' }
];

const TONES = [
    { id: 'friendly', name: 'Friendly', description: 'Warm and approachable' },
    { id: 'professional', name: 'Professional', description: 'Formal and business-like' },
    { id: 'casual', name: 'Casual', description: 'Relaxed and informal' }
];

const LENGTHS = [
    { id: 'short', name: 'Short', description: '100-300 words' },
    { id: 'medium', name: 'Medium', description: '300-600 words' },
    { id: 'long', name: 'Long', description: '600+ words' }
];

export default function UnifiedAIContentGenerator({
    context,
    propertyData,
    onContentGenerated,
    onClose,
    preselectedLanguage = 'en',
    preselectedPlatforms = ['website'],
    isOpen = true
}: UnifiedAIContentGeneratorProps) {
    // State
    const [selectedProperty, setSelectedProperty] = useState<PropertyData | null>(propertyData || null);
    const [availableProperties, setAvailableProperties] = useState<PropertyData[]>([]);
    const [selectedLanguages, setSelectedLanguages] = useState<string[]>([preselectedLanguage]);
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(preselectedPlatforms);
    const [selectedTone, setSelectedTone] = useState('friendly');
    const [selectedLength, setSelectedLength] = useState('medium');
    const [customPrompts, setCustomPrompts] = useState<Record<string, string>>({});
    const [languagePrompts, setLanguagePrompts] = useState<Record<string, string>>({});
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [generatedContent, setGeneratedContent] = useState<Record<string, Record<string, PlatformContent>> | null>(null);

    // Load available properties
    useEffect(() => {
        if (context === 'standalone' || context === 'property_creation') {
            loadAvailableProperties();
        }
    }, [context]);

    const loadAvailableProperties = async () => {
        try {
            const response = await fetch('/api/v1/ai-unified/properties', {
                headers: {
                    'Authorization': `Bearer ${authManager.getState().token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setAvailableProperties(data.data || []);
            }
        } catch (err) {
            console.error('Failed to load properties:', err);
        }
    };

    const handleLanguageToggle = (language: string) => {
        setSelectedLanguages(prev =>
            prev.includes(language)
                ? prev.filter(l => l !== language)
                : [...prev, language]
        );
    };

    const handlePlatformToggle = (platform: string) => {
        setSelectedPlatforms(prev =>
            prev.includes(platform)
                ? prev.filter(p => p !== platform)
                : [...prev, platform]
        );
    };

    const handleCustomPromptChange = (key: string, value: string) => {
        if (key.startsWith('platform_')) {
            const platform = key.replace('platform_', '');
            setCustomPrompts(prev => ({ ...prev, [platform]: value }));
        } else if (key.startsWith('language_')) {
            const language = key.replace('language_', '');
            setLanguagePrompts(prev => ({ ...prev, [language]: value }));
        }
    };

    const generateContent = async () => {
        if (!selectedProperty && context !== 'property_creation') {
            setError('Please select a property first');
            return;
        }

        if (selectedLanguages.length === 0) {
            setError('Please select at least one language');
            return;
        }

        if (selectedPlatforms.length === 0) {
            setError('Please select at least one platform');
            return;
        }

        try {
            setIsGenerating(true);
            setError(null);

            const requestData = {
                context,
                property_data: selectedProperty || {},
                languages: selectedLanguages,
                platforms: selectedPlatforms,
                custom_prompts: Object.keys(customPrompts).length > 0 ? customPrompts : undefined,
                language_prompts: Object.keys(languagePrompts).length > 0 ? languagePrompts : undefined,
                generation_options: {
                    tone: selectedTone,
                    length: selectedLength,
                    include_hashtags: true,
                    include_cta: true,
                    max_title_length: context === 'property_creation' ? 100 : 200
                }
            };

            console.log('=== UNIFIED AI REQUEST ===');
            console.log('Request URL:', '/api/v1/ai-unified/generate-unified');
            console.log('Request data:', requestData);
            console.log('=== END REQUEST ===');

            const response = await fetch('/api/v1/ai-unified/generate-unified', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authManager.getState().token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate content');
            }

            const data = await response.json();

            console.log('=== UNIFIED AI RESPONSE ===');
            console.log('Response status:', response.status);
            console.log('Response data:', data);
            console.log('=== END RESPONSE ===');

            setGeneratedContent(data.content);

            if (onContentGenerated) {
                onContentGenerated(data.content);
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            console.error('Error generating content:', err);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleClose = () => {
        if (onClose) {
            onClose();
        }
    };

    if (!isOpen) {
        return null;
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <div className="flex items-center space-x-3">
                        <SparklesIcon className="h-6 w-6 text-blue-600" />
                        <h2 className="text-xl font-semibold text-gray-900">
                            AI Content Generator
                        </h2>
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                            {context.charAt(0).toUpperCase() + context.slice(1)}
                        </span>
                    </div>
                    <button
                        onClick={handleClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <XMarkIcon className="h-6 w-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Property Selection (for standalone and property_creation contexts) */}
                    {(context === 'standalone' || context === 'property_creation') && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Property
                            </label>
                            <select
                                value={selectedProperty?.id || ''}
                                onChange={(e) => {
                                    const property = availableProperties.find(p => p.id === e.target.value);
                                    setSelectedProperty(property || null);
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="">Select a property...</option>
                                {availableProperties.map((property) => (
                                    <option key={property.id} value={property.id}>
                                        {property.title} - {property.location}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    {/* Language Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            <LanguageIcon className="h-4 w-4 inline mr-1" />
                            Languages
                        </label>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                            {STANDARD_LANGUAGES.map((lang) => (
                                <label key={lang.code} className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={selectedLanguages.includes(lang.code)}
                                        onChange={() => handleLanguageToggle(lang.code)}
                                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                    <span className="text-sm text-gray-700">{lang.name}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Platform Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Platforms
                        </label>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {PLATFORMS.map((platform) => (
                                <label key={platform.id} className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={selectedPlatforms.includes(platform.id)}
                                        onChange={() => handlePlatformToggle(platform.id)}
                                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                    <span className="text-sm text-gray-700">
                                        {platform.icon} {platform.name}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Generation Options */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Tone
                            </label>
                            <select
                                value={selectedTone}
                                onChange={(e) => setSelectedTone(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            >
                                {TONES.map((tone) => (
                                    <option key={tone.id} value={tone.id}>
                                        {tone.name} - {tone.description}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Length
                            </label>
                            <select
                                value={selectedLength}
                                onChange={(e) => setSelectedLength(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            >
                                {LENGTHS.map((length) => (
                                    <option key={length.id} value={length.id}>
                                        {length.name} - {length.description}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Custom Prompts */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Custom Prompts (Optional)
                        </label>
                        <div className="space-y-3">
                            {/* Platform-specific prompts */}
                            {selectedPlatforms.map((platform) => (
                                <div key={`platform_${platform}`}>
                                    <label className="block text-xs text-gray-600 mb-1">
                                        {PLATFORMS.find(p => p.id === platform)?.name} Prompt
                                    </label>
                                    <textarea
                                        value={customPrompts[platform] || ''}
                                        onChange={(e) => handleCustomPromptChange(`platform_${platform}`, e.target.value)}
                                        placeholder={`Custom prompt for ${platform}...`}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                                        rows={2}
                                    />
                                </div>
                            ))}

                            {/* Language-specific prompts */}
                            {selectedLanguages.map((language) => (
                                <div key={`language_${language}`}>
                                    <label className="block text-xs text-gray-600 mb-1">
                                        {getLanguageName(language)} Language Prompt
                                    </label>
                                    <textarea
                                        value={languagePrompts[language] || ''}
                                        onChange={(e) => handleCustomPromptChange(`language_${language}`, e.target.value)}
                                        placeholder={`Custom prompt for ${getLanguageName(language)}...`}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                                        rows={2}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-md p-3">
                            <p className="text-sm text-red-600">{error}</p>
                        </div>
                    )}

                    {/* Generate Button */}
                    <div className="flex justify-end space-x-3">
                        <button
                            onClick={handleClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={generateContent}
                            disabled={isGenerating}
                            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                        >
                            {isGenerating ? (
                                <>
                                    <ArrowPathIcon className="h-4 w-4 animate-spin" />
                                    <span>Generating...</span>
                                </>
                            ) : (
                                <>
                                    <SparklesIcon className="h-4 w-4" />
                                    <span>Generate Content</span>
                                </>
                            )}
                        </button>
                    </div>

                    {/* Generated Content Display */}
                    {generatedContent && (
                        <div className="mt-6 border-t border-gray-200 pt-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Generated Content</h3>
                            <div className="space-y-4">
                                {Object.entries(generatedContent).map(([platform, languages]) => (
                                    <div key={platform} className="border border-gray-200 rounded-lg p-4">
                                        <h4 className="font-medium text-gray-900 mb-3">
                                            {PLATFORMS.find(p => p.id === platform)?.icon} {PLATFORMS.find(p => p.id === platform)?.name}
                                        </h4>
                                        <div className="space-y-3">
                                            {Object.entries(languages).map(([language, content]) => (
                                                <div key={`${platform}_${language}`} className="bg-gray-50 rounded-md p-3">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <span className="text-sm font-medium text-gray-700">
                                                            {getLanguageName(language)}
                                                        </span>
                                                        <span className="text-xs text-gray-500">
                                                            {content.metadata?.tone} • {content.metadata?.length}
                                                        </span>
                                                    </div>
                                                    <div className="space-y-2">
                                                        <div>
                                                            <span className="text-xs font-medium text-gray-600">Title:</span>
                                                            <p className="text-sm text-gray-900 font-medium">{content.title}</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-xs font-medium text-gray-600">Content:</span>
                                                            <p className="text-sm text-gray-900 whitespace-pre-wrap">{content.body}</p>
                                                        </div>
                                                        {content.hashtags.length > 0 && (
                                                            <div>
                                                                <span className="text-xs font-medium text-gray-600">Hashtags:</span>
                                                                <p className="text-sm text-blue-600">{content.hashtags.join(' ')}</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
