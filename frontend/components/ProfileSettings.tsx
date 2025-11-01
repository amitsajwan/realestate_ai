'use client'

import { LoadingButton } from '@/components/LoadingStates'
import { useAsyncOperation, useMultipleLoading } from '@/hooks/useLoading'
import { apiService } from '@/lib/api/centralized-client'
import { authManager } from '@/lib/auth'
import { handleError, showSuccess } from '@/lib/error-handler'
import { FormValidator, profileSettingsSchema } from '@/lib/form-validation'
import { applyBrandTheme, getBrandTheme } from '@/lib/theme'
import { CheckIcon, ExclamationTriangleIcon, SparklesIcon, UserIcon } from '@heroicons/react/24/outline'
import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'react-hot-toast'

interface BrandingSuggestions {
  tagline: string
  about: string
  colors: {
    primary: string
    secondary: string
    accent: string
  }
}

interface UserProfile {
  user_id: string
  name: string
  email: string
  phone?: string
  whatsapp?: string
  company?: string
  experience_years?: string
  specialization_areas?: string
  tagline?: string
  social_bio?: string
  about?: string
  address?: string
  city?: string
  state?: string
  pincode?: string
  languages?: string[]
  logo_url?: string
  brandingSuggestions?: BrandingSuggestions | null
  // Additional branding fields from onboarding
  branding_data?: any
  brand_theme?: any
  brand_style?: string
  brand_personality?: string
  brand_keywords?: string
  brand_inspiration?: string
}

export default function ProfileSettings() {
  const [formData, setFormData] = useState<UserProfile>({
    user_id: authManager.getState().user?.id || 'default_user',
    name: '',
    email: '',
    phone: '',
    whatsapp: '',
    company: '',
    experience_years: '0',
    specialization_areas: '',
    tagline: '',
    social_bio: '',
    about: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    languages: [],
    logo_url: '',
    brandingSuggestions: null,
    branding_data: null,
    brand_theme: null,
    brand_style: '',
    brand_personality: '',
    brand_keywords: '',
    brand_inspiration: ''
  })

  const [brandingSuggestions, setBrandingSuggestions] = useState<any[]>([])
  const [selectedBranding, setSelectedBranding] = useState<number | null>(null)

  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([])
  const [isProfileLoaded, setIsProfileLoaded] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [currentAppliedTheme, setCurrentAppliedTheme] = useState<any>(null)

  // Refs for cleanup and race condition prevention
  const isMountedRef = useRef(true)
  const isLoadingRef = useRef(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Use loading hooks for consistent state management
  const profileOperation = useAsyncOperation<UserProfile>()
  const brandingOperation = useAsyncOperation<BrandingSuggestions>()
  const multipleLoading = useMultipleLoading()

  // Form validation
  const validator = new FormValidator(profileSettingsSchema)

  const isLoading = isLoadingProfile || profileOperation.isLoading
  const isSaving = multipleLoading.isLoading('saveProfile')

  // Debug logging
  console.log('[ProfileSettings] Loading states:', {
    isLoadingProfile,
    profileOperationLoading: profileOperation.isLoading,
    isProfileLoaded,
    isLoading,
    isSaving
  })

  // Constants
  const MAX_RETRIES = 3
  const RETRY_DELAY = 1000 // 1 second

  const availableLanguages = [
    'English', 'Hindi', 'Marathi', 'Gujarati', 'Tamil', 'Telugu',
    'Kannada', 'Malayalam', 'Bengali', 'Punjabi', 'Urdu', 'Other'
  ]

  // Cleanup function
  const cleanup = useCallback(() => {
    isMountedRef.current = false
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }, [])

  // Retry with exponential backoff
  const retryWithBackoff = useCallback(async (fn: () => Promise<any>, retries: number = MAX_RETRIES): Promise<any> => {
    try {
      return await fn()
    } catch (error) {
      if (retries > 0 && isMountedRef.current) {
        const delay = RETRY_DELAY * Math.pow(2, MAX_RETRIES - retries)
        console.warn(`[ProfileSettings] Retrying in ${delay}ms... (${retries} retries left)`)
        await new Promise(resolve => setTimeout(resolve, delay))
        return retryWithBackoff(fn, retries - 1)
      }
      throw error
    }
  }, [])

  const loadUserProfile = useCallback(async (isRetry: boolean = false) => {
    // Prevent multiple simultaneous calls using ref
    if (isLoadingRef.current || isProfileLoaded) {
      return
    }

    // Don't retry if component is unmounted
    if (!isMountedRef.current) {
      return
    }

    isLoadingRef.current = true
    setIsLoadingProfile(true)
    setLoadError(null)

    // Create abort controller for this request
    abortControllerRef.current = new AbortController()

    try {
      // Get current user from auth manager
      const authState = authManager.getState()
      const currentUser = authState.user

      // Try to load from backend API with retry logic
      let profileData = null
      try {
        const response = await retryWithBackoff(async () => {
          return await apiService.getUserProfile(authManager.getState().user?.id || 'default_user')
        })

        console.log('[ProfileSettings] API Response:', response)
        if (response && response.success && response.profile) {
          profileData = response.profile
          console.log('[ProfileSettings] Profile data found:', profileData)
        } else {
          console.log('[ProfileSettings] No profile data in response:', response)
        }
      } catch (error) {
        // Only log as info if it's a 404 or similar (no profile exists)
        if (error instanceof Error && error.message.includes('404')) {
          console.info('[ProfileSettings] No existing profile found, will use onboarding data')
        } else {
          console.warn('[ProfileSettings] API error, using fallback data:', error)
        }
      }

      // Update state regardless of mount status to prevent race conditions
      console.log('[ProfileSettings] Checking if component is mounted:', isMountedRef.current)
      // Note: We'll update state anyway to prevent data loss from race conditions

      // Merge onboarding data with profile data, prioritizing profile data
      const mergedData = {
        user_id: profileData?.user_id || authManager.getState().user?.id || 'default_user',
        name: profileData?.name || (currentUser ? `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() : ''),
        email: profileData?.email || currentUser?.email || '',
        phone: profileData?.phone || currentUser?.phone || '',
        whatsapp: profileData?.whatsapp || profileData?.phone || currentUser?.phone || '',
        company: profileData?.company || '',
        experience_years: profileData?.experience_years || '0',
        specialization_areas: profileData?.specialization_areas || '',
        tagline: profileData?.tagline || '',
        social_bio: profileData?.social_bio || profileData?.about || '',
        about: profileData?.about || '',
        address: profileData?.address || '',
        city: profileData?.city || '',
        state: profileData?.state || '',
        pincode: profileData?.pincode || '',
        languages: profileData?.languages || [],
        logo_url: profileData?.logo_url || '',
        brandingSuggestions: profileData?.brandingSuggestions || null,
        // Include all branding fields from onboarding
        branding_data: profileData?.branding_data || null,
        brand_theme: profileData?.brand_theme || null,
        brand_style: profileData?.brand_style || '',
        brand_personality: profileData?.brand_personality || '',
        brand_keywords: profileData?.brand_keywords || '',
        brand_inspiration: profileData?.brand_inspiration || ''
      }

      console.log('[ProfileSettings] About to update state with merged data:', mergedData)

      // Update state with safety checks
      try {
        setFormData(mergedData)
        setSelectedLanguages(mergedData.languages || [])
        console.log('[ProfileSettings] Setting isProfileLoaded to true')
        setIsProfileLoaded(true)
        setIsLoadingProfile(false) // Reset loading state
        setRetryCount(0) // Reset retry count on success
        console.log('[ProfileSettings] State update completed')
      } catch (error) {
        console.error('[ProfileSettings] Error updating state:', error)
        // Still try to set the loaded flag to prevent infinite loading
        setIsProfileLoaded(true)
        setIsLoadingProfile(false) // Reset loading state even on error
      }

      // If we have onboarding data but no profile, show a message
      if (currentUser && !profileData) {
        toast.success('Onboarding data loaded! Please review and save your profile.')
      }

      return mergedData
    } catch (error) {
      console.error('[ProfileSettings] Error loading profile:', error)

      if (!isMountedRef.current) {
        return
      }

      const errorMessage = error instanceof Error ? error.message : 'Failed to load profile data'
      setLoadError(errorMessage)

      if (!isRetry && retryCount < MAX_RETRIES) {
        setRetryCount(prev => prev + 1)
        console.warn(`[ProfileSettings] Will retry loading profile (attempt ${retryCount + 1}/${MAX_RETRIES})`)
        // Retry after a delay
        setTimeout(() => {
          if (isMountedRef.current) {
            loadUserProfile(true)
          }
        }, RETRY_DELAY)
      } else {
        toast.error(`Failed to load profile data${retryCount >= MAX_RETRIES ? ' after multiple attempts' : ''}`)
      }
    } finally {
      if (isMountedRef.current) {
        isLoadingRef.current = false
        setIsLoadingProfile(false)
      }
      abortControllerRef.current = null
    }
  }, [isProfileLoaded, retryCount, retryWithBackoff])

  // Load profile on mount
  useEffect(() => {
    if (!isProfileLoaded && !isLoadingRef.current) {
      loadUserProfile()
    }
  }, []) // Empty dependency array - only run on mount

  // Load current applied theme separately
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const appliedTheme = getBrandTheme()
      setCurrentAppliedTheme(appliedTheme)
    }
  }, []) // Load theme on mount

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup()
    }
  }, [cleanup])

  const handleInputChange = (field: keyof UserProfile, value: any) => {
    const updatedData = {
      ...formData,
      [field]: value
    }
    setFormData(updatedData)

    // Real-time validation for relevant fields
    if (['name', 'email', 'phone', 'whatsapp', 'pincode', 'tagline', 'social_bio', 'about'].includes(field as string)) {
      validator.validateField(field as string, value)
    }
  }

  const handleBlur = (field: string) => {
    validator.touch(field)
  }

  const handleLanguageToggle = (language: string) => {
    const updatedLanguages = selectedLanguages.includes(language)
      ? selectedLanguages.filter(lang => lang !== language)
      : [...selectedLanguages, language]

    setSelectedLanguages(updatedLanguages)
    handleInputChange('languages', updatedLanguages)
  }

  const handleSave = async () => {
    // Validate all fields before saving
    const isValid = validator.validateAll(formData)

    if (!isValid) {
      const errors = validator.getErrors()
      const firstError = Object.values(errors)[0]
      if (firstError) {
        toast.error(firstError)
      }
      return
    }

    multipleLoading.setLoading('saveProfile', true)

    try {
      await apiService.updateUserProfile(authManager.getState().user?.id || 'default_user', { ...formData })
      showSuccess('Profile saved successfully!')
    } catch (error) {
      handleError(error, 'Failed to save profile')
    } finally {
      multipleLoading.setLoading('saveProfile', false)
    }
  }

  const handleGenerateBranding = async () => {
    if (!formData.company?.trim()) {
      toast.error('Please enter your company name first')
      return
    }

    const response = await brandingOperation.execute(
      () => apiService.getBrandingSuggestions({
        company_name: formData.company || '',
        agent_name: formData.name,
        position: formData.specialization_areas,
        business_type: 'Residential',
        target_audience: 'General clients',
        brand_style: 'Professional'
      }),
      {
        successMessage: 'AI branding suggestions generated successfully!',
        errorMessage: 'Failed to generate branding suggestions'
      }
    )

    if (response?.suggestions && response.suggestions.length > 0) {
      // Store all suggestions for selection
      setBrandingSuggestions(response.suggestions)
      setSelectedBranding(response.selectedIndex || 0)

      // Transform the selected suggestion for formData
      const selectedSuggestion = response.suggestions[response.selectedIndex || 0]
      const transformedSuggestion = {
        tagline: selectedSuggestion.tagline || `${formData.company} - Professional Real Estate Services`,
        about: selectedSuggestion.about || `Welcome to ${formData.company}, your trusted partner in real estate.`,
        colors: {
          primary: selectedSuggestion.colorPalette?.primary || selectedSuggestion.primaryColor || '#3b82f6',
          secondary: selectedSuggestion.colorPalette?.secondary || selectedSuggestion.secondaryColor || '#64748b',
          accent: selectedSuggestion.colorPalette?.accent || '#10b981'
        }
      }

      setFormData(prev => ({
        ...prev,
        brandingSuggestions: transformedSuggestion
      }))
    } else if (response && Array.isArray(response) && response.length > 0) {
      // Fallback for old API format
      const suggestion = response[0]
      setFormData(prev => ({
        ...prev,
        brandingSuggestions: {
          tagline: suggestion.tagline,
          about: suggestion.about,
          colors: suggestion.colors
        }
      }))
    }
  }

  const handleSelectBranding = (index: number) => {
    if (brandingSuggestions[index]) {
      setSelectedBranding(index)
      const selectedSuggestion = brandingSuggestions[index]

      const transformedSuggestion = {
        tagline: selectedSuggestion.tagline || `${formData.company} - Professional Real Estate Services`,
        about: selectedSuggestion.about || `Welcome to ${formData.company}, your trusted partner in real estate.`,
        colors: {
          primary: selectedSuggestion.colorPalette?.primary || selectedSuggestion.primaryColor || '#3b82f6',
          secondary: selectedSuggestion.colorPalette?.secondary || selectedSuggestion.secondaryColor || '#64748b',
          accent: selectedSuggestion.colorPalette?.accent || '#10b981'
        }
      }

      setFormData(prev => ({
        ...prev,
        brandingSuggestions: transformedSuggestion
      }))
    }
  }

  const handleApplyBranding = async () => {
    if (!formData.brandingSuggestions?.colors) {
      toast.error('No branding suggestions available to apply')
      return
    }

    const brandTheme = {
      primary: formData.brandingSuggestions.colors.primary,
      secondary: formData.brandingSuggestions.colors.secondary,
      accent: formData.brandingSuggestions.colors.accent
    }

    applyBrandTheme(brandTheme) // Now persists by default
    setCurrentAppliedTheme(brandTheme) // Update local state immediately

    // Also save the branding suggestions to the profile
    try {
      await apiService.updateUserProfile(authManager.getState().user?.id || 'default_user', {
        ...formData,
        brandingSuggestions: formData.brandingSuggestions
      })
      toast.success('Brand theme applied and saved to profile!')
    } catch (error) {
      handleError(error, 'Failed to save branding to profile')
      // Theme was still applied, so don't show error for that
    }
  }

  const handleProfileSetup = () => {
    // Logic to open profile form, e.g., setIsEditing(true) or navigate
    console.log('Starting profile setup');
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="glass-card p-8">
        <div className="flex items-center gap-3 mb-8">
          <UserIcon className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-white">Profile Settings</h1>
        </div>

        {isLoading && (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-white">Loading profile...</span>
          </div>
        )}

        {loadError && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800">Failed to load profile</h3>
                <p className="text-sm text-red-600 mt-1">{loadError}</p>
                {retryCount < MAX_RETRIES && (
                  <p className="text-xs text-red-500 mt-1">
                    Retrying... (Attempt {retryCount + 1}/{MAX_RETRIES})
                  </p>
                )}
              </div>
              <button
                onClick={() => {
                  setLoadError(null)
                  setRetryCount(0)
                  loadUserProfile()
                }}
                className="ml-4 px-3 py-1 bg-red-100 text-red-800 text-sm rounded hover:bg-red-200 transition-colors"
                disabled={isLoading}
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {!isLoading && (
          <p className="text-gray-300 mb-8">
            Manage your profile, preferences, and account settings.
          </p>
        )}

        {!isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                Personal Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="profile-name" className="block text-sm font-medium text-gray-300 mb-2">Full Name *</label>
                  <input
                    id="profile-name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    onBlur={() => handleBlur('name')}
                    className={`form-input ${validator.hasFieldError('name') ? 'border-red-300' : validator.isFieldValid('name') ? 'border-green-300' : ''
                      }`}
                    placeholder="Enter your full name"
                    aria-describedby={validator.hasFieldError('name') ? 'name-error' : undefined}
                  />
                  {validator.hasFieldError('name') && (
                    <p id="name-error" className="mt-1 text-sm text-red-400" role="alert">
                      {validator.getFieldError('name')}
                    </p>
                  )}
                </div>
                <div>
                  <label htmlFor="profile-email" className="block text-sm font-medium text-gray-300 mb-2">Email *</label>
                  <input
                    id="profile-email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    onBlur={() => handleBlur('email')}
                    className={`form-input ${validator.hasFieldError('email') ? 'border-red-300' : validator.isFieldValid('email') ? 'border-green-300' : ''
                      }`}
                    placeholder="Enter your email"
                    aria-describedby={validator.hasFieldError('email') ? 'email-error' : undefined}
                  />
                  {validator.hasFieldError('email') && (
                    <p id="email-error" className="mt-1 text-sm text-red-400" role="alert">
                      {validator.getFieldError('email')}
                    </p>
                  )}
                </div>
                <div>
                  <label htmlFor="profile-phone" className="block text-sm font-medium text-gray-300 mb-2">Phone</label>
                  <input
                    id="profile-phone"
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    onBlur={() => handleBlur('phone')}
                    className={`form-input ${validator.hasFieldError('phone') ? 'border-red-300' : validator.isFieldValid('phone') ? 'border-green-300' : ''
                      }`}
                    placeholder="Enter your phone number"
                    aria-describedby={validator.hasFieldError('phone') ? 'phone-error' : undefined}
                  />
                  {validator.hasFieldError('phone') && (
                    <p id="phone-error" className="mt-1 text-sm text-red-400" role="alert">
                      {validator.getFieldError('phone')}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">WhatsApp</label>
                  <input
                    type="tel"
                    value={formData.whatsapp}
                    onChange={(e) => handleInputChange('whatsapp', e.target.value)}
                    onBlur={() => handleBlur('whatsapp')}
                    className={`form-input ${validator.hasFieldError('whatsapp') ? 'border-red-300' : validator.isFieldValid('whatsapp') ? 'border-green-300' : ''
                      }`}
                    placeholder="Enter your WhatsApp number"
                    aria-describedby={validator.hasFieldError('whatsapp') ? 'whatsapp-error' : undefined}
                  />
                  {validator.hasFieldError('whatsapp') && (
                    <p id="whatsapp-error" className="mt-1 text-sm text-red-400" role="alert">
                      {validator.getFieldError('whatsapp')}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
                Company Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Company</label>
                  <input
                    type="text"
                    value={formData.company}
                    onChange={(e) => handleInputChange('company', e.target.value)}
                    className="form-input"
                    placeholder="Enter your company name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Experience (Years)</label>
                  <input
                    type="number"
                    value={formData.experience_years}
                    onChange={(e) => handleInputChange('experience_years', e.target.value)}
                    className="form-input"
                    placeholder="Years of experience"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Specialization Areas</label>
                  <select
                    value={formData.specialization_areas}
                    onChange={(e) => handleInputChange('specialization_areas', e.target.value)}
                    className="form-input"
                  >
                    <option value="">Select specialization area</option>
                    <option value="Residential">Residential</option>
                    <option value="Commercial">Commercial</option>
                    <option value="Luxury">Luxury</option>
                    <option value="Industrial">Industrial</option>
                    <option value="Land Development">Land Development</option>
                    <option value="Investment Properties">Investment Properties</option>
                    <option value="New Construction">New Construction</option>
                    <option value="Rental Properties">Rental Properties</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Tagline</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={formData.tagline || ''}
                      onChange={(e) => handleInputChange('tagline', e.target.value)}
                      onBlur={() => handleBlur('tagline')}
                      className={`form-input flex-1 ${validator.hasFieldError('tagline') ? 'border-red-300' : validator.isFieldValid('tagline') ? 'border-green-300' : ''
                        }`}
                      placeholder={formData.tagline || "Your professional tagline"}
                      aria-describedby={validator.hasFieldError('tagline') ? 'tagline-error' : undefined}
                    />
                    {formData.brandingSuggestions && (
                      <button
                        type="button"
                        onClick={() => handleInputChange('tagline', formData.brandingSuggestions?.tagline || '')}
                        className="btn-outline px-3 py-2 text-sm whitespace-nowrap"
                        title="Use AI suggestion"
                      >
                        Use AI
                      </button>
                    )}
                  </div>
                  {validator.hasFieldError('tagline') && (
                    <p id="tagline-error" className="mt-1 text-sm text-red-400" role="alert">
                      {validator.getFieldError('tagline')}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Onboarding Branding Status Section - Show if branding exists from onboarding */}
            {(formData.branding_data || formData.brand_theme) && (
              <div className="glass-card p-6">
                <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                  <CheckIcon className="w-5 h-5 text-green-400" />
                  Your Onboarding Branding
                </h3>

                <div className="bg-green-900/20 border border-green-700 rounded-lg p-4 mb-6">
                  <div className="flex items-center mb-2">
                    <CheckIcon className="w-5 h-5 text-green-400 mr-2" />
                    <h4 className="text-lg font-medium text-green-100">Branding Setup Complete</h4>
                  </div>
                  <p className="text-green-200 text-sm">
                    Your branding was configured during onboarding and is active across your platform.
                  </p>
                </div>

                {/* Display branding details */}
                <div className="space-y-4">
                  {formData.tagline && (
                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <h4 className="text-lg font-medium text-white mb-2">Current Tagline</h4>
                      <p className="text-gray-100">{formData.tagline}</p>
                    </div>
                  )}

                  {formData.about && (
                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <h4 className="text-lg font-medium text-white mb-2">About Description</h4>
                      <p className="text-gray-100 leading-relaxed">{formData.about}</p>
                    </div>
                  )}

                  {formData.brand_theme && (
                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <h4 className="text-lg font-medium text-white mb-3">Active Brand Colors</h4>
                      <div className="flex gap-4">
                        <div className="text-center">
                          <div
                            className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                            style={{ backgroundColor: formData.brand_theme.primary || '#3b82f6' }}
                          ></div>
                          <p className="text-xs text-gray-300 font-medium">Primary</p>
                          <p className="text-xs text-gray-100 font-mono">{formData.brand_theme.primary || '#3b82f6'}</p>
                        </div>
                        <div className="text-center">
                          <div
                            className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                            style={{ backgroundColor: formData.brand_theme.secondary || '#64748b' }}
                          ></div>
                          <p className="text-xs text-gray-300 font-medium">Secondary</p>
                          <p className="text-xs text-gray-100 font-mono">{formData.brand_theme.secondary || '#64748b'}</p>
                        </div>
                        <div className="text-center">
                          <div
                            className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                            style={{ backgroundColor: formData.brand_theme.accent || '#10b981' }}
                          ></div>
                          <p className="text-xs text-gray-300 font-medium">Accent</p>
                          <p className="text-xs text-gray-100 font-mono">{formData.brand_theme.accent || '#10b981'}</p>
                        </div>
                      </div>
                      <p className="text-xs text-green-300 mt-2">✓ These colors are your established brand theme</p>
                    </div>
                  )}

                  {(formData.brand_style || formData.brand_personality) && (
                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <h4 className="text-lg font-medium text-white mb-3">Brand Personality</h4>
                      <div className="grid grid-cols-2 gap-4">
                        {formData.brand_style && (
                          <div>
                            <p className="text-sm text-gray-300 font-medium">Style</p>
                            <p className="text-gray-100">{formData.brand_style}</p>
                          </div>
                        )}
                        {formData.brand_personality && (
                          <div>
                            <p className="text-sm text-gray-300 font-medium">Personality</p>
                            <p className="text-gray-100">{formData.brand_personality}</p>
                          </div>
                        )}
                      </div>
                      {formData.brand_keywords && (
                        <div className="mt-3">
                          <p className="text-sm text-gray-300 font-medium">Keywords</p>
                          <p className="text-gray-100">{formData.brand_keywords}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* AI Branding Section */}
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <SparklesIcon className="w-5 h-5 text-purple-400" />
                AI Branding {(formData.branding_data || formData.brand_theme) ? '- Generate New Options' : ''}
              </h3>

              {!formData.brandingSuggestions ? (
                <div className="text-center py-8">
                  <p className="text-gray-400 mb-4">
                    {(formData.branding_data || formData.brand_theme)
                      ? 'Generate new AI-powered branding alternatives or refresh your current branding'
                      : 'Generate AI-powered branding suggestions for your business'
                    }
                  </p>
                  <LoadingButton
                    onClick={handleGenerateBranding}
                    isLoading={brandingOperation.isLoading}
                    disabled={!formData.company?.trim()}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Generate Branding
                  </LoadingButton>
                  {!formData.company?.trim() && (
                    <p className="text-sm text-amber-400 mt-2">Please enter your company name first</p>
                  )}
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Multiple Branding Options */}
                  {brandingSuggestions.length > 0 && (
                    <div>
                      <h4 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                        <SparklesIcon className="w-5 h-5 text-purple-400" />
                        Choose Your Brand Style ({brandingSuggestions.length} Options)
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        {brandingSuggestions.map((suggestion, index) => (
                          <div
                            key={index}
                            onClick={() => handleSelectBranding(index)}
                            className={`cursor-pointer p-4 rounded-lg border-2 transition-all duration-200 ${selectedBranding === index
                              ? 'border-purple-500 bg-purple-900/20 shadow-md'
                              : 'border-gray-600 hover:border-gray-500 hover:shadow-sm bg-gray-800/30'
                              }`}
                          >
                            <div className="flex items-center justify-between mb-3">
                              <h5 className="font-semibold text-gray-200">{suggestion.designStyle || 'Modern'}</h5>
                              {selectedBranding === index && (
                                <CheckIcon className="w-5 h-5 text-purple-400" />
                              )}
                            </div>

                            {/* Color Palette Preview */}
                            <div className="flex space-x-2 mb-3">
                              <div
                                className="w-6 h-6 rounded-full border border-gray-500 shadow-sm"
                                style={{ backgroundColor: suggestion.colorPalette?.primary || suggestion.primaryColor || '#3b82f6' }}
                                title="Primary"
                              />
                              <div
                                className="w-6 h-6 rounded-full border border-gray-500 shadow-sm"
                                style={{ backgroundColor: suggestion.colorPalette?.secondary || suggestion.secondaryColor || '#64748b' }}
                                title="Secondary"
                              />
                              <div
                                className="w-6 h-6 rounded-full border border-gray-500 shadow-sm"
                                style={{ backgroundColor: suggestion.colorPalette?.accent || '#10b981' }}
                                title="Accent"
                              />
                            </div>

                            {/* Brand Personality */}
                            <p className="text-sm text-gray-300 mb-2">{suggestion.brandPersonality || 'Professional & Trustworthy'}</p>
                            <p className="text-xs text-gray-400">{suggestion.fontFamily || 'Clean Typography'}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Selected Branding Details */}
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <h4 className="text-lg font-medium text-white mb-2">Suggested Tagline</h4>
                    <p className="text-gray-100">{formData.brandingSuggestions.tagline}</p>
                  </div>

                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <h4 className="text-lg font-medium text-white mb-2">About Description</h4>
                    <p className="text-gray-100 leading-relaxed">{formData.brandingSuggestions.about}</p>
                  </div>

                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <h4 className="text-lg font-medium text-white mb-3">Current Applied Brand Colors</h4>
                    <div className="flex gap-4">
                      <div className="text-center">
                        <div
                          className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                          style={{ backgroundColor: currentAppliedTheme?.primary || '#3b82f6' }}
                        ></div>
                        <p className="text-xs text-gray-300 font-medium">Primary</p>
                        <p className="text-xs text-gray-100 font-mono">{currentAppliedTheme?.primary || '#3b82f6'}</p>
                      </div>
                      <div className="text-center">
                        <div
                          className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                          style={{ backgroundColor: currentAppliedTheme?.secondary || '#64748b' }}
                        ></div>
                        <p className="text-xs text-gray-300 font-medium">Secondary</p>
                        <p className="text-xs text-gray-100 font-mono">{currentAppliedTheme?.secondary || '#64748b'}</p>
                      </div>
                      <div className="text-center">
                        <div
                          className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                          style={{ backgroundColor: currentAppliedTheme?.accent || '#10b981' }}
                        ></div>
                        <p className="text-xs text-gray-300 font-medium">Accent</p>
                        <p className="text-xs text-gray-100 font-mono">{currentAppliedTheme?.accent || '#10b981'}</p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-300 mt-2">✓ These colors are currently applied to your app theme</p>
                  </div>

                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <h4 className="text-lg font-medium text-white mb-3">AI Suggested Colors</h4>
                    <div className="flex gap-4">
                      <div className="text-center">
                        <div
                          className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                          style={{ backgroundColor: formData.brandingSuggestions?.colors?.primary || '#3b82f6' }}
                        ></div>
                        <p className="text-xs text-gray-300 font-medium">Primary</p>
                        <p className="text-xs text-gray-100 font-mono">{formData.brandingSuggestions?.colors?.primary || '#3b82f6'}</p>
                      </div>
                      <div className="text-center">
                        <div
                          className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                          style={{ backgroundColor: formData.brandingSuggestions?.colors?.secondary || '#64748b' }}
                        ></div>
                        <p className="text-xs text-gray-300 font-medium">Secondary</p>
                        <p className="text-xs text-gray-100 font-mono">{formData.brandingSuggestions?.colors?.secondary || '#64748b'}</p>
                      </div>
                      <div className="text-center">
                        <div
                          className="w-12 h-12 rounded-lg mb-2 border-2 border-gray-600 shadow-sm"
                          style={{ backgroundColor: formData.brandingSuggestions?.colors?.accent || '#06b6d4' }}
                        ></div>
                        <p className="text-xs text-gray-300 font-medium">Accent</p>
                        <p className="text-xs text-gray-100 font-mono">{formData.brandingSuggestions?.colors?.accent || '#06b6d4'}</p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-300 mt-2">💡 Click "Apply Branding" to use these colors</p>
                  </div>

                  <div className="flex gap-3">
                    <LoadingButton
                      onClick={handleGenerateBranding}
                      isLoading={brandingOperation.isLoading}
                      className="btn-outline flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Regenerate
                    </LoadingButton>
                    <button
                      onClick={handleApplyBranding}
                      className="btn-brand flex-1"
                    >
                      Apply Branding
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {!isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Location & Contact
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Address</label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    className="form-input"
                    placeholder="Enter your address"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">City</label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => handleInputChange('city', e.target.value)}
                    className="form-input"
                    placeholder="Enter your city"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">State</label>
                  <input
                    type="text"
                    value={formData.state}
                    onChange={(e) => handleInputChange('state', e.target.value)}
                    className="form-input"
                    placeholder="Enter your state"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Pincode</label>
                  <input
                    type="text"
                    value={formData.pincode}
                    onChange={(e) => handleInputChange('pincode', e.target.value)}
                    onBlur={() => handleBlur('pincode')}
                    className={`form-input ${validator.hasFieldError('pincode') ? 'border-red-300' : validator.isFieldValid('pincode') ? 'border-green-300' : ''
                      }`}
                    placeholder="Enter your pincode"
                    aria-describedby={validator.hasFieldError('pincode') ? 'pincode-error' : undefined}
                  />
                  {validator.hasFieldError('pincode') && (
                    <p id="pincode-error" className="mt-1 text-sm text-red-400" role="alert">
                      {validator.getFieldError('pincode')}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                Languages & Bio
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Languages Spoken</label>
                  <div className="grid grid-cols-2 gap-2">
                    {availableLanguages.map((language) => (
                      <label key={language} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedLanguages.includes(language)}
                          onChange={() => handleLanguageToggle(language)}
                          className="rounded border-gray-600 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-300">{language}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-gray-300">About Me</label>
                    {formData.brandingSuggestions && (
                      <button
                        type="button"
                        onClick={() => handleInputChange('about', formData.brandingSuggestions?.about || '')}
                        className="btn-outline px-3 py-1 text-xs"
                        title="Use AI suggestion"
                      >
                        Use AI Description
                      </button>
                    )}
                  </div>
                  <textarea
                    value={formData.about}
                    onChange={(e) => handleInputChange('about', e.target.value)}
                    onBlur={() => handleBlur('about')}
                    className={`form-input h-24 resize-none ${validator.hasFieldError('about') ? 'border-red-300' : validator.isFieldValid('about') ? 'border-green-300' : ''
                      }`}
                    placeholder="Tell us about yourself..."
                    aria-describedby={validator.hasFieldError('about') ? 'about-error' : undefined}
                  />
                  {validator.hasFieldError('about') && (
                    <p id="about-error" className="mt-1 text-sm text-red-400" role="alert">
                      {validator.getFieldError('about')}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {!isLoading && (
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mt-12 pt-6 border-t border-white/10">
            <div className="text-sm text-gray-400">
              Last updated: {new Date().toLocaleDateString()}
            </div>
            <div className="flex space-x-4">
              <button
                type="button"
                onClick={() => {
                  setLoadError(null)
                  setRetryCount(0)
                  setIsProfileLoaded(false)
                  loadUserProfile()
                }}
                className="btn-outline px-6 py-2"
                disabled={isLoading || isSaving}
              >
                Reset
              </button>
              <LoadingButton
                onClick={handleSave}
                isLoading={multipleLoading.isLoading('saveProfile')}
                className="btn-primary px-8 py-2 flex items-center gap-2"
              >
                <CheckIcon className="h-4 w-4" />
                Save Changes
              </LoadingButton>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
