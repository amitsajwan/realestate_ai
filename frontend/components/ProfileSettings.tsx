'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { UserIcon, CheckIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { authManager } from '@/lib/auth'
import { apiService } from '@/lib/api'
import { applyBrandTheme } from '@/lib/theme'
import { handleError, showSuccess, withErrorHandling } from '@/lib/error-handler'
import { User, BrandingSuggestion, OnboardingFormData } from '@/types/user'
import { useAsyncOperation, useMultipleLoading } from '@/hooks/useLoading'
import { LoadingButton, LoadingOverlay } from '@/components/LoadingStates'
import { toast } from 'react-hot-toast'
import { profileSettingsSchema, FormValidator } from '@/lib/form-validation'

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
}

export default function ProfileSettings() {
  const [formData, setFormData] = useState<UserProfile>({
    user_id: 'default_user',
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
    brandingSuggestions: null
  })

  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([])
  
  // Use loading hooks for consistent state management
  const profileOperation = useAsyncOperation<UserProfile>()
  const brandingOperation = useAsyncOperation<BrandingSuggestions>()
  const multipleLoading = useMultipleLoading()
  
  // Form validation
  const validator = new FormValidator(profileSettingsSchema)
  
  const isLoading = profileOperation.isLoading
  const isSaving = multipleLoading.isLoading('saveProfile')

  const availableLanguages = [
    'English', 'Hindi', 'Marathi', 'Gujarati', 'Tamil', 'Telugu', 
    'Kannada', 'Malayalam', 'Bengali', 'Punjabi', 'Urdu', 'Other'
  ]

  const loadUserProfile = useCallback(async () => {
    await profileOperation.execute(async () => {
      // Get current user from auth manager
      const authState = authManager.getState()
      const currentUser = authState.user
      
      // Try to load from backend API first
      let profileData = null
      try {
        const response = await apiService.getDefaultUserProfile()
        if (response) {
          profileData = response;
        }
      } catch (error) {
  console.info('[ProfileSettings] No existing profile found, will use onboarding data')
      }
      
      // Merge onboarding data with profile data, prioritizing profile data
      const mergedData = {
        user_id: profileData?.id || 'default_user',
        name: profileData?.firstName && profileData?.lastName ? `${profileData.firstName} ${profileData.lastName}`.trim() : (currentUser ? `${currentUser.firstName || ''} ${currentUser.lastName || ''}`.trim() : ''),
        email: profileData?.email || currentUser?.email || '',
        phone: profileData?.phone || currentUser?.phone || '',
        whatsapp: currentUser?.phone || '',
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
        logo_url: ''
      }
      
      setFormData(mergedData)
      setSelectedLanguages(mergedData.languages || [])
      
      // If we have onboarding data but no profile, show a message
      if (currentUser && !profileData) {
        toast.success('Onboarding data loaded! Please review and save your profile.')
      }
      
      return mergedData
    })
  }, [profileOperation])

  useEffect(() => {
    loadUserProfile()
  }, [loadUserProfile])

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
      await apiService.updateProfile({ ...formData })
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

    const suggestions = await brandingOperation.execute(
      () => apiService.getBrandingSuggestions({
        company_name: formData.company || '',
        agent_name: formData.name,
        position: formData.specialization_areas
      }),
      {
        successMessage: 'AI branding suggestions generated successfully!',
        errorMessage: 'Failed to generate branding suggestions'
      }
    )
    
    if (suggestions) {
      setFormData(prev => ({
        ...prev,
        brandingSuggestions: suggestions
      }))
    }
  }

  const handleApplyBranding = () => {
    if (!formData.brandingSuggestions) return

    const brandTheme = {
      primary: formData.brandingSuggestions.colors.primary,
      secondary: formData.brandingSuggestions.colors.secondary,
      accent: formData.brandingSuggestions.colors.accent
    }

    applyBrandTheme(brandTheme) // Now persists by default
    toast.success('Brand theme applied and saved!')
  }

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
                    className={`form-input ${
                      validator.hasFieldError('name') ? 'border-red-300' : validator.isFieldValid('name') ? 'border-green-300' : ''
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
                    className={`form-input ${
                      validator.hasFieldError('email') ? 'border-red-300' : validator.isFieldValid('email') ? 'border-green-300' : ''
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
                    className={`form-input ${
                      validator.hasFieldError('phone') ? 'border-red-300' : validator.isFieldValid('phone') ? 'border-green-300' : ''
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
                    className={`form-input ${
                      validator.hasFieldError('whatsapp') ? 'border-red-300' : validator.isFieldValid('whatsapp') ? 'border-green-300' : ''
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
                      value={formData.tagline}
                      onChange={(e) => handleInputChange('tagline', e.target.value)}
                      onBlur={() => handleBlur('tagline')}
                      className={`form-input flex-1 ${
                        validator.hasFieldError('tagline') ? 'border-red-300' : validator.isFieldValid('tagline') ? 'border-green-300' : ''
                      }`}
                      placeholder="Your professional tagline"
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

            {/* AI Branding Section */}
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <SparklesIcon className="w-5 h-5 text-purple-400" />
                AI Branding
              </h3>
              
              {!formData.brandingSuggestions ? (
                <div className="text-center py-8">
                  <p className="text-gray-400 mb-4">Generate AI-powered branding suggestions for your business</p>
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
                <div className="space-y-4">
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-white mb-2">Suggested Tagline</h4>
                    <p className="text-gray-300">{formData.brandingSuggestions.tagline}</p>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-white mb-2">About Description</h4>
                    <p className="text-gray-300">{formData.brandingSuggestions.about}</p>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-white mb-3">Brand Colors</h4>
                    <div className="flex gap-4">
                      <div className="text-center">
                        <div 
                          className="w-12 h-12 rounded-lg mb-2 border border-gray-600" 
                          style={{ backgroundColor: formData.brandingSuggestions.colors.primary }}
                        ></div>
                        <p className="text-xs text-gray-400">Primary</p>
                        <p className="text-xs text-white font-mono">{formData.brandingSuggestions.colors.primary}</p>
                      </div>
                      <div className="text-center">
                        <div 
                          className="w-12 h-12 rounded-lg mb-2 border border-gray-600" 
                          style={{ backgroundColor: formData.brandingSuggestions.colors.secondary }}
                        ></div>
                        <p className="text-xs text-gray-400">Secondary</p>
                        <p className="text-xs text-white font-mono">{formData.brandingSuggestions.colors.secondary}</p>
                      </div>
                      <div className="text-center">
                        <div 
                          className="w-12 h-12 rounded-lg mb-2 border border-gray-600" 
                          style={{ backgroundColor: formData.brandingSuggestions.colors.accent }}
                        ></div>
                        <p className="text-xs text-gray-400">Accent</p>
                        <p className="text-xs text-white font-mono">{formData.brandingSuggestions.colors.accent}</p>
                      </div>
                    </div>
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
                    className={`form-input ${
                      validator.hasFieldError('pincode') ? 'border-red-300' : validator.isFieldValid('pincode') ? 'border-green-300' : ''
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
                    className={`form-input h-24 resize-none ${
                      validator.hasFieldError('about') ? 'border-red-300' : validator.isFieldValid('about') ? 'border-green-300' : ''
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
                onClick={loadUserProfile}
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
