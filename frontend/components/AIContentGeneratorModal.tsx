'use client'

import { XMarkIcon } from '@heroicons/react/24/outline'
import AIContentGenerator from './AIContentGenerator'

interface AIContentGeneratorModalProps {
    isOpen: boolean
    onClose: () => void
    propertyData?: any
}

export default function AIContentGeneratorModal({
    isOpen,
    onClose,
    propertyData
}: AIContentGeneratorModalProps) {
    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex min-h-screen items-center justify-center p-4">
                {/* Backdrop */}
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
                    onClick={onClose}
                />

                {/* Modal */}
                <div className="relative bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-200">
                        <h2 className="text-xl font-semibold text-gray-900">
                            AI Content Generator
                        </h2>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 transition-colors"
                        >
                            <XMarkIcon className="h-6 w-6" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-6">
                        <AIContentGenerator
                            propertyData={propertyData}
                            onContentGenerated={(content) => {
                                console.log('Content generated:', content)
                                // You can add additional logic here if needed
                            }}
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}
