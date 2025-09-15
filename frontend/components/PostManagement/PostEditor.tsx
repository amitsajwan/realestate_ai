import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Post, PostUpdateRequest } from '../../types/post';

interface PostEditorProps {
    post: Post;
    onPostUpdated: (post: Post) => void;
    onCancel: () => void;
}

export const PostEditor: React.FC<PostEditorProps> = ({
    post,
    onPostUpdated,
    onCancel
}) => {
    const [title, setTitle] = useState(post.title);
    const [content, setContent] = useState(post.content);
    const [language, setLanguage] = useState(post.language);
    const [channels, setChannels] = useState<string[]>(post.channels);
    const [isDirty, setIsDirty] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
    const [showAiSuggestions, setShowAiSuggestions] = useState(false);
    const [aiEnhancing, setAiEnhancing] = useState(false);

    const languageOptions = [
        { value: 'en', label: 'English' },
        { value: 'hi', label: 'Hindi' },
        { value: 'ta', label: 'Tamil' },
        { value: 'te', label: 'Telugu' },
        { value: 'bn', label: 'Bengali' },
        { value: 'gu', label: 'Gujarati' },
        { value: 'kn', label: 'Kannada' },
        { value: 'ml', label: 'Malayalam' },
        { value: 'mr', label: 'Marathi' },
        { value: 'pa', label: 'Punjabi' },
        { value: 'ur', label: 'Urdu' }
    ];

    const channelOptions = [
        { id: 'facebook', name: 'Facebook', icon: '📘' },
        { id: 'instagram', name: 'Instagram', icon: '📷' },
        { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
        { id: 'website', name: 'Website', icon: '🌐' },
        { id: 'email', name: 'Email', icon: '📧' }
    ];

    useEffect(() => {
        const hasChanges =
            title !== post.title ||
            content !== post.content ||
            language !== post.language ||
            JSON.stringify(channels.sort()) !== JSON.stringify(post.channels.sort());

        setIsDirty(hasChanges);
    }, [title, content, language, channels, post]);

    const handleSave = async () => {
        try {
            setLoading(true);
            setError(null);

            const updates: PostUpdateRequest = {
                title,
                content,
                language,
                channels
            };

            const updatedPost = await api.posts.update(post.id, updates);
            onPostUpdated(updatedPost);
        } catch (error: any) {
            setError(error.message || 'Failed to save post');
        } finally {
            setLoading(false);
        }
    };

    const handleAiEnhance = async () => {
        try {
            setAiEnhancing(true);
            setError(null);

            const suggestions = await api.posts.getAiSuggestions(post.id);
            setAiSuggestions(suggestions.suggestions || []);
            setShowAiSuggestions(true);
        } catch (error: any) {
            setError(error.message || 'Failed to get AI suggestions');
        } finally {
            setAiEnhancing(false);
        }
    };

    const handleApplySuggestion = (suggestion: string) => {
        setContent(suggestion);
        setShowAiSuggestions(false);
    };

    const toggleChannel = (channelId: string) => {
        setChannels(prev =>
            prev.includes(channelId)
                ? prev.filter(id => id !== channelId)
                : [...prev, channelId]
        );
    };

    const formatDate = (date: string) => {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold text-gray-900">Edit Post</h2>
                            <p className="text-sm text-gray-600 mt-1">
                                Created: {formatDate(post.created_at)} • Version: {post.version}
                            </p>
                        </div>
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={handleAiEnhance}
                                disabled={aiEnhancing}
                                className="px-4 py-2 text-sm font-medium text-purple-700 bg-purple-100 rounded-lg hover:bg-purple-200 disabled:opacity-50"
                            >
                                {aiEnhancing ? 'Getting suggestions...' : 'AI Enhance'}
                            </button>
                            <button
                                onClick={onCancel}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[60vh]">
                    {error && (
                        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
                            <div className="flex">
                                <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                <div className="ml-3">
                                    <p className="text-sm text-red-800">{error}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="space-y-6">
                        {/* Title */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Post Title
                            </label>
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="Enter post title"
                            />
                        </div>

                        {/* Language */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Language
                            </label>
                            <select
                                value={language}
                                onChange={(e) => setLanguage(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                {languageOptions.map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Content */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Content
                            </label>
                            <textarea
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="Enter post content"
                                rows={8}
                            />
                            <div className="mt-1 text-sm text-gray-500">
                                {content.length} characters
                            </div>
                        </div>

                        {/* Channels */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Publishing Channels
                            </label>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                {channelOptions.map((channel) => (
                                    <label
                                        key={channel.id}
                                        className={`flex items-center space-x-2 p-3 border rounded-lg cursor-pointer transition-colors ${channels.includes(channel.id)
                                                ? 'border-blue-500 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                            }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={channels.includes(channel.id)}
                                            onChange={() => toggleChannel(channel.id)}
                                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="text-lg">{channel.icon}</span>
                                        <span className="text-sm font-medium">{channel.name}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* AI Suggestions */}
                        {showAiSuggestions && aiSuggestions.length > 0 && (
                            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                                <h3 className="text-sm font-medium text-purple-900 mb-3">AI Suggestions</h3>
                                <div className="space-y-2">
                                    {aiSuggestions.map((suggestion, index) => (
                                        <div key={index} className="flex items-start space-x-3">
                                            <div className="flex-1 text-sm text-purple-800 bg-white p-3 rounded border">
                                                {suggestion}
                                            </div>
                                            <button
                                                onClick={() => handleApplySuggestion(suggestion)}
                                                className="px-3 py-1 text-xs font-medium text-purple-700 bg-purple-100 rounded hover:bg-purple-200"
                                            >
                                                Apply
                                            </button>
                                        </div>
                                    ))}
                                </div>
                                <button
                                    onClick={() => setShowAiSuggestions(false)}
                                    className="mt-3 text-sm text-purple-600 hover:text-purple-800"
                                >
                                    Close suggestions
                                </button>
                            </div>
                        )}

                        {/* Post Info */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h3 className="text-sm font-medium text-gray-900 mb-2">Post Information</h3>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="text-gray-500">Status:</span>
                                    <span className="ml-2 font-medium">{post.status}</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">AI Generated:</span>
                                    <span className="ml-2 font-medium">{post.ai_generated ? 'Yes' : 'No'}</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Created:</span>
                                    <span className="ml-2 font-medium">{formatDate(post.created_at)}</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Last Updated:</span>
                                    <span className="ml-2 font-medium">{formatDate(post.updated_at)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
                    <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-500">
                            {isDirty && 'You have unsaved changes'}
                        </div>

                        <div className="flex items-center space-x-3">
                            <button
                                onClick={onCancel}
                                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                Cancel
                            </button>

                            <button
                                onClick={handleSave}
                                disabled={!isDirty || loading}
                                className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PostEditor;
