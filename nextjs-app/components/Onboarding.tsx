'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { 
  UserIcon, 
  BuildingOfficeIcon, 
  SparklesIcon, 
  ShieldCheckIcon,
  PhotoIcon,
  CheckIcon,
  ArrowLeftIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline'
import { authManager, User } from '@/lib/auth'
import toast from 'react-hot-toast'

interface OnboardingProps {
  user: User
  onComplete: () => void
}

const onboardingSteps = [
  {
    id: 1,
    title: 'Personal Information',
    description: 'Tell us about yourself',
    icon: UserIcon,
    fields: ['firstName', 'lastName', 'phone']
  },
  {
    id: 2,
    title: 'Company Details',
    description: 'Your business information',
    icon: BuildingOfficeIcon,
    fields: ['company', 'position', 'licenseNumber']
  },
  {
    id: 3,
    title: 'AI Branding',
    description: 'Customize your AI assistant',
    icon: SparklesIcon,
    fields: ['aiStyle', 'aiTone']
  },
  {
    id: 4,
    title: 'Facebook Connect',
    description: 'Connect your social media',
    icon: BuildingOfficeIcon,
    fields: ['facebookPage']
  },
  {
    id: 5,
    title: 'Compliance',
    description: 'Legal requirements',
    icon: ShieldCheckIcon,
    fields: ['termsAccepted', 'privacyAccepted']
  },
  {
    id: 6,
    title: 'Profile Setup',
    description: 'Photo & preferences',
    icon: PhotoIcon,
    fields: ['profilePhoto', 'preferences']
  },
  {
    id: 7,
    title: 'Complete',
    description: 'You\'re all set!',
    icon: CheckIcon,
    fields: []
  }
]

export default function Onboarding({ user, onComplete }: OnboardingProps) {
  const [currentStep, setCurrentStep] = useState(user.onboardingStep || 1)
  const [formData, setFormData] = useState({
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
    preferences: []
  })
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleNext = async () => {
    if (currentStep < 7) {
      setIsLoading(true)
      try {
        await authManager.updateOnboarding(currentStep + 1, formData)
        setCurrentStep(currentStep + 1)
        toast.success('Progress saved!')
      } catch (error) {
        toast.error('Failed to save progress')
      } finally {
        setIsLoading(false)
      }
    } else {
      onComplete()
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    if (currentStep < 7) {
      setCurrentStep(currentStep + 1)
    }
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
          </div>
        )

      case 7:
        return (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <CheckIcon className="w-10 h-10 text-green-600" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">
                Welcome to PropertyAI!
              </h3>
              <p className="text-gray-600">
                Your account is now set up and ready to use. Start exploring the platform and discover how AI can help you succeed in real estate.
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
                Step {currentStep} of 7
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
              {currentStep < 7 && (
                <button
                  onClick={handleSkip}
                  className="text-gray-500 hover:text-gray-700 font-medium"
                >
                  Skip
                </button>
              )}
              
              <button
                onClick={handleNext}
                disabled={isLoading}
                className="btn-primary flex items-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <span>{currentStep === 7 ? 'Get Started' : 'Next'}</span>
                    <ArrowRightIcon className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
