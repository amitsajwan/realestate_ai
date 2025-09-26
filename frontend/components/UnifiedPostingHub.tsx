'use client'

import { apiService } from '@/lib/api/centralized-client'
import { STANDARD_LANGUAGES, getLanguageName } from '@/lib/languageConfig'
import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  Clock,
  Copy,
  Facebook,
  Globe,
  Instagram,
  Linkedin,
  Save,
  Share,
  Sparkles,
  Twitter,
  X
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'

// Unified Types
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
  status?: string
}

interface GeneratedContent {
  id: string
  platform: 'website' | 'facebook' | 'instagram' | 'linkedin' | 'twitter'
  content: string
  title?: string
  hashtags: string[]
  media_urls: string[]
  status: 'draft' | 'ready' | 'published'
  created_at: string
  language: string
}

interface UnifiedPostingHubProps {
  // Mode determines the behavior and UI
  mode: 'quick-post' | 'standalone' | 'marketing-hub' | 'property-creation'

  // Property data (optional for standalone mode)
  propertyData?: PropertyData

  // Callbacks
  onContentGenerated?: (content: GeneratedContent[]) => void
  onPublish?: (content: GeneratedContent[], language?: string) => void
  onClose?: () => void

  // UI state
  isOpen?: boolean

  // Preselected options
  preselectedLanguage?: string
  preselectedPlatforms?: string[]
  preselectedProperty?: string
}

// Platform configurations
const PLATFORMS = {
  website: { name: 'Website', icon: Globe, color: 'text-blue-600' },
  facebook: { name: 'Facebook', icon: Facebook, color: 'text-blue-700' },
  instagram: { name: 'Instagram', icon: Instagram, color: 'text-pink-600' },
  linkedin: { name: 'LinkedIn', icon: Linkedin, color: 'text-blue-800' },
  twitter: { name: 'Twitter', icon: Twitter, color: 'text-blue-400' }
} as const

export default function UnifiedPostingHub({
  mode = 'quick-post',
  propertyData,
  onContentGenerated,
  onPublish,
  onClose,
  isOpen = true,
  preselectedLanguage = 'en',
  preselectedPlatforms = ['website', 'facebook', 'instagram'],
  preselectedProperty
}: UnifiedPostingHubProps) {
  console.log('[UnifiedPostingHub] Component props:', {
    mode,
    propertyData,
    isOpen,
    preselectedLanguage,
    preselectedPlatforms,
    preselectedProperty
  })
  // State management
  const [availableProperties, setAvailableProperties] = useState<PropertyData[]>([])
  const [selectedProperty, setSelectedProperty] = useState<PropertyData | null>(propertyData || null)
  const [selectedLanguage, setSelectedLanguage] = useState(preselectedLanguage)
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(preselectedPlatforms)
  const [customPrompt, setCustomPrompt] = useState('')
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState(1)
  const [editingContent, setEditingContent] = useState<GeneratedContent | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [isRateLimited, setIsRateLimited] = useState(false)
  const [publishingStatus, setPublishingStatus] = useState<'idle' | 'publishing' | 'success' | 'error'>('idle')
  const [showManualEditor, setShowManualEditor] = useState(false)
  const [manualContent, setManualContent] = useState<{
    title: string
    content: string
    hashtags: string[]
  }>({
    title: '',
    content: '',
    hashtags: []
  })
  const [savedDrafts, setSavedDrafts] = useState<GeneratedContent[]>([])
  const [showDraftManager, setShowDraftManager] = useState(false)

  // Load available properties for standalone and marketing-hub modes
  useEffect(() => {
    if (mode === 'standalone' || mode === 'marketing-hub') {
      loadAvailableProperties()
    }
  }, [mode])

  // Set preselected property
  useEffect(() => {
    if (preselectedProperty && availableProperties.length > 0) {
      const property = availableProperties.find(p => p.id === preselectedProperty)
      if (property) {
        setSelectedProperty(property)
      }
    }
  }, [preselectedProperty, availableProperties])

  // Debug logging for property data
  useEffect(() => {
    console.log('[UnifiedPostingHub] Debug info:', {
      mode,
      propertyData,
      selectedProperty,
      hasPropertyData: !!propertyData,
      hasSelectedProperty: !!selectedProperty
    })
  }, [mode, propertyData, selectedProperty])

  // Ensure property data is set when component receives it
  useEffect(() => {
    if (propertyData && !selectedProperty) {
      console.log('[UnifiedPostingHub] Setting property data from props:', propertyData)
      setSelectedProperty(propertyData)
    }
  }, [propertyData, selectedProperty])

  // Reset component state when opening in property-creation mode
  useEffect(() => {
    if (mode === 'property-creation' && isOpen) {
      console.log('[UnifiedPostingHub] Resetting state for property-creation mode')
      setCurrentStep(1)
      setGeneratedContent([])
      setError(null)
      setSuccess(null)
      setPublishingStatus('idle')
      setIsGenerating(false)
      setIsPublishing(false)
      setEditingContent(null)
      setSearchTerm('')
      setIsRateLimited(false)
      setSavedDrafts([])
      setShowDraftManager(false)
    }
  }, [mode, isOpen])

  const loadAvailableProperties = async () => {
    try {
      const data = await apiService.getProperties()
      setAvailableProperties(Array.isArray(data) ? data : (data as any)?.data || [])
    } catch (error) {
      console.error('Error loading properties:', error)
    }
  }

  const generateContent = useCallback(async () => {
    if (!selectedProperty && mode !== 'standalone') {
      toast.error('Please select a property first')
      return
    }

    if (isRateLimited) {
      toast.error('Please wait before generating more content')
      return
    }

    setIsGenerating(true)
    setError(null)
    setSuccess(null)
    setPublishingStatus('idle')

    const startTime = performance.now()

    try {
      const requestData = {
        context: mode === 'property-creation' ? 'property_creation' : 'publishing',
        property_data: selectedProperty || propertyData,
        languages: [selectedLanguage],
        platforms: selectedPlatforms,
        custom_prompts: customPrompt ? { website: customPrompt } : undefined,
        generation_options: {
          tone: 'friendly',
          length: 'medium',
          include_hashtags: true,
          include_cta: true,
          max_title_length: mode === 'property-creation' ? 100 : 200
        }
      }

      console.log('=== UNIFIED POSTING HUB AI REQUEST ===')
      console.log('Mode:', mode)
      console.log('Request data:', requestData)
      console.log('=== END REQUEST ===')

      const result = await apiService.generateAIContent(requestData)

      console.log('=== UNIFIED POSTING HUB AI RESPONSE ===')
      console.log('Generated content:', result)
      console.log('=== END RESPONSE ===')

      // Transform unified API response to our GeneratedContent format
      const transformedContent: GeneratedContent[] = []

      if (result.content) {
        Object.entries(result.content).forEach(([platform, languages]: [string, any]) => {
          Object.entries(languages).forEach(([lang, content]: [string, any]) => {
            transformedContent.push({
              id: `${platform}-${lang}-${Date.now()}`,
              platform: platform as any,
              content: content.body || content.content || '',
              title: content.title || '',
              hashtags: content.hashtags || ['#RealEstate', '#Property', '#DreamHome'],
              media_urls: selectedProperty?.images || [],
              status: 'draft',
              created_at: new Date().toISOString(),
              language: lang
            })
          })
        })
      }

      setGeneratedContent(transformedContent)
      setCurrentStep(2)

      // Track performance
      const duration = performance.now() - startTime
      console.log(`Content generation took ${duration.toFixed(2)}ms`)

      toast.success('Content generated successfully!')
      setSuccess('Content generated successfully!')

      if (onContentGenerated) {
        onContentGenerated(transformedContent)
      }
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate content'
      setError(errorMessage)
      console.error('Error generating content:', error)

      // Handle rate limiting and show manual editor as fallback
      if (error.status === 429 || errorMessage.includes('Rate limit') || errorMessage.includes('rate limit')) {
        setIsRateLimited(true)
        setShowManualEditor(true)
        toast.error('AI rate limit reached. You can create content manually below.')
      } else {
        toast.error(errorMessage)
        // Show manual editor as fallback for any AI generation failure
        setShowManualEditor(true)
        toast('AI generation failed. You can create content manually below.')
      }
    } finally {
      setIsGenerating(false)
    }
  }, [selectedProperty, mode, propertyData, selectedLanguage, selectedPlatforms, customPrompt, isRateLimited, onContentGenerated])

  const createManualContent = useCallback(() => {
    if (!manualContent.title.trim() || !manualContent.content.trim()) {
      toast.error('Please enter both title and content')
      return
    }

    const manualGeneratedContent: GeneratedContent[] = selectedPlatforms.map(platform => ({
      id: `manual_${platform}_${Date.now()}`,
      platform: platform as 'website' | 'facebook' | 'instagram' | 'linkedin' | 'twitter',
      language: selectedLanguage,
      title: manualContent.title,
      content: manualContent.content,
      hashtags: manualContent.hashtags,
      status: 'ready' as const,
      ai_generated: false,
      media_urls: [],
      created_at: new Date().toISOString()
    }))

    console.log('[UnifiedPostingHub] Manual content created:', JSON.stringify(manualGeneratedContent, null, 2))
    setGeneratedContent(manualGeneratedContent)
    setShowManualEditor(false)
    setCurrentStep(2)
    toast.success('Manual content created successfully!')
  }, [manualContent, selectedPlatforms, selectedLanguage])

  const handleEditContent = useCallback((content: GeneratedContent) => {
    setEditingContent(content)
    setManualContent({
      title: content.title || '',
      content: content.content || '',
      hashtags: content.hashtags || []
    })
    setShowManualEditor(true)
  }, [])

  const saveEditedContent = useCallback(() => {
    if (!editingContent || !manualContent.title.trim() || !manualContent.content.trim()) {
      toast.error('Please enter both title and content')
      return
    }

    setGeneratedContent(prev => prev.map(content =>
      content.id === editingContent.id
        ? {
          ...content,
          title: manualContent.title,
          content: manualContent.content,
          hashtags: manualContent.hashtags
        }
        : content
    ))

    setEditingContent(null)
    setShowManualEditor(false)
    setManualContent({ title: '', content: '', hashtags: [] })
    toast.success('Content updated successfully!')
  }, [editingContent, manualContent])

  const publishContent = useCallback(async () => {
    if (generatedContent.length === 0) {
      toast.error('No content to publish')
      return
    }

    // Check if all content is empty
    const hasValidContent = generatedContent.some(content =>
      content.content && content.content.trim() !== ''
    )

    if (!hasValidContent) {
      toast.error('No valid content to publish. Please create content manually.')
      setShowManualEditor(true)
      return
    }

    setIsPublishing(true)
    setError(null)
    setPublishingStatus('publishing')

    try {
      // Prepare content for each platform
      const contentForPublishing = generatedContent
        .filter(content => selectedPlatforms.includes(content.platform))
        .map(content => ({
          platform: content.platform,
          title: content.title,
          content: content.content,
          hashtags: content.hashtags,
          language: content.language
        }))

      const publishData = {
        content_type: "property",
        content_id: selectedProperty?.id || propertyData?.id,
        channels: selectedPlatforms,
        auto_translate: true,
        target_languages: [selectedLanguage],
        facebook_page_mappings: {},
        schedule_at: new Date().toISOString(),  // Send current time for immediate publishing
        content: contentForPublishing  // Include the actual content to publish
      }

      console.log('[UnifiedPostingHub] Publishing with data:', JSON.stringify(publishData, null, 2))
      const result = await apiService.publishContent(publishData)

      // Create a post record in the database for the Posts Management Hub
      try {
        console.log('[UnifiedPostingHub] Generated content array:', JSON.stringify(generatedContent, null, 2))
        console.log('[UnifiedPostingHub] Selected platforms:', selectedPlatforms)

        // Create a post record for each platform
        for (const contentItem of generatedContent) {
          console.log('[UnifiedPostingHub] Processing content item:', JSON.stringify(contentItem, null, 2))

          if (selectedPlatforms.includes(contentItem.platform)) {
            // Validate content before creating post
            if (!contentItem.content || contentItem.content.trim() === '') {
              console.error('[UnifiedPostingHub] Content is empty for platform:', contentItem.platform)
              // Use a fallback content instead of skipping
              contentItem.content = 'Content published successfully'
            }

            const postData = {
              property_id: selectedProperty?.id || propertyData?.id,
              title: contentItem.title || 'AI Generated Content',
              content: contentItem.content || 'Content published successfully',
              language: contentItem.language || selectedLanguage,
              channels: [contentItem.platform],
              ai_generated: contentItem.ai_generated || false, // Use the actual ai_generated flag from content
              ai_prompt: contentItem.ai_generated ? 'AI generated content for publishing' : undefined, // Don't send ai_prompt for manual content
              hashtags: contentItem.hashtags || [],
              tags: [], // Add required fields
              media_urls: [] // Add required fields
            }

            console.log('[UnifiedPostingHub] Raw contentItem:', JSON.stringify(contentItem, null, 2))
            console.log('[UnifiedPostingHub] Constructed postData:', JSON.stringify(postData, null, 2))

            // Final validation - ensure content is never empty
            if (!postData.content || postData.content.trim() === '') {
              console.error('[UnifiedPostingHub] Post data content is still empty, using fallback')
              postData.content = 'Content published successfully'
            }

            console.log('[UnifiedPostingHub] Creating post record for platform:', contentItem.platform, JSON.stringify(postData, null, 2))
            await apiService.createPost(postData)
            console.log('[UnifiedPostingHub] Post record created successfully for platform:', contentItem.platform)
          }
        }

        // Refresh the Posts Management Hub if it's available
        if ((window as any).refreshPostsManagementHub) {
          console.log('[UnifiedPostingHub] Refreshing Posts Management Hub...')
            ; (window as any).refreshPostsManagementHub()
        }
      } catch (postError) {
        console.error('[UnifiedPostingHub] Error creating post record:', postError)
        // Don't fail the entire operation if post creation fails
      }

      // Update status to published
      setGeneratedContent(prev =>
        prev.map(content =>
          selectedPlatforms.includes(content.platform)
            ? { ...content, status: 'published' as const }
            : content
        )
      )

      setPublishingStatus('success')
      setSuccess('Content published successfully!')
      setCurrentStep(3)

      toast.success('Content published successfully!')

      if (onPublish) {
        onPublish(generatedContent, selectedLanguage)
      }
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to publish content'
      setError(errorMessage)
      setPublishingStatus('error')
      console.error('Error publishing content:', error)
      toast.error(errorMessage)
    } finally {
      setIsPublishing(false)
    }
  }, [generatedContent, selectedProperty, propertyData, selectedPlatforms, selectedLanguage, onPublish])

  const saveAsDraft = useCallback(async () => {
    if (generatedContent.length === 0) {
      toast.error('No content to save')
      return
    }

    try {
      for (const content of generatedContent) {
        const postData = {
          property_id: selectedProperty?.id || propertyData?.id,
          title: content.title || '',
          content: content.content,
          language: content.language,
          channels: [content.platform],
          ai_generated: true,
          ai_prompt: customPrompt || 'AI generated content',
          hashtags: content.hashtags,
          status: 'draft'
        }

        await apiService.createPost(postData)
      }

      // Add to local drafts
      setSavedDrafts(prev => [...prev, ...generatedContent])
      setSuccess('Content saved as draft!')
      toast.success('Content saved as draft!')
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to save draft'
      setError(errorMessage)
      console.error('Error saving draft:', error)
      toast.error(errorMessage)
    }
  }, [generatedContent, selectedProperty, propertyData, customPrompt])

  const copyToClipboard = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Content copied to clipboard!')
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
      toast.error('Failed to copy to clipboard')
    }
  }, [])

  const filteredProperties = useMemo(() => {
    if (!searchTerm) return availableProperties
    return availableProperties.filter(property =>
      property.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      property.location.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [availableProperties, searchTerm])


  const handlePlatformToggle = (platform: string) => {
    setSelectedPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    )
  }

  const handleLanguageToggle = (language: string) => {
    setSelectedLanguage(language)
  }

  const resetForm = () => {
    setSelectedProperty(null)
    setSelectedLanguage(preselectedLanguage)
    setSelectedPlatforms(preselectedPlatforms)
    setCustomPrompt('')
    setGeneratedContent([])
    setError(null)
    setSuccess(null)
    setCurrentStep(1)
  }

  console.log('[UnifiedPostingHub] Render check - isOpen:', isOpen, 'currentStep:', currentStep, 'mode:', mode)
  if (!isOpen) {
    console.log('[UnifiedPostingHub] Component not rendering - isOpen is false')
    return null
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
        data-testid="unified-posting-hub"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Sparkles className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900" data-testid="hub-title">
              {mode === 'quick-post' && 'Quick Post Generator'}
              {mode === 'standalone' && 'AI Content Generator'}
              {mode === 'marketing-hub' && 'Property Marketing Hub'}
              {mode === 'property-creation' && 'Property Content Creator'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {mode === 'standalone' && 'Create new content from scratch using AI'}
              {mode === 'marketing-hub' && 'Manage marketing content for your properties'}
              {mode === 'property-creation' && 'Generate content for your newly created property'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <AnimatePresence mode="wait">
            {/* Step 1: Configuration */}
            {currentStep === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                {/* Property Selection (for standalone and marketing-hub modes) */}
                {(mode === 'standalone' || mode === 'marketing-hub') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {mode === 'marketing-hub' ? 'Select Property for Marketing' : 'Select Property for Content Creation'}
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="Search properties..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      {searchTerm && (
                        <button
                          onClick={() => setSearchTerm('')}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                    <div className="mt-2 max-h-48 overflow-y-auto border border-gray-300 rounded-md">
                      {filteredProperties.length === 0 ? (
                        <div className="p-3 text-sm text-gray-500 text-center">
                          {searchTerm ? 'No properties found' : 'No properties available'}
                        </div>
                      ) : (
                        filteredProperties.map((property) => (
                          <button
                            key={property.id}
                            onClick={() => setSelectedProperty(property)}
                            className={`w-full p-3 text-left hover:bg-gray-50 transition-colors ${selectedProperty?.id === property.id
                              ? 'bg-blue-50 border-l-4 border-blue-500'
                              : 'border-l-4 border-transparent'
                              }`}
                          >
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-medium text-gray-900">{property.title}</div>
                                <div className="text-sm text-gray-600">{property.location}</div>
                                <div className="text-xs text-gray-500">{property.propertyType}</div>
                              </div>
                              <div className="text-right">
                                <div className="font-semibold text-gray-900">₹{(property.price / 100000).toFixed(0)}L</div>
                                <div className="text-xs text-gray-500">{property.bedrooms} bed • {property.bathrooms} bath</div>
                              </div>
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                    {selectedProperty && (
                      <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-medium text-blue-900">Selected Property</div>
                            <div className="text-sm text-blue-700">{selectedProperty.title}</div>
                          </div>
                          <button
                            onClick={() => setSelectedProperty(null)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Property Display (for property-creation mode) */}
                {mode === 'property-creation' && selectedProperty && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Property for Content Generation
                    </label>
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span className="text-sm font-medium text-green-800">Newly Created Property</span>
                          </div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-1">{selectedProperty.title}</h3>
                          <div className="text-sm text-gray-600 mb-2">{selectedProperty.location}</div>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>{selectedProperty.propertyType}</span>
                            <span>•</span>
                            <span>{selectedProperty.bedrooms} bed • {selectedProperty.bathrooms} bath</span>
                            <span>•</span>
                            <span className="font-semibold text-green-700">₹{(selectedProperty.price / 100000).toFixed(0)}L</span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                            <CheckCircle className="h-6 w-6 text-green-600" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Platform Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Select Platforms
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {Object.entries(PLATFORMS).map(([key, platform]) => {
                      const Icon = platform.icon
                      return (
                        <motion.button
                          key={key}
                          onClick={() => handlePlatformToggle(key)}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          className={`p-4 rounded-xl border-2 transition-all duration-200 min-h-[80px] flex flex-col items-center justify-center ${selectedPlatforms.includes(key)
                            ? 'border-blue-500 bg-blue-50 shadow-md'
                            : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                            }`}
                        >
                          <Icon className={`h-6 w-6 mb-2 ${platform.color}`} />
                          <span className="text-sm font-medium text-gray-700">
                            {platform.name}
                          </span>
                        </motion.button>
                      )
                    })}
                  </div>
                </div>

                {/* Language Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Select Language
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {STANDARD_LANGUAGES.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => handleLanguageToggle(lang.code)}
                        className={`p-2 rounded-md text-sm font-medium transition-colors ${selectedLanguage === lang.code
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                      >
                        {lang.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom Prompt */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Custom Prompt (Optional)
                  </label>
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="Add specific instructions for content generation..."
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                  />
                </div>

                {/* Error/Success Messages */}
                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}

                {success && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-600">{success}</p>
                  </div>
                )}

                {/* Generate Button */}
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowManualEditor(true)}
                    className="px-6 py-3 bg-gray-600 text-white rounded-md hover:bg-gray-700 flex items-center space-x-2"
                  >
                    <span>Create Manually</span>
                  </button>
                  <button
                    onClick={generateContent}
                    disabled={isGenerating || (!selectedProperty && mode !== 'property-creation')}
                    className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {isGenerating ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        <span>Generate Content</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Manual Content Editor - Fallback when AI fails or for editing */}
                {showManualEditor && (
                  <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center space-x-2 mb-4">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                      <h3 className="text-lg font-medium text-yellow-800">
                        {editingContent ? 'Edit Content' : 'Manual Content Editor'}
                      </h3>
                    </div>
                    <p className="text-sm text-yellow-700 mb-4">
                      {editingContent
                        ? 'Edit your content below. Changes will be saved to the existing content.'
                        : 'AI generation is currently unavailable. You can create your content manually below.'
                      }
                    </p>

                    <div className="space-y-4">
                      {/* Title Input */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Post Title *
                        </label>
                        <input
                          type="text"
                          value={manualContent.title}
                          onChange={(e) => setManualContent(prev => ({ ...prev, title: e.target.value }))}
                          placeholder="Enter a compelling title for your post..."
                          className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      {/* Content Input */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Post Content *
                        </label>
                        <textarea
                          value={manualContent.content}
                          onChange={(e) => setManualContent(prev => ({ ...prev, content: e.target.value }))}
                          placeholder="Write your post content here... Be engaging and include relevant details about the property."
                          className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          rows={6}
                        />
                      </div>

                      {/* Hashtags Input */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Hashtags (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={manualContent.hashtags.join(', ')}
                          onChange={(e) => setManualContent(prev => ({
                            ...prev,
                            hashtags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                          }))}
                          placeholder="realestate, luxury, downtown, investment"
                          className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      {/* Action Buttons */}
                      <div className="flex justify-end space-x-3">
                        <button
                          onClick={() => {
                            setShowManualEditor(false)
                            setEditingContent(null)
                            setManualContent({ title: '', content: '', hashtags: [] })
                          }}
                          className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={editingContent ? saveEditedContent : createManualContent}
                          className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center space-x-2"
                        >
                          <span>{editingContent ? 'Save Changes' : 'Create Content'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 2: Generated Content */}
            {currentStep === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Generated Content
                  </h3>
                  <button
                    onClick={() => setCurrentStep(1)}
                    className="text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    <span>Back to Settings</span>
                  </button>
                </div>

                <div className="space-y-4">
                  {generatedContent.map((content) => {
                    const platform = PLATFORMS[content.platform as keyof typeof PLATFORMS]
                    const Icon = platform?.icon || Globe

                    return (
                      <div key={content.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <Icon className={`h-5 w-5 ${platform?.color || 'text-gray-600'}`} />
                            <span className="font-medium text-gray-900">
                              {platform?.name || content.platform}
                            </span>
                            <span className="text-sm text-gray-500">
                              ({getLanguageName(content.language)})
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${content.status === 'draft'
                              ? 'bg-gray-100 text-gray-700'
                              : content.status === 'published'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-blue-100 text-blue-700'
                              }`}>
                              {content.status}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => copyToClipboard(content.content)}
                              className="text-gray-600 hover:text-gray-700 p-1"
                              title="Copy content"
                            >
                              <Copy className="h-4 w-4" />
                            </button>
                          </div>
                        </div>

                        <div className="mb-3">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Title
                          </label>
                          <input
                            type="text"
                            value={content.title || ''}
                            onChange={(e) => {
                              console.log('[UnifiedPostingHub] Title changed for content ID:', content.id, 'New title:', e.target.value)
                              setGeneratedContent(prev => {
                                const updated = prev.map(c =>
                                  c.id === content.id
                                    ? { ...c, title: e.target.value }
                                    : c
                                )
                                console.log('[UnifiedPostingHub] Updated generatedContent after title change:', JSON.stringify(updated, null, 2))
                                return updated
                              })
                            }}
                            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter a compelling title..."
                          />
                        </div>

                        <div className="mb-3">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Content
                          </label>
                          <textarea
                            value={content.content}
                            onChange={(e) => {
                              console.log('[UnifiedPostingHub] Content changed for content ID:', content.id, 'New content:', e.target.value)
                              setGeneratedContent(prev => {
                                const updated = prev.map(c =>
                                  c.id === content.id
                                    ? { ...c, content: e.target.value }
                                    : c
                                )
                                console.log('[UnifiedPostingHub] Updated generatedContent after content change:', JSON.stringify(updated, null, 2))
                                return updated
                              })
                            }}
                            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            rows={4}
                            placeholder="Enter your content here..."
                          />
                        </div>

                        <div className="mb-3">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Hashtags (comma-separated)
                          </label>
                          <input
                            type="text"
                            value={content.hashtags.join(', ')}
                            onChange={(e) => {
                              const hashtags = e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                              setGeneratedContent(prev => prev.map(c =>
                                c.id === content.id
                                  ? { ...c, hashtags }
                                  : c
                              ))
                            }}
                            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="realestate, luxury, downtown, investment"
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={saveAsDraft}
                    className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 flex items-center justify-center space-x-2 transition-colors"
                  >
                    <Save className="h-4 w-4" />
                    <span>Save as Draft</span>
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={publishContent}
                    disabled={isPublishing || generatedContent.length === 0}
                    className={`flex-1 px-6 py-3 rounded-lg font-medium flex items-center justify-center space-x-2 transition-all ${isPublishing || generatedContent.length === 0
                      ? 'bg-gray-400 text-white cursor-not-allowed'
                      : publishingStatus === 'success'
                        ? 'bg-green-600 text-white'
                        : publishingStatus === 'error'
                          ? 'bg-red-600 text-white'
                          : 'bg-blue-600 text-white hover:bg-blue-700'
                      }`}
                  >
                    {isPublishing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Publishing...</span>
                      </>
                    ) : publishingStatus === 'success' ? (
                      <>
                        <CheckCircle className="h-4 w-4" />
                        <span>Published!</span>
                      </>
                    ) : publishingStatus === 'error' ? (
                      <>
                        <AlertCircle className="h-4 w-4" />
                        <span>Failed</span>
                      </>
                    ) : (
                      <>
                        <Share className="h-4 w-4" />
                        <span>Publish Now</span>
                      </>
                    )}
                  </motion.button>
                </div>

                {/* Draft Manager Toggle */}
                {savedDrafts.length > 0 && (
                  <div className="flex justify-center">
                    <button
                      onClick={() => setShowDraftManager(!showDraftManager)}
                      className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                    >
                      <Clock className="h-4 w-4" />
                      <span>View Saved Drafts ({savedDrafts.length})</span>
                    </button>
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 3: Success */}
            {currentStep === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="text-center space-y-6"
              >
                <div className="flex justify-center">
                  <CheckCircle className="h-16 w-16 text-green-500" />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Content Published Successfully!
                  </h3>
                  <p className="text-gray-600">
                    Your content has been published to the selected platforms.
                  </p>
                </div>

                <div className="flex justify-center space-x-4">
                  <button
                    onClick={resetForm}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Create More Content
                  </button>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Close
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}