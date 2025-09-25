'use client'

import {
    Bars3Icon,
    EyeIcon,
    EyeSlashIcon,
    XMarkIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface DashboardWidget {
    id: string
    title: string
    description: string
    component: string
    enabled: boolean
    order: number
    category: 'overview' | 'analytics' | 'content' | 'properties'
    size: 'small' | 'medium' | 'large'
}

interface DashboardCustomizationProps {
    isOpen: boolean
    onClose: () => void
    onSave: (widgets: DashboardWidget[]) => void
    currentWidgets: DashboardWidget[]
}

const defaultWidgets: DashboardWidget[] = [
    {
        id: 'stats-overview',
        title: 'Statistics Overview',
        description: 'Key metrics and performance indicators',
        component: 'DashboardStats',
        enabled: true,
        order: 1,
        category: 'overview',
        size: 'large'
    },
    {
        id: 'recent-properties',
        title: 'Recent Properties',
        description: 'Latest property listings and updates',
        component: 'RecentProperties',
        enabled: true,
        order: 2,
        category: 'properties',
        size: 'medium'
    },
    {
        id: 'quick-actions',
        title: 'Quick Actions',
        description: 'Common tasks and shortcuts',
        component: 'QuickActions',
        enabled: true,
        order: 3,
        category: 'overview',
        size: 'small'
    },
    {
        id: 'content-performance',
        title: 'Content Performance',
        description: 'Marketing content engagement metrics',
        component: 'ContentPerformance',
        enabled: false,
        order: 4,
        category: 'analytics',
        size: 'medium'
    },
    {
        id: 'lead-analytics',
        title: 'Lead Analytics',
        description: 'Lead generation and conversion tracking',
        component: 'LeadAnalytics',
        enabled: false,
        order: 5,
        category: 'analytics',
        size: 'medium'
    },
    {
        id: 'recent-posts',
        title: 'Recent Posts',
        description: 'Latest social media and marketing posts',
        component: 'RecentPosts',
        enabled: false,
        order: 6,
        category: 'content',
        size: 'small'
    },
    {
        id: 'property-map',
        title: 'Property Map',
        description: 'Geographic distribution of properties',
        component: 'PropertyMap',
        enabled: false,
        order: 7,
        category: 'properties',
        size: 'large'
    },
    {
        id: 'team-activity',
        title: 'Team Activity',
        description: 'Recent team member activities',
        component: 'TeamActivity',
        enabled: false,
        order: 8,
        category: 'overview',
        size: 'small'
    }
]

export default function DashboardCustomization({
    isOpen,
    onClose,
    onSave,
    currentWidgets
}: DashboardCustomizationProps) {
    const [widgets, setWidgets] = useState<DashboardWidget[]>(currentWidgets)
    const [draggedWidget, setDraggedWidget] = useState<string | null>(null)
    const [filter, setFilter] = useState<'all' | 'overview' | 'analytics' | 'content' | 'properties'>('all')

    useEffect(() => {
        setWidgets(currentWidgets)
    }, [currentWidgets])

    const filteredWidgets = widgets.filter(widget =>
        filter === 'all' || widget.category === filter
    )

    const toggleWidget = (widgetId: string) => {
        setWidgets(prev => prev.map(widget =>
            widget.id === widgetId
                ? { ...widget, enabled: !widget.enabled }
                : widget
        ))
    }

    const moveWidget = (fromIndex: number, toIndex: number) => {
        const newWidgets = [...widgets]
        const [movedWidget] = newWidgets.splice(fromIndex, 1)
        newWidgets.splice(toIndex, 0, movedWidget)

        // Update order numbers
        const updatedWidgets = newWidgets.map((widget, index) => ({
            ...widget,
            order: index + 1
        }))

        setWidgets(updatedWidgets)
    }

    const handleDragStart = (widgetId: string) => {
        setDraggedWidget(widgetId)
    }

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
    }

    const handleDrop = (e: React.DragEvent, targetIndex: number) => {
        e.preventDefault()

        if (!draggedWidget) return

        const draggedIndex = widgets.findIndex(w => w.id === draggedWidget)
        if (draggedIndex !== -1 && draggedIndex !== targetIndex) {
            moveWidget(draggedIndex, targetIndex)
        }

        setDraggedWidget(null)
    }

    const handleSave = () => {
        onSave(widgets)
        onClose()
    }

    const handleReset = () => {
        setWidgets(defaultWidgets)
    }

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case 'overview':
                return '📊'
            case 'analytics':
                return '📈'
            case 'content':
                return '📝'
            case 'properties':
                return '🏠'
            default:
                return '📄'
        }
    }

    const getSizeLabel = (size: string) => {
        switch (size) {
            case 'small':
                return 'Small'
            case 'medium':
                return 'Medium'
            case 'large':
                return 'Large'
            default:
                return 'Medium'
        }
    }

    if (!isOpen) return null

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
        >
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl mx-4 bg-white dark:bg-gray-800 rounded-xl shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                            Customize Dashboard
                        </h2>
                        <p className="text-gray-600 dark:text-gray-400 mt-1">
                            Arrange and configure your dashboard widgets
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                    >
                        <XMarkIcon className="w-6 h-6" />
                    </button>
                </div>

                {/* Filters */}
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-4">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Filter by category:
                        </span>
                        <div className="flex space-x-2">
                            {[
                                { key: 'all', label: 'All' },
                                { key: 'overview', label: 'Overview' },
                                { key: 'analytics', label: 'Analytics' },
                                { key: 'content', label: 'Content' },
                                { key: 'properties', label: 'Properties' }
                            ].map(({ key, label }) => (
                                <button
                                    key={key}
                                    onClick={() => setFilter(key as any)}
                                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${filter === key
                                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                                        }`}
                                >
                                    {label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Widgets List */}
                <div className="p-6 max-h-96 overflow-y-auto">
                    <div className="space-y-3">
                        {filteredWidgets.map((widget, index) => (
                            <motion.div
                                key={widget.id}
                                drag
                                dragConstraints={{ left: 0, right: 0 }}
                                onDragStart={() => handleDragStart(widget.id)}
                                onDragOver={handleDragOver}
                                onDrop={(e) => handleDrop(e, index)}
                                className={`flex items-center space-x-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border-2 transition-all ${draggedWidget === widget.id
                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                    : 'border-transparent hover:border-gray-300 dark:hover:border-gray-600'
                                    }`}
                            >
                                {/* Drag Handle */}
                                <div className="cursor-move">
                                    <Bars3Icon className="w-5 h-5 text-gray-400" />
                                </div>

                                {/* Widget Info */}
                                <div className="flex-1">
                                    <div className="flex items-center space-x-3">
                                        <span className="text-2xl">
                                            {getCategoryIcon(widget.category)}
                                        </span>
                                        <div>
                                            <h3 className="font-medium text-gray-900 dark:text-white">
                                                {widget.title}
                                            </h3>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                {widget.description}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Widget Details */}
                                <div className="flex items-center space-x-4">
                                    <span className="px-2 py-1 bg-gray-200 dark:bg-gray-600 text-xs text-gray-600 dark:text-gray-300 rounded-full">
                                        {getSizeLabel(widget.size)}
                                    </span>
                                    <span className="px-2 py-1 bg-gray-200 dark:bg-gray-600 text-xs text-gray-600 dark:text-gray-300 rounded-full">
                                        {widget.category}
                                    </span>
                                </div>

                                {/* Toggle */}
                                <button
                                    onClick={() => toggleWidget(widget.id)}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${widget.enabled
                                        ? 'bg-blue-600'
                                        : 'bg-gray-200 dark:bg-gray-600'
                                        }`}
                                >
                                    <span
                                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${widget.enabled ? 'translate-x-6' : 'translate-x-1'
                                            }`}
                                    />
                                </button>

                                {/* Visibility Icon */}
                                {widget.enabled ? (
                                    <EyeIcon className="w-5 h-5 text-green-500" />
                                ) : (
                                    <EyeSlashIcon className="w-5 h-5 text-gray-400" />
                                )}
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
                    <button
                        onClick={handleReset}
                        className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                    >
                        Reset to Default
                    </button>

                    <div className="flex space-x-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Save Changes
                        </button>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    )
}
