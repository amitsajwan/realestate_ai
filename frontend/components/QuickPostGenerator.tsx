'use client'

import { AnimatePresence, motion } from 'framer-motion'
import {
    ArrowLeft,
    ArrowRight,
    Edit3,
    Eye,
    Facebook,
    Globe,
    Heart,
    Instagram,
    MessageCircle,
    Settings,
    Share,
    Sparkles,
    X
} from 'lucide-react'
import { useEffect, useState } from 'react'

interface PropertyData {
    id: string
    title: string
    location: string
    price: number
    bedrooms: number
    bathrooms: number
    propertyType: string
    area?: number
    description?: string
    images?: string[]
}

interface GeneratedContent {
    id: string
    platform: 'website' | 'facebook' | 'instagram'
    content: string
    hashtags: string[]
    media_urls: string[]
    status: 'draft' | 'ready' | 'published'
    created_at: string
}

interface QuickPostGeneratorProps {
    isOpen: boolean
    onClose: () => void
    propertyData: PropertyData
    onPublish: (content: GeneratedContent[]) => void
    onBack: () => void
}

export default function QuickPostGenerator({
    isOpen,
    onClose,
    propertyData,
    onPublish,
    onBack
}: QuickPostGeneratorProps) {
    const [isGenerating, setIsGenerating] = useState(false)
    const [generatedContent, setGeneratedContent] = useState<GeneratedContent[]>([])
    const [selectedPlatform, setSelectedPlatform] = useState<'website' | 'facebook' | 'instagram'>('website')
    const [editingContent, setEditingContent] = useState<string | null>(null)
    const [customPrompt, setCustomPrompt] = useState('')
    const [language, setLanguage] = useState('en')
    const [isPublishing, setIsPublishing] = useState(false)

    // Generate content when modal opens
    useEffect(() => {
        if (isOpen && generatedContent.length === 0) {
            generateContent()
        }
    }, [isOpen])

    const generateContent = async () => {
        setIsGenerating(true)
        try {
            // Simulate AI content generation
            await new Promise(resolve => setTimeout(resolve, 2000))

            const mockContent: GeneratedContent[] = [
                {
                    id: '1',
                    platform: 'website',
                    content: `**${propertyData.title}**\n\n**Location:** ${propertyData.location}\n**Price:** ${formatPrice(propertyData.price)}\n**Bedrooms:** ${propertyData.bedrooms}\n**Bathrooms:** ${propertyData.bathrooms}\n**Property Type:** ${propertyData.propertyType}\n${propertyData.area ? `**Area:** ${propertyData.area} sq ft\n` : ''}\n**Description:**\n${propertyData.description || 'Beautiful property with modern amenities and great connectivity.'}\n\n**Contact us today for a viewing!**`,
                    hashtags: ['#RealEstate', '#Property', '#DreamHome'],
                    media_urls: propertyData.images || [],
                    status: 'draft',
                    created_at: new Date().toISOString()
                },
                {
                    id: '2',
                    platform: 'facebook',
                    content: `Just Listed! This beautiful ${propertyData.bedrooms} bed, ${propertyData.bathrooms} bath home in ${propertyData.location} is perfect for your family. Features include modern amenities and a great location. Asking ${formatPrice(propertyData.price)}!`,
                    hashtags: ['#RealEstate', '#NewHome', '#Property', '#DreamHome'],
                    media_urls: propertyData.images || [],
                    status: 'draft',
                    created_at: new Date().toISOString()
                }
            ]

            setGeneratedContent(mockContent)
        } catch (error) {
            console.error('Error generating content:', error)
        } finally {
            setIsGenerating(false)
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

    const handleEditContent = (contentId: string) => {
        setEditingContent(contentId)
    }

    const handleSaveEdit = (contentId: string, newContent: string) => {
        setGeneratedContent(prev =>
            prev.map(content =>
                content.id === contentId
                    ? { ...content, content: newContent }
                    : content
            )
        )
        setEditingContent(null)
    }

    const handlePublish = async () => {
        setIsPublishing(true)
        try {
            // Simulate publishing
            await new Promise(resolve => setTimeout(resolve, 1500))

            // Update status to published
            setGeneratedContent(prev =>
                prev.map(content => ({ ...content, status: 'published' as const }))
            )

            onPublish(generatedContent)
        } catch (error) {
            console.error('Error publishing:', error)
        } finally {
            setIsPublishing(false)
        }
    }

    const currentContent = generatedContent.find(content => content.platform === selectedPlatform)

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4 overflow-y-auto">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ duration: 0.3, ease: "easeOut" }}
                        className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[95vh] overflow-y-auto my-8"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b border-gray-200">
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={onBack}
                                    className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                    <ArrowLeft className="w-5 h-5" />
                                </button>
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">AI Content Generator</h2>
                                    <p className="text-gray-600">Create engaging social media posts for your property</p>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="flex h-[calc(90vh-120px)]">
                            {/* Left Panel - Property Details */}
                            <div className="w-1/3 border-r border-gray-200 p-6 overflow-y-auto">
                                <h3 className="font-semibold text-gray-900 mb-4">Property Details</h3>

                                <div className="space-y-4">
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h4 className="font-medium text-gray-900 mb-2">{propertyData.title}</h4>
                                        <p className="text-gray-600 text-sm mb-3">{propertyData.location}</p>

                                        <div className="grid grid-cols-2 gap-2 text-sm">
                                            <div>
                                                <span className="text-gray-500">Bedrooms:</span>
                                                <span className="ml-2 font-medium">{propertyData.bedrooms}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Bathrooms:</span>
                                                <span className="ml-2 font-medium">{propertyData.bathrooms}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Type:</span>
                                                <span className="ml-2 font-medium">{propertyData.propertyType}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Price:</span>
                                                <span className="ml-2 font-medium text-green-600">{formatPrice(propertyData.price)}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {propertyData.description && (
                                        <div className="bg-gray-50 rounded-lg p-4">
                                            <h5 className="font-medium text-gray-900 mb-2">Description</h5>
                                            <p className="text-gray-600 text-sm">{propertyData.description}</p>
                                        </div>
                                    )}

                                    {/* AI Settings */}
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h5 className="font-medium text-gray-900 mb-3">AI Settings</h5>

                                        <div className="space-y-3">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Language
                                                </label>
                                                <select
                                                    value={language}
                                                    onChange={(e) => setLanguage(e.target.value)}
                                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                >
                                                    <option value="en">English</option>
                                                    <option value="hi">Hindi</option>
                                                    <option value="ta">Tamil</option>
                                                    <option value="te">Telugu</option>
                                                </select>
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Custom Prompt (Optional)
                                                </label>
                                                <textarea
                                                    value={customPrompt}
                                                    onChange={(e) => setCustomPrompt(e.target.value)}
                                                    placeholder="Add specific requirements..."
                                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                    rows={3}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Right Panel - Generated Content */}
                            <div className="flex-1 p-6 overflow-y-auto">
                                {isGenerating ? (
                                    <div className="flex items-center justify-center h-full">
                                        <div className="text-center">
                                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                                            <h3 className="text-lg font-medium text-gray-900 mb-2">Generating Content</h3>
                                            <p className="text-gray-600">AI is creating engaging posts for your property...</p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-6">
                                        {/* Platform Tabs */}
                                        <div className="flex gap-2 border-b border-gray-200">
                                            <button
                                                onClick={() => setSelectedPlatform('website')}
                                                className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${selectedPlatform === 'website'
                                                    ? 'text-green-600 border-b-2 border-green-600'
                                                    : 'text-gray-500 hover:text-gray-700'
                                                    }`}
                                            >
                                                <Globe className="w-4 h-4" />
                                                Website
                                            </button>
                                            <button
                                                onClick={() => setSelectedPlatform('facebook')}
                                                className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${selectedPlatform === 'facebook'
                                                    ? 'text-blue-600 border-b-2 border-blue-600'
                                                    : 'text-gray-500 hover:text-gray-700'
                                                    }`}
                                            >
                                                <Facebook className="w-4 h-4" />
                                                Facebook
                                            </button>
                                            <button
                                                onClick={() => setSelectedPlatform('instagram')}
                                                className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${selectedPlatform === 'instagram'
                                                    ? 'text-pink-600 border-b-2 border-pink-600'
                                                    : 'text-gray-500 hover:text-gray-700'
                                                    }`}
                                            >
                                                <Instagram className="w-4 h-4" />
                                                Instagram
                                            </button>
                                        </div>

                                        {/* Content Preview */}
                                        {currentContent && (
                                            <motion.div
                                                key={currentContent.id}
                                                initial={{ opacity: 0, x: 20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                className="bg-white border border-gray-200 rounded-xl overflow-hidden"
                                            >
                                                {/* Platform Header */}
                                                <div className={`p-4 ${selectedPlatform === 'website' ? 'bg-green-50' : selectedPlatform === 'facebook' ? 'bg-blue-50' : 'bg-pink-50'
                                                    }`}>
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            {selectedPlatform === 'website' ? (
                                                                <Globe className="w-6 h-6 text-green-600" />
                                                            ) : selectedPlatform === 'facebook' ? (
                                                                <Facebook className="w-6 h-6 text-blue-600" />
                                                            ) : (
                                                                <Instagram className="w-6 h-6 text-pink-600" />
                                                            )}
                                                            <div>
                                                                <h4 className="font-semibold text-gray-900">
                                                                    {selectedPlatform === 'website' ? 'Website Listing' : selectedPlatform === 'facebook' ? 'Facebook Post' : 'Instagram Post'}
                                                                </h4>
                                                                <p className="text-sm text-gray-600">Preview</p>
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <button
                                                                onClick={() => handleEditContent(currentContent.id)}
                                                                className="flex items-center gap-1 px-3 py-1 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                                                            >
                                                                <Edit3 className="w-4 h-4" />
                                                                Edit
                                                            </button>
                                                            <button className="flex items-center gap-1 px-3 py-1 text-sm text-gray-600 hover:text-gray-800 transition-colors">
                                                                <Settings className="w-4 h-4" />
                                                                Settings
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Content Body */}
                                                <div className="p-6">
                                                    {/* Media Preview */}
                                                    <div className="mb-4">
                                                        <div className="grid grid-cols-2 gap-2">
                                                            {propertyData.images && propertyData.images.length > 0 ? (
                                                                propertyData.images.slice(0, 4).map((image, index) => (
                                                                    <div key={index} className="aspect-square bg-gray-200 rounded-lg overflow-hidden">
                                                                        <img
                                                                            src={image}
                                                                            alt={`Property ${index + 1}`}
                                                                            className="w-full h-full object-cover"
                                                                        />
                                                                    </div>
                                                                ))
                                                            ) : (
                                                                <div className="col-span-2 aspect-video bg-gray-200 rounded-lg flex items-center justify-center">
                                                                    <span className="text-gray-500">No images available</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Post Content */}
                                                    <div className="mb-4">
                                                        {editingContent === currentContent.id ? (
                                                            <textarea
                                                                value={currentContent.content}
                                                                onChange={(e) => {
                                                                    setGeneratedContent(prev =>
                                                                        prev.map(content =>
                                                                            content.id === currentContent.id
                                                                                ? { ...content, content: e.target.value }
                                                                                : content
                                                                        )
                                                                    )
                                                                }}
                                                                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                                rows={4}
                                                                onBlur={() => handleSaveEdit(currentContent.id, currentContent.content)}
                                                                onKeyDown={(e) => {
                                                                    if (e.key === 'Enter' && e.ctrlKey) {
                                                                        handleSaveEdit(currentContent.id, currentContent.content)
                                                                    }
                                                                }}
                                                                autoFocus
                                                            />
                                                        ) : (
                                                            <p className="text-gray-900 leading-relaxed">{currentContent.content}</p>
                                                        )}
                                                    </div>

                                                    {/* Hashtags */}
                                                    <div className="mb-4">
                                                        <div className="flex flex-wrap gap-2">
                                                            {currentContent.hashtags.map((hashtag, index) => (
                                                                <span
                                                                    key={index}
                                                                    className="px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
                                                                >
                                                                    {hashtag}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    {/* Social Media Interactions */}
                                                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                                                        <div className="flex items-center gap-4">
                                                            <button className="flex items-center gap-1 text-gray-600 hover:text-gray-800 transition-colors">
                                                                <Heart className="w-5 h-5" />
                                                                <span className="text-sm">12</span>
                                                            </button>
                                                            <button className="flex items-center gap-1 text-gray-600 hover:text-gray-800 transition-colors">
                                                                <MessageCircle className="w-5 h-5" />
                                                                <span className="text-sm">5</span>
                                                            </button>
                                                            <button className="flex items-center gap-1 text-gray-600 hover:text-gray-800 transition-colors">
                                                                <Share className="w-5 h-5" />
                                                                <span className="text-sm">3</span>
                                                            </button>
                                                        </div>
                                                        <div className="flex items-center gap-1 text-gray-500 text-sm">
                                                            <Eye className="w-4 h-4" />
                                                            <span>250 views</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        )}

                                        {/* Action Buttons */}
                                        <div className="flex gap-4 pt-6 border-t border-gray-200">
                                            <button
                                                onClick={generateContent}
                                                disabled={isGenerating}
                                                className="flex items-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                                            >
                                                <Sparkles className="w-4 h-4" />
                                                Regenerate Content
                                            </button>

                                            <button
                                                onClick={handlePublish}
                                                disabled={isPublishing || generatedContent.length === 0}
                                                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50"
                                            >
                                                {isPublishing ? (
                                                    <>
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                                        Publishing...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Globe className="w-4 h-4" />
                                                        Publish to {selectedPlatform === 'website' ? 'Website' : selectedPlatform === 'facebook' ? 'Facebook' : 'Instagram'}
                                                        <ArrowRight className="w-4 h-4" />
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
