'use client'

import { Channel } from '@/types/social_publishing'
import { motion } from 'framer-motion'
import { useState } from 'react'

interface QuickSetupPanelProps {
    platforms: Channel[]
    languages: string[]
    style: 'friendly' | 'luxury' | 'investor'
    onPlatformToggle: (platform: Channel) => void
    onLanguageToggle: (language: string) => void
    onStyleChange: (style: 'friendly' | 'luxury' | 'investor') => void
    onGenerate: () => void
    canProceed: boolean
    platformOptions: Array<{
        code: Channel
        name: string
        icon: string
        description: string
    }>
    languageOptions: Array<{
        code: string
        name: string
        flag: string
    }>
    styleOptions: Array<{
        code: 'friendly' | 'luxury' | 'investor'
        name: string
        description: string
    }>
}

export default function QuickSetupPanel({
    platforms,
    languages,
    style,
    onPlatformToggle,
    onLanguageToggle,
    onStyleChange,
    onGenerate,
    canProceed,
    platformOptions,
    languageOptions,
    styleOptions
}: QuickSetupPanelProps) {

    const [activeTab, setActiveTab] = useState<'platforms' | 'languages' | 'style'>('platforms')

    return (
        <div className="flex flex-col h-full bg-gray-50">
            {/* Tab Navigation */}
            <div className="bg-white border-b border-gray-200">
                <div className="flex">
                    {[
                        { id: 'platforms', label: 'Platforms', icon: '📱' },
                        { id: 'languages', label: 'Languages', icon: '🌍' },
                        { id: 'style', label: 'Style', icon: '🎯' }
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`flex-1 flex items-center justify-center space-x-2 py-4 px-2 border-b-2 transition-colors ${activeTab === tab.id
                                ? 'border-blue-500 text-blue-600 bg-blue-50'
                                : 'border-transparent text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            <span className="text-lg">{tab.icon}</span>
                            <span className="text-sm font-medium">{tab.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
                <div className="p-4">
                    {activeTab === 'platforms' && (
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="space-y-4"
                        >
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                    Choose Social Platforms
                                </h3>
                                <p className="text-sm text-gray-600 mb-4">
                                    Select where you want to publish your content
                                </p>
                            </div>

                            <div className="space-y-3">
                                {platformOptions.map((platform) => (
                                    <motion.div
                                        key={platform.code}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => onPlatformToggle(platform.code)}
                                        className={`p-4 rounded-xl border-2 transition-all cursor-pointer ${platforms.includes(platform.code)
                                            ? 'border-blue-500 bg-blue-50'
                                            : 'border-gray-200 bg-white hover:border-gray-300'
                                            }`}
                                    >
                                        <div className="flex items-center space-x-4">
                                            <div className={`text-3xl ${platforms.includes(platform.code) ? 'scale-110' : ''} transition-transform`}>
                                                {platform.icon}
                                            </div>
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-gray-900">{platform.name}</h4>
                                                <p className="text-sm text-gray-600">{platform.description}</p>
                                            </div>
                                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${platforms.includes(platform.code)
                                                ? 'border-blue-500 bg-blue-500'
                                                : 'border-gray-300'
                                                }`}>
                                                {platforms.includes(platform.code) && (
                                                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                                    </svg>
                                                )}
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {activeTab === 'languages' && (
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="space-y-4"
                        >
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                    Choose Languages
                                </h3>
                                <p className="text-sm text-gray-600 mb-4">
                                    AI will generate content in each selected language
                                </p>
                            </div>

                            <div className="grid grid-cols-1 gap-3">
                                {languageOptions.map((language) => (
                                    <motion.div
                                        key={language.code}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => onLanguageToggle(language.code)}
                                        className={`p-3 rounded-lg border-2 transition-all cursor-pointer ${languages.includes(language.code)
                                            ? 'border-blue-500 bg-blue-50'
                                            : 'border-gray-200 bg-white hover:border-gray-300'
                                            }`}
                                    >
                                        <div className="flex items-center space-x-3">
                                            <span className="text-2xl">{language.flag}</span>
                                            <div className="flex-1">
                                                <p className="font-medium text-gray-900 text-sm">{language.name}</p>
                                            </div>
                                            <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${languages.includes(language.code)
                                                ? 'border-blue-500 bg-blue-500'
                                                : 'border-gray-300'
                                                }`}>
                                                {languages.includes(language.code) && (
                                                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                                    </svg>
                                                )}
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>

                            {languages.length > 0 && (
                                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                                    <p className="text-sm text-green-800">
                                        <span className="font-medium">{languages.length}</span> language{languages.length > 1 ? 's' : ''} selected
                                    </p>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {activeTab === 'style' && (
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="space-y-4"
                        >
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                    Choose Content Style
                                </h3>
                                <p className="text-sm text-gray-600 mb-4">
                                    Select the tone and style for your content
                                </p>
                            </div>

                            <div className="space-y-3">
                                {styleOptions.map((styleOption) => (
                                    <motion.div
                                        key={styleOption.code}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => onStyleChange(styleOption.code)}
                                        className={`p-4 rounded-xl border-2 transition-all cursor-pointer ${style === styleOption.code
                                            ? 'border-blue-500 bg-blue-50'
                                            : 'border-gray-200 bg-white hover:border-gray-300'
                                            }`}
                                    >
                                        <div className="flex items-center space-x-4">
                                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${style === styleOption.code
                                                ? 'border-blue-500 bg-blue-500'
                                                : 'border-gray-300'
                                                }`}>
                                                {style === styleOption.code && (
                                                    <div className="w-3 h-3 bg-white rounded-full" />
                                                )}
                                            </div>
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-gray-900">{styleOption.name}</h4>
                                                <p className="text-sm text-gray-600">{styleOption.description}</p>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>

            {/* Bottom Action */}
            <div className="bg-white border-t border-gray-200 p-4">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <p className="text-sm font-medium text-gray-900">Ready to generate?</p>
                        <p className="text-xs text-gray-600">
                            {platforms.length} platform{platforms.length !== 1 ? 's' : ''} • {languages.length} language{languages.length !== 1 ? 's' : ''}
                        </p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm font-medium text-blue-600">
                            {platforms.length * languages.length} posts will be created
                        </p>
                    </div>
                </div>

                <button
                    onClick={onGenerate}
                    disabled={!canProceed}
                    className={`w-full py-4 px-6 rounded-xl font-semibold text-white transition-all ${canProceed
                        ? 'bg-blue-600 hover:bg-blue-700 active:scale-95'
                        : 'bg-gray-300 cursor-not-allowed'
                        }`}
                >
                    <div className="flex items-center justify-center space-x-2">
                        <span>✨</span>
                        <span>Generate Content</span>
                    </div>
                </button>
            </div>
        </div>
    )
}
