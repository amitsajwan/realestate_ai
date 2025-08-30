import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { authManager } from '@/lib/auth'
import { apiService } from '@/lib/api'
import { handleError, showSuccess, withErrorHandling } from '@/lib/error-handler'
import { BrandingSuggestion } from '@/types/user'
import { useAsyncOperation, useMultipleLoading } from '@/hooks/useLoading'
import { LoadingButton, LoadingOverlay } from '@/components/LoadingStates';
import { applyBrandTheme } from '@/lib/theme';
import { UserIcon, BuildingOfficeIcon, SparklesIcon, ShareIcon, DocumentTextIcon, PhotoIcon, CheckIcon, ArrowRightIcon } from '@heroicons/react/24/outline';
import { validatePassword } from '@/lib/validation';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const onboardingSteps = [
  { id: 1, title: 'Personal Info', icon: UserIcon },
  { id: 2, title: 'Company', icon: BuildingOfficeIcon },
  { id: 3, title: 'AI Branding', icon: SparklesIcon },
  { id: 4, title: 'Social', icon: ShareIcon },
  { id: 5, title: 'Terms', icon: DocumentTextIcon },
  { id: 6, title: 'Photo', icon: PhotoIcon }
];

interface OnboardingProps {
  user: {
    id: string;
    email: string;
    first_name?: string;
    last_name?: string;
    phone?: string;
    onboarding_completed?: boolean;
    onboardingStep?: number;
    firstName?: string;
    lastName?: string;
    company?: string;
    position?: string;
    licenseNumber?: string;
  };
  currentStep: number;
  onStepChange: (step: number) => void;
  onComplete: () => void;
}

interface OnboardingFormData {
  firstName: string;
  lastName: string;
  phone: string;
  company: string;
  position: string;
  licenseNumber: string;
  aiStyle: string;
  aiTone: string;
  facebookPage: string;
  termsAccepted: boolean;
  privacyAccepted: boolean;
  profilePhoto: string;
  preferences: string[];
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
  console.log('[Onboarding] User object:', user);
  const [currentStep, setCurrentStep] = useState(user.onboardingStep || 1)
  const [formData, setFormData] = useState<OnboardingFormData>({
    firstName: user.firstName || '',
    lastName: user.lastName || '',
    phone: user.phone || '',
    company: user.company || '',
    position: user.position || '',
    licenseNumber: user.licenseNumber || '',
    aiStyle: 'Professional',
    aiTone: 'Friendly',
    facebookPage: '',
    termsAccepted: false,
    privacyAccepted: false,
    profilePhoto: '',
    preferences: [],
    brandingSuggestions: null
  })
  const [brandingSuggestions, setBrandingSuggestions] = useState<BrandingSuggestion[]>([])
  const [selectedBranding, setSelectedBranding] = useState<number | null>(null)
  
  // Use loading hooks for consistent state management
  const brandingOperation = useAsyncOperation<BrandingSuggestion[]>()
  const multipleLoading = useMultipleLoading()
  const router = useRouter()

  // Sync currentStep with user prop changes
  useEffect(() => {
    if (user.onboardingStep && user.onboardingStep !== currentStep) {
      setCurrentStep(user.onboardingStep)
    }
  }, [user.onboardingStep, currentStep])

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const validateCurrentStep = () => {
    switch (currentStep) {
      case 1:
        if (!formData.firstName?.trim()) {
          toast.error('Please enter your first name')
          return false
        }
        if (!formData.lastName?.trim()) {
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
    }
    return true
  }

  const handleNext = async () => {
  console.debug('[Onboarding] handleNext called - Current step:', currentStep)
  console.debug('[Onboarding] Form data:', formData)
    
    // Validate current step before proceeding
    if (!validateCurrentStep()) {
      return
    }
    
    if (currentStep < 6) {
      multipleLoading.setLoading('next', true)
      
      try {
        const { error } = await withErrorHandling(
          () => authManager.updateOnboarding(currentStep + 1, formData),
          'Save Onboarding Progress',
          'Progress saved!'
        )
        
        if (!error) {
          console.info('[Onboarding] updateOnboarding successful, updating step to:', currentStep + 1)
          setCurrentStep(currentStep + 1)
        }
      } catch (err) {
        console.error('[Onboarding] Error during update:', err)
        const errorMessage = err && typeof err === 'object' && 'message' in err && typeof err.message === 'string' ? err.message : 'Failed to update onboarding information'
        toast.error(errorMessage)
      } finally {
        multipleLoading.setLoading('next', false)
      }
    } else {
      // Complete onboarding on step 6
      await handleComplete()
    }
  }

  const handleComplete = async () => {
    multipleLoading.setLoading('complete', true);
    
    try {
      console.log('[Onboarding] Starting onboarding completion process');
      const { error } = await withErrorHandling(
        () => authManager.updateOnboarding(6, formData, true),
        'Complete Onboarding',
        'Onboarding completed!'
      );
      
      if (!error) {
        console.log('[Onboarding] Onboarding completed successfully, calling onComplete callback');
        // Force a small delay to ensure state updates are processed
        setTimeout(() => {
          console.log('[Onboarding] Executing onComplete callback after delay');
          onComplete();
        }, 1000); // Increased delay to ensure state updates are processed
      }
    } catch (err) {
      console.error('[Onboarding] Error during completion:', err);
      const errorMessage = err && typeof err === 'object' && 'message' in err && typeof err.message === 'string' ? err.message : 'Failed to complete onboarding';
      toast.error(errorMessage);
    } finally {
      multipleLoading.setLoading('complete', false);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
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

    const suggestions = await brandingOperation.execute(
      () => apiService.getBrandingSuggestions({
        company_name: formData.company,
        agent_name: `${formData.firstName} ${formData.lastName}`.trim(),
        position: formData.position
      }),
      {
        successMessage: 'Branding suggestions generated successfully!',
        errorMessage: 'Failed to generate branding suggestions'
      }
    )
    
    if (suggestions) {
      handleInputChange('brandingSuggestions', suggestions)
    }
  }

  const handleApplyBranding = () => {
    if (!formData.brandingSuggestions) return

    // Apply the branding theme to the application
    const brandTheme = {
      primary: formData.brandingSuggestions.colors.primary,
      secondary: formData.brandingSuggestions.colors.secondary,
      accent: formData.brandingSuggestions.colors.accent
    }
    
    applyBrandTheme(brandTheme) // Now persists by default
    toast.success('Branding applied and saved successfully!')
  }

  const renderStepContent = () => {
    const step = onboardingSteps[currentStep - 1]

    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
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
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
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
          <div className="space-y-6">
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
          <div className="space-y-6">
            {/* AI Branding Suggestions */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <SparklesIcon className="w-5 h-5 mr-2 text-purple-600" />
                AI Branding Suggestions
              </h3>
              
              {formData.brandingSuggestions ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Suggested Tagline
                    </label>
                    <div className="p-3 bg-white rounded border">
                      <p className="text-gray-800 font-medium">{formData.brandingSuggestions.tagline}</p>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      About Description
                    </label>
                    <div className="p-3 bg-white rounded border">
                      <p className="text-gray-700">{formData.brandingSuggestions.about}</p>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Brand Colors
                    </label>
                    <div className="flex space-x-4">
                      <div className="text-center">
                        <div 
                          className="w-12 h-12 rounded-full border-2 border-gray-300 mx-auto mb-1"
                          style={{ backgroundColor: formData.brandingSuggestions.colors.primary }}
                        ></div>
                        <span className="text-xs text-gray-600">Primary</span>
                      </div>
                      <div className="text-center">
                        <div 
                          className="w-12 h-12 rounded-full border-2 border-gray-300 mx-auto mb-1"
                          style={{ backgroundColor: formData.brandingSuggestions.colors.secondary }}
                        ></div>
                        <span className="text-xs text-gray-600">Secondary</span>
                      </div>
                      <div className="text-center">
                        <div 
                          className="w-12 h-12 rounded-full border-2 border-gray-300 mx-auto mb-1"
                          style={{ backgroundColor: formData.brandingSuggestions.colors.accent }}
                        ></div>
                        <span className="text-xs text-gray-600">Accent</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-3">
                    <LoadingButton
                      onClick={handleGenerateBranding}
                      isLoading={brandingOperation.isLoading}
                      className="btn-outline flex-1"
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
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600 mb-4">
                    Generate AI-powered branding suggestions based on your company name
                  </p>
                  <LoadingButton
                    onClick={handleGenerateBranding}
                    isLoading={brandingOperation.isLoading}
                    disabled={!formData.company}
                    className="btn-primary"
                  >
                    Generate Branding
                  </LoadingButton>
                  {!formData.company && (
                    <p className="text-sm text-orange-600 mt-2">
                      Please enter your company name in the previous step
                    </p>
                  )}
                </div>
              )}
            </div>
            
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
           <div className="space-y-6">
             <div className="text-center">
               <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                 <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                   <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
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
          <div className="space-y-6">
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
          <div className="space-y-6">
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
                Click "Complete Setup" to finish your onboarding and start using PropertyAI.
              </p>
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
        <div className="glass-card">
          {/* Progress Bar */}
          <div className="mb-8">
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
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium ${
                    currentStep > step.id 
                      ? 'bg-green-500 text-white' 
                      : currentStep === step.id 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-gray-200 text-gray-500'
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
           <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
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
