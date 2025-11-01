'use client'

import {
    AdjustmentsHorizontalIcon,
    ArrowRightOnRectangleIcon,
    Bars3Icon,
    BellIcon,
    BuildingOfficeIcon,
    ChartBarIcon,
    CogIcon,
    DocumentTextIcon,
    GlobeAltIcon,
    HomeIcon,
    PlusIcon,
    SparklesIcon,
    UserIcon,
    UsersIcon,
    XMarkIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'

interface NavigationItem {
    name: string
    icon: any
    id: string
    highlight?: boolean
    badge?: string
    position?: 'bottom'
}

const navigation: NavigationItem[] = [
    { name: 'Dashboard', icon: HomeIcon, id: 'dashboard' },
    { name: 'Properties', icon: BuildingOfficeIcon, id: 'properties' },
    { name: 'Property Marketing Hub', icon: DocumentTextIcon, id: 'property-marketing-hub', highlight: true },
    { name: 'Add Property', icon: PlusIcon, id: 'property-form' },
    { name: 'Analytics', icon: ChartBarIcon, id: 'analytics' },
    { name: 'CRM', icon: UsersIcon, id: 'crm' },
    { name: 'Team', icon: UsersIcon, id: 'team-management' },
    { name: 'Website', icon: GlobeAltIcon, id: 'public-website' },
    { name: 'Facebook', icon: CogIcon, id: 'facebook' },
    { name: 'Profile', icon: UserIcon, id: 'profile' },
]

interface MobileFirstNavigationProps {
    activeSection: string
    onSectionChange: (section: string) => void
    user?: any
    properties?: any[]
    onShowDashboardCustomization: () => void
    onShowAIContentModal: () => void
}

export default function MobileFirstNavigation({
    activeSection,
    onSectionChange,
    user,
    properties = [],
    onShowDashboardCustomization,
    onShowAIContentModal
}: MobileFirstNavigationProps) {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

    const handleSectionChange = (sectionId: string) => {
        onSectionChange(sectionId)
        setIsMobileMenuOpen(false)
    }

    return (
        <>
            {/* Unified Header - Works on both Mobile and Desktop */}
            <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-lg border-b border-gray-200 shadow-sm">
                <div className="px-4 py-3 max-w-7xl mx-auto">
                    <div className="flex items-center justify-between">
                        {/* Logo and Menu Button */}
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                                className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
                                aria-label="Toggle mobile menu"
                            >
                                {isMobileMenuOpen ? (
                                    <XMarkIcon className="w-6 h-6" />
                                ) : (
                                    <Bars3Icon className="w-6 h-6" />
                                )}
                            </button>
                            <div className="flex items-center space-x-2">
                                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                                    <HomeIcon className="w-5 h-5 text-white" />
                                </div>
                                <h1 className="text-lg font-bold text-gray-900">PropertyAI</h1>
                            </div>
                        </div>

                        {/* Desktop Navigation */}
                        <nav className="hidden md:flex items-center space-x-6">
                            {navigation.slice(0, 5).map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => onSectionChange(item.id)}
                                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                                        activeSection === item.id
                                            ? 'bg-blue-50 text-blue-600'
                                            : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                                >
                                    <item.icon className="w-5 h-5" />
                                    <span className="font-medium">{item.name}</span>
                                </button>
                            ))}
                        </nav>

                        {/* Right Side Actions */}
                        <div className="flex items-center space-x-2">
                            {/* Create Post Button */}
                            {properties.length > 0 && (
                                <button
                                    onClick={onShowAIContentModal}
                                    className="p-2 bg-blue-600 text-white rounded-lg shadow-sm"
                                    aria-label="Create new post"
                                >
                                    <SparklesIcon className="w-5 h-5" />
                                </button>
                            )}

                            {/* Notifications */}
                            <button
                                className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors relative"
                                aria-label="Notifications"
                            >
                                <BellIcon className="w-5 h-5" />
                                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
                            </button>

                            {/* User Profile */}
                            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                                <span className="text-white text-sm font-medium">
                                    {(user?.first_name || 'A').charAt(0).toUpperCase()}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {isMobileMenuOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="fixed inset-0 bg-black bg-opacity-50 z-40"
                            onClick={() => setIsMobileMenuOpen(false)}
                        />

                        {/* Mobile Menu */}
                        <motion.div
                            initial={{ x: -300 }}
                            animate={{ x: 0 }}
                            exit={{ x: -300 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed left-0 top-0 bottom-0 w-80 bg-white shadow-xl z-50 overflow-y-auto"
                        >
                            <div className="p-6">
                                {/* Menu Header */}
                                <div className="flex items-center justify-between mb-8">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
                                            <HomeIcon className="w-6 h-6 text-white" />
                                        </div>
                                        <div>
                                            <h2 className="text-lg font-bold text-gray-900">PropertyAI</h2>
                                            <p className="text-sm text-gray-500">Real Estate Platform</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setIsMobileMenuOpen(false)}
                                        className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                                        aria-label="Close menu"
                                    >
                                        <XMarkIcon className="w-6 h-6" />
                                    </button>
                                </div>

                                {/* Navigation Items */}
                                <nav className="space-y-2">
                                    {navigation.map((item) => {
                                        const Icon = item.icon
                                        const isActive = activeSection === item.id

                                        return (
                                            <button
                                                key={item.id}
                                                onClick={() => handleSectionChange(item.id)}
                                                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200 ${isActive
                                                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                                    : 'text-gray-700 hover:bg-gray-50'
                                                    }`}
                                            >
                                                <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
                                                <span className="font-medium">{item.name}</span>
                                                {item.highlight && (
                                                    <span className="ml-auto px-2 py-1 bg-blue-100 text-blue-600 text-xs font-medium rounded-full">
                                                        New
                                                    </span>
                                                )}
                                            </button>
                                        )
                                    })}
                                </nav>

                                {/* User Section */}
                                <div className="mt-8 pt-6 border-t border-gray-200">
                                    <div className="flex items-center space-x-3 mb-4">
                                        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                                            <span className="text-white font-medium">
                                                {(user?.first_name || 'A').charAt(0).toUpperCase()}
                                            </span>
                                        </div>
                                        <div>
                                            <p className="font-medium text-gray-900">
                                                {user?.first_name || 'Agent'} {user?.last_name || ''}
                                            </p>
                                            <p className="text-sm text-gray-500">Real Estate Agent</p>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <button
                                            onClick={() => {
                                                onShowDashboardCustomization()
                                                setIsMobileMenuOpen(false)
                                            }}
                                            className="w-full flex items-center space-x-3 px-4 py-3 text-gray-700 hover:bg-gray-50 rounded-xl transition-colors"
                                        >
                                            <AdjustmentsHorizontalIcon className="w-5 h-5" />
                                            <span>Customize Dashboard</span>
                                        </button>

                                        <button
                                            className="w-full flex items-center space-x-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                                            aria-label="Sign out"
                                        >
                                            <ArrowRightOnRectangleIcon className="w-5 h-5" />
                                            <span>Sign Out</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Bottom Navigation for Mobile */}
            <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-2 z-30 md:hidden">
                <div className="flex items-center justify-around">
                    {navigation.slice(0, 5).map((item) => {
                        const Icon = item.icon
                        const isActive = activeSection === item.id

                        return (
                            <button
                                key={item.id}
                                onClick={() => handleSectionChange(item.id)}
                                className={`flex flex-col items-center space-y-1 p-2 rounded-lg transition-colors ${isActive ? 'text-blue-600' : 'text-gray-500'
                                    }`}
                                aria-label={item.name}
                            >
                                <Icon className="w-5 h-5" />
                                <span className="text-xs font-medium">{item.name}</span>
                            </button>
                        )
                    })}
                </div>
            </nav>

            {/* Bottom spacing for mobile navigation */}
            <div className="h-20 md:hidden" />
        </>
    )
}
