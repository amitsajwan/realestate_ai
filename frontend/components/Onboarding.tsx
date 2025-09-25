'use client'

import { LoadingButton } from '@/components/LoadingStates';
import { useAsyncOperation, useMultipleLoading } from '@/hooks/useLoading';
import { BrandingSuggestion } from '@/lib/agent/types';
import { apiService } from '@/lib/api/centralized-client';
import { authManager, User } from '@/lib/auth';
import { withErrorHandling } from '@/lib/error-handler';
import { applyBrandTheme } from '@/lib/theme';
import { ArrowLeftIcon, ArrowRightIcon, BuildingOfficeIcon, CheckIcon, DocumentTextIcon, PhotoIcon, ShareIcon, SparklesIcon, UserIcon } from '@heroicons/react/24/outline';
import { AnimatePresence, motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';

const onboardingSteps = [
  { id: 1, title: 'Personal Info', icon: UserIcon },
  { id: 2, title: 'Company', icon: BuildingOfficeIcon },
  { id: 3, title: 'AI Branding', icon: SparklesIcon },
  { id: 4, title: 'Social', icon: ShareIcon },
  { id: 5, title: 'Terms', icon: DocumentTextIcon },
  { id: 6, title: 'Photo', icon: PhotoIcon }
];

interface OnboardingProps {
  user: User;
  currentStep: number;
  onStepChange: (step: number) => void;
  onComplete: () => void;
}

interface OnboardingFormData {
  first_name: string;
  last_name: string;
  phone: string;
  company: string;
  position: string;
  licenseNumber: string;
  businessType: string;
  targetAudience: string;
  aiStyle: string;
  aiTone: string;
  facebookPage: string;
  termsAccepted: boolean;
  privacyAccepted: boolean;
  profilePhoto: string;
  preferences: string[];
  // Enhanced branding preferences
  brandStyle: string;
  brandPersonality: string;
  brandKeywords: string;
  brandInspiration: string;
  brandingSuggestions: {
    tagline: string;
    about: string;
    colors: {
      primary: string;
      secondary: string;
      accent: string;
    };
  } | null;
}

const Onboarding: React.FC<OnboardingProps> = ({ user, currentStep: initialStep, onStepChange, onComplete }) => {
  // Reduced logging to prevent spam
  console.log('[Onboarding] Component initialized with step:', initialStep);
  const [currentStep, setCurrentStep] = useState(initialStep || 1)
  const [formData, setFormData] = useState<OnboardingFormData>({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    company: user?.company || '',
    position: '',
    licenseNumber: '',
    businessType: 'Residential',
    targetAudience: 'General clients',
    aiStyle: 'Professional',
    aiTone: 'Friendly',
    facebookPage: '',
    termsAccepted: false,
    privacyAccepted: false,
    profilePhoto: '',
    preferences: [],
    // Enhanced branding preferences
    brandStyle: 'Professional',
    brandPersonality: 'Trustworthy',
    brandKeywords: '',
    brandInspiration: '',
    brandingSuggestions: null
  })
  const [brandingSuggestions, setBrandingSuggestions] = useState<BrandingSuggestion[]>([])
  const [selectedBranding, setSelectedBranding] = useState<number | null>(null)

  // Use loading hooks for consistent state management
  const brandingOperation = useAsyncOperation<BrandingSuggestion[]>()
  const multipleLoading = useMultipleLoading()

  // Handle step changes from parent component
  useEffect(() => {
    if (initialStep && initialStep !== currentStep) {
      console.log('[Onboarding] Step changed from parent:', initialStep);
      setCurrentStep(initialStep);
    }
  }, [initialStep]); // Remove currentStep from dependencies to prevent infinite loop

  // Update form data when user object changes (e.g., from server refresh)
  useEffect(() => {
    if (user) {
      console.log('[Onboarding] Updating form data from user object:', {
        first_name: user.first_name,
        last_name: user.last_name,
        phone: user.phone,
        company: user.company
      });
      setFormData(prev => ({
        ...prev,
        first_name: user.first_name || prev.first_name,
        last_name: user.last_name || prev.last_name,
        phone: user.phone || prev.phone,
        company: user.company || prev.company,
        // Keep existing values for fields not in user object
        position: prev.position,
        licenseNumber: prev.licenseNumber
      }));
    }
  }, [user?.id, user?.first_name, user?.last_name, user?.phone, user?.company]);

  // Notify parent of step changes
  useEffect(() => {
    if (onStepChange) {
      onStepChange(currentStep);
    }
  }, [currentStep, onStepChange]);
  const router = useRouter()

  // Note: Removed conflicting useEffect that was resetting step to user.onboarding_step

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const validateCurrentStep = () => {
    switch (currentStep) {
      case 1:
        if (!formData.first_name?.trim()) {
          toast.error('Please enter your first name')
          return false
        }
        if (!formData.last_name?.trim()) {
          toast.error('Please enter your last name')
          return false
        }
        break
      case 2:
        if (!formData.company?.trim()) {
          toast.error('Please enter your company name')
          return false
        }
        if (!formData.position?.trim()) {
          toast.error('Please enter your position')
          return false
        }
        if (!formData.businessType) {
          toast.error('Please select your business type')
          return false
        }
        if (!formData.targetAudience) {
          toast.error('Please select your target audience')
          return false
        }
        break
      case 3:
        if (!formData.aiStyle) {
          toast.error('Please select an AI content style')
          return false
        }
        if (!formData.aiTone) {
          toast.error('Please select an AI tone')
          return false
        }
        break
      case 5:
        if (!formData.termsAccepted) {
          toast.error('Please accept the Terms of Service')
          return false
        }
        if (!formData.privacyAccepted) {
          toast.error('Please accept the Privacy Policy')
          return false
        }
        break
      case 6:
        // Photo step - no validation required, user can skip
        break
    }
    return true
  }

  const handleNext = async () => {
    console.debug('[Onboarding] handleNext called - Current step:', currentStep)
    console.debug('[Onboarding] Form data:', formData)

    // Validate current step before proceeding
    if (!validateCurrentStep()) {
      console.debug('[Onboarding] Validation failed, not proceeding')
      return
    }

    console.debug('[Onboarding] Validation passed, proceeding with step logic')

    if (currentStep < 6) {
      console.debug('[Onboarding] Current step < 6, advancing to next step')
      multipleLoading.setLoading('next', true)

      try {
        // Try to save progress to backend, but don't block navigation if it fails        
        const { error } = await withErrorHandling(
          () => authManager.updateOnboarding(currentStep + 1, formData),
          'Save Onboarding Progress',
          'Progress saved!'
        )

        // if (!error) {
        //   console.info('[Onboarding] updateOnboarding successful, updating step to:', currentStep + 1)
        // } else {
        //   console.warn('[Onboarding] updateOnboarding failed, but continuing with step navigation')
        // }

        // Always update the step, regardless of backend save result
        console.debug('[Onboarding] Setting currentStep to:', currentStep + 1)
        setCurrentStep(currentStep + 1)

      } catch (err) {
        console.error('[Onboarding] Error during update:', err)
        console.warn('[Onboarding] Backend save failed, but continuing with step navigation')

        // Still update the step even if backend save fails
        console.debug('[Onboarding] Setting currentStep to (error case):', currentStep + 1)
        setCurrentStep(currentStep + 1)

        // Show a warning but don't block the user
        toast.error('Progress not saved to server, but you can continue')
      } finally {
        multipleLoading.setLoading('next', false)
      }
    } else if (currentStep === 6) {
      console.debug('[Onboarding] Current step is 6, completing onboarding')
      // Complete onboarding on step 6
      await handleComplete()
    } else {
      console.debug('[Onboarding] Unexpected step:', currentStep)
    }
  }

  const handleComplete = async () => {
    console.debug('[Onboarding] handleComplete called')
    multipleLoading.setLoading('complete', true);

    try {
      console.log('[Onboarding] Starting onboarding completion process');

      // Complete onboarding with all form data
      const { error } = await withErrorHandling(
        () => authManager.updateOnboarding(6, formData, true),
        'Complete Onboarding',
        'Onboarding completed!'
      );

      console.log('[Onboarding] Onboarding completion response:', { error });

      // Force auth state refresh
      await authManager.init();

      // Check auth state after refresh
      const updatedState = authManager.getState();
      console.log('[Onboarding] Auth state after completion:', {
        isAuthenticated: updatedState.isAuthenticated,
        user: updatedState.user,
        onboarding_completed: updatedState.user?.onboarding_completed,
        onboarding_step: updatedState.user?.onboarding_step
      });

      // Call onComplete callback to trigger redirect
      console.log('[Onboarding] Calling onComplete callback');
      onComplete();

    } catch (err) {
      console.error('[Onboarding] Error during completion:', err);
      const errorMessage = err && typeof err === 'object' && 'message' in err && typeof err.message === 'string' ? err.message : 'Failed to complete onboarding';
      toast.error(errorMessage);

      // Even if there's an error, try to redirect
      console.log('[Onboarding] Attempting redirect despite error');
      onComplete();
    } finally {
      multipleLoading.setLoading('complete', false);
    }
  };

  const handleBack = () => {
    console.debug('[Onboarding] handleBack called - Current step:', currentStep)
    if (currentStep > 1) {
      console.debug('[Onboarding] Setting currentStep to:', currentStep - 1)
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    if (currentStep < 6) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleGenerateBranding = async () => {
    if (!formData.company) {
      toast.error('Please enter your company name first')
      return
    }

    console.log('[Onboarding] Generating branding with enhanced data:', {
      company_name: formData.company,
      agent_name: `${formData.first_name} ${formData.last_name}`.trim(),
      position: formData.position,
      business_type: formData.businessType,
      target_audience: formData.targetAudience,
      brand_style: formData.brandStyle,
      brand_personality: formData.brandPersonality,
      brand_keywords: formData.brandKeywords,
      brand_inspiration: formData.brandInspiration
    });

    const response = await brandingOperation.execute(
      () => apiService.getBrandingSuggestions({
        company_name: formData.company,
        agent_name: `${formData.first_name} ${formData.last_name}`.trim(),
        position: formData.position,
        business_type: formData.businessType || 'Residential',
        target_audience: formData.targetAudience || 'General clients',
        brand_style: formData.brandStyle,
        brand_tone: formData.aiTone,
        additionalContext: formData.brandKeywords
      }),
      {
        successMessage: 'Branding suggestions generated successfully!',
        errorMessage: 'Failed to generate branding suggestions'
      }
    )

    if (response?.suggestions && response.suggestions.length > 0) {
      console.log('[Onboarding] Received branding response:', response);

      // Store all suggestions for selection
      setBrandingSuggestions(response.suggestions)
      setSelectedBranding(response.selectedIndex || 0)

      // Transform the selected suggestion for formData
      const selectedSuggestion = response.suggestions[response.selectedIndex || 0]
      const transformedSuggestion = {
        tagline: selectedSuggestion.tagline || `${formData.company} - Professional Real Estate Services`,
        about: selectedSuggestion.about || `Welcome to ${formData.company}, your trusted partner in real estate. We specialize in helping you find your dream home with personalized service and expert guidance.`,
        colors: {
          primary: selectedSuggestion.colorPalette?.primary || selectedSuggestion.primaryColor || '#3b82f6',
          secondary: selectedSuggestion.colorPalette?.secondary || selectedSuggestion.secondaryColor || '#64748b',
          accent: selectedSuggestion.colorPalette?.accent || '#10b981'
        }
      }

      setFormData(prev => ({
        ...prev,
        brandingSuggestions: transformedSuggestion
      }));
    }
  }

  const handleSelectBranding = (index: number) => {
    if (brandingSuggestions[index]) {
      setSelectedBranding(index)
      const selectedSuggestion = brandingSuggestions[index]

      const transformedSuggestion = {
        tagline: selectedSuggestion.tagline || `${formData.company} - Professional Real Estate Services`,
        about: selectedSuggestion.about || `Welcome to ${formData.company}, your trusted partner in real estate. We specialize in helping you find your dream home with personalized service and expert guidance.`,
        colors: {
          primary: selectedSuggestion.colorPalette?.primary || selectedSuggestion.primaryColor || '#3b82f6',
          secondary: selectedSuggestion.colorPalette?.secondary || selectedSuggestion.secondaryColor || '#64748b',
          accent: selectedSuggestion.colorPalette?.accent || '#10b981'
        }
      }

      setFormData(prev => ({
        ...prev,
        brandingSuggestions: transformedSuggestion
      }));
    }
  }

  const handleApplyBranding = async () => {
    if (!formData.brandingSuggestions) {
      toast.error('No branding suggestions available to apply')
      return
    }

    try {
      // Apply the branding theme to the application
      const brandTheme = {
        primary: formData.brandingSuggestions.colors.primary,
        secondary: formData.brandingSuggestions.colors.secondary,
        accent: formData.brandingSuggestions.colors.accent
      }

      console.log('[Onboarding] Applying brand theme:', brandTheme);
      applyBrandTheme(brandTheme) // Now persists by default

      // Save branding data to user profile for future use
      const brandingData = {
        tagline: formData.brandingSuggestions.tagline,
        about: formData.brandingSuggestions.about,
        brand_theme: brandTheme,
        brand_style: formData.brandStyle,
        brand_personality: formData.brandPersonality,
        brand_keywords: formData.brandKeywords,
        brand_inspiration: formData.brandInspiration
      }

      // Update user profile with branding data
      try {
        await authManager.updateOnboarding(currentStep, { ...formData, brandingData })
        console.log('[Onboarding] Branding data saved to user profile');
      } catch (error) {
        console.warn('[Onboarding] Failed to save branding data to profile:', error);
        // Don't block the user if profile update fails
      }

      toast.success('Branding applied and saved successfully! Your website and dashboard will reflect these changes.')

      // Force a page refresh to ensure all components pick up the new theme
      setTimeout(() => {
        if (typeof window !== 'undefined') {
          window.location.reload();
        }
      }, 1000);

    } catch (error) {
      console.error('[Onboarding] Error applying branding:', error);
      toast.error('Failed to apply branding. Please try again.')
    }
  }

  const renderStepContent = () => {
    const step = onboardingSteps[currentStep - 1]

    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6 px-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => handleInputChange('first_name', e.target.value)}
                  className="form-input"
                  placeholder="John"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name *
                </label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => handleInputChange('last_name', e.target.value)}
                  className="form-input"
                  placeholder="Doe"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                className="form-input"
                placeholder="+91 98765 43210"
              />
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6 px-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Name *
              </label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
                className="form-input"
                placeholder="Real Estate Pro"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Position
              </label>
              <input
                type="text"
                value={formData.position}
                onChange={(e) => handleInputChange('position', e.target.value)}
                className="form-input"
                placeholder="Senior Agent"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Type *
                </label>
                <select
                  value={formData.businessType}
                  onChange={(e) => handleInputChange('businessType', e.target.value)}
                  className="form-input"
                >
                  <option value="Residential">Residential</option>
                  <option value="Commercial">Commercial</option>
                  <option value="Luxury">Luxury</option>
                  <option value="Investment">Investment</option>
                  <option value="Mixed">Mixed</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Audience *
                </label>
                <select
                  value={formData.targetAudience}
                  onChange={(e) => handleInputChange('targetAudience', e.target.value)}
                  className="form-input"
                >
                  <option value="First-time buyers">First-time buyers</option>
                  <option value="Luxury clients">Luxury clients</option>
                  <option value="Families">Families</option>
                  <option value="Investors">Investors</option>
                  <option value="General clients">General clients</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                License Number
              </label>
              <input
                type="text"
                value={formData.licenseNumber}
                onChange={(e) => handleInputChange('licenseNumber', e.target.value)}
                className="form-input"
                placeholder="RE123456"
              />
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6 px-2">
            {/* Branding Preferences */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <SparklesIcon className="w-5 h-5 mr-2 text-purple-600" />
                Branding Preferences
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Brand Style
                  </label>
                  <select
                    value={formData.brandStyle}
                    onChange={(e) => handleInputChange('brandStyle', e.target.value)}
                    className="form-input"
                  >
                    <option value="Professional">Professional</option>
                    <option value="Modern">Modern</option>
                    <option value="Traditional">Traditional</option>
                    <option value="Luxury">Luxury</option>
                    <option value="Minimalist">Minimalist</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Brand Personality
                  </label>
                  <select
                    value={formData.brandPersonality}
                    onChange={(e) => handleInputChange('brandPersonality', e.target.value)}
                    className="form-input"
                  >
                    <option value="Trustworthy">Trustworthy</option>
                    <option value="Innovative">Innovative</option>
                    <option value="Friendly">Friendly</option>
                    <option value="Authoritative">Authoritative</option>
                    <option value="Approachable">Approachable</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Brand Keywords
                  </label>
                  <input
                    type="text"
                    value={formData.brandKeywords}
                    onChange={(e) => handleInputChange('brandKeywords', e.target.value)}
                    className="form-input"
                    placeholder="e.g., luxury, family, investment, modern"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Brand Inspiration
                  </label>
                  <input
                    type="text"
                    value={formData.brandInspiration}
                    onChange={(e) => handleInputChange('brandInspiration', e.target.value)}
                    className="form-input"
                    placeholder="e.g., Apple, Mercedes, local competitors"
                  />
                </div>
              </div>

              <div className="text-center py-8">
                <div className="max-w-md mx-auto">
                  <SparklesIcon className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">AI-Powered Branding</h3>
                  <p className="text-gray-600 mb-6">
                    Let our AI create personalized branding suggestions for your real estate business, including colors,
                    fonts, taglines, and content that matches your style and target audience.
                  </p>

                  {(!formData.company || !formData.businessType || !formData.targetAudience) ? (
                    <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg mb-4">
                      <p className="text-sm text-orange-700 mb-2">
                        <strong>Complete these steps first:</strong>
                      </p>
                      <ul className="text-sm text-orange-600 text-left list-disc list-inside space-y-1">
                        {!formData.company && <li>Add your company name</li>}
                        {!formData.businessType && <li>Select your business type</li>}
                        {!formData.targetAudience && <li>Define your target audience</li>}
                      </ul>
                    </div>
                  ) : (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg mb-4">
                      <p className="text-sm text-green-700">
                        ✓ Ready to generate branding for <strong>{formData.company}</strong> targeting <strong>{formData.targetAudience}</strong>
                      </p>
                    </div>
                  )}

                  <LoadingButton
                    onClick={handleGenerateBranding}
                    isLoading={brandingOperation.isLoading}
                    disabled={!formData.company || !formData.businessType || !formData.targetAudience}
                    className="btn-primary px-8 py-3"
                  >
                    {brandingOperation.isLoading ? (
                      <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generating branding ideas...
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <SparklesIcon className="w-4 h-4 mr-2" />
                        {brandingSuggestions.length > 0 ? 'Generate New Ideas' : 'Generate Branding'}
                      </span>
                    )}
                  </LoadingButton>

                  {brandingOperation.error && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-700">
                        <strong>Error:</strong> {String(brandingOperation.error) || 'Failed to generate branding suggestions'}
                      </p>
                      <button
                        onClick={handleGenerateBranding}
                        className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                      >
                        Try again
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* AI Branding Suggestions */}
            {brandingSuggestions.length > 0 && (
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                  <SparklesIcon className="w-5 h-5 mr-2 text-green-600" />
                  Choose Your Brand Style ({brandingSuggestions.length} Options)
                </h3>

                {/* Branding Options Selector */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  {brandingSuggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      onClick={() => handleSelectBranding(index)}
                      className={`cursor-pointer p-4 rounded-lg border-2 transition-all duration-200 ${selectedBranding === index
                        ? 'border-blue-500 bg-blue-50 shadow-md'
                        : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                        }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-gray-800">{suggestion.designStyle}</h4>
                        {selectedBranding === index && (
                          <CheckIcon className="w-5 h-5 text-blue-600" />
                        )}
                      </div>

                      {/* Color Palette Preview */}
                      <div className="flex space-x-2 mb-3">
                        <div
                          className="w-8 h-8 rounded-full border-2 border-white shadow-sm"
                          style={{ backgroundColor: suggestion.colorPalette?.primary || suggestion.primaryColor }}
                          title="Primary"
                        />
                        <div
                          className="w-8 h-8 rounded-full border-2 border-white shadow-sm"
                          style={{ backgroundColor: suggestion.colorPalette?.secondary || suggestion.secondaryColor }}
                          title="Secondary"
                        />
                        <div
                          className="w-8 h-8 rounded-full border-2 border-white shadow-sm"
                          style={{ backgroundColor: suggestion.colorPalette?.accent || '#10b981' }}
                          title="Accent"
                        />
                      </div>

                      {/* Brand Personality */}
                      <p className="text-sm text-gray-600 mb-2">{suggestion.brandPersonality}</p>
                      <p className="text-xs text-gray-500">{suggestion.fontFamily}</p>
                    </div>
                  ))}
                </div>

                {/* Selected Branding Details */}
                {selectedBranding !== null && brandingSuggestions[selectedBranding] && (
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200 mb-4">
                    <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <SparklesIcon className="w-5 h-5 mr-2 text-blue-600" />
                      {brandingSuggestions[selectedBranding].designStyle} Style Preview
                    </h4>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Left Column - Content */}
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Tagline</label>
                          <div className="p-3 bg-white rounded border border-gray-200">
                            <p className="text-gray-800 font-medium">{brandingSuggestions[selectedBranding].tagline}</p>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">About Section</label>
                          <div className="p-3 bg-white rounded border border-gray-200 max-h-32 overflow-y-auto">
                            <p className="text-gray-700 text-sm leading-relaxed">{brandingSuggestions[selectedBranding].about}</p>
                          </div>
                        </div>

                        {/* Logo Ideas */}
                        {brandingSuggestions[selectedBranding].logoIdeas && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Logo Concepts</label>
                            <div className="space-y-2">
                              {brandingSuggestions[selectedBranding].logoIdeas.map((idea: string, idx: number) => (
                                <div key={idx} className="p-2 bg-white rounded border border-gray-200">
                                  <p className="text-sm text-gray-700">{idea}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Right Column - Visual Elements */}
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Color Palette</label>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="text-center">
                              <div
                                className="w-16 h-16 rounded-lg border-2 border-white shadow-md mx-auto mb-2"
                                style={{ backgroundColor: brandingSuggestions[selectedBranding].colorPalette?.primary }}
                              />
                              <span className="text-xs text-gray-600 font-medium">Primary</span>
                              <p className="text-xs text-gray-500">{brandingSuggestions[selectedBranding].colorPalette?.primary}</p>
                            </div>
                            <div className="text-center">
                              <div
                                className="w-16 h-16 rounded-lg border-2 border-white shadow-md mx-auto mb-2"
                                style={{ backgroundColor: brandingSuggestions[selectedBranding].colorPalette?.secondary }}
                              />
                              <span className="text-xs text-gray-600 font-medium">Secondary</span>
                              <p className="text-xs text-gray-500">{brandingSuggestions[selectedBranding].colorPalette?.secondary}</p>
                            </div>
                            <div className="text-center">
                              <div
                                className="w-16 h-16 rounded-lg border-2 border-white shadow-md mx-auto mb-2"
                                style={{ backgroundColor: brandingSuggestions[selectedBranding].colorPalette?.accent || '#10b981' }}
                              />
                              <span className="text-xs text-gray-600 font-medium">Accent</span>
                              <p className="text-xs text-gray-500">{brandingSuggestions[selectedBranding].colorPalette?.accent || '#10b981'}</p>
                            </div>
                            <div className="text-center">
                              <div
                                className="w-16 h-16 rounded-lg border-2 border-white shadow-md mx-auto mb-2"
                                style={{ backgroundColor: brandingSuggestions[selectedBranding].colorPalette?.neutral || '#f7fafc' }}
                              />
                              <span className="text-xs text-gray-600 font-medium">Neutral</span>
                              <p className="text-xs text-gray-500">{brandingSuggestions[selectedBranding].colorPalette?.neutral || '#f7fafc'}</p>
                            </div>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Typography</label>
                          <div className="p-4 bg-white rounded border border-gray-200">
                            <div className="space-y-2">
                              <div style={{ fontFamily: brandingSuggestions[selectedBranding].fontFamily }}>
                                <p className="text-lg font-bold text-gray-800">Heading Sample</p>
                                <p className="text-sm text-gray-600">Body text in {brandingSuggestions[selectedBranding].fontFamily}</p>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Brand Voice</label>
                          <div className="p-3 bg-white rounded border border-gray-200">
                            <p className="text-sm text-gray-700">{brandingSuggestions[selectedBranding].brandVoice}</p>
                            <p className="text-xs text-gray-500 mt-1">{brandingSuggestions[selectedBranding].targetMessage}</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Website Preview */}
                    <div className="mt-6">
                      <label className="block text-sm font-medium text-gray-700 mb-3">Website Preview</label>
                      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
                        {/* Mock Website Header */}
                        <div
                          className="p-4 text-white"
                          style={{
                            backgroundColor: brandingSuggestions[selectedBranding].colorPalette?.primary,
                            fontFamily: brandingSuggestions[selectedBranding].fontFamily
                          }}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <h2 className="text-xl font-bold">{formData.company}</h2>
                              <p className="text-sm opacity-90">{brandingSuggestions[selectedBranding].tagline}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm">{formData.first_name} {formData.last_name}</p>
                              <p className="text-xs opacity-75">{formData.position || 'Real Estate Agent'}</p>
                            </div>
                          </div>
                        </div>

                        {/* Mock Website Content */}
                        <div className="p-4 bg-gray-50">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="md:col-span-2">
                              <h3
                                className="font-semibold mb-2 text-gray-800"
                                style={{ fontFamily: brandingSuggestions[selectedBranding].fontFamily }}
                              >
                                About {formData.company}
                              </h3>
                              <p className="text-sm text-gray-600 leading-relaxed">
                                {brandingSuggestions[selectedBranding].about?.substring(0, 150)}...
                              </p>
                              <button
                                className="mt-3 px-4 py-2 text-white text-sm rounded font-medium"
                                style={{ backgroundColor: brandingSuggestions[selectedBranding].colorPalette?.secondary }}
                              >
                                Contact Us
                              </button>
                            </div>
                            <div className="bg-white p-3 rounded border">
                              <h4
                                className="font-medium mb-2 text-gray-800"
                                style={{
                                  color: brandingSuggestions[selectedBranding].colorPalette?.primary,
                                  fontFamily: brandingSuggestions[selectedBranding].fontFamily
                                }}
                              >
                                Featured Property
                              </h4>
                              <div className="h-20 bg-gray-200 rounded mb-2"></div>
                              <p className="text-xs text-gray-600">Beautiful 3BR home...</p>
                              <div
                                className="mt-2 text-xs font-medium"
                                style={{ color: brandingSuggestions[selectedBranding].colorPalette?.accent || '#10b981' }}
                              >
                                $450,000
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Reasoning */}
                    <div className="mt-4 p-3 bg-blue-100 rounded border border-blue-200">
                      <p className="text-sm text-blue-800">
                        <strong>Why this style:</strong> {brandingSuggestions[selectedBranding].reasoning}
                      </p>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex space-x-3">
                  <LoadingButton
                    onClick={handleGenerateBranding}
                    isLoading={brandingOperation.isLoading}
                    className="btn-outline flex-1"
                  >
                    Generate New Options
                  </LoadingButton>
                  <button
                    onClick={handleApplyBranding}
                    disabled={selectedBranding === null}
                    className="btn-brand flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Apply Selected Style
                  </button>
                </div>
              </div>
            )}

            {/* AI Content Preferences */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Content Style
                </label>
                <select
                  value={formData.aiStyle}
                  onChange={(e) => handleInputChange('aiStyle', e.target.value)}
                  className="form-input"
                >
                  <option value="Professional">Professional</option>
                  <option value="Casual">Casual</option>
                  <option value="Luxury">Luxury</option>
                  <option value="Family-friendly">Family-friendly</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Tone
                </label>
                <select
                  value={formData.aiTone}
                  onChange={(e) => handleInputChange('aiTone', e.target.value)}
                  className="form-input"
                >
                  <option value="Friendly">Friendly</option>
                  <option value="Formal">Formal</option>
                  <option value="Enthusiastic">Enthusiastic</option>
                  <option value="Calm">Calm</option>
                </select>
              </div>
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6 px-2">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Connect Facebook
              </h3>
              <p className="text-gray-600 mb-6">
                Connect your Facebook page to automatically post properties and engage with leads.
              </p>
              <button className="btn-primary">
                Connect Facebook Page
              </button>
            </div>
          </div>
        )

      case 5:
        return (
          <div className="space-y-6 px-2">
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                id="terms"
                checked={formData.termsAccepted}
                onChange={(e) => handleInputChange('termsAccepted', e.target.checked)}
                className="mt-1"
              />
              <label htmlFor="terms" className="text-sm text-gray-700">
                I agree to the Terms of Service and accept the conditions for using PropertyAI.
              </label>
            </div>
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                id="privacy"
                checked={formData.privacyAccepted}
                onChange={(e) => handleInputChange('privacyAccepted', e.target.checked)}
                className="mt-1"
              />
              <label htmlFor="privacy" className="text-sm text-gray-700">
                I have read and agree to the Privacy Policy and consent to the processing of my data.
              </label>
            </div>
          </div>
        )

      case 6:
        return (
          <div className="space-y-6 px-2">
            <div className="text-center">
              <PhotoIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Profile Photo
              </h3>
              <p className="text-gray-600 mb-6">
                Upload a profile photo to personalize your account (optional).
              </p>
              <button className="btn-outline">
                Upload Photo
              </button>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
              <CheckIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <h4 className="text-lg font-semibold text-green-800 mb-1">
                Almost Done!
              </h4>
              <p className="text-green-700 text-sm">
                Click &quot;Complete Setup&quot; to finish your onboarding and start using PropertyAI.
              </p>
              <div className="mt-4 space-x-2">
                <button
                  onClick={() => {
                    console.log('[Onboarding] Force redirect to dashboard');
                    if (typeof window !== 'undefined') {
                      window.location.href = '/dashboard';
                    }
                  }}
                  className="btn-outline text-sm"
                >
                  Force Redirect (Debug)
                </button>
              </div>
            </div>
          </div>
        )



      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="glass-card bg-white p-6 md:p-8">
          {/* Progress Bar */}
          <div className="mb-8 px-2">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-800">
                {onboardingSteps[currentStep - 1].title}
              </h2>
              <span className="text-sm text-gray-500">
                Step {currentStep} of 6
              </span>
            </div>

            {/* Progress Steps */}
            <div className="flex justify-between items-center">
              {onboardingSteps.map((step, index) => (
                <div key={step.id} className="flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors duration-200 ${currentStep > step.id
                    ? 'bg-green-500 text-white'
                    : currentStep === step.id
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-500 hover:bg-gray-300 hover:scale-105'
                    }`}>
                    {currentStep > step.id ? (
                      <CheckIcon className="w-5 h-5" />
                    ) : (
                      <step.icon className="w-5 h-5" />
                    )}
                  </div>
                  <span className="text-xs text-gray-500 mt-1 text-center">
                    {step.title}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Step Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderStepContent()}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200 px-2">
            <div className="flex space-x-3">
              <button
                onClick={handleBack}
                disabled={currentStep === 1}
                className="btn-outline flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowLeftIcon className="w-4 h-4" />
                <span>Back</span>
              </button>

              <button
                onClick={() => {
                  authManager.logout()
                  router.push('/login')
                }}
                className="text-gray-500 hover:text-gray-700 font-medium"
              >
                Logout
              </button>
            </div>

            <div className="flex space-x-3">
              {currentStep < 6 && (
                <button
                  onClick={handleSkip}
                  className="text-gray-500 hover:text-gray-700 font-medium"
                >
                  Skip
                </button>
              )}

              <LoadingButton
                onClick={handleNext}
                isLoading={multipleLoading.isLoading('next') || multipleLoading.isLoading('complete')}
                className="btn-primary flex items-center space-x-2"
              >
                <span>{currentStep === 6 ? 'Complete Onboarding' : 'Next Step'}</span>
                <ArrowRightIcon className="w-4 h-4" />
              </LoadingButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Onboarding;
