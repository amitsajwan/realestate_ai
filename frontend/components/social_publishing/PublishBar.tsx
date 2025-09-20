'use client'

import { Button } from '@/components/UI';
import { PublishBarProps } from '@/types/social_publishing';
import {
    CheckCircleIcon,
    ClipboardDocumentIcon,
    ClockIcon,
    RocketLaunchIcon
} from '@heroicons/react/24/outline';
import { useState } from 'react';

export default function PublishBar({
    readyDrafts,
    onPublish,
    onSchedule,
    onExport,
    isPublishing
}: PublishBarProps) {

    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [scheduleDate, setScheduleDate] = useState('');
    const [scheduleTime, setScheduleTime] = useState('');

    const getReadyCountByChannel = () => {
        const counts: Record<string, number> = {};
        readyDrafts.forEach(draft => {
            counts[draft.channel] = (counts[draft.channel] || 0) + 1;
        });
        return counts;
    };

    const getReadyCountByLanguage = () => {
        const counts: Record<string, number> = {};
        readyDrafts.forEach(draft => {
            counts[draft.language] = (counts[draft.language] || 0) + 1;
        });
        return counts;
    };

    const handleSchedule = () => {
        if (scheduleDate && scheduleTime) {
            const scheduleAt = new Date(`${scheduleDate}T${scheduleTime}`).toISOString();
            onSchedule(scheduleAt);
            setShowScheduleModal(false);
        }
    };

    const handleExport = () => {
        const exportData = readyDrafts.map(draft => ({
            channel: draft.channel,
            language: draft.language,
            title: draft.title,
            body: draft.body,
            hashtags: draft.hashtags
        }));

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `social-posts-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        onExport();
    };

    const channelCounts = getReadyCountByChannel();
    const languageCounts = getReadyCountByLanguage();

    if (readyDrafts.length === 0) {
        return (
            <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-600 p-4">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center">
                        <p className="text-gray-500 dark:text-gray-400">
                            No content ready for publishing. Generate and mark content as ready first.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-600 p-4 shadow-lg">
                <div className="max-w-7xl mx-auto">
                    <div className="flex items-center justify-between">
                        {/* Ready Counts */}
                        <div className="flex items-center space-x-6">
                            <div className="flex items-center space-x-2">
                                <CheckCircleIcon className="w-5 h-5 text-green-500" />
                                <span className="font-medium text-primary">
                                    {readyDrafts.length} Ready
                                </span>
                            </div>

                            <div className="flex space-x-4 text-sm text-secondary">
                                {Object.entries(channelCounts).map(([channel, count]) => (
                                    <span key={channel}>
                                        {channel}: {count}
                                    </span>
                                ))}
                            </div>

                            <div className="flex space-x-4 text-sm text-secondary">
                                {Object.entries(languageCounts).map(([language, count]) => (
                                    <span key={language}>
                                        {language}: {count}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center space-x-3">
                            <Button
                                variant="outline"
                                onClick={handleExport}
                                disabled={isPublishing}
                            >
                                <ClipboardDocumentIcon className="w-4 h-4 mr-2" />
                                Export
                            </Button>

                            <Button
                                variant="outline"
                                onClick={() => setShowScheduleModal(true)}
                                disabled={isPublishing}
                            >
                                <ClockIcon className="w-4 h-4 mr-2" />
                                Schedule
                            </Button>

                            <Button
                                variant="primary"
                                onClick={onPublish}
                                disabled={isPublishing}
                                className="min-w-[120px]"
                            >
                                {isPublishing ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                                        Publishing...
                                    </>
                                ) : (
                                    <>
                                        <RocketLaunchIcon className="w-4 h-4 mr-2" />
                                        Publish Now
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Schedule Modal */}
            {showScheduleModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
                        <h3 className="text-lg font-semibold text-primary mb-4">
                            Schedule Publishing
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-primary mb-2">
                                    Date
                                </label>
                                <input
                                    type="date"
                                    value={scheduleDate}
                                    onChange={(e) => setScheduleDate(e.target.value)}
                                    min={new Date().toISOString().split('T')[0]}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-primary mb-2">
                                    Time
                                </label>
                                <input
                                    type="time"
                                    value={scheduleTime}
                                    onChange={(e) => setScheduleTime(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                />
                            </div>
                        </div>

                        <div className="flex justify-end space-x-3 mt-6">
                            <Button
                                variant="outline"
                                onClick={() => setShowScheduleModal(false)}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="primary"
                                onClick={handleSchedule}
                                disabled={!scheduleDate || !scheduleTime}
                            >
                                Schedule
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
