'use client'

import { authManager } from '@/lib/auth'
import { propertiesAPI } from '@/lib/properties/api'
import {
    ArrowLeftIcon,
    ArrowRightIcon,
    BuildingOfficeIcon,
    CameraIcon,
    CheckIcon,
    CloudArrowUpIcon,
    CurrencyDollarIcon,
    MapPinIcon,
    SparklesIcon,
    XMarkIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import toast from 'react-hot-toast'

interface FormData {
    propertyAddress: string
    area: string
    city: string
    state: string
    pincode: string
    propertyType: string
    bedrooms: number
    bathrooms: number
    areaSqft: number
    price: number
    description: string
    images: string[]
    title: string
    amenities: string
}

interface AISuggestion {
    title: string
    description: string
    price?: number
    amenities?: string[]
}

const FORM_STEPS = [
    {
        id: 'location',
        title: 'Where is your property located?',
        description: 'Start by entering the property address. Our system will detect property type and market insights.',
        icon: MapPinIcon
    },
    {
        id: 'details',
        title: 'Property Details',
        description: 'Tell us more about your property features and specifications.',
        icon: BuildingOfficeIcon
    },
    {
        id: 'pricing',
        title: 'Pricing & Description',
        description: 'Set your asking price and add a compelling description.',
        icon: CurrencyDollarIcon
    },
    {
        id: 'images',
        title: 'Property Images',
        description: 'Upload high-quality photos to showcase your property.',
        icon: CameraIcon
    }
]

export default function MobilePropertyForm({ onSuccess }: { onSuccess?: () => void }) {
    const [currentStep, setCurrentStep] = useState(0)
    const [formData, setFormData] = useState<FormData>({
        propertyAddress: '',
        area: '',
        city: '',
        state: '',
        pincode: '',
        propertyType: '',
        bedrooms: 0,
        bathrooms: 0,
        areaSqft: 0,
        price: 0,
        description: '',
        images: [],
        title: '',
        amenities: ''
    })
    const [isGeneratingAI, setIsGeneratingAI] = useState(false)
    const [aiSuggestion, setAiSuggestion] = useState<AISuggestion | null>(null)
    const [uploadingImages, setUploadingImages] = useState(false)
    const [isLoading, setIsLoading] = useState(false)


    const nextStep = () => {
        // Validate current step before moving to next
        if (currentStep === 0) {
            // Validate location step
            if (!formData.propertyAddress || !formData.area || !formData.city || !formData.state || !formData.pincode) {
                alert('Please fill in all required fields before proceeding.')
                return
            }
        } else if (currentStep === 1) {
            // Validate details step
            if (!formData.propertyType || formData.bedrooms === 0 || formData.bathrooms === 0 || formData.areaSqft === 0) {
                alert('Please fill in all required fields before proceeding.')
                return
            }
        } else if (currentStep === 2) {
            // Validate pricing step
            if (!formData.title || !formData.price || !formData.description) {
                alert('Please fill in all required fields before proceeding.')
                return
            }
        }

        if (currentStep < FORM_STEPS.length - 1) {
            setCurrentStep(currentStep + 1)
        }
    }

    const prevStep = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1)
        }
    }

    const handleInputChange = (field: keyof FormData, value: any) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }))
    }

    const generateAIContent = async () => {
        setIsGeneratingAI(true)
        try {
            // Validate required fields
            if (!formData.propertyAddress || !formData.propertyType || !formData.bedrooms || !formData.bathrooms || !formData.areaSqft) {
                toast.error('Please fill in Address, Property Type, Bedrooms, Bathrooms, and Area before generating AI content.')
                return
            }

            const aiResult = await propertiesAPI.generateAIContent({
                context: 'property_creation',
                property_data: {
                    address: formData.propertyAddress,
                    property_type: formData.propertyType,
                    bedrooms: formData.bedrooms,
                    bathrooms: formData.bathrooms,
                    area: formData.areaSqft,
                    price: formData.price || undefined,
                    amenities: formData.amenities || '',
                    description: formData.description || '',
                    title: formData.title || ''
                },
                languages: ['en'],
                platforms: ['website'],
                generation_options: {
                    tone: 'professional',
                    length: 'medium',
                    include_hashtags: false,
                    include_cta: false,
                    max_title_length: 100
                }
            })

            if (aiResult.content?.website?.en) {
                const suggestion: AISuggestion = {
                    title: aiResult.content.website.en.title || '',
                    description: aiResult.content.website.en.body || '',
                    amenities: formData.amenities ? formData.amenities.split(',').map(a => a.trim()) : []
                }
                setAiSuggestion(suggestion)
                toast.success('AI content generated successfully!')
            } else {
                toast.error('Failed to generate AI content. Please try again.')
            }
        } catch (error: any) {
            console.error('Failed to generate AI content:', error)
            toast.error(`Failed to generate AI content: ${error.message || 'Unknown error'}`)
        } finally {
            setIsGeneratingAI(false)
        }
    }

    const applyAIContent = () => {
        if (!aiSuggestion) return

        setFormData(prev => ({
            ...prev,
            title: aiSuggestion.title,
            description: aiSuggestion.description,
            amenities: aiSuggestion.amenities?.join(', ') || ''
        }))
        toast.success('AI content applied to form!')
    }

    const handleImageUpload = async (files: FileList) => {
        if (!files || files.length === 0) return

        setUploadingImages(true)
        try {
            const formData = new FormData()
            Array.from(files).forEach(file => {
                formData.append('files', file)
            })

            const response = await propertiesAPI.uploadImages(formData)

            if (response.success && response.files) {
                const newImageUrls = response.files.map((file: any) => file.url || file.path)
                setFormData(prev => ({
                    ...prev,
                    images: [...prev.images, ...newImageUrls]
                }))
                toast.success(`${files.length} image(s) uploaded successfully!`)
            } else {
                toast.error('Failed to upload images')
            }
        } catch (error) {
            console.error('Error uploading images:', error)
            toast.error('Failed to upload images. Please try again.')
        } finally {
            setUploadingImages(false)
        }
    }

    const removeImage = (index: number) => {
        setFormData(prev => ({
            ...prev,
            images: prev.images.filter((_, i) => i !== index)
        }))
    }

    const handleSubmit = async () => {
        console.log('Form submitted:', formData)

        try {
            setIsLoading(true)

            // Get current user agent_id
            let agentId = 'anonymous_agent'
            try {
                const authState = authManager.getState()
                if (authState.user && (authState.user as any).agent_id) {
                    agentId = (authState.user as any).agent_id
                }
            } catch (error) {
                console.warn('Could not get current user, using anonymous agent_id:', error)
            }

            // Transform data for unified property service
            const propertyData = {
                title: formData.title || 'Property Listing',
                description: formData.description || '',
                property_type: formData.propertyType || 'Apartment',
                location: `${formData.propertyAddress}, ${formData.city}, ${formData.state}`,
                price: Number(formData.price) || 0,
                bedrooms: Number(formData.bedrooms) || 0,
                bathrooms: Number(formData.bathrooms) || 0,
                area_sqft: Number(formData.areaSqft) || Number(formData.area) || 0,
                features: [],
                images: formData.images,
                amenities: formData.amenities || '',
                agent_id: agentId
            }

            console.log('🚀 CALLING API with propertyData:', JSON.stringify(propertyData, null, 2))

            const response = await propertiesAPI.createProperty(propertyData)

            console.log('🚀 API call completed, response:', response)

            if (response.success) {
                toast.success('Property created successfully!')
                onSuccess?.()
            } else {
                console.error('Property creation failed:', response)
                toast.error('Failed to create property. Please try again.')
            }
        } catch (error: any) {
            console.error('❌ Failed to create property:', error)
            console.error('❌ Error message:', error.message)
            console.error('❌ Error stack:', error.stack)
            console.error('❌ Full error object:', JSON.stringify(error, null, 2))

            toast.error(`Failed to create property: ${error.message || 'Unknown error'}. Please try again.`)
        } finally {
            setIsLoading(false)
        }
    }

    const renderStepContent = () => {
        switch (currentStep) {
            case 0: // Location
                return (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="mobile-form-step space-y-6"
                    >
                        <div className="mobile-step-header">
                            <div className="mobile-step-icon bg-blue-100">
                                <MapPinIcon className="w-8 h-8 text-blue-600" />
                            </div>
                            <h2 className="mobile-step-title">Where is your property located?</h2>
                            <p className="mobile-step-description">
                                Start by entering the property address. Our system will detect property type and market insights.
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div className="mobile-form-field">
                                <label className="mobile-form-label">
                                    Property Address *
                                </label>
                                <input
                                    type="text"
                                    value={formData.propertyAddress}
                                    onChange={(e) => handleInputChange('propertyAddress', e.target.value)}
                                    placeholder="e.g., 123 Marine Drive, Mumbai"
                                    className="mobile-form-input"
                                    required
                                />
                            </div>

                            <div className="mobile-form-field">
                                <label className="mobile-form-label">
                                    Area/Locality *
                                </label>
                                <input
                                    type="text"
                                    value={formData.area}
                                    onChange={(e) => handleInputChange('area', e.target.value)}
                                    placeholder="e.g., Bandra West, Mumbai"
                                    className="mobile-form-input"
                                    required
                                />
                            </div>

                            <div className="mobile-form-grid-2">
                                <div className="mobile-form-field">
                                    <label className="mobile-form-label">
                                        City *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.city}
                                        onChange={(e) => handleInputChange('city', e.target.value)}
                                        placeholder="Mumbai"
                                        className="mobile-form-input"
                                        required
                                    />
                                </div>
                                <div className="mobile-form-field">
                                    <label className="mobile-form-label">
                                        State *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.state}
                                        onChange={(e) => handleInputChange('state', e.target.value)}
                                        placeholder="Maharashtra"
                                        className="mobile-form-input"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="mobile-form-field">
                                <label className="mobile-form-label">
                                    Pincode *
                                </label>
                                <input
                                    type="text"
                                    value={formData.pincode}
                                    onChange={(e) => handleInputChange('pincode', e.target.value)}
                                    placeholder="400001"
                                    className="mobile-form-input"
                                    required
                                />
                            </div>
                        </div>
                    </motion.div>
                )

            case 1: // Details
                return (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-6"
                    >
                        <div className="text-center mb-8">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <BuildingOfficeIcon className="w-8 h-8 text-green-600" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">Property Details</h2>
                            <p className="text-gray-600 text-sm leading-relaxed px-4">
                                Tell us more about your property features and specifications.
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Property Type *
                                </label>
                                <select
                                    value={formData.propertyType}
                                    onChange={(e) => handleInputChange('propertyType', e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                                    required
                                >
                                    <option value="">Select property type</option>
                                    <option value="apartment">Apartment</option>
                                    <option value="villa">Villa</option>
                                    <option value="house">House</option>
                                    <option value="plot">Plot</option>
                                    <option value="commercial">Commercial</option>
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Bedrooms *
                                    </label>
                                    <select
                                        value={formData.bedrooms}
                                        onChange={(e) => handleInputChange('bedrooms', parseInt(e.target.value))}
                                        className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                                        required
                                    >
                                        <option value={0}>Select</option>
                                        <option value={1}>1</option>
                                        <option value={2}>2</option>
                                        <option value={3}>3</option>
                                        <option value={4}>4</option>
                                        <option value={5}>5+</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Bathrooms *
                                    </label>
                                    <select
                                        value={formData.bathrooms}
                                        onChange={(e) => handleInputChange('bathrooms', parseInt(e.target.value))}
                                        className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                                        required
                                    >
                                        <option value={0}>Select</option>
                                        <option value={1}>1</option>
                                        <option value={2}>2</option>
                                        <option value={3}>3</option>
                                        <option value={4}>4</option>
                                        <option value={5}>5+</option>
                                    </select>
                                </div>
                            </div>

                            <div className="mobile-form-field">
                                <label className="mobile-form-label">
                                    Area (sq ft) *
                                </label>
                                <input
                                    type="number"
                                    value={formData.areaSqft}
                                    onChange={(e) => handleInputChange('areaSqft', parseInt(e.target.value))}
                                    placeholder="1200"
                                    className="mobile-form-input"
                                    required
                                />
                            </div>
                        </div>
                    </motion.div>
                )

            case 2: // Pricing & Description
                return (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-6"
                    >
                        <div className="text-center mb-8">
                            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CurrencyDollarIcon className="w-8 h-8 text-yellow-600" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">Pricing & Description</h2>
                            <p className="text-gray-600 text-sm leading-relaxed px-4">
                                Set your asking price and add a compelling description.
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Property Title *
                                </label>
                                <input
                                    type="text"
                                    value={formData.title}
                                    onChange={(e) => handleInputChange('title', e.target.value)}
                                    placeholder="e.g., Beautiful 3BHK Apartment in Bandra West"
                                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Price (₹) *
                                </label>
                                <input
                                    type="number"
                                    value={formData.price}
                                    onChange={(e) => handleInputChange('price', parseInt(e.target.value))}
                                    placeholder="5000000"
                                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Description *
                                </label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => handleInputChange('description', e.target.value)}
                                    placeholder="Describe your property's key features, amenities, and what makes it special..."
                                    rows={4}
                                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base resize-none"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Amenities
                                </label>
                                <textarea
                                    value={formData.amenities}
                                    onChange={(e) => handleInputChange('amenities', e.target.value)}
                                    placeholder="e.g., Swimming pool, Gym, 24/7 Security, Parking, Garden"
                                    rows={3}
                                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base resize-none"
                                />
                            </div>

                            {/* AI Content Generation */}
                            <div className="space-y-3">
                                <div className="flex space-x-4">
                                    <button
                                        type="button"
                                        onClick={generateAIContent}
                                        disabled={isGeneratingAI || !formData.propertyAddress || !formData.propertyType}
                                        className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-3 px-6 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all duration-200"
                                    >
                                        {isGeneratingAI ? (
                                            <>
                                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                                <span>Generating...</span>
                                            </>
                                        ) : (
                                            <>
                                                <SparklesIcon className="w-5 h-5" />
                                                <span>Generate AI Content</span>
                                            </>
                                        )}
                                    </button>

                                    {aiSuggestion && (
                                        <button
                                            type="button"
                                            onClick={applyAIContent}
                                            className="bg-green-600 hover:bg-green-700 text-white py-3 px-6 rounded-xl font-semibold flex items-center space-x-2 transition-all duration-200"
                                        >
                                            <CheckIcon className="w-5 h-5" />
                                            <span>Apply</span>
                                        </button>
                                    )}
                                </div>

                                {/* Help text for disabled button */}
                                {(!formData.propertyAddress || !formData.propertyType) && (
                                    <div className="text-sm text-gray-500 flex items-center space-x-2">
                                        <span>Please fill in the address and property type in the previous steps to enable AI content generation.</span>
                                    </div>
                                )}
                            </div>

                            {/* AI Suggestion Display */}
                            {aiSuggestion && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="bg-purple-50 rounded-xl p-4 border border-purple-200"
                                >
                                    <div className="flex items-center space-x-2 mb-3">
                                        <SparklesIcon className="w-5 h-5 text-purple-600" />
                                        <span className="font-semibold text-purple-900">AI Generated Content</span>
                                    </div>
                                    <div className="space-y-3">
                                        <div>
                                            <h4 className="font-medium text-purple-900 mb-1">Title:</h4>
                                            <p className="text-purple-800 text-sm">{aiSuggestion.title}</p>
                                        </div>
                                        <div>
                                            <h4 className="font-medium text-purple-900 mb-1">Description:</h4>
                                            <p className="text-purple-800 text-sm whitespace-pre-line">{aiSuggestion.description}</p>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </div>
                    </motion.div>
                )

            case 3: // Images
                return (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-6"
                    >
                        <div className="text-center mb-8">
                            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CameraIcon className="w-8 h-8 text-purple-600" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">Property Images</h2>
                            <p className="text-gray-600 text-sm leading-relaxed px-4">
                                Upload high-quality photos to showcase your property.
                            </p>
                        </div>

                        <div className="space-y-4">
                            {/* Image Upload Area */}
                            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-indigo-500 transition-colors">
                                <input
                                    type="file"
                                    multiple
                                    accept="image/*"
                                    onChange={(e) => e.target.files && handleImageUpload(e.target.files)}
                                    className="hidden"
                                    id="image-upload"
                                    disabled={uploadingImages}
                                />
                                <label
                                    htmlFor="image-upload"
                                    className={`cursor-pointer flex flex-col items-center space-y-4 ${uploadingImages ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                    <CloudArrowUpIcon className="w-12 h-12 text-gray-400" />
                                    <div>
                                        <p className="text-lg font-semibold text-gray-900">
                                            {uploadingImages ? 'Uploading...' : 'Click to upload images'}
                                        </p>
                                        <p className="text-sm text-gray-500">
                                            PNG, JPG, JPEG up to 10MB each
                                        </p>
                                    </div>
                                </label>
                            </div>

                            {/* Uploaded Images Grid */}
                            {formData.images.length > 0 && (
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                    {formData.images.map((imageUrl, index) => (
                                        <div key={index} className="relative group">
                                            <img
                                                src={imageUrl}
                                                alt={`Property image ${index + 1}`}
                                                className="w-full h-32 object-cover rounded-lg"
                                            />
                                            <button
                                                onClick={() => removeImage(index)}
                                                className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <XMarkIcon className="w-4 h-4" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Image Tips */}
                            <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-200">
                                <div className="flex items-center space-x-2 mb-2">
                                    <span className="font-semibold text-indigo-900">Image Tips</span>
                                </div>
                                <ul className="text-sm text-indigo-800 space-y-1">
                                    <li>• Use high-resolution images (at least 1920x1080)</li>
                                    <li>• Include exterior, interior, and key features</li>
                                    <li>• Ensure good lighting and clean spaces</li>
                                    <li>• Upload 5-10 images for best results</li>
                                </ul>
                            </div>
                        </div>
                    </motion.div>
                )

            default:
                return null
        }
    }

    return (
        <div className="mobile-form-container">
            {/* Mobile Header */}
            <div className="mobile-form-header">
                <div className="mobile-form-header-content">
                    <div className="w-8" /> {/* Spacer for alignment */}

                    <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-600">
                            Step {currentStep + 1} of {FORM_STEPS.length}
                        </span>
                    </div>

                    <div className="w-8" /> {/* Spacer for alignment */}
                </div>

                {/* Progress Bar */}
                <div className="mobile-progress-bar">
                    <div
                        className="mobile-progress-fill"
                        style={{ width: `${((currentStep + 1) / FORM_STEPS.length) * 100}%` }}
                    />
                </div>
            </div>

            {/* Form Content */}
            <div className="mobile-form-card">
                <form onSubmit={(e) => e.preventDefault()}>
                    <div className="mobile-form-content">
                        <AnimatePresence mode="wait">
                            {renderStepContent()}
                        </AnimatePresence>
                    </div>

                    {/* Navigation Buttons */}
                    <div className="mobile-form-actions">
                        <button
                            type="button"
                            onClick={prevStep}
                            disabled={currentStep === 0}
                            className="mobile-form-button mobile-form-button-secondary flex items-center space-x-2"
                            aria-label="Previous step"
                        >
                            <ArrowLeftIcon className="w-4 h-4" />
                            <span>Previous</span>
                        </button>

                        {currentStep === FORM_STEPS.length - 1 ? (
                            <button
                                type="button"
                                onClick={handleSubmit}
                                className="mobile-form-button mobile-form-button-primary flex items-center space-x-2"
                                aria-label="Submit form"
                            >
                                <CheckIcon className="w-4 h-4" />
                                <span>Submit</span>
                            </button>
                        ) : (
                            <button
                                type="button"
                                onClick={nextStep}
                                className="mobile-form-button mobile-form-button-primary flex items-center space-x-2"
                                aria-label="Next step"
                            >
                                <span>Next</span>
                                <ArrowRightIcon className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </form>
            </div>

            {/* Bottom spacing for mobile navigation */}
            <div className="mobile-form-bottom-spacing" />
        </div>
    )
}
