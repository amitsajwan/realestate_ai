'use client'

import { apiService } from '@/lib/api/centralized-client'
import { STANDARD_LANGUAGES } from '@/lib/languageConfig'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowLeft,
  CheckCircle,
  Copy,
  Facebook,
  Globe,
  Instagram,
  Linkedin,
  Share,
  Sparkles,
  Twitter,
  X
} from 'lucide-react'
import { Reducer, useCallback, useEffect, useMemo, useReducer } from 'react'
import toast from 'react-hot-toast'
import ImageSelectionPanel from './ImageSelectionPanel'

// --- TYPE DEFINITIONS ---
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
  ai_generated?: boolean
}

interface UnifiedPostingHubProps {
  mode: 'quick-post' | 'standalone' | 'marketing-hub' | 'property-creation'
  propertyData?: PropertyData
  onContentGenerated?: (content: GeneratedContent[]) => void
  onPublish?: (content: GeneratedContent[], language?: string) => void
  onClose?: () => void
  isOpen?: boolean
  preselectedLanguage?: string
  preselectedPlatforms?: string[]
  preselectedProperty?: string
}

// --- CONSTANTS ---
const PLATFORMS = {
  website: { name: 'Website', icon: Globe, color: 'text-blue-600' },
  facebook: { name: 'Facebook', icon: Facebook, color: 'text-blue-700' },
  instagram: { name: 'Instagram', icon: Instagram, color: 'text-pink-600' },
  linkedin: { name: 'LinkedIn', icon: Linkedin, color: 'text-blue-800' },
  twitter: { name: 'Twitter', icon: Twitter, color: 'text-blue-400' }
} as const

// --- STATE MANAGEMENT (useReducer) ---
type State = {
  availableProperties: PropertyData[]
  selectedProperty: PropertyData | null
  selectedLanguage: string
  selectedPlatforms: string[]
  customPrompt: string
  generatedContent: GeneratedContent[]
  status: 'idle' | 'generating' | 'publishing' | 'error' | 'success'
  error: string | null
  success: string | null
  currentStep: number
  editingContent: GeneratedContent | null
  searchTerm: string
  isRateLimited: boolean
  publishingStatus: 'idle' | 'publishing' | 'success' | 'error'
  savedDrafts: GeneratedContent[]
  showDraftManager: boolean
  selectedImages: string[]
  showImageSelection: boolean
  imageSelectionMode: 'auto' | 'manual'
}

type Action =
  | { type: 'SET_PROPERTIES'; payload: PropertyData[] }
  | { type: 'SET_SELECTED_PROPERTY'; payload: PropertyData | null }
  | { type: 'SET_LANGUAGE'; payload: string }
  | { type: 'TOGGLE_PLATFORM'; payload: string }
  | { type: 'SET_CUSTOM_PROMPT'; payload: string }
  | { type: 'START_GENERATION' }
  | { type: 'GENERATION_SUCCESS'; payload: GeneratedContent[] }
  | { type: 'GENERATION_FAILURE'; payload: string; isRateLimited?: boolean }
  | { type: 'START_PUBLISHING' }
  | { type: 'PUBLISH_SUCCESS' }
  | { type: 'PUBLISH_FAILURE'; payload: string }
  | { type: 'UPDATE_CONTENT'; payload: GeneratedContent }
  | { type: 'SET_STEP'; payload: number }
  | { type: 'SET_SEARCH_TERM'; payload: string }
  | { type: 'SET_SELECTED_IMAGES'; payload: string[] }
  | { type: 'TOGGLE_IMAGE_SELECTION' }
  | { type: 'SET_IMAGE_SELECTION_MODE'; payload: 'auto' | 'manual' }
  | { type: 'RESET'; payload: Partial<State> }

const reducer: Reducer<State, Action> = (state, action) => {
  switch (action.type) {
    case 'SET_PROPERTIES':
      return { ...state, availableProperties: action.payload }
    case 'SET_SELECTED_PROPERTY':
      return { ...state, selectedProperty: action.payload, searchTerm: '' }
    case 'SET_LANGUAGE':
      return { ...state, selectedLanguage: action.payload }
    case 'TOGGLE_PLATFORM':
      const newPlatforms = state.selectedPlatforms.includes(action.payload)
        ? state.selectedPlatforms.filter(p => p !== action.payload)
        : [...state.selectedPlatforms, action.payload]
      return { ...state, selectedPlatforms: newPlatforms }
    case 'SET_CUSTOM_PROMPT':
      return { ...state, customPrompt: action.payload }
    case 'START_GENERATION':
      return { ...state, status: 'generating', error: null, success: null }
    case 'GENERATION_SUCCESS':
      return { ...state, status: 'success', generatedContent: action.payload, currentStep: 2, success: 'Content generated successfully!' }
    case 'GENERATION_FAILURE':
      return { ...state, status: 'error', error: action.payload, isRateLimited: action.isRateLimited ?? state.isRateLimited }
    case 'START_PUBLISHING':
      return { ...state, status: 'publishing', publishingStatus: 'publishing', error: null }
    case 'PUBLISH_SUCCESS':
      const publishedContent = state.generatedContent.map(content =>
        state.selectedPlatforms.includes(content.platform)
          ? { ...content, status: 'published' as const }
          : content
      )
      return { ...state, status: 'success', publishingStatus: 'success', generatedContent: publishedContent, currentStep: 3, success: 'Content published successfully!' }
    case 'PUBLISH_FAILURE':
      return { ...state, status: 'error', publishingStatus: 'error', error: action.payload }
    case 'UPDATE_CONTENT':
      const updatedContent = state.generatedContent.map(c => (c.id === action.payload.id ? action.payload : c))
      return { ...state, generatedContent: updatedContent }
    case 'SET_STEP':
      return { ...state, currentStep: action.payload }
    case 'SET_SEARCH_TERM':
      return { ...state, searchTerm: action.payload }
    case 'SET_SELECTED_IMAGES':
      return { ...state, selectedImages: action.payload }
    case 'TOGGLE_IMAGE_SELECTION':
      return { ...state, showImageSelection: !state.showImageSelection }
    case 'SET_IMAGE_SELECTION_MODE':
      return { ...state, imageSelectionMode: action.payload }
    case 'RESET':
      return { ...initialState, ...action.payload }
    default:
      return state
  }
}

const initialState: State = {
  availableProperties: [],
  selectedProperty: null,
  selectedLanguage: 'en',
  selectedPlatforms: ['website', 'facebook', 'instagram'],
  customPrompt: '',
  generatedContent: [],
  status: 'idle',
  error: null,
  success: null,
  currentStep: 1,
  editingContent: null,
  searchTerm: '',
  isRateLimited: false,
  publishingStatus: 'idle',
  savedDrafts: [],
  showDraftManager: false,
  selectedImages: [],
  showImageSelection: false,
  imageSelectionMode: 'auto',
}

// --- COMPONENT ---
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
  const [state, dispatch] = useReducer(reducer, {
    ...initialState,
    selectedProperty: propertyData || null,
    selectedLanguage: preselectedLanguage,
    selectedPlatforms: preselectedPlatforms
  })

  // Destructure state for easier access
  const {
    availableProperties,
    selectedProperty,
    selectedLanguage,
    selectedPlatforms,
    customPrompt,
    generatedContent,
    status,
    error,
    success,
    currentStep,
    searchTerm,
    isRateLimited,
    publishingStatus,
    selectedImages,
    imageSelectionMode
  } = state

  // Load available properties for standalone and marketing-hub modes
  useEffect(() => {
    if (mode === 'standalone' || mode === 'marketing-hub') {
      apiService
        .getProperties()
        .then(data => dispatch({ type: 'SET_PROPERTIES', payload: Array.isArray(data) ? data : (data as any)?.data || [] }))
        .catch(err => console.error('Error loading properties:', err))
    }
  }, [mode])

  // Set preselected property
  useEffect(() => {
    if (preselectedProperty && availableProperties.length > 0) {
      const property = availableProperties.find(p => p.id === preselectedProperty)
      if (property) {
        dispatch({ type: 'SET_SELECTED_PROPERTY', payload: property })
      }
    }
  }, [preselectedProperty, availableProperties])

  // Ensure property data is set when component receives it
  useEffect(() => {
    if (propertyData && !selectedProperty) {
      dispatch({ type: 'SET_SELECTED_PROPERTY', payload: propertyData })
    }
  }, [propertyData, selectedProperty])

  // Reset component state when opening in property-creation mode
  useEffect(() => {
    if (mode === 'property-creation' && isOpen) {
      dispatch({ type: 'RESET', payload: { selectedProperty: propertyData || null } })
    }
  }, [mode, isOpen, propertyData])

  // Auto-select images when property or platforms change
  useEffect(() => {
    const images = selectedProperty?.images || propertyData?.images
    if (images && images.length > 0 && imageSelectionMode === 'auto') {
      const maxImages = Math.min(
        ...selectedPlatforms.map(platform => {
          const limits = { instagram: 10, facebook: 20, linkedin: 9, twitter: 4, website: 50 }
          return limits[platform as keyof typeof limits] || 10
        })
      )
      const autoSelected = images.slice(0, maxImages)
      dispatch({ type: 'SET_SELECTED_IMAGES', payload: autoSelected })
    }
  }, [selectedProperty, propertyData, selectedPlatforms, imageSelectionMode])

  const populateContentWithPropertyData = useCallback(() => {
    const property = selectedProperty || propertyData
    if (!property) {
      toast.error('No property data available for fallback content generation')
      return
    }

    const platformsToUse = selectedPlatforms.length > 0 ? selectedPlatforms : Object.keys(PLATFORMS)
    const populatedContent: GeneratedContent[] = platformsToUse.map(platform => {
      const isPlaceholderDescription = !property.description || property.description.trim() === '' || property.description.includes('AI-generated description')

      const content = isPlaceholderDescription
        ? `🏡 ${property.title} in ${property.location}!\n\nThis beautiful ${property.propertyType} features ${property.bedrooms} bedrooms and ${property.bathrooms} bathrooms.\n\n💰 Price: ₹${(property.price / 100000).toFixed(0)}L\n📍 Location: ${property.location}\n🏠 ${property.bedrooms} bed • ${property.bathrooms} bath\n\nContact me for more details! 📞`
        : property.description!

      const hashtags = ['#realestate', `#${property.location?.toLowerCase().replace(/\s+/g, '')}`].filter(Boolean)

      return {
        id: `populated_${platform}_${Date.now()}`,
        platform: platform as any,
        content,
        title: property.title,
        hashtags,
        media_urls: selectedImages.length > 0 ? selectedImages : (property.images || []),
        status: 'draft',
        created_at: new Date().toISOString(),
        language: selectedLanguage,
        ai_generated: false
      }
    })

    dispatch({ type: 'GENERATION_SUCCESS', payload: populatedContent })
    toast.success('Content populated from property data!')
    onContentGenerated?.(populatedContent)

  }, [selectedProperty, propertyData, selectedPlatforms, selectedLanguage, selectedImages, onContentGenerated])

  // Auto-populate content effect
  useEffect(() => {
    if ((selectedProperty || propertyData) && generatedContent.length === 0 && selectedPlatforms.length > 0 && currentStep === 1) {
      populateContentWithPropertyData()
    }
  }, [selectedProperty, propertyData, selectedPlatforms.length, generatedContent.length, currentStep, populateContentWithPropertyData])

  const generateContent = useCallback(async () => {
    if (!selectedProperty) {
      toast.error('Please select a property first')
      return
    }
    if (isRateLimited) {
      toast.error('Please wait before generating more content')
      return
    }

    dispatch({ type: 'START_GENERATION' })

    try {
      const requestData = {
        context: mode === 'property-creation' ? 'property_creation' : 'publishing',
        property_data: selectedProperty,
        languages: [selectedLanguage],
        platforms: selectedPlatforms,
        custom_prompts: customPrompt ? { website: customPrompt } : undefined
      }

      const result = await apiService.generateAIContent(requestData)

      const transformedContent: GeneratedContent[] = []
      if (result.content) {
        Object.entries(result.content).forEach(([platform, languages]: [string, any]) => {
          Object.entries(languages).forEach(([lang, content]: [string, any]) => {
            transformedContent.push({
              id: `${platform}-${lang}-${Date.now()}`,
              platform: platform as any,
              content: content.body || content.content || '',
              title: content.title || '',
              hashtags: content.hashtags || [],
              media_urls: selectedImages.length > 0 ? selectedImages : (selectedProperty?.images || []),
              status: 'draft',
              created_at: new Date().toISOString(),
              language: lang,
              ai_generated: true
            })
          })
        })
      }

      dispatch({ type: 'GENERATION_SUCCESS', payload: transformedContent })
      onContentGenerated?.(transformedContent)

    } catch (err: any) {
      const errorMessage = err.message || 'Failed to generate content'
      dispatch({ type: 'GENERATION_FAILURE', payload: errorMessage, isRateLimited: err.statusCode === 429 })
      toast.error(errorMessage)
      populateContentWithPropertyData() // Fallback
    }
  }, [selectedProperty, mode, selectedLanguage, selectedPlatforms, customPrompt, isRateLimited, onContentGenerated, populateContentWithPropertyData, selectedImages])

  const publishContent = useCallback(async () => {
    if (generatedContent.length === 0) {
      toast.error('No content to publish')
      return
    }
    dispatch({ type: 'START_PUBLISHING' })

    try {
      const contentForPublishing = generatedContent
        .filter(c => selectedPlatforms.includes(c.platform))
        .map(c => ({ ...c }))

      const publishData = {
        content_type: "property",
        content_id: selectedProperty?.id,
        channels: selectedPlatforms,
        content: contentForPublishing
      }

      await apiService.publishContent(publishData)

      for (const contentItem of contentForPublishing) {
        await apiService.createPost({
          property_id: selectedProperty?.id,
          title: contentItem.title || 'AI Generated Content',
          content: contentItem.content,
          language: contentItem.language,
          channels: [contentItem.platform],
          ai_generated: contentItem.ai_generated,
          hashtags: contentItem.hashtags,
          tags: [],
          media_urls: contentItem.media_urls
        })
      }

      dispatch({ type: 'PUBLISH_SUCCESS' })
      toast.success('Content published successfully!')
      onPublish?.(generatedContent, selectedLanguage)

    } catch (err: any) {
      const errorMessage = err.message || 'Failed to publish content'
      dispatch({ type: 'PUBLISH_FAILURE', payload: errorMessage })
      toast.error(errorMessage)
    }
  }, [generatedContent, selectedProperty, selectedPlatforms, selectedLanguage, onPublish])

  const copyToClipboard = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Content copied to clipboard!')
    } catch (err) {
      toast.error('Failed to copy to clipboard')
    }
  }, [])

  const filteredProperties = useMemo(() => {
    if (!searchTerm) return availableProperties
    return availableProperties.filter(p =>
      p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.location.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [availableProperties, searchTerm])

  const isGenerating = status === 'generating'
  const isPublishing = status === 'publishing'

  if (!isOpen) return null

  // --- RENDER LOGIC ---
  const renderHeader = () => (
    <div className="flex items-center justify-between p-6 border-b border-gray-200">
      <div className="flex items-center space-x-3">
        <Sparkles className="h-6 w-6 text-blue-600" />
        <h2 className="text-xl font-semibold text-gray-900">
          {mode.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())} Hub
        </h2>
      </div>
      <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
        <X className="h-6 w-6" />
      </button>
    </div>
  )

  const renderStep1 = () => (
    <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
      {/* Property Selection */}
      {(mode === 'standalone' || mode === 'marketing-hub') && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Property</label>
          <input
            type="text"
            placeholder="Search properties..."
            value={searchTerm}
            onChange={(e) => dispatch({ type: 'SET_SEARCH_TERM', payload: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-md"
          />
          <div className="mt-2 max-h-48 overflow-y-auto border border-gray-300 rounded-md">
            {filteredProperties.map((property) => (
              <button
                key={property.id}
                onClick={() => dispatch({ type: 'SET_SELECTED_PROPERTY', payload: property })}
                className={`w-full p-3 text-left hover:bg-gray-50 ${selectedProperty?.id === property.id ? 'bg-blue-50' : ''}`}
              >
                <div className="font-medium text-gray-900">{property.title}</div>
                <div className="text-sm text-gray-600">{property.location}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Platform Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Platforms</label>
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
          {Object.entries(PLATFORMS).map(([key, { name, icon: Icon, color }]) => (
            <button
              key={key}
              onClick={() => dispatch({ type: 'TOGGLE_PLATFORM', payload: key })}
              className={`flex flex-col items-center justify-center p-3 border rounded-lg transition-all ${selectedPlatforms.includes(key) ? 'border-blue-500 bg-blue-50 shadow-sm' : 'border-gray-300 bg-white hover:border-gray-400'
                }`}
            >
              <Icon className={`h-6 w-6 mb-1 ${color}`} />
              <span className="text-sm font-medium text-gray-800">{name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Language Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Language</label>
        <select
          value={selectedLanguage}
          onChange={(e) => dispatch({ type: 'SET_LANGUAGE', payload: e.target.value })}
          className="w-full p-3 border border-gray-300 rounded-md bg-white"
        >
          {STANDARD_LANGUAGES.map(lang => (
            <option key={lang.code} value={lang.code}>{lang.name}</option>
          ))}
        </select>
      </div>

      {/* Custom Prompt */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Custom Prompt (Optional)</label>
        <textarea
          rows={2}
          value={customPrompt}
          onChange={(e) => dispatch({ type: 'SET_CUSTOM_PROMPT', payload: e.target.value })}
          placeholder="e.g., 'Make it sound more luxurious', 'Focus on the family-friendly aspects'"
          className="w-full p-3 border border-gray-300 rounded-md"
        />
      </div>
    </motion.div>
  )

  const renderStep2 = () => (
    <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={() => dispatch({ type: 'SET_STEP', payload: 1 })} className="flex items-center text-sm font-medium text-gray-600 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Configuration
        </button>
        <button onClick={generateContent} disabled={isGenerating} className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
          <Sparkles className="h-4 w-4 mr-2" />
          {isGenerating ? 'Regenerating...' : 'Regenerate'}
        </button>
      </div>
      {/* Image Selection for Generated Content */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">
            Select Images for Posts ({selectedImages.length} selected)
          </h3>
          <div className="flex space-x-2">
            <button
              onClick={() => dispatch({ type: 'SET_IMAGE_SELECTION_MODE', payload: 'auto' })}
              className={`px-3 py-1 text-sm rounded-md ${
                imageSelectionMode === 'auto' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Auto
            </button>
            <button
              onClick={() => dispatch({ type: 'SET_IMAGE_SELECTION_MODE', payload: 'manual' })}
              className={`px-3 py-1 text-sm rounded-md ${
                imageSelectionMode === 'manual' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Manual
            </button>
            <button
              onClick={() => dispatch({ type: 'TOGGLE_IMAGE_SELECTION' })}
              className="px-3 py-1 text-sm bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              {showImageSelection ? 'Hide' : 'Select Images'}
            </button>
          </div>
        </div>
        
        {showImageSelection && (
          <div className="mt-4">
            <ImageSelectionPanel
              propertyImages={selectedProperty?.images || propertyData?.images || []}
              selectedImages={selectedImages}
              onImageSelect={(images) => dispatch({ type: 'SET_SELECTED_IMAGES', payload: images })}
              platforms={selectedPlatforms}
            />
          </div>
        )}
      </div>

      <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-2">
        {generatedContent.map(content => {
          const platformInfo = PLATFORMS[content.platform as keyof typeof PLATFORMS];
          const Icon = platformInfo.icon
          return (
            <div key={content.id} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Icon className={`h-5 w-5 ${platformInfo.color}`} />
                  <h4 className="font-semibold text-gray-800">{platformInfo.name} Content</h4>
                </div>
                <button onClick={() => copyToClipboard(content.content)} className="text-gray-400 hover:text-gray-600"><Copy className="h-4 w-4" /></button>
              </div>
              {content.title && (
                <input
                  type="text"
                  value={content.title}
                  onChange={(e) => dispatch({ type: 'UPDATE_CONTENT', payload: { ...content, title: e.target.value } })}
                  className="w-full p-2 mb-2 font-semibold bg-white border border-gray-300 rounded-md"
                />
              )}
              <textarea
                value={content.content}
                onChange={(e) => dispatch({ type: 'UPDATE_CONTENT', payload: { ...content, content: e.target.value } })}
                rows={6}
                className="w-full p-2 bg-white border border-gray-300 rounded-md text-sm"
              />
              <p className="mt-2 text-xs text-gray-500">Hashtags: {content.hashtags.join(' ')}</p>
              <p className="mt-1 text-xs text-blue-600">Images: {selectedImages.length} selected</p>
            </div>
          );
        })}
      </div>
    </motion.div>
  )

  const renderStep3 = () => (
    <motion.div key="step3" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-12">
      <CheckCircle className="w-16 h-16 mx-auto text-green-500" />
      <h3 className="mt-4 text-2xl font-semibold text-gray-900">Published Successfully!</h3>
      <p className="mt-2 text-gray-600">Your content has been posted to the selected platforms.</p>
      <div className="mt-6">
        <button onClick={onClose} className="px-6 py-2 font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
          Close
        </button>
      </div>
    </motion.div>
  )

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {renderHeader()}
        <div className="p-6 overflow-y-auto flex-grow">
          <AnimatePresence mode="wait">
            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}
          </AnimatePresence>
        </div>

        {/* Footer */}
        {currentStep !== 3 && (
          <div className="flex items-center justify-end p-6 border-t border-gray-200 bg-gray-50 space-x-3">
            <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
              Cancel
            </button>
            {currentStep === 1 && (
              <button onClick={generateContent} disabled={isGenerating || !selectedProperty || selectedPlatforms.length === 0} className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
                <Sparkles className="h-4 w-4 mr-2" />
                {isGenerating ? 'Generating...' : 'Generate Content'}
              </button>
            )}
            {currentStep === 2 && (
              <button onClick={publishContent} disabled={isPublishing} className="flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50">
                <Share className="h-4 w-4 mr-2" />
                {isPublishing ? 'Publishing...' : 'Publish Now'}
              </button>
            )}
          </div>
        )}
      </motion.div>
    </div>
  )
}