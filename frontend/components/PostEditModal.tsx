'use client'

import { api } from '@/lib/api'
import {
    CalendarIcon,
    PencilIcon,
    RocketLaunchIcon,
    TrashIcon,
    XMarkIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import toast from 'react-hot-toast'

interface Post {
    id: string
    title: string
    content: string
    status: 'draft' | 'published' | 'scheduled' | 'promoted'
    channels: string[]
    media_urls?: string[]
    publishedAt?: string
    scheduledAt?: string
    promotedAt?: string
    createdAt: string
    analytics?: {
        views: number
        likes: number
        shares: number
        reach: number
    }
    propertyTitle?: string
}

interface PostEditModalProps {
    post: Post | null
    isOpen: boolean
    onClose: () => void
    onSave: (updatedPost: Post) => void
    onDelete: (postId: string) => void
}

const CHANNEL_OPTIONS = [
    { id: 'facebook', name: 'Facebook', icon: '📘' },
    { id: 'instagram', name: 'Instagram', icon: '📷' },
    { id: 'twitter', name: 'Twitter', icon: '🐦' },
    { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
    { id: 'website', name: 'Website', icon: '🌐' }
]

export default function PostEditModal({ post, isOpen, onClose, onSave, onDelete }: PostEditModalProps) {
    const [formData, setFormData] = useState({
        title: '',
        content: '',
        channels: [] as string[],
        status: 'draft' as 'draft' | 'published' | 'scheduled' | 'promoted',
        scheduledDate: '',
        scheduledTime: ''
    })
    const [loading, setLoading] = useState(false)

    // Initialize form data when post changes
    useState(() => {
        if (post) {
            setFormData({
                title: post.title,
                content: post.content,
                channels: post.channels || [],
                status: post.status,
                scheduledDate: post.scheduledAt ? new Date(post.scheduledAt).toISOString().split('T')[0] : '',
                scheduledTime: post.scheduledAt ? new Date(post.scheduledAt).toTimeString().slice(0, 5) : ''
            })
        }
    })

    const handleInputChange = (field: string, value: any) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }))
    }

    const handleChannelToggle = (channelId: string) => {
        setFormData(prev => ({
            ...prev,
            channels: prev.channels.includes(channelId)
                ? prev.channels.filter(c => c !== channelId)
                : [...prev.channels, channelId]
        }))
    }

    const handleSave = async () => {
        if (!post) return

        setLoading(true)
        try {
            // TODO: Implement API call to update post
            const updatedPost = {
                ...post,
                title: formData.title,
                content: formData.content,
                channels: formData.channels,
                status: formData.status,
                scheduledAt: formData.status === 'scheduled' && formData.scheduledDate && formData.scheduledTime
                    ? new Date(`${formData.scheduledDate}T${formData.scheduledTime}`).toISOString()
                    : post.scheduledAt
            }

            onSave(updatedPost)
            toast.success('Post updated successfully')
            onClose()
        } catch (error) {
            console.error('Error updating post:', error)
            toast.error('Failed to update post')
        } finally {
            setLoading(false)
        }
    }

    const handlePublish = async () => {
        if (!post) return

        setLoading(true)
        try {
            // TODO: Implement API call to publish post
            const updatedPost = {
                ...post,
                title: formData.title,
                content: formData.content,
                channels: formData.channels,
                status: 'published' as const,
                publishedAt: new Date().toISOString()
            }

            onSave(updatedPost)
            toast.success('Post published successfully')
            onClose()
        } catch (error) {
            console.error('Error publishing post:', error)
            toast.error('Failed to publish post')
        } finally {
            setLoading(false)
        }
    }

    const handleSchedule = async () => {
        if (!post || !formData.scheduledDate || !formData.scheduledTime) {
            toast.error('Please select a date and time for scheduling')
            return
        }

        setLoading(true)
        try {
            // TODO: Implement API call to schedule post
            const updatedPost = {
                ...post,
                title: formData.title,
                content: formData.content,
                channels: formData.channels,
                status: 'scheduled' as const,
                scheduledAt: new Date(`${formData.scheduledDate}T${formData.scheduledTime}`).toISOString()
            }

            onSave(updatedPost)
            toast.success('Post scheduled successfully')
            onClose()
        } catch (error) {
            console.error('Error scheduling post:', error)
            toast.error('Failed to schedule post')
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async () => {
        if (!post) return

        if (!confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
            return
        }

        setLoading(true)
        try {
            await api.enhancedPosts.delete(post.id)
            onDelete(post.id)
            toast.success('Post deleted successfully')
            onClose()
        } catch (error) {
            console.error('Error deleting post:', error)
            toast.error('Failed to delete post')
        } finally {
            setLoading(false)
        }
    }

    if (!post) return null

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
                    onClick={onClose}
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b border-gray-200">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                    <PencilIcon className="w-5 h-5 text-blue-600" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-semibold text-gray-900">Edit Post</h2>
                                    <p className="text-sm text-gray-500">Modify your post content and settings</p>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                            >
                                <XMarkIcon className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
                            <div className="space-y-6">
                                {/* Post Title */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Post Title
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.title}
                                        onChange={(e) => handleInputChange('title', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        placeholder="Enter post title..."
                                    />
                                </div>

                                {/* Post Content */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Post Content
                                    </label>
                                    <textarea
                                        value={formData.content}
                                        onChange={(e) => handleInputChange('content', e.target.value)}
                                        rows={8}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                                        placeholder="Write your post content..."
                                    />
                                </div>

                                {/* Publishing Channels */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-3">
                                        Publishing Channels
                                    </label>
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                        {CHANNEL_OPTIONS.map((channel) => (
                                            <label
                                                key={channel.id}
                                                className={`flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${formData.channels.includes(channel.id)
                                                    ? 'border-blue-500 bg-blue-50'
                                                    : 'border-gray-200 hover:border-gray-300'
                                                    }`}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={formData.channels.includes(channel.id)}
                                                    onChange={() => handleChannelToggle(channel.id)}
                                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                />
                                                <span className="text-2xl">{channel.icon}</span>
                                                <span className="text-sm font-medium text-gray-900">
                                                    {channel.name}
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                {/* Post Status */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-3">
                                        Post Status
                                    </label>
                                    <div className="grid grid-cols-3 gap-3">
                                        {[
                                            { id: 'draft', label: 'Draft', icon: '📝' },
                                            { id: 'published', label: 'Publish Now', icon: '🚀' },
                                            { id: 'scheduled', label: 'Schedule', icon: '⏰' }
                                        ].map((status) => (
                                            <label
                                                key={status.id}
                                                className={`flex items-center justify-center space-x-2 p-3 border rounded-lg cursor-pointer transition-colors ${formData.status === status.id
                                                    ? 'border-blue-500 bg-blue-50'
                                                    : 'border-gray-200 hover:border-gray-300'
                                                    }`}
                                            >
                                                <input
                                                    type="radio"
                                                    name="status"
                                                    value={status.id}
                                                    checked={formData.status === status.id}
                                                    onChange={(e) => handleInputChange('status', e.target.value)}
                                                    className="text-blue-600 focus:ring-blue-500"
                                                />
                                                <span className="text-lg">{status.icon}</span>
                                                <span className="text-sm font-medium text-gray-900">
                                                    {status.label}
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                {/* Scheduling Options */}
                                {formData.status === 'scheduled' && (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                                Date
                                            </label>
                                            <input
                                                type="date"
                                                value={formData.scheduledDate}
                                                onChange={(e) => handleInputChange('scheduledDate', e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                                Time
                                            </label>
                                            <input
                                                type="time"
                                                value={formData.scheduledTime}
                                                onChange={(e) => handleInputChange('scheduledTime', e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* Post Images Preview */}
                                {post.media_urls && post.media_urls.length > 0 && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-3">
                                            Post Images
                                        </label>
                                        <div className="grid grid-cols-4 gap-3">
                                            {post.media_urls.map((url, index) => (
                                                <div key={index} className="relative">
                                                    <img
                                                        src={url}
                                                        alt={`Post image ${index + 1}`}
                                                        className="w-full h-20 object-cover rounded-lg"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
                            <button
                                onClick={handleDelete}
                                disabled={loading}
                                className="flex items-center space-x-2 px-4 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                            >
                                <TrashIcon className="w-4 h-4" />
                                <span>Delete</span>
                            </button>

                            <div className="flex items-center space-x-3">
                                <button
                                    onClick={onClose}
                                    disabled={loading}
                                    className="px-4 py-2 text-gray-600 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={loading}
                                    className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
                                >
                                    {loading ? 'Saving...' : 'Save Changes'}
                                </button>
                                {formData.status === 'published' && (
                                    <button
                                        onClick={handlePublish}
                                        disabled={loading}
                                        className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        <RocketLaunchIcon className="w-4 h-4" />
                                        <span>Publish</span>
                                    </button>
                                )}
                                {formData.status === 'scheduled' && (
                                    <button
                                        onClick={handleSchedule}
                                        disabled={loading}
                                        className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        <CalendarIcon className="w-4 h-4" />
                                        <span>Schedule</span>
                                    </button>
                                )}
                            </div>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    )
}
