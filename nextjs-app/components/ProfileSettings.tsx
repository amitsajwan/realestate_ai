'use client'

import React, { useState, useEffect } from 'react'
import { UserIcon, CheckIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { authManager } from '@/lib/auth'
import { apiService } from '@/lib/api'
import { applyBrandTheme } from '@/lib/theme'
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
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  const availableLanguages = [
    'English', 'Hindi', 'Marathi', 'Gujarati', 'Tamil', 'Telugu', 
    'Kannada', 'Malayalam', 'Bengali', 'Punjabi', 'Urdu', 'Other'
  ]

  useEffect(() => {
    loadUserProfile()
  }, [])

  const loadUserProfile = async () => {
    setIsLoading(true)
    try {
      // Get current user from auth manager
      const authState = authManager.getState()
      const currentUser = authState.user
      
      // Try to load from backend API first
      let profileData = null
      try {
        const response = await apiService.getDefaultUserProfile()
        if (response.success && response.data) {
          profileData = response.data
        }
      } catch (error) {
        console.log('No existing profile found, will use onboarding data')
      }
      
      // Merge onboarding data with profile data, prioritizing profile data
      const mergedData = {
        user_id: profileData?.user_id || 'default_user',
        name: profileData?.name || (currentUser ? `${currentUser.firstName || ''} ${currentUser.lastName || ''}`.trim() : ''),
        email: profileData?.email || currentUser?.email || '',
        phone: profileData?.phone || currentUser?.phone || '',
        whatsapp: profileData?.whatsapp || currentUser?.phone || '',
        company: profileData?.company || currentUser?.company || '',
        experience_years: profileData?.experience_years || '0',
        specialization_areas: Array.isArray(profileData?.specialization_areas) 
          ? profileData.specialization_areas.join(', ') 
          : (profileData?.specialization_areas || ''),
        tagline: profileData?.tagline || '',
        social_bio: profileData?.social_bio || '',
        about: profileData?.about || '',
        address: profileData?.address || '',
        city: profileData?.city || '',
        state: profileData?.state || '',
        pincode: profileData?.pincode || '',
        languages: profileData?.languages || [],
        logo_url: profileData?.logo_url || ''
      }
      
      setFormData(mergedData)
      setSelectedLanguages(mergedData.languages || [])
      
      // If we have onboarding data but no profile, show a message
      if (currentUser && !profileData) {
        toast.success('Onboarding data loaded! Please review and save your profile.')
      }
      
    } catch (error) {
      console.error('Failed to load profile:', error)
      toast.error('Failed to load profile data')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (field: keyof UserProfile, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleLanguageToggle = (language: string) => {
    const updatedLanguages = selectedLanguages.includes(language)
      ? selectedLanguages.filter(lang => lang !== language)
      : [...selectedLanguages, language]
    
    setSelectedLanguages(updatedLanguages)
    handleInputChange('languages', updatedLanguages)
  }

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error('Name is required')
      return
    }

    if (!formData.email.trim()) {
      toast.error('Email is required')
      return
    }

    setIsSaving(true)
    try {
      // Ensure data types match backend expectations
      const profileData = {
        ...formData
      }
      
      const response = await apiService.createOrUpdateProfile(profileData)
      if (response.success) {
        toast.success('Profile saved successfully!')
      } else {
        throw new Error(response.message || 'Failed to save profile')
      }
    } catch (error: any) {
      console.error('Save error:', error)
      
      // Parse detailed error messages from server response
      if (error.response?.data?.detail) {
        // Handle validation errors
        if (typeof error.response.data.detail === 'string') {
          toast.error(error.response.data.detail)
        } else if (Array.isArray(error.response.data.detail)) {
          // Handle Pydantic validation errors
          const errorMessages = error.response.data.detail.map((err: any) => 
            `${err.loc?.join(' → ') || 'Field'}: ${err.msg}`
          ).join('\n')
          toast.error(`Validation errors:\n${errorMessages}`)
        } else {
          toast.error('Validation failed. Please check your input.')
        }
      } else if (error.message) {
        toast.error(error.message)
      } else {
        toast.error('Failed to save profile. Please try again.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  const handleGenerateBranding = async () => {
    if (!formData.company?.trim()) {
      toast.error('Please enter your company name first')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/v1/agent/branding-suggest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: formData.company,
          agent_name: formData.name,
          specialization_areas: formData.specialization_areas,
          experience_years: formData.experience_years,
          location: `${formData.city || ''} ${formData.state || ''}`.trim() || 'Not specified',
          phone: formData.phone
        })
      })

      if (!response.ok) {
        throw new Error('Failed to generate branding suggestions')
      }

      const data = await response.json()
      setFormData(prev => ({
        ...prev,
        brandingSuggestions: data
      }))
      toast.success('AI branding suggestions generated!')
    } catch (error) {
      console.error('Branding generation error:', error)
      toast.error('Failed to generate branding suggestions')
    } finally {
      setIsLoading(false)
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
                  <label className="block text-sm font-medium text-gray-300 mb-2">Full Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="form-input"
                    placeholder="Enter your full name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Email *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className="form-input"
                    placeholder="Enter your email"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Phone</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    className="form-input"
                    placeholder="Enter your phone number"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">WhatsApp</label>
                  <input
                    type="tel"
                    value={formData.whatsapp}
                    onChange={(e) => handleInputChange('whatsapp', e.target.value)}
                    className="form-input"
                    placeholder="Enter your WhatsApp number"
                  />
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
                      className="form-input flex-1"
                      placeholder="Your professional tagline"
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
                  <button
                    onClick={handleGenerateBranding}
                    disabled={isLoading || !formData.company?.trim()}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Generating...' : 'Generate Branding'}
                  </button>
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
                    <button
                      onClick={handleGenerateBranding}
                      disabled={isLoading}
                      className="btn-outline flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? 'Regenerating...' : 'Regenerate'}
                    </button>
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
                    className="form-input"
                    placeholder="Enter your pincode"
                  />
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
                    className="form-input h-24 resize-none"
                    placeholder="Tell us about yourself..."
                  />
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
              <button
                type="button"
                onClick={handleSave}
                disabled={isSaving}
                className="btn-primary px-8 py-2 flex items-center gap-2"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <CheckIcon className="h-4 w-4" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
