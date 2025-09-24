'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, CheckCircle, Home, Sparkles, X } from 'lucide-react'
import { useEffect, useState } from 'react'

interface PropertySuccessModalProps {
    isOpen: boolean
    onClose: () => void
    propertyData: {
        id: string
        title: string
        location: string
        price: number
        bedrooms: number
        bathrooms: number
        propertyType: string
        images?: string[]
    }
    onCreateSocialPosts: () => void
    onGoToDashboard: () => void
}

export default function PropertySuccessModal({
    isOpen,
    onClose,
    propertyData,
    onCreateSocialPosts,
    onGoToDashboard
}: PropertySuccessModalProps) {
    const [isCreatingPosts, setIsCreatingPosts] = useState(false)

    const handleCreateSocialPosts = async () => {
        setIsCreatingPosts(true)
        try {
            // Small delay for better UX
            await new Promise(resolve => setTimeout(resolve, 500))
            onCreateSocialPosts()
        } finally {
            setIsCreatingPosts(false)
        }
    }

    const formatPrice = (price: number) => {
        if (price >= 10000000) {
            return `₹${(price / 10000000).toFixed(1)}Cr`
        } else if (price >= 100000) {
            return `₹${(price / 100000).toFixed(0)}L`
        } else {
            return `₹${price.toLocaleString()}`
        }
    }

    // Prevent body scroll when modal is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden'
        } else {
            document.body.style.overflow = 'unset'
        }

        return () => {
            document.body.style.overflow = 'unset'
        }
    }, [isOpen])

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
                                Property Created Successfully!
                            </motion.h2>

                            <motion.p
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.4 }}
                                className="text-gray-600 text-lg"
                            >
                                Your property is now live and ready for marketing
                            </motion.p>
                        </div>

                        {/* Property Preview */}
                        <div className="p-8">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.5 }}
                                className="bg-gray-50 rounded-xl p-6 mb-8"
                            >
                                <div className="flex items-start gap-4">
                                    {/* Property Image */}
                                    <div className="w-24 h-24 bg-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
                                        {propertyData.images && propertyData.images.length > 0 ? (
                                            <img
                                                src={propertyData.images[0]}
                                                alt={propertyData.title}
                                                className="w-full h-full object-cover rounded-lg"
                                            />
                                        ) : (
                                            <Home className="w-8 h-8 text-gray-400" />
                                        )}
                                    </div>

                                    {/* Property Details */}
                                    <div className="flex-1">
                                        <h3 className="font-semibold text-gray-900 text-lg mb-1">
                                            {propertyData.title}
                                        </h3>
                                        <p className="text-gray-600 mb-2">{propertyData.location}</p>
                                        <div className="flex items-center gap-4 text-sm text-gray-500">
                                            <span>{propertyData.bedrooms} bed</span>
                                            <span>{propertyData.bathrooms} bath</span>
                                            <span>{propertyData.propertyType}</span>
                                        </div>
                                        <div className="mt-2">
                                            <span className="text-2xl font-bold text-green-600">
                                                {formatPrice(propertyData.price)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Social Post Previews */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.6 }}
                                className="mb-8"
                            >
                                <h4 className="font-semibold text-gray-900 mb-4 text-center">
                                    Ready-to-publish website listings
                                </h4>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {/* Just Listed Post */}
                                    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                        <div className="flex items-center justify-between mb-3">
                                            <span className="text-sm font-medium text-gray-700">Just Listed!</span>
                                            <Sparkles className="w-4 h-4 text-purple-500" />
                                        </div>
                                        <div className="text-sm text-gray-600 mb-2">
                                            Just Listed! {propertyData.bedrooms} Bed, {propertyData.bathrooms} Bath in {propertyData.location}
                                        </div>
                                        <div className="text-xs text-blue-600">
                                            #RealEstate #NewHome
                                        </div>
                                        <div className="mt-3 w-full h-20 bg-gray-100 rounded flex items-center justify-center">
                                            <Home className="w-6 h-6 text-gray-400" />
                                        </div>
                                    </div>

                                    {/* Open House Post */}
                                    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                        <div className="flex items-center justify-between mb-3">
                                            <span className="text-sm font-medium text-gray-700">Open House</span>
                                            <Sparkles className="w-4 h-4 text-purple-500" />
                                        </div>
                                        <div className="text-sm text-gray-600 mb-2">
                                            Open House this Saturday! Come see your dream home. {propertyData.location}
                                        </div>
                                        <div className="text-xs text-blue-600">
                                            #OpenHouse #Property
                                        </div>
                                        <div className="mt-3 w-full h-20 bg-gray-100 rounded flex items-center justify-center">
                                            <Home className="w-6 h-6 text-gray-400" />
                                        </div>
                                    </div>

                                    {/* Virtual Tour Post */}
                                    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                        <div className="flex items-center justify-between mb-3">
                                            <span className="text-sm font-medium text-gray-700">Virtual Tour</span>
                                            <Sparkles className="w-4 h-4 text-purple-500" />
                                        </div>
                                        <div className="text-sm text-gray-600 mb-2">
                                            Virtual Tour Available Now! Explore from anywhere.
                                        </div>
                                        <div className="text-xs text-blue-600">
                                            #VirtualTour
                                        </div>
                                        <div className="mt-3 w-full h-20 bg-gray-100 rounded flex items-center justify-center">
                                            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                                                <div className="w-0 h-0 border-l-[6px] border-l-gray-600 border-y-[4px] border-y-transparent ml-1"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Action Buttons */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.7 }}
                                className="flex flex-col sm:flex-row gap-4"
                            >
                                <button
                                    onClick={handleCreateSocialPosts}
                                    disabled={isCreatingPosts}
                                    className="flex-1 flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isCreatingPosts ? (
                                        <>
                                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                            Creating Posts...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-5 h-5" />
                                            Create Website Posts
                                            <ArrowRight className="w-4 h-4" />
                                        </>
                                    )}
                                </button>

                                <button
                                    onClick={onGoToDashboard}
                                    className="flex-1 px-6 py-4 border border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-colors"
                                >
                                    Go to Dashboard
                                </button>
                            </motion.div>

                            {/* Promise Text */}
                            <motion.p
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.8 }}
                                className="text-center text-sm text-gray-500 mt-4"
                            >
                                ⚡ AI will generate your posts in 30 seconds
                            </motion.p>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
