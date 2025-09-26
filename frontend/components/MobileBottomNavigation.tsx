'use client'

import {
    BuildingOfficeIcon,
    ChartBarIcon,
    HomeIcon,
    PlusIcon,
    SparklesIcon,
    UserGroupIcon,
    UserIcon
} from '@heroicons/react/24/outline'
import {
    BuildingOfficeIcon as BuildingSolidIcon,
    ChartBarIcon as ChartSolidIcon,
    HomeIcon as HomeSolidIcon,
    UserGroupIcon as UserGroupSolidIcon,
    UserIcon as UserSolidIcon
} from '@heroicons/react/24/solid'
import { motion } from 'framer-motion'
import { useState } from 'react'

interface NavigationItem {
    id: string
    label: string
    icon: any
    solidIcon: any
    href?: string
    onClick?: () => void
    badge?: string | number
}

interface MobileBottomNavigationProps {
    activeSection: string
    onSectionChange: (section: string) => void
    className?: string
}

export default function MobileBottomNavigation({
    activeSection,
    onSectionChange,
    className = ''
}: MobileBottomNavigationProps) {
    const [showQuickActions, setShowQuickActions] = useState(false)

    const navigationItems: NavigationItem[] = [
        {
            id: 'dashboard',
            label: 'Dashboard',
            icon: HomeIcon,
            solidIcon: HomeSolidIcon,
            href: '/'
        },
        {
            id: 'properties',
            label: 'Properties',
            icon: BuildingOfficeIcon,
            solidIcon: BuildingSolidIcon,
            href: '/properties'
        },
        {
            id: 'analytics',
            label: 'Analytics',
            icon: ChartBarIcon,
            solidIcon: ChartSolidIcon,
            href: '/analytics'
        },
        {
            id: 'crm',
            label: 'CRM',
            icon: UserGroupIcon,
            solidIcon: UserGroupSolidIcon,
            href: '/crm'
        },
        {
            id: 'profile',
            label: 'Profile',
            icon: UserIcon,
            solidIcon: UserSolidIcon,
            href: '/profile'
        }
    ]

    const quickActions = [
        {
            id: 'add-property',
            label: 'Add Property',
            icon: PlusIcon,
            solidIcon: PlusIcon,
            onClick: () => onSectionChange('property-form')
        },
        {
            id: 'ai-generate',
            label: 'AI Generate',
            icon: SparklesIcon,
            solidIcon: SparklesIcon,
            onClick: () => onSectionChange('ai-content')
        },
        {
            id: 'marketing-hub',
            label: 'Marketing Hub',
            icon: BuildingOfficeIcon,
            solidIcon: BuildingSolidIcon,
            onClick: () => onSectionChange('property-marketing-hub')
        }
    ]

    const handleItemClick = (item: NavigationItem) => {
        if (item.onClick) {
            item.onClick()
        } else if (item.href) {
            onSectionChange(item.id)
        }
        setShowQuickActions(false)
    }

    const isActive = (itemId: string) => {
        return activeSection === itemId
    }

    return (
        <div className={`fixed bottom-0 left-0 right-0 z-40 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 safe-area-pb ${className}`}>
            {/* Quick Actions Overlay */}
            {showQuickActions && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 20 }}
                    className="absolute bottom-full left-0 right-0 p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700"
                >
                    <div className="flex justify-center space-x-4">
                        {quickActions.map((action) => (
                            <motion.button
                                key={action.id}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => handleItemClick(action)}
                                className="flex flex-col items-center space-y-2 p-3 bg-gray-50 dark:bg-gray-700 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                            >
                                <action.icon className="w-6 h-6 text-gray-600 dark:text-gray-300" />
                                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                                    {action.label}
                                </span>
                            </motion.button>
                        ))}
                    </div>
                </motion.div>
            )}

            {/* Main Navigation */}
            <div className="flex items-center justify-around px-2 py-3">
                {navigationItems.map((item) => {
                    const active = isActive(item.id)
                    const IconComponent = active ? item.solidIcon : item.icon

                    return (
                        <motion.button
                            key={item.id}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => handleItemClick(item)}
                            className={`relative flex flex-col items-center space-y-1 p-3 rounded-lg transition-colors min-h-[48px] min-w-[48px] ${active
                                    ? 'text-blue-600 dark:text-blue-400'
                                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                                }`}
                        >
                            {/* Badge */}
                            {item.badge && (
                                <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                                    {item.badge}
                                </div>
                            )}

                            {/* Icon */}
                            <IconComponent className="w-6 h-6" />

                            {/* Label */}
                            <span className="text-xs font-medium truncate max-w-[60px]">
                                {item.label}
                            </span>

                            {/* Active Indicator */}
                            {active && (
                                <motion.div
                                    layoutId="activeIndicator"
                                    className="absolute top-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-blue-600 dark:bg-blue-400 rounded-full"
                                />
                            )}
                        </motion.button>
                    )
                })}

                {/* Quick Actions Button */}
                <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setShowQuickActions(!showQuickActions)}
                    className={`flex flex-col items-center space-y-1 p-3 rounded-lg transition-colors min-h-[48px] min-w-[48px] ${showQuickActions
                            ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                        }`}
                >
                    <motion.div
                        animate={{ rotate: showQuickActions ? 45 : 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        <PlusIcon className="w-6 h-6" />
                    </motion.div>
                    <span className="text-xs font-medium">More</span>
                </motion.button>
            </div>

            {/* Safe Area for iPhone */}
            <div className="h-safe-area-inset-bottom bg-white dark:bg-gray-900" />
        </div>
    )
}
