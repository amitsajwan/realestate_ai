'use client'

import { AIDraft } from '@/types/social_publishing'
import {
    CheckCircleIcon,
    ChevronDownIcon,
    ChevronUpIcon,
    ClipboardDocumentIcon,
    ClockIcon,
    RocketLaunchIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'

interface PublishingBottomSheetProps {
    readyDrafts: AIDraft[]
    onPublish: () => void
    onSchedule: (scheduleAt: string) => void
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

export default function PublishingBottomSheet({
    readyDrafts,
    onPublish,
    onSchedule
}: PublishingBottomSheetProps) {

    const [isExpanded, setIsExpanded] = useState(false)
    const [showScheduleModal, setShowScheduleModal] = useState(false)
    const [scheduleDate, setScheduleDate] = useState('')
    const [scheduleTime, setScheduleTime] = useState('')

    const getReadyCountByChannel = () => {
        const counts: Record<string, number> = {}
        readyDrafts.forEach(draft => {
            counts[draft.channel] = (counts[draft.channel] || 0) + 1
        })
        return counts
    }

    const getReadyCountByLanguage = () => {
        const counts: Record<string, number> = {}
        readyDrafts.forEach(draft => {
            counts[draft.language] = (counts[draft.language] || 0) + 1
        })
        return counts
    }

    const handleSchedule = () => {
        if (scheduleDate && scheduleTime) {
            const scheduleAt = new Date(`${scheduleDate}T${scheduleTime}`).toISOString()
            onSchedule(scheduleAt)
            setShowScheduleModal(false)
            setScheduleDate('')
            setScheduleTime('')
        }
    }

    const handleExport = () => {
        const exportData = readyDrafts.map(draft => ({
            channel: draft.channel,
            language: draft.language,
            title: draft.title,
            body: draft.body,
            hashtags: draft.hashtags
        }))

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `social-posts-${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    const channelCounts = getReadyCountByChannel()
    const languageCounts = getReadyCountByLanguage()

    if (readyDrafts.length === 0) {
        return null
    }

    return (
        <>
            {/* Bottom Sheet */}
            <motion.div
                initial={{ y: '100%' }}
                animate={{ y: 0 }}
                className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-40"
            >
                {/* Handle */}
                <div className="flex justify-center pt-2 pb-1">
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                    >
                        {isExpanded ? (
                            <ChevronDownIcon className="w-5 h-5" />
                        ) : (
                            <ChevronUpIcon className="w-5 h-5" />
                        )}
                    </button>
                </div>

                {/* Main Content */}
                <div className="px-4 pb-4">
                    {!isExpanded ? (
                        /* Collapsed State */
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <div className="flex items-center space-x-2">
                                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                                    <span className="font-semibold text-gray-900">
                                        {readyDrafts.length} Ready
                                    </span>
                                </div>

                                <div className="hidden sm:flex space-x-4 text-sm text-gray-600">
                                    {Object.entries(channelCounts).map(([channel, count]) => (
                                        <span key={channel}>
                                            {channel}: {count}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <button
                                onClick={onPublish}
                                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 active:scale-95 transition-all"
                            >
                                <RocketLaunchIcon className="w-4 h-4" />
                                <span>Publish Now</span>
                            </button>
                        </div>
                    ) : (
                        /* Expanded State */
                        <div className="space-y-4">
                            {/* Summary */}
                            <div className="bg-gray-50 rounded-lg p-3">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-semibold text-gray-900">Ready to Publish</h3>
                                    <span className="text-sm text-gray-600">
                                        {readyDrafts.length} post{readyDrafts.length !== 1 ? 's' : ''}
                                    </span>
                                </div>

                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <p className="text-gray-600 mb-1">Platforms</p>
                                        <div className="flex flex-wrap gap-1">
                                            {Object.entries(channelCounts).map(([channel, count]) => (
                                                <span key={channel} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs">
                                                    {channel}: {count}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <p className="text-gray-600 mb-1">Languages</p>
                                        <div className="flex flex-wrap gap-1">
                                            {Object.entries(languageCounts).map(([language, count]) => (
                                                <span key={language} className="px-2 py-1 bg-green-100 text-green-800 rounded-md text-xs">
                                                    {LANGUAGE_NAMES[language as keyof typeof LANGUAGE_NAMES] || language}: {count}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Draft List */}
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                                {readyDrafts.map((draft, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                                <span className="text-sm font-medium text-blue-600">
                                                    {draft.channel === 'facebook' ? '📘' : '📷'}
                                                </span>
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-900 text-sm">
                                                    {LANGUAGE_NAMES[draft.language as keyof typeof LANGUAGE_NAMES] || draft.language}
                                                </p>
                                                <p className="text-xs text-gray-600 capitalize">{draft.channel}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-xs text-gray-500 truncate max-w-32">
                                                {draft.title}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Action Buttons */}
                            <div className="grid grid-cols-3 gap-2">
                                <button
                                    onClick={handleExport}
                                    className="flex flex-col items-center space-y-1 p-3 bg-gray-100 rounded-lg hover:bg-gray-200 active:scale-95 transition-all"
                                >
                                    <ClipboardDocumentIcon className="w-5 h-5 text-gray-600" />
                                    <span className="text-xs font-medium text-gray-700">Export</span>
                                </button>

                                <button
                                    onClick={() => setShowScheduleModal(true)}
                                    className="flex flex-col items-center space-y-1 p-3 bg-gray-100 rounded-lg hover:bg-gray-200 active:scale-95 transition-all"
                                >
                                    <ClockIcon className="w-5 h-5 text-gray-600" />
                                    <span className="text-xs font-medium text-gray-700">Schedule</span>
                                </button>

                                <button
                                    onClick={onPublish}
                                    className="flex flex-col items-center space-y-1 p-3 bg-blue-600 rounded-lg hover:bg-blue-700 active:scale-95 transition-all"
                                >
                                    <RocketLaunchIcon className="w-5 h-5 text-white" />
                                    <span className="text-xs font-medium text-white">Publish</span>
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </motion.div>

            {/* Schedule Modal */}
            <AnimatePresence>
                {showScheduleModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-white rounded-xl w-full max-w-md p-6"
                        >
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                Schedule Publishing
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Date
                                    </label>
                                    <input
                                        type="date"
                                        value={scheduleDate}
                                        onChange={(e) => setScheduleDate(e.target.value)}
                                        min={new Date().toISOString().split('T')[0]}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Time
                                    </label>
                                    <input
                                        type="time"
                                        value={scheduleTime}
                                        onChange={(e) => setScheduleTime(e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                            </div>

                            <div className="flex space-x-3 mt-6">
                                <button
                                    onClick={() => setShowScheduleModal(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSchedule}
                                    disabled={!scheduleDate || !scheduleTime}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    Schedule
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    )
}
