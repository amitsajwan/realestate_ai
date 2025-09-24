'use client'

import {
    AlertCircle,
    Calendar,
    CheckCircle,
    Clock,
    Globe,
    Grid,
    List,
    PencilIcon,
    Plus,
    Sparkles as SparklesIcon,
    TrashIcon,
    X
} from 'lucide-react'
import { useEffect, useState } from 'react'
import PublishDraftsButton from './PublishDraftsButton'

// Content Types
enum ContentType {
    PROPERTY = 'property',
    ENHANCED_POST = 'enhanced_post',
    AI_DRAFT = 'ai_draft',
    MARKETING_POST = 'marketing_post'
}

// Status Types
enum PublishingStatus {
    DRAFT = 'draft',
    SCHEDULED = 'scheduled',
    PUBLISHED = 'published',
    FAILED = 'failed'
}

interface ContentItem {
    id: string
    content_type: ContentType
    title: string
    description?: string
    status: PublishingStatus
    channels: string[]
    scheduled_at?: string
    published_at?: string
    created_at: string
    updated_at: string
    thumbnail?: string
    ai_generated?: boolean
}

interface UnifiedPublishingDashboardProps {
    onRefresh?: () => void
    preselectedPropertyId?: string
    onClearPreselectedProperty?: () => void
}

const contentTypeLabels = {
    [ContentType.PROPERTY]: 'Property Listing',
    [ContentType.ENHANCED_POST]: 'Marketing Post',
    [ContentType.AI_DRAFT]: 'AI Generated',
    [ContentType.MARKETING_POST]: 'Social Content'
}

const statusConfig = {
    [PublishingStatus.DRAFT]: { icon: Clock, color: 'text-gray-500', bg: 'bg-gray-100' },
    [PublishingStatus.SCHEDULED]: { icon: Calendar, color: 'text-blue-500', bg: 'bg-blue-100' },
    [PublishingStatus.PUBLISHED]: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-100' },
    [PublishingStatus.FAILED]: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-100' }
}

export default function UnifiedPublishingDashboard({ onRefresh, preselectedPropertyId, onClearPreselectedProperty }: UnifiedPublishingDashboardProps) {
    const [contentItems, setContentItems] = useState<ContentItem[]>([])
    const [loading, setLoading] = useState(true)
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
    const [selectedItems, setSelectedItems] = useState<string[]>([])
    const [filterStatus, setFilterStatus] = useState<PublishingStatus | 'all'>('all')
    const [filterType, setFilterType] = useState<ContentType | 'all'>('all')
    const [showBatchPublish, setShowBatchPublish] = useState(false)
    const [selectedChannels, setSelectedChannels] = useState<string[]>([])
    const [publishing, setPublishing] = useState(false)

    // AI Generation states
    const [showAIModal, setShowAIModal] = useState(false)
    const [availableProperties, setAvailableProperties] = useState<any[]>([])
    const [selectedProperty, setSelectedProperty] = useState<string>('')
    const [selectedContentType, setSelectedContentType] = useState<string>('social_post')
    const [selectedLanguage, setSelectedLanguage] = useState<string>('en')
    const [customPrompt, setCustomPrompt] = useState<string>('')
    const [isGenerating, setIsGenerating] = useState(false)
    const [propertySearchTerm, setPropertySearchTerm] = useState<string>('')

    // Load content from unified APIs
    useEffect(() => {
        loadContent()
    }, [])

    // Load available properties for AI generation
    useEffect(() => {
        if (showAIModal) {
            loadAvailableProperties()
        }
    }, [showAIModal])

    // Pre-select property if provided and auto-open modal
    useEffect(() => {
        if (preselectedPropertyId && availableProperties.length > 0) {
            setSelectedProperty(preselectedPropertyId)
            // Auto-open the AI modal when property is pre-selected
            setShowAIModal(true)
        }
    }, [preselectedPropertyId, availableProperties])

    const loadAvailableProperties = async () => {
        try {
            const token = localStorage.getItem('auth_token')
            if (!token) return

            const response = await fetch('/api/v1/ai-content/properties', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                redirect: 'follow'  // Ensure redirects are followed
            })

            if (response.ok) {
                const properties = await response.json()
                setAvailableProperties(properties)
            }
        } catch (error) {
            console.error('Error loading properties:', error)
        }
    }

    const handleAIGenerate = async () => {
        if (!selectedProperty) {
            alert('Please select a property first')
            return
        }

        setIsGenerating(true)
        try {
            const token = localStorage.getItem('auth_token')
            if (!token) {
                alert('Authentication required')
                return
            }

            const response = await fetch('/api/v1/ai-content/generate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    property_id: selectedProperty,
                    content_type: selectedContentType,
                    language: selectedLanguage,
                    custom_prompt: customPrompt || undefined,
                    channels: ['facebook', 'instagram']
                }),
                redirect: 'follow'  // Ensure redirects are followed
            })

            if (response.ok) {
                const result = await response.json()
                console.log('AI content generated:', result)

                // Refresh content list
                await loadContent()

                // Close modal and reset form
                setShowAIModal(false)
                setSelectedProperty('')
                setCustomPrompt('')
                setPropertySearchTerm('')
                // Clear preselected property
                if (onClearPreselectedProperty) {
                    onClearPreselectedProperty()
                }

                alert('AI content generated successfully!')
            } else {
                throw new Error('Failed to generate content')
            }
        } catch (error) {
            console.error('Error generating AI content:', error)
            alert('Failed to generate AI content. Please try again.')
        } finally {
            setIsGenerating(false)
        }
    }

    const loadContent = async () => {
        setLoading(true)
        try {
            // Get auth token for authenticated requests
            const token = localStorage.getItem('auth_token')
            if (!token) {
                console.error('No auth token found')
                setContentItems([])
                return
            }

            // Load content from our new unified APIs with authentication
            const timestamp = Date.now() // Cache buster
            const [contentResponse, publishingLogsResponse] = await Promise.all([
                fetch(`/api/v1/content/?_t=${timestamp}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }),
                fetch(`/api/v1/publishing-logs/?_t=${timestamp}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                })
            ])

            if (!contentResponse.ok) {
                throw new Error(`Content API error: ${contentResponse.status}`)
            }

            const contentData = await contentResponse.json()
            const publishingLogsData = publishingLogsResponse.ok ? await publishingLogsResponse.json() : []

            console.log('Content API Response:', contentData)
            console.log('Publishing Logs API Response:', publishingLogsData)

            // Transform API data to our ContentItem format
            const transformedContent: ContentItem[] = contentData.map((item: any) => ({
                id: item.content_id || item._id || item.id,
                content_type: mapContentType(item.content_type),
                title: item.title,
                description: (item.content || item.body || '')?.substring(0, 100) + '...',
                status: mapPublishingStatus(item.status),
                channels: item.channels || [],
                scheduled_at: item.scheduled_at,
                published_at: item.published_at,
                created_at: item.created_at,
                updated_at: item.updated_at,
                thumbnail: item.media_urls?.[0] || item.media_ids?.[0],
                ai_generated: item.metadata?.ai_generated || item.is_draft || false
            }))

            setContentItems(transformedContent)
        } catch (error) {
            console.error('Error loading content:', error)
            // Fallback to empty array if API fails
            setContentItems([])
        } finally {
            setLoading(false)
        }
    }

    // Helper functions to map API data to our enums
    const mapContentType = (apiType: string): ContentType => {
        switch (apiType) {
            case 'property': return ContentType.PROPERTY
            case 'marketing_post': return ContentType.MARKETING_POST
            case 'ai_draft': return ContentType.AI_DRAFT
            case 'ai_facebook_post': return ContentType.AI_DRAFT
            case 'ai_instagram_post': return ContentType.AI_DRAFT
            case 'ai_website_post': return ContentType.AI_DRAFT
            case 'ai_social_post': return ContentType.AI_DRAFT
            default: return ContentType.ENHANCED_POST
        }
    }

    const mapPublishingStatus = (apiStatus: string): PublishingStatus => {
        switch (apiStatus) {
            case 'draft': return PublishingStatus.DRAFT
            case 'scheduled': return PublishingStatus.SCHEDULED
            case 'published': return PublishingStatus.PUBLISHED
            case 'failed': return PublishingStatus.FAILED
            default: return PublishingStatus.DRAFT
        }
    }

    // Filter properties based on search term
    const filteredProperties = availableProperties.filter(property => {
        if (!propertySearchTerm) return true
        const searchLower = propertySearchTerm.toLowerCase()
        return (
            property.title?.toLowerCase().includes(searchLower) ||
            property.location?.toLowerCase().includes(searchLower) ||
            property.property_type?.toLowerCase().includes(searchLower)
        )
    })

    // Filter content based on selected filters
    const filteredItems = contentItems.filter(item => {
        const statusMatch = filterStatus === 'all' || item.status === filterStatus
        const typeMatch = filterType === 'all' || item.content_type === filterType
        return statusMatch && typeMatch
    })

    const toggleItemSelection = (itemId: string) => {
        setSelectedItems(prev =>
            prev.includes(itemId)
                ? prev.filter(id => id !== itemId)
                : [...prev, itemId]
        )
    }

    const selectAllVisible = () => {
        const visibleIds = filteredItems.map(item => item.id)
        setSelectedItems(visibleIds)
    }

    const clearSelection = () => {
        setSelectedItems([])
    }

    const handlePublishSuccess = () => {
        // Refresh content after successful publishing
        loadContent()
        // Clear selection
        setSelectedItems([])
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading content...</p>
                </div>
            </div>
        )
    }

    return (
        <>
            <div className="max-w-7xl mx-auto p-6">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Property Marketing Hub</h1>
                            <p className="text-gray-600 mt-1">Unified workspace for property management, content creation, and publishing</p>
                        </div>

                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => setShowAIModal(true)}
                                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                            >
                                <SparklesIcon className="w-4 h-4" />
                                AI Generate
                            </button>
                            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                                <Plus className="w-4 h-4" />
                                Create Content
                            </button>

                            <button
                                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                {viewMode === 'grid' ? <List className="w-5 h-5" /> : <Grid className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Total Content</p>
                                    <p className="text-2xl font-bold text-gray-900">{contentItems.length}</p>
                                </div>
                                <div className="p-2 bg-blue-100 rounded-lg">
                                    <Globe className="w-5 h-5 text-blue-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Published</p>
                                    <p className="text-2xl font-bold text-green-600">
                                        {contentItems.filter(item => item.status === PublishingStatus.PUBLISHED).length}
                                    </p>
                                </div>
                                <div className="p-2 bg-green-100 rounded-lg">
                                    <CheckCircle className="w-5 h-5 text-green-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Scheduled</p>
                                    <p className="text-2xl font-bold text-blue-600">
                                        {contentItems.filter(item => item.status === PublishingStatus.SCHEDULED).length}
                                    </p>
                                </div>
                                <div className="p-2 bg-blue-100 rounded-lg">
                                    <Calendar className="w-5 h-5 text-blue-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Drafts</p>
                                    <p className="text-2xl font-bold text-gray-600">
                                        {contentItems.filter(item => item.status === PublishingStatus.DRAFT).length}
                                    </p>
                                </div>
                                <div className="p-2 bg-gray-100 rounded-lg">
                                    <Clock className="w-5 h-5 text-gray-600" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="bg-white rounded-lg border border-gray-200">
                    <div className="p-4 border-b border-gray-200">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <select
                                    value={filterStatus}
                                    onChange={(e) => setFilterStatus(e.target.value as PublishingStatus | 'all')}
                                    className="border border-gray-300 rounded px-3 py-1 text-sm"
                                >
                                    <option value="all">All Status</option>
                                    <option value={PublishingStatus.DRAFT}>Draft</option>
                                    <option value={PublishingStatus.SCHEDULED}>Scheduled</option>
                                    <option value={PublishingStatus.PUBLISHED}>Published</option>
                                    <option value={PublishingStatus.FAILED}>Failed</option>
                                </select>

                                <select
                                    value={filterType}
                                    onChange={(e) => setFilterType(e.target.value as ContentType | 'all')}
                                    className="border border-gray-300 rounded px-3 py-1 text-sm"
                                >
                                    <option value="all">All Types</option>
                                    <option value={ContentType.PROPERTY}>Properties</option>
                                    <option value={ContentType.ENHANCED_POST}>Marketing Posts</option>
                                    <option value={ContentType.AI_DRAFT}>AI Generated</option>
                                </select>
                            </div>

                            {selectedItems.length > 0 && (
                                <div className="flex items-center gap-3">
                                    <span className="text-sm text-gray-600">
                                        {selectedItems.length} selected
                                    </span>
                                    <PublishDraftsButton
                                        draftIds={selectedItems}
                                        onPublishSuccess={handlePublishSuccess}
                                        className="px-3 py-1 text-sm"
                                    />
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="p-4">
                        {contentItems.length === 0 ? (
                            <div className="text-center py-12">
                                <Globe className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-gray-900 mb-2">No content found</h3>
                                <p className="text-gray-600 mb-4">Create your first piece of content to get started.</p>
                                <button
                                    onClick={() => setShowAIModal(true)}
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                                >
                                    <SparklesIcon className="w-4 h-4" />
                                    Generate AI Content
                                </button>
                            </div>
                        ) : (
                            <div className={viewMode === 'grid'
                                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                                : 'space-y-4'
                            }>
                                {filteredItems.map((item) => (
                                    <div
                                        key={item.id}
                                        className={`border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow ${selectedItems.includes(item.id) ? 'ring-2 ring-blue-500' : ''
                                            }`}
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <div className="flex items-center gap-2">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedItems.includes(item.id)}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setSelectedItems(prev => [...prev, item.id])
                                                        } else {
                                                            setSelectedItems(prev => prev.filter(id => id !== item.id))
                                                        }
                                                    }}
                                                    className="rounded border-gray-300"
                                                />
                                                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig[item.status].bg} ${statusConfig[item.status].color}`}>
                                                    {(() => {
                                                        const IconComponent = statusConfig[item.status].icon;
                                                        return <IconComponent className="w-3 h-3" />;
                                                    })()}
                                                    {item.status}
                                                </span>
                                                {item.ai_generated && (
                                                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                                                        <SparklesIcon className="w-3 h-3" />
                                                        AI
                                                    </span>
                                                )}
                                            </div>
                                            <span className="text-xs text-gray-500">
                                                {contentTypeLabels[item.content_type]}
                                            </span>
                                        </div>

                                        <h3 className="font-medium text-gray-900 mb-2">{item.title}</h3>
                                        <p className="text-sm text-gray-600 mb-3">{item.description}</p>

                                        {item.thumbnail && (
                                            <div className="mb-3">
                                                <img
                                                    src={item.thumbnail}
                                                    alt={item.title}
                                                    className="w-full h-32 object-cover rounded"
                                                />
                                            </div>
                                        )}

                                        <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                                            <span>{new Date(item.created_at).toLocaleDateString()}</span>
                                            {item.scheduled_at && (
                                                <span>Scheduled: {new Date(item.scheduled_at).toLocaleDateString()}</span>
                                            )}
                                        </div>

                                        <div className="flex items-center justify-between">
                                            <div className="flex flex-wrap gap-1">
                                                {item.channels.map((channel) => (
                                                    <span
                                                        key={channel}
                                                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                                                    >
                                                        {channel}
                                                    </span>
                                                ))}
                                            </div>
                                            <div className="flex gap-1">
                                                <button className="p-1 text-gray-400 hover:text-gray-600">
                                                    <PencilIcon className="w-4 h-4" />
                                                </button>
                                                <button className="p-1 text-gray-400 hover:text-gray-600">
                                                    <TrashIcon className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* AI Generation Modal */}
            {showAIModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-900">AI Content Generation</h3>
                            <button
                                onClick={() => {
                                    setShowAIModal(false)
                                    setPropertySearchTerm('')
                                    // Clear preselected property
                                    if (onClearPreselectedProperty) {
                                        onClearPreselectedProperty()
                                    }
                                }}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Select Property
                                </label>

                                {/* Property Search */}
                                <div className="mb-2">
                                    <input
                                        type="text"
                                        placeholder="Search properties..."
                                        value={propertySearchTerm}
                                        onChange={(e) => setPropertySearchTerm(e.target.value)}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                {/* Property Selection */}
                                <div className="max-h-48 overflow-y-auto border border-gray-300 rounded-lg">
                                    {filteredProperties.length === 0 ? (
                                        <div className="p-3 text-sm text-gray-500 text-center">
                                            {propertySearchTerm ? 'No properties found matching your search' : 'No properties available'}
                                        </div>
                                    ) : (
                                        <div className="space-y-1 p-1">
                                            {filteredProperties.map((property) => (
                                                <div
                                                    key={property.id}
                                                    onClick={() => setSelectedProperty(property.id)}
                                                    className={`p-3 rounded-lg cursor-pointer transition-colors ${selectedProperty === property.id
                                                        ? 'bg-blue-50 border-2 border-blue-200'
                                                        : 'hover:bg-gray-50 border-2 border-transparent'
                                                        }`}
                                                >
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex-1">
                                                            <h4 className="font-medium text-gray-900 text-sm">
                                                                {property.title}
                                                            </h4>
                                                            <p className="text-xs text-gray-600 mt-1">
                                                                {property.location}
                                                            </p>
                                                            {property.property_type && (
                                                                <span className="inline-block mt-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                                                    {property.property_type}
                                                                </span>
                                                            )}
                                                        </div>
                                                        {property.price && (
                                                            <div className="text-right">
                                                                <p className="text-sm font-medium text-gray-900">
                                                                    ₹{(property.price / 100000).toFixed(0)}L
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Selected Property Display */}
                                {selectedProperty && (
                                    <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                                        <p className="text-xs text-blue-700">
                                            Selected: {availableProperties.find(p => p.id === selectedProperty)?.title}
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Content Type
                                </label>
                                <select
                                    value={selectedContentType}
                                    onChange={(e) => setSelectedContentType(e.target.value)}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="social_post">Social Media Post</option>
                                    <option value="property_description">Property Description</option>
                                    <option value="email_template">Email Template</option>
                                    <option value="ad_template">Advertisement</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Language
                                </label>
                                <select
                                    value={selectedLanguage}
                                    onChange={(e) => setSelectedLanguage(e.target.value)}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="en">English</option>
                                    <option value="hi">Hindi</option>
                                    <option value="ta">Tamil</option>
                                    <option value="te">Telugu</option>
                                    <option value="bn">Bengali</option>
                                    <option value="gu">Gujarati</option>
                                    <option value="kn">Kannada</option>
                                    <option value="ml">Malayalam</option>
                                    <option value="mr">Marathi</option>
                                    <option value="pa">Punjabi</option>
                                    <option value="ur">Urdu</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Custom Prompt (Optional)
                                </label>
                                <textarea
                                    value={customPrompt}
                                    onChange={(e) => setCustomPrompt(e.target.value)}
                                    placeholder="Add any specific requirements for the AI content..."
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    rows={3}
                                />
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={() => {
                                        setShowAIModal(false)
                                        setPropertySearchTerm('')
                                        // Clear preselected property
                                        if (onClearPreselectedProperty) {
                                            onClearPreselectedProperty()
                                        }
                                    }}
                                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleAIGenerate}
                                    disabled={!selectedProperty || isGenerating}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                                >
                                    {isGenerating ? (
                                        <>
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                            Generating...
                                        </>
                                    ) : (
                                        <>
                                            <SparklesIcon className="w-4 h-4" />
                                            Generate Content
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}
