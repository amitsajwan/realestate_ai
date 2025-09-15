import React from 'react';
import { PostFilters, PostStatus, Template } from '../../types/post';

interface PostFiltersPanelProps {
    filters: PostFilters;
    onFilterChange: (filters: Partial<PostFilters>) => void;
    templates: Template[];
}

export const PostFiltersPanel: React.FC<PostFiltersPanelProps> = ({
    filters,
    onFilterChange,
    templates
}) => {
    const statusOptions: { value: PostStatus; label: string }[] = [
        { value: 'draft', label: 'Draft' },
        { value: 'published', label: 'Published' },
        { value: 'scheduled', label: 'Scheduled' },
        { value: 'archived', label: 'Archived' }
    ];

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
        { value: 'facebook', label: 'Facebook' },
        { value: 'instagram', label: 'Instagram' },
        { value: 'linkedin', label: 'LinkedIn' },
        { value: 'website', label: 'Website' },
        { value: 'email', label: 'Email' }
    ];

    const clearFilters = () => {
        onFilterChange({
            status: undefined,
            language: undefined,
            channels: undefined,
            ai_generated: undefined,
            date_from: undefined,
            date_to: undefined
        });
    };

    const hasActiveFilters = () => {
        return !!(
            filters.status ||
            filters.language ||
            (filters.channels && filters.channels.length > 0) ||
            filters.ai_generated !== undefined ||
            filters.date_from ||
            filters.date_to
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Filters</h3>
                {hasActiveFilters() && (
                    <button
                        onClick={clearFilters}
                        className="text-sm text-blue-600 hover:text-blue-800"
                    >
                        Clear all
                    </button>
                )}
            </div>

            {/* Status Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                </label>
                <select
                    value={filters.status || ''}
                    onChange={(e) => onFilterChange({
                        status: e.target.value as PostStatus || undefined
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="">All statuses</option>
                    {statusOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Language Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Language
                </label>
                <select
                    value={filters.language || ''}
                    onChange={(e) => onFilterChange({
                        language: e.target.value || undefined
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="">All languages</option>
                    {languageOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Channels Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Channels
                </label>
                <div className="space-y-2">
                    {channelOptions.map((channel) => (
                        <label key={channel.value} className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={filters.channels?.includes(channel.value) || false}
                                onChange={(e) => {
                                    const currentChannels = filters.channels || [];
                                    const newChannels = e.target.checked
                                        ? [...currentChannels, channel.value]
                                        : currentChannels.filter(c => c !== channel.value);
                                    onFilterChange({ channels: newChannels.length > 0 ? newChannels : undefined });
                                }}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-700">{channel.label}</span>
                        </label>
                    ))}
                </div>
            </div>

            {/* AI Generated Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Type
                </label>
                <div className="space-y-2">
                    <label className="flex items-center space-x-2">
                        <input
                            type="radio"
                            name="ai_generated"
                            checked={filters.ai_generated === undefined}
                            onChange={() => onFilterChange({ ai_generated: undefined })}
                            className="text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">All content</span>
                    </label>
                    <label className="flex items-center space-x-2">
                        <input
                            type="radio"
                            name="ai_generated"
                            checked={filters.ai_generated === true}
                            onChange={() => onFilterChange({ ai_generated: true })}
                            className="text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">AI Generated</span>
                    </label>
                    <label className="flex items-center space-x-2">
                        <input
                            type="radio"
                            name="ai_generated"
                            checked={filters.ai_generated === false}
                            onChange={() => onFilterChange({ ai_generated: false })}
                            className="text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">Manual</span>
                    </label>
                </div>
            </div>

            {/* Date Range Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date Range
                </label>
                <div className="space-y-2">
                    <div>
                        <label className="block text-xs text-gray-500 mb-1">From</label>
                        <input
                            type="date"
                            value={filters.date_from || ''}
                            onChange={(e) => onFilterChange({
                                date_from: e.target.value || undefined
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-gray-500 mb-1">To</label>
                        <input
                            type="date"
                            value={filters.date_to || ''}
                            onChange={(e) => onFilterChange({
                                date_to: e.target.value || undefined
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>
                </div>
            </div>

            {/* Template Filter */}
            {templates.length > 0 && (
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Template
                    </label>
                    <select
                        value={filters.template_id || ''}
                        onChange={(e) => onFilterChange({
                            template_id: e.target.value || undefined
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        <option value="">All templates</option>
                        {templates.map((template) => (
                            <option key={template.id} value={template.id}>
                                {template.name}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* Quick Filters */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quick Filters
                </label>
                <div className="space-y-2">
                    <button
                        onClick={() => onFilterChange({ status: 'draft' })}
                        className="w-full text-left px-3 py-2 text-sm text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100"
                    >
                        Draft Posts
                    </button>
                    <button
                        onClick={() => onFilterChange({ status: 'published' })}
                        className="w-full text-left px-3 py-2 text-sm text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100"
                    >
                        Published Posts
                    </button>
                    <button
                        onClick={() => onFilterChange({ ai_generated: true })}
                        className="w-full text-left px-3 py-2 text-sm text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100"
                    >
                        AI Generated
                    </button>
                    <button
                        onClick={() => onFilterChange({
                            date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
                        })}
                        className="w-full text-left px-3 py-2 text-sm text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100"
                    >
                        Last 7 days
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PostFiltersPanel;
