'use client'

import { PreviewPanelProps } from '@/types/social_publishing';
import {
    CheckCircleIcon,
    ComputerDesktopIcon,
    DevicePhoneMobileIcon,
    ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

export default function PreviewPanel({ draft, channel }: PreviewPanelProps) {

    const getCharCount = () => {
        return draft.title.length + draft.body.length + draft.hashtags.join(' ').length;
    };

    const getCharStatus = () => {
        const count = getCharCount();
        const limits = channel === 'instagram' ? 2200 : 5000;
        const percentage = (count / limits) * 100;

        if (percentage >= 100) return { status: 'error', message: 'Exceeds limit' };
        if (percentage >= 80) return { status: 'warning', message: 'Approaching limit' };
        return { status: 'success', message: 'Within limits' };
    };

    const charStatus = getCharStatus();
    const charCount = getCharCount();
    const limits = channel === 'instagram' ? 2200 : 5000;

    const renderFacebookPreview = () => (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <div className="flex items-start space-x-3">
                <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-sm">A</span>
                </div>
                <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-semibold text-gray-900 dark:text-white">Amit Real Estate</h4>
                        <span className="text-gray-500 text-sm">2h</span>
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                            {draft.title}
                        </h3>
                        <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                            {draft.body}
                        </p>
                        {draft.hashtags.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                                {draft.hashtags.map((tag, index) => (
                                    <span key={index} className="text-blue-600 dark:text-blue-400 text-sm">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );

    const renderInstagramPreview = () => (
        <div className="bg-black rounded-lg overflow-hidden" style={{ width: '300px', height: '400px' }}>
            {/* Instagram Header */}
            <div className="flex items-center justify-between p-3 border-b border-gray-700">
                <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-tr from-yellow-400 to-pink-500 rounded-full"></div>
                    <span className="text-white font-semibold text-sm">amit_realestate</span>
                </div>
                <span className="text-white text-lg">⋯</span>
            </div>

            {/* Instagram Image Placeholder */}
            <div className="h-48 bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
                <span className="text-white text-4xl">🏠</span>
            </div>

            {/* Instagram Content */}
            <div className="p-3 space-y-2">
                <div className="flex items-center space-x-3">
                    <span className="text-white text-xl">❤️</span>
                    <span className="text-white text-xl">💬</span>
                    <span className="text-white text-xl">📤</span>
                    <span className="text-white text-xl ml-auto">🔖</span>
                </div>

                <div className="text-white text-sm">
                    <span className="font-semibold">amit_realestate</span>
                    <span className="ml-2">{draft.title}</span>
                </div>

                <div className="text-white text-sm whitespace-pre-wrap">
                    {draft.body}
                </div>

                {draft.hashtags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                        {draft.hashtags.slice(0, 5).map((tag, index) => (
                            <span key={index} className="text-blue-400 text-sm">
                                {tag}
                            </span>
                        ))}
                        {draft.hashtags.length > 5 && (
                            <span className="text-gray-400 text-sm">
                                +{draft.hashtags.length - 5} more
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-semibold text-primary mb-3">
                    Preview
                </h3>
                <p className="text-sm text-secondary mb-4">
                    See how your post will look on {channel === 'facebook' ? 'Facebook' : 'Instagram'}
                </p>
            </div>

            {/* Character Count Status */}
            <div className="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-primary">Character Count</span>
                    <div className="flex items-center space-x-2">
                        {charStatus.status === 'error' && (
                            <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
                        )}
                        {charStatus.status === 'warning' && (
                            <ExclamationTriangleIcon className="w-4 h-4 text-yellow-500" />
                        )}
                        {charStatus.status === 'success' && (
                            <CheckCircleIcon className="w-4 h-4 text-green-500" />
                        )}
                        <span className={`text-sm font-medium ${charStatus.status === 'error' ? 'text-red-500' :
                                charStatus.status === 'warning' ? 'text-yellow-500' :
                                    'text-green-500'
                            }`}>
                            {charStatus.message}
                        </span>
                    </div>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                        className={`h-2 rounded-full ${charStatus.status === 'error' ? 'bg-red-500' :
                                charStatus.status === 'warning' ? 'bg-yellow-500' :
                                    'bg-green-500'
                            }`}
                        style={{ width: `${Math.min((charCount / limits) * 100, 100)}%` }}
                    ></div>
                </div>
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                    <span>{charCount} characters</span>
                    <span>Limit: {limits}</span>
                </div>
            </div>

            {/* Platform Preview */}
            <div className="space-y-4">
                <div className="flex items-center space-x-2">
                    {channel === 'facebook' ? (
                        <ComputerDesktopIcon className="w-5 h-5 text-blue-500" />
                    ) : (
                        <DevicePhoneMobileIcon className="w-5 h-5 text-pink-500" />
                    )}
                    <span className="font-medium text-primary">
                        {channel === 'facebook' ? 'Facebook' : 'Instagram'} Preview
                    </span>
                </div>

                <div className="flex justify-center">
                    {channel === 'facebook' ? renderFacebookPreview() : renderInstagramPreview()}
                </div>
            </div>

            {/* Warnings */}
            {charCount > limits && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <div className="flex items-start space-x-2">
                        <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mt-0.5" />
                        <div>
                            <h4 className="font-medium text-red-800 dark:text-red-200">
                                Content Too Long
                            </h4>
                            <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                                Your content exceeds the {limits} character limit by {charCount - limits} characters.
                                Please shorten the content before publishing.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {draft.hashtags.length > 30 && (
                <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <div className="flex items-start space-x-2">
                        <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500 mt-0.5" />
                        <div>
                            <h4 className="font-medium text-yellow-800 dark:text-yellow-200">
                                Too Many Hashtags
                            </h4>
                            <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                                You have {draft.hashtags.length} hashtags. Instagram recommends a maximum of 30 hashtags.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
