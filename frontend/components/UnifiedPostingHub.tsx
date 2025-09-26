'use client'

import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  Edit3,
  Eye,
  Facebook,
  Globe,
  Heart,
  Instagram,
  Linkedin,
  MessageCircle,
  Plus,
  Settings,
  Share,
  Sparkles,
  Twitter,
  X,
  Clock,
  Calendar,
  Save,
  Copy,
  ExternalLink,
  AlertCircle
} from 'lucide-react'
import { useEffect, useState, useMemo, useCallback } from 'react'
import { apiService } from '@/lib/api/centralized-client'
import { STANDARD_LANGUAGES, getLanguageName } from '@/lib/languageConfig'
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

  const loadAvailableProperties = async () => {
    try {
      const data = await apiService.getProperties()
      setAvailableProperties(data.data || [])
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
      
      // Handle rate limiting
      if (error.status === 429) {
        setIsRateLimited(true)
        toast.error('Rate limit reached. Please wait a moment.')
        setTimeout(() => setIsRateLimited(false), 60000) // 1 minute
      } else {
        toast.error(errorMessage)
      }
    } finally {
      setIsGenerating(false)
    }
  }, [selectedProperty, mode, propertyData, selectedLanguage, selectedPlatforms, customPrompt, isRateLimited, onContentGenerated])

  const publishContent = useCallback(async () => {
    if (generatedContent.length === 0) {
      toast.error('No content to publish')
      return
    }

    setIsPublishing(true)
    setError(null)
    setPublishingStatus('publishing')

    try {
      const publishData = {
        content_type: "property",
        content_id: selectedProperty?.id || propertyData?.id,
        channels: selectedPlatforms,
        auto_translate: true,
        target_languages: [selectedLanguage],
        facebook_page_mappings: {}
      }

      const result = await apiService.publishContent(publishData)

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

  const handleEditContent = (content: GeneratedContent) => {
    setEditingContent(content)
  }

  const handleSaveEdit = (updatedContent: GeneratedContent) => {
    setGeneratedContent(prev =>
      prev.map(content =>
        content.id === updatedContent.id ? updatedContent : content
      )
    )
    setEditingContent(null)
  }

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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Sparkles className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              {mode === 'quick-post' && 'Quick Post Generator'}
              {mode === 'standalone' && 'AI Content Generator'}
              {mode === 'marketing-hub' && 'Marketing Content Hub'}
              {mode === 'property-creation' && 'Property Content Creator'}
            </h2>
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
                      Select Property
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
                            className={`w-full p-3 text-left hover:bg-gray-50 transition-colors ${
                              selectedProperty?.id === property.id
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
                          className={`p-4 rounded-xl border-2 transition-all duration-200 min-h-[80px] flex flex-col items-center justify-center ${
                            selectedPlatforms.includes(key)
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
                        className={`p-2 rounded-md text-sm font-medium transition-colors ${
                          selectedLanguage === lang.code
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
                <div className="flex justify-end">
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
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              content.status === 'draft' 
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
                            <button
                              onClick={() => handleEditContent(content)}
                              className="text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                            >
                              <Edit3 className="h-4 w-4" />
                              <span>Edit</span>
                            </button>
                          </div>
                        </div>
                        
                        {content.title && (
                          <h4 className="font-semibold text-gray-900 mb-2">{content.title}</h4>
                        )}
                        
                        <p className="text-gray-700 mb-3 whitespace-pre-wrap">
                          {content.content}
                        </p>
                        
                        {content.hashtags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {content.hashtags.map((tag, index) => (
                              <span
                                key={index}
                                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
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
                    className={`flex-1 px-6 py-3 rounded-lg font-medium flex items-center justify-center space-x-2 transition-all ${
                      isPublishing || generatedContent.length === 0
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