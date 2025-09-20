'use client'

import { Button } from '@/components/UI'
import {
    BuildingOfficeIcon,
    ChartBarIcon,
    HomeIcon,
    PlusIcon,
    SparklesIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'

interface MobileNavigationProps {
    activeSection: string
    onSectionChange: (section: string) => void
    isOpen: boolean
    onClose: () => void
}

const mobileNavigation = [
    { name: 'Dashboard', icon: HomeIcon, id: 'dashboard' },
    { name: 'Properties', icon: BuildingOfficeIcon, id: 'properties' },
    { name: 'Add Property', icon: PlusIcon, id: 'property-form' },
    { name: 'AI Tools', icon: SparklesIcon, id: 'ai-content' },
    { name: 'Analytics', icon: ChartBarIcon, id: 'analytics' },
]

export function MobileNavigation({
    activeSection,
    onSectionChange,
    isOpen,
    onClose
}: MobileNavigationProps) {
    return (
        <>
            {/* Mobile Bottom Navigation */}
            <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
                <div className="grid grid-cols-5 gap-1">
                    {mobileNavigation.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => onSectionChange(item.id)}
                            className={`flex flex-col items-center py-3 px-2 transition-colors ${activeSection === item.id
                                    ? 'text-brand-primary bg-blue-50'
                                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                                }`}
                        >
                            <item.icon className="w-6 h-6 mb-1" />
                            <span className="text-xs font-medium">{item.name}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Mobile Sidebar Overlay */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
                            onClick={onClose}
                        />
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="lg:hidden fixed left-0 top-0 bottom-0 z-50 w-80 bg-white shadow-2xl overflow-y-auto"
                        >
                            <div className="p-6">
                                <div className="flex items-center justify-between mb-8">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                                            <HomeIcon className="w-6 h-6 text-white" />
                                        </div>
                                        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                                            PropertyAI
                                        </h1>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={onClose}
                                        className="text-gray-500 hover:text-gray-700"
                                    >
                                        ✕
                                    </Button>
                                </div>

                                <nav className="space-y-2">
                                    {[
                                        { name: 'Dashboard', icon: HomeIcon, id: 'dashboard' },
                                        { name: 'Properties', icon: BuildingOfficeIcon, id: 'properties' },
                                        { name: 'Property Management', icon: BuildingOfficeIcon, id: 'property-management' },
                                        { name: 'Add Property', icon: PlusIcon, id: 'property-form' },
                                        { name: 'AI Tools', icon: SparklesIcon, id: 'ai-content' },
                                        { name: 'Analytics', icon: ChartBarIcon, id: 'analytics' },
                                    ].map((item) => (
                                        <button
                                            key={item.id}
                                            onClick={() => {
                                                onSectionChange(item.id)
                                                onClose()
                                            }}
                                            className={`w-full flex items-center space-x-4 px-4 py-4 rounded-xl text-left transition-all duration-200 ${activeSection === item.id
                                                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                                                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                                                }`}
                                        >
                                            <item.icon className="w-6 h-6" />
                                            <span className="font-medium text-lg">{item.name}</span>
                                        </button>
                                    ))}
                                </nav>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    )
}
