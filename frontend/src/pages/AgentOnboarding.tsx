import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBranding } from '../contexts/BrandingContext';
import { useAuth } from '../contexts/AuthContext';
import ColorPicker from '../components/common/ColorPicker';
import FileUpload from '../components/common/FileUpload';
import ProgressBar from '../components/common/ProgressBar';
import { 
  UserIcon, 
  BuildingOfficeIcon, 
  PaintBrushIcon, 
  CheckCircleIcon,
  SparklesIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  completed: boolean;
}

interface AIRecommendations {
  welcome_message: string;
  recommended_specializations: string[];
  suggested_service_areas: string[];
  marketing_tips: string[];
  branding_colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
  suggested_tagline: string;
}

const AgentOnboarding: React.FC = () => {
  const navigate = useNavigate();
  const { branding, updateBranding } = useBranding();
  const { user } = useAuth();
  
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    // Personal Information
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    license_number: '',
    years_experience: 0,
    
    // Company Information
    company_name: '',
    company_description: '',
    
    // Professional Details
    specializations: [] as string[],
    service_areas: [] as string[],
    certifications: [] as string[],
    
    // Branding
    logo: null as File | null,
    primary_color: branding.colors.primary,
    secondary_color: branding.colors.secondary,
    accent_color: branding.colors.accent,
    tagline: ''
  });

  const [aiRecommendations, setAiRecommendations] = useState<AIRecommendations | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);

  const steps: OnboardingStep[] = [
    {
      id: 'personal',
      title: 'Personal Information',
      description: 'Tell us about yourself and your experience',
      icon: UserIcon,
      completed: false
    },
    {
      id: 'company',
      title: 'Company & Branding',
      description: 'Set up your company profile and branding',
      icon: BuildingOfficeIcon,
      completed: false
    },
    {
      id: 'customization',
      title: 'Customize Branding',
      description: 'Personalize your colors and visual identity',
      icon: PaintBrushIcon,
      completed: false
    },
    {
      id: 'review',
      title: 'Review & Complete',
      description: 'Review your profile and finish setup',
      icon: CheckCircleIcon,
      completed: false
    }
  ];

  // Update step completion status
  useEffect(() => {
    const updatedSteps = steps.map((step, index) => {
      let completed = false;
      
      switch (step.id) {
        case 'personal':
          completed = !!(formData.first_name && formData.last_name && formData.email && formData.license_number);
          break;
        case 'company':
          completed = !!(formData.company_name && formData.company_description);
          break;
        case 'customization':
          completed = !!(formData.primary_color && formData.secondary_color && formData.accent_color);
          break;
        case 'review':
          completed = steps.slice(0, 3).every(s => s.completed);
          break;
      }
      
      return { ...step, completed };
    });
    
    // Update branding preview in real-time
    updateBranding({
      colors: {
        primary: formData.primary_color,
        secondary: formData.secondary_color,
        accent: formData.accent_color,
        text: branding.colors.text,
        background: branding.colors.background
      },
      assets: {
        company_name: formData.company_name,
        tagline: formData.tagline
      }
    });
  }, [formData, branding.colors.text, branding.colors.background]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSpecializationChange = (specialization: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      specializations: checked 
        ? [...prev.specializations, specialization]
        : prev.specializations.filter(s => s !== specialization)
    }));
  };

  const handleServiceAreaChange = (area: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      specializations: checked 
        ? [...prev.service_areas, area]
        : prev.service_areas.filter(a => a !== area)
    }));
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Navigate to dashboard
      navigate('/dashboard');
    } catch (error) {
      console.error('Error completing onboarding:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderPersonalInfoStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to World Glass Gen AI</h2>
        <p className="text-gray-600">Let's get to know you and set up your professional profile</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">First Name *</label>
          <input
            type="text"
            value={formData.first_name}
            onChange={(e) => handleInputChange('first_name', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Enter your first name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Last Name *</label>
          <input
            type="text"
            value={formData.last_name}
            onChange={(e) => handleInputChange('last_name', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Enter your last name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="your.email@example.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => handleInputChange('phone', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="+1 (555) 123-4567"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">License Number *</label>
          <input
            type="text"
            value={formData.license_number}
            onChange={(e) => handleInputChange('license_number', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Enter your real estate license number"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Years of Experience</label>
          <select
            value={formData.years_experience}
            onChange={(e) => handleInputChange('years_experience', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value={0}>0 years</option>
            <option value={1}>1 year</option>
            <option value={2}>2 years</option>
            <option value={3}>3 years</option>
            <option value={4}>4 years</option>
            <option value={5}>5+ years</option>
          </select>
        </div>
      </div>

      <div className="mt-8">
        <label className="block text-sm font-medium text-gray-700 mb-4">Specializations</label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {['Residential Sales', 'Commercial', 'Luxury Properties', 'First-time Buyers', 'Investment Properties', 'Rentals'].map((spec) => (
            <label key={spec} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.specializations.includes(spec)}
                onChange={(e) => handleSpecializationChange(spec, e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">{spec}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  const renderCompanyStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Company & Branding</h2>
        <p className="text-gray-600">Set up your company profile and start building your brand</p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Company Name</label>
          <input
            type="text"
            value={formData.company_name}
            onChange={(e) => handleInputChange('company_name', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Your Company Name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Company Description</label>
          <textarea
            value={formData.company_description}
            onChange={(e) => handleInputChange('company_description', e.target.value)}
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Tell us about your company, mission, and what makes you unique..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Company Logo</label>
          <FileUpload
            onFileSelect={(file) => handleInputChange('logo', file)}
            acceptedTypes="image/*"
            maxSize={5 * 1024 * 1024} // 5MB
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Service Areas</label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {['Downtown', 'Suburbs', 'Rural Areas', 'Beachfront', 'Mountain View', 'City Center'].map((area) => (
              <label key={area} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.service_areas.includes(area)}
                  onChange={(e) => handleServiceAreaChange(area, e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">{area}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderCustomizationStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Customize Your Branding</h2>
        <p className="text-gray-600">Choose colors that represent your brand and personality</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Primary Color</label>
            <ColorPicker
              color={formData.primary_color}
              onChange={(color) => handleInputChange('primary_color', color)}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Secondary Color</label>
            <ColorPicker
              color={formData.secondary_color}
              onChange={(color) => handleInputChange('secondary_color', color)}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Accent Color</label>
            <ColorPicker
              color={formData.accent_color}
              onChange={(color) => handleInputChange('accent_color', color)}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Company Tagline</label>
            <input
              type="text"
              value={formData.tagline}
              onChange={(e) => handleInputChange('tagline', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Your unique tagline..."
            />
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Brand Preview</h3>
            
            <div className="space-y-4">
              <div className="text-center">
                {formData.logo && (
                  <img 
                    src={URL.createObjectURL(formData.logo)} 
                    alt="Logo preview" 
                    className="w-20 h-20 mx-auto mb-3 object-contain"
                  />
                )}
                <h4 className="text-xl font-bold" style={{ color: formData.primary_color }}>
                  {formData.company_name || 'Your Company Name'}
                </h4>
                {formData.tagline && (
                  <p className="text-sm text-gray-600 mt-1">{formData.tagline}</p>
                )}
              </div>

              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-6 h-6 rounded-full" 
                    style={{ backgroundColor: formData.primary_color }}
                  />
                  <span className="text-sm text-gray-700">Primary Color</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-6 h-6 rounded-full" 
                    style={{ backgroundColor: formData.secondary_color }}
                  />
                  <span className="text-sm text-gray-700">Secondary Color</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-6 h-6 rounded-full" 
                    style={{ backgroundColor: formData.accent_color }}
                  />
                  <span className="text-sm text-gray-700">Accent Color</span>
                </div>
              </div>

              <button
                onClick={() => setPreviewMode(!previewMode)}
                className="w-full px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors"
                style={{ backgroundColor: formData.primary_color }}
              >
                {previewMode ? 'Hide' : 'Show'} Live Preview
              </button>
            </div>
          </div>

          {previewMode && (
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Live Preview</h3>
              <div className="space-y-3">
                <button 
                  className="w-full px-4 py-2 text-white rounded-lg font-medium"
                  style={{ backgroundColor: formData.primary_color }}
                >
                  Primary Button
                </button>
                <button 
                  className="w-full px-4 py-2 text-white rounded-lg font-medium"
                  style={{ backgroundColor: formData.secondary_color }}
                >
                  Secondary Button
                </button>
                <div 
                  className="w-full px-4 py-2 text-white rounded-lg text-center font-medium"
                  style={{ backgroundColor: formData.accent_color }}
                >
                  Accent Element
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Review Your Profile</h2>
        <p className="text-gray-600">Review all the information before completing your setup</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h3>
            <div className="space-y-2 text-sm">
              <p><span className="font-medium">Name:</span> {formData.first_name} {formData.last_name}</p>
              <p><span className="font-medium">Email:</span> {formData.email}</p>
              <p><span className="font-medium">Phone:</span> {formData.phone || 'Not provided'}</p>
              <p><span className="font-medium">License:</span> {formData.license_number}</p>
              <p><span className="font-medium">Experience:</span> {formData.years_experience} years</p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Company & Branding</h3>
            <div className="space-y-2 text-sm">
              <p><span className="font-medium">Company:</span> {formData.company_name || 'Not provided'}</p>
              <p><span className="font-medium">Tagline:</span> {formData.tagline || 'Not provided'}</p>
              <p><span className="font-medium">Logo:</span> {formData.logo ? 'Uploaded' : 'Not uploaded'}</p>
              <p><span className="font-medium">Specializations:</span> {formData.specializations.join(', ') || 'None selected'}</p>
              <p><span className="font-medium">Service Areas:</span> {formData.service_areas.join(', ') || 'None selected'}</p>
            </div>
          </div>
        </div>

        {aiRecommendations && (
          <div className="mt-6 p-4 bg-gradient-to-r from-primary-50 to-secondary-50 rounded-lg border border-primary-200">
            <div className="flex items-center space-x-2 mb-3">
              <SparklesIcon className="w-5 h-5 text-primary-600" />
              <h4 className="text-lg font-semibold text-primary-900">AI Recommendations</h4>
            </div>
            <p className="text-primary-800 mb-3">{aiRecommendations.welcome_message}</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium text-primary-900 mb-1">Recommended Specializations:</p>
                <ul className="text-primary-800 space-y-1">
                  {aiRecommendations.recommended_specializations.map((spec, index) => (
                    <li key={index} className="flex items-center space-x-2">
                      <CheckCircleIcon className="w-4 h-4 text-primary-600" />
                      <span>{spec}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="font-medium text-primary-900 mb-1">Marketing Tips:</p>
                <ul className="text-primary-800 space-y-1">
                  {aiRecommendations.marketing_tips.map((tip, index) => (
                    <li key={index} className="flex items-center space-x-2">
                      <CheckCircleIcon className="w-4 h-4 text-primary-600" />
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-center space-x-4">
        <button
          onClick={handlePrevious}
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
        >
          Previous
        </button>
        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="px-8 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Setting up...</span>
            </>
          ) : (
            <>
              <span>Complete Setup</span>
              <ArrowRightIcon className="w-5 h-5" />
            </>
          )}
        </button>
      </div>
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 0:
        return renderPersonalInfoStep();
      case 1:
        return renderCompanyStep();
      case 2:
        return renderCustomizationStep();
      case 3:
        return renderReviewStep();
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <ProgressBar 
            current={currentStep + 1} 
            total={steps.length} 
            className="mb-6"
          />
          
          {/* Step Indicators */}
          <div className="flex justify-between items-center">
            {steps.map((step, index) => (
              <div key={step.id} className="flex flex-col items-center">
                <div className={`
                  w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all duration-200
                  ${index <= currentStep 
                    ? 'bg-primary-600 text-white' 
                    : 'bg-gray-200 text-gray-500'
                  }
                  ${step.completed ? 'ring-4 ring-primary-200' : ''}
                `}>
                  {step.completed ? (
                    <CheckCircleIcon className="w-6 h-6" />
                  ) : (
                    <step.icon className="w-6 h-6" />
                  )}
                </div>
                <div className="text-center">
                  <p className={`text-sm font-medium ${
                    index <= currentStep ? 'text-primary-600' : 'text-gray-500'
                  }`}>
                    {step.title}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-xl shadow-lg p-6 md:p-8">
          {renderCurrentStep()}
        </div>

        {/* Navigation */}
        {currentStep < steps.length - 1 && (
          <div className="mt-8 flex justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={handleNext}
              disabled={!steps[currentStep].completed}
              className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <span>Next</span>
              <ArrowRightIcon className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentOnboarding;