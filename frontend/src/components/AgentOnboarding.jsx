import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  UserIcon, PaletteIcon, TargetIcon, CogIcon, ShieldCheckIcon,
  ChevronRightIcon, CheckIcon, SparklesIcon, UploadIcon
} from '@heroicons/react/24/outline';

const AgentOnboarding = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [agentData, setAgentData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    company_name: '',
    license_number: '',
    experience_years: 0,
    bio: '',
    specialties: [],
    service_areas: [],
    property_types: [],
    price_ranges: [],
    logo_url: '',
    brand_name: '',
    tagline: '',
    primary_color: '#3B82F6',
    secondary_color: '#1E40AF',
    accent_color: '#F59E0B',
    text_color: '#1F2937',
    background_color: '#FFFFFF'
  });
  
  const [aiSuggestions, setAiSuggestions] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const steps = [
    {
      id: 'profile',
      title: 'Complete Your Profile',
      description: 'Add your basic information and experience',
      icon: UserIcon,
      required: true
    },
    {
      id: 'branding',
      title: 'Set Up Your Brand',
      description: 'Customize your visual identity and colors',
      icon: PaletteIcon,
      required: true
    },
    {
      id: 'specialties',
      title: 'Define Your Specialties',
      description: 'Select your focus areas and service regions',
      icon: TargetIcon,
      required: true
    },
    {
      id: 'crm_setup',
      title: 'Configure Your CRM',
      description: 'Set up AI preferences and automation',
      icon: CogIcon,
      required: false
    },
    {
      id: 'verification',
      title: 'Verify Your Account',
      description: 'Upload required documents for verification',
      icon: ShieldCheckIcon,
      required: true
    }
  ];

  const specialties = [
    'Residential', 'Commercial', 'Luxury', 'Investment', 'First-time Buyers',
    'Move-up Buyers', 'Seniors', 'New Construction', 'Foreclosures', 'Short Sales'
  ];

  const propertyTypes = [
    'Single Family', 'Condo', 'Townhouse', 'Multi-family', 'Land',
    'Commercial', 'Industrial', 'Mixed Use'
  ];

  const priceRanges = [
    'Under $200k', '$200k-$500k', '$500k-$1M', '$1M-$2M', '$2M+'
  ];

  const handleInputChange = (field, value) => {
    setAgentData(prev => ({ ...prev, [field]: value }));
  };

  const handleSpecialtyToggle = (specialty) => {
    setAgentData(prev => ({
      ...prev,
      specialties: prev.specialties.includes(specialty)
        ? prev.specialties.filter(s => s !== specialty)
        : [...prev.specialties, specialty]
    }));
  };

  const handlePropertyTypeToggle = (type) => {
    setAgentData(prev => ({
      ...prev,
      property_types: prev.property_types.includes(type)
        ? prev.property_types.filter(t => t !== type)
        : [...prev.property_types, type]
    }));
  };

  const handlePriceRangeToggle = (range) => {
    setAgentData(prev => ({
      ...prev,
      price_ranges: prev.price_ranges.includes(range)
        ? prev.price_ranges.filter(r => r !== range)
        : [...prev.price_ranges, range]
    }));
  };

  const handleColorChange = (colorField, value) => {
    setAgentData(prev => ({ ...prev, [colorField]: value }));
  };

  const handleLogoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsLoading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 10;
      });
    }, 100);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const logoUrl = URL.createObjectURL(file);
      handleInputChange('logo_url', logoUrl);
      setUploadProgress(100);
      
      setTimeout(() => setUploadProgress(0), 1000);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getAISuggestions = async () => {
    setIsLoading(true);
    try {
      // Simulate AI API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const suggestions = {
        brand_name_suggestions: [
          `${agentData.company_name || agentData.first_name} Real Estate Group`,
          'Elite Properties',
          'Premier Realty'
        ],
        tagline_options: [
          'Your Trusted Real Estate Partner',
          'Excellence in Every Transaction',
          'Where Dreams Find Homes'
        ],
        color_scheme: {
          primary: '#3B82F6',
          secondary: '#1E40AF',
          accent: '#F59E0B',
          text: '#1F2937',
          background: '#FFFFFF'
        }
      };
      
      setAiSuggestions(suggestions);
    } catch (error) {
      console.error('Failed to get AI suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    const step = steps[currentStep];
    if (!step.required) return true;
    
    switch (step.id) {
      case 'profile':
        return agentData.first_name && agentData.last_name && agentData.email;
      case 'branding':
        return agentData.brand_name || agentData.logo_url;
      case 'specialties':
        return agentData.specialties.length > 0 && agentData.service_areas.length > 0;
      case 'verification':
        return true; // Always allow proceeding
      default:
        return true;
    }
  };

  const renderStepContent = () => {
    const step = steps[currentStep];
    
    switch (step.id) {
      case 'profile':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  value={agentData.first_name}
                  onChange={(e) => handleInputChange('first_name', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your first name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name *
                </label>
                <input
                  type="text"
                  value={agentData.last_name}
                  onChange={(e) => handleInputChange('last_name', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your last name"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email *
                </label>
                <input
                  type="email"
                  value={agentData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your email"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  value={agentData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your phone number"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Name
              </label>
              <input
                type="text"
                value={agentData.company_name}
                onChange={(e) => handleInputChange('company_name', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your company name"
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  License Number
                </label>
                <input
                  type="text"
                  value={agentData.license_number}
                  onChange={(e) => handleInputChange('license_number', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your license number"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Years of Experience
                </label>
                <input
                  type="number"
                  value={agentData.experience_years}
                  onChange={(e) => handleInputChange('experience_years', parseInt(e.target.value) || 0)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0"
                  min="0"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bio
              </label>
              <textarea
                value={agentData.bio}
                onChange={(e) => handleInputChange('bio', e.target.value)}
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Tell us about yourself and your real estate expertise..."
              />
            </div>
          </motion.div>
        );

      case 'branding':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg">
              <div className="flex items-center gap-3 mb-4">
                <SparklesIcon className="h-6 w-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">AI-Powered Branding Suggestions</h3>
              </div>
              <button
                onClick={getAISuggestions}
                disabled={isLoading}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? 'Generating...' : 'Get AI Suggestions'}
              </button>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Brand Name
              </label>
              <input
                type="text"
                value={agentData.brand_name}
                onChange={(e) => handleInputChange('brand_name', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your brand name"
              />
              {aiSuggestions.brand_name_suggestions && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {aiSuggestions.brand_name_suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleInputChange('brand_name', suggestion)}
                      className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tagline
              </label>
              <input
                type="text"
                value={agentData.tagline}
                onChange={(e) => handleInputChange('tagline', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your tagline"
              />
              {aiSuggestions.tagline_options && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {aiSuggestions.tagline_options.map((option, index) => (
                    <button
                      key={index}
                      onClick={() => handleInputChange('tagline', option)}
                      className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full"
                    >
                      {option}
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Logo
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                {agentData.logo_url ? (
                  <div className="space-y-4">
                    <img
                      src={agentData.logo_url}
                      alt="Logo preview"
                      className="mx-auto h-24 w-24 object-contain"
                    />
                    <button
                      onClick={() => handleInputChange('logo_url', '')}
                      className="text-red-600 hover:text-red-700 text-sm"
                    >
                      Remove Logo
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <div>
                      <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        Upload Logo
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleLogoUpload}
                          className="hidden"
                        />
                      </label>
                    </div>
                    <p className="text-sm text-gray-500">
                      PNG, JPG, GIF up to 10MB
                    </p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Color
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={agentData.primary_color}
                    onChange={(e) => handleColorChange('primary_color', e.target.value)}
                    className="h-12 w-12 rounded border border-gray-300"
                  />
                  <input
                    type="text"
                    value={agentData.primary_color}
                    onChange={(e) => handleColorChange('primary_color', e.target.value)}
                    className="flex-1 px-3 py-3 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secondary Color
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={agentData.secondary_color}
                    onChange={(e) => handleColorChange('secondary_color', e.target.value)}
                    className="h-12 w-12 rounded border border-gray-300"
                  />
                  <input
                    type="text"
                    value={agentData.secondary_color}
                    onChange={(e) => handleColorChange('secondary_color', e.target.value)}
                    className="flex-1 px-3 py-3 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Accent Color
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={agentData.accent_color}
                  onChange={(e) => handleColorChange('accent_color', e.target.value)}
                  className="h-12 w-12 rounded border border-gray-300"
                />
                <input
                  type="text"
                  value={agentData.accent_color}
                  onChange={(e) => handleColorChange('accent_color', e.target.value)}
                  className="flex-1 px-3 py-3 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          </motion.div>
        );

      case 'specialties':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Select Your Specialties *
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {specialties.map((specialty) => (
                  <button
                    key={specialty}
                    onClick={() => handleSpecialtyToggle(specialty)}
                    className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                      agentData.specialties.includes(specialty)
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {specialty}
                  </button>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Service Areas *
              </label>
              <div className="space-y-3">
                {['Downtown', 'Suburbs', 'Rural', 'Coastal', 'Mountain', 'Urban'].map((area) => (
                  <button
                    key={area}
                    onClick={() => {
                      const currentAreas = agentData.service_areas;
                      const newAreas = currentAreas.includes(area)
                        ? currentAreas.filter(a => a !== area)
                        : [...currentAreas, area];
                      handleInputChange('service_areas', newAreas);
                    }}
                    className={`w-full p-3 rounded-lg border-2 text-left transition-colors ${
                      agentData.service_areas.includes(area)
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {area}
                  </button>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Property Types
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {propertyTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => handlePropertyTypeToggle(type)}
                    className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                      agentData.property_types.includes(type)
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Price Ranges
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {priceRanges.map((range) => (
                  <button
                    key={range}
                    onClick={() => handlePriceRangeToggle(range)}
                    className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                      agentData.price_ranges.includes(range)
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        );

      case 'crm_setup':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-blue-50 p-6 rounded-lg">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                AI-Powered CRM Configuration
              </h3>
              <p className="text-blue-700">
                Our AI will help you set up the perfect CRM strategy based on your profile and preferences.
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AI Communication Style
              </label>
              <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option>Professional and Formal</option>
                <option>Friendly and Casual</option>
                <option>Direct and Concise</option>
                <option>Warm and Personal</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notification Preferences
              </label>
              <div className="space-y-3">
                {['Email', 'SMS', 'Push Notifications', 'Phone Calls'].map((method) => (
                  <label key={method} className="flex items-center">
                    <input type="checkbox" className="mr-3 h-4 w-4 text-blue-600" />
                    {method}
                  </label>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Lead Response Time
              </label>
              <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option>Immediately (within 5 minutes)</option>
                <option>Within 1 hour</option>
                <option>Within 4 hours</option>
                <option>Within 24 hours</option>
              </select>
            </div>
          </motion.div>
        );

      case 'verification':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-yellow-50 p-6 rounded-lg">
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">
                Account Verification Required
              </h3>
              <p className="text-yellow-700">
                Please upload the required documents to verify your account and complete the onboarding process.
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Real Estate License
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
                <div className="mt-4">
                  <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                    Upload License
                    <input type="file" accept=".pdf,.png,.jpg,.jpeg" className="hidden" />
                  </label>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  PDF, PNG, JPG up to 10MB
                </p>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Government ID (Optional)
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
                <div className="mt-4">
                  <label className="cursor-pointer bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700">
                    Upload ID
                    <input type="file" accept=".pdf,.png,.jpg,.jpeg" className="hidden" />
                  </label>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  PDF, PNG, JPG up to 10MB
                </p>
              </div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckIcon className="h-5 w-5 text-green-600" />
                <span className="text-green-800 font-medium">
                  Verification documents will be reviewed within 24-48 hours
                </span>
              </div>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Agent Onboarding</h1>
              <p className="text-gray-600">Complete your profile to get started</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>Step {currentStep + 1} of {steps.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex items-center justify-between py-4">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  index <= currentStep
                    ? 'border-blue-500 bg-blue-500 text-white'
                    : 'border-gray-300 bg-white text-gray-400'
                }`}>
                  {index < currentStep ? (
                    <CheckIcon className="h-5 w-5" />
                  ) : (
                    <step.icon className="h-5 w-5" />
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-0.5 mx-2 ${
                    index < currentStep ? 'bg-blue-500' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-sm border p-8">
          {/* Step Header */}
          <div className="mb-8">
            <div className="flex items-center gap-4 mb-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-blue-100">
                <steps[currentStep].icon className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {steps[currentStep].title}
                </h2>
                <p className="text-gray-600">{steps[currentStep].description}</p>
              </div>
            </div>
            
            {steps[currentStep].required && (
              <div className="text-sm text-red-600">
                * Required fields
              </div>
            )}
          </div>

          {/* Step Content */}
          {renderStepContent()}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-12 pt-8 border-t">
            <button
              onClick={prevStep}
              disabled={currentStep === 0}
              className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <div className="flex items-center gap-4">
              {currentStep < steps.length - 1 ? (
                <button
                  onClick={nextStep}
                  disabled={!canProceed()}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  Next Step
                  <ChevronRightIcon className="h-4 w-4" />
                </button>
              ) : (
                <button
                  onClick={() => console.log('Complete onboarding')}
                  disabled={!canProceed()}
                  className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  Complete Onboarding
                  <CheckIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Upload Progress Overlay */}
      {uploadProgress > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-sm w-full mx-4">
            <div className="text-center">
              <div className="mb-4">
                <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
              </div>
              <h3 className="text-lg font-semibold mb-2">Uploading Logo</h3>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600">{uploadProgress}% Complete</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentOnboarding;