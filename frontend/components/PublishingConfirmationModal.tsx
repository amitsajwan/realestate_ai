'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle, ExternalLink, Eye, Facebook, Globe, Heart, Instagram, MessageCircle, TrendingUp, X } from 'lucide-react'
import { useEffect, useState } from 'react'

interface PublishingResult {
    platform: 'website' | 'facebook' | 'instagram'
    postId: string
    url: string
    status: 'success' | 'failed'
    error?: string
}

interface PublishingConfirmationModalProps {
    isOpen: boolean
    onClose: () => void
    publishingResults: PublishingResult[]
    propertyData: {
        id: string
        title: string
        location: string
    }
    onViewPosts: () => void
}

export default function PublishingConfirmationModal({
    isOpen,
    onClose,
    publishingResults,
    propertyData,
    onViewPosts
}: PublishingConfirmationModalProps) {
    const [analyticsData, setAnalyticsData] = useState({
        views: 0,
        likes: 0,
        comments: 0,
        shares: 0
    })

    const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(true)

    useEffect(() => {
        if (isOpen) {
            // Simulate loading analytics data
            const loadAnalytics = async () => {
                setIsLoadingAnalytics(true)
                await new Promise(resolve => setTimeout(resolve, 1000))

                setAnalyticsData({
                    views: 250,
                    likes: 12,
                    comments: 5,
                    shares: 3
                })
                setIsLoadingAnalytics(false)
            }

            loadAnalytics()
        }
    }, [isOpen])

    const successfulResults = publishingResults.filter(result => result.status === 'success')
    const failedResults = publishingResults.filter(result => result.status === 'failed')

    const getPlatformIcon = (platform: string) => {
        switch (platform) {
            case 'website':
                return <Globe className="w-5 h-5 text-green-600" />
            case 'facebook':
                return <Facebook className="w-5 h-5 text-blue-600" />
            case 'instagram':
                return <Instagram className="w-5 h-5 text-pink-600" />
            default:
                return null
        }
    }

    const getPlatformName = (platform: string) => {
        switch (platform) {
            case 'website':
                return 'Website'
            case 'facebook':
                return 'Facebook'
            case 'instagram':
                return 'Instagram'
            default:
                return platform
        }
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4 overflow-y-auto">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ duration: 0.3, ease: "easeOut" }}
                        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[95vh] overflow-y-auto my-8"
                    >
                        {/* Header */}
                        <div className="relative p-8 text-center border-b border-gray-100">
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            {/* Success Icon */}
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                                className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
                            >
                                <CheckCircle className="w-10 h-10 text-green-600" />
                            </motion.div>

                            {/* Title */}
                            <motion.h2
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                                className="text-3xl font-bold text-gray-900 mb-2"
                            >
                                Posts Successfully Created!
                            </motion.h2>

                            <motion.p
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.4 }}
                                className="text-gray-600 text-lg"
                            >
                                Your property is now being promoted across social media
                            </motion.p>
                        </div>

                        <div className="p-8 space-y-6">
                            {/* Publishing Status */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.5 }}
                                className="space-y-4"
                            >
                                <h3 className="font-semibold text-gray-900 text-lg">Publishing Status</h3>

                                <div className="space-y-3">
                                    {successfulResults.map((result, index) => (
                                        <motion.div
                                            key={result.platform}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.6 + index * 0.1 }}
                                            className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg"
                                        >
                                            <div className="flex items-center gap-3">
                                                {getPlatformIcon(result.platform)}
                                                <div>
                                                    <p className="font-medium text-gray-900">
                                                        Shared to {getPlatformName(result.platform)}
                                                    </p>
                                                    <p className="text-sm text-gray-600">
                                                        Post published successfully
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <CheckCircle className="w-5 h-5 text-green-600" />
                                                <a
                                                    href={result.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-blue-600 hover:text-blue-800 transition-colors"
                                                >
                                                    <ExternalLink className="w-4 h-4" />
                                                </a>
                                            </div>
                                        </motion.div>
                                    ))}

                                    {failedResults.map((result, index) => (
                                        <motion.div
                                            key={result.platform}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.6 + (successfulResults.length + index) * 0.1 }}
                                            className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-lg"
                                        >
                                            <div className="flex items-center gap-3">
                                                {getPlatformIcon(result.platform)}
                                                <div>
                                                    <p className="font-medium text-gray-900">
                                                        Failed to publish to {getPlatformName(result.platform)}
                                                    </p>
                                                    <p className="text-sm text-red-600">
                                                        {result.error || 'Unknown error occurred'}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center">
                                                    <X className="w-3 h-3 text-red-600" />
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </motion.div>

                            {/* Performance Preview */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.7 }}
                                className="bg-gray-50 rounded-xl p-6"
                            >
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-semibold text-gray-900 text-lg">Performance Preview</h3>
                                    <TrendingUp className="w-5 h-5 text-green-600" />
                                </div>

                                {isLoadingAnalytics ? (
                                    <div className="space-y-4">
                                        <div className="animate-pulse">
                                            <div className="h-32 bg-gray-200 rounded-lg mb-4"></div>
                                            <div className="grid grid-cols-3 gap-4">
                                                <div className="h-16 bg-gray-200 rounded"></div>
                                                <div className="h-16 bg-gray-200 rounded"></div>
                                                <div className="h-16 bg-gray-200 rounded"></div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {/* Simple Chart */}
                                        <div className="h-32 bg-white rounded-lg p-4 border border-gray-200">
                                            <div className="flex items-end justify-between h-full">
                                                {[20, 35, 45, 60, 80].map((height, index) => (
                                                    <motion.div
                                                        key={index}
                                                        initial={{ height: 0 }}
                                                        animate={{ height: `${height}%` }}
                                                        transition={{ delay: 0.8 + index * 0.1, duration: 0.5 }}
                                                        className="w-8 bg-gradient-to-t from-blue-500 to-blue-400 rounded-t"
                                                    />
                                                ))}
                                            </div>
                                            <div className="flex justify-between text-xs text-gray-500 mt-2">
                                                <span>Mon</span>
                                                <span>Tue</span>
                                                <span>Wed</span>
                                                <span>Thu</span>
                                                <span>Fri</span>
                                            </div>
                                        </div>

                                        {/* Metrics */}
                                        <div className="grid grid-cols-3 gap-4">
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: 0.9 }}
                                                className="text-center"
                                            >
                                                <div className="flex items-center justify-center gap-1 mb-1">
                                                    <Eye className="w-4 h-4 text-blue-600" />
                                                    <span className="text-2xl font-bold text-gray-900">{analyticsData.views}</span>
                                                </div>
                                                <p className="text-sm text-gray-600">Views</p>
                                            </motion.div>

                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: 1.0 }}
                                                className="text-center"
                                            >
                                                <div className="flex items-center justify-center gap-1 mb-1">
                                                    <Heart className="w-4 h-4 text-red-600" />
                                                    <span className="text-2xl font-bold text-gray-900">{analyticsData.likes}</span>
                                                </div>
                                                <p className="text-sm text-gray-600">Likes</p>
                                            </motion.div>

                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: 1.1 }}
                                                className="text-center"
                                            >
                                                <div className="flex items-center justify-center gap-1 mb-1">
                                                    <MessageCircle className="w-4 h-4 text-green-600" />
                                                    <span className="text-2xl font-bold text-gray-900">{analyticsData.comments}</span>
                                                </div>
                                                <p className="text-sm text-gray-600">Comments</p>
                                            </motion.div>
                                        </div>
                                    </div>
                                )}
                            </motion.div>

                            {/* Property Info */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.8 }}
                                className="bg-blue-50 rounded-xl p-4"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                        <span className="text-blue-600 font-semibold text-lg">
                                            {propertyData.title.charAt(0)}
                                        </span>
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-gray-900">{propertyData.title}</h4>
                                        <p className="text-sm text-gray-600">{propertyData.location}</p>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Action Button */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.9 }}
                                className="pt-4"
                            >
                                <button
                                    onClick={onViewPosts}
                                    className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                                >
                                    <Eye className="w-5 h-5" />
                                    View All Posts
                                    <ExternalLink className="w-4 h-4" />
                                </button>
                            </motion.div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
