"use client";

import React, { useState, useEffect } from 'react';
import { SparklesIcon, LanguageIcon, DocumentTextIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface PropertyData {
  id: string;
  title: string;
  location: string;
  price: string;
  property_type?: string;
  features?: string[];
}

interface GeneratedContent {
  content: string;
  optimized_content: {
    facebook: string;
    instagram: string;
    linkedin: string;
    twitter: string;
  };
  language: string;
  template_used?: string;
}

interface AIContentGeneratorProps {
  propertyData?: PropertyData;
  onContentGenerated?: (content: GeneratedContent) => void;
}

const AIContentGenerator: React.FC<AIContentGeneratorProps> = ({ 
  propertyData, 
  onContentGenerated 
}) => {
  const [selectedProperty, setSelectedProperty] = useState<PropertyData | null>(propertyData || null);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [availableProperties, setAvailableProperties] = useState<PropertyData[]>([]);
  const [availableTemplates, setAvailableTemplates] = useState<Array<{id: string, name: string}>>([]);

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'Hindi' },
    { code: 'ta', name: 'Tamil' },
    { code: 'te', name: 'Telugu' },
    { code: 'bn', name: 'Bengali' },
    { code: 'gu', name: 'Gujarati' },
    { code: 'kn', name: 'Kannada' },
    { code: 'ml', name: 'Malayalam' },
    { code: 'mr', name: 'Marathi' },
    { code: 'pa', name: 'Punjabi' },
    { code: 'ur', name: 'Urdu' }
  ];

  // Load available properties and templates on component mount
  useEffect(() => {
    loadAvailableProperties();
    loadAvailableTemplates();
  }, []);

  const loadAvailableProperties = async () => {
    try {
      const response = await fetch('/api/properties', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableProperties(data.data || []);
      }
    } catch (err) {
      console.error('Failed to load properties:', err);
    }
  };

  const loadAvailableTemplates = async () => {
    try {
      const response = await fetch('/api/templates', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableTemplates(data.data || []);
      }
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  };

  const generateContent = async () => {
    if (!selectedProperty) {
      setError('Please select a property first');
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);

      const response = await fetch('/api/ai/generate-content', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          property_data: selectedProperty,
          language: selectedLanguage,
          custom_prompt: customPrompt,
          template_id: selectedTemplate || null
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate content');
      }

      const data = await response.json();
      setGeneratedContent(data.data);
      
      if (onContentGenerated) {
        onContentGenerated(data.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsGenerating(false);
    }
  };

  const regenerateContent = async () => {
    if (!selectedProperty) return;
    
    try {
      setIsGenerating(true);
      setError(null);

      const response = await fetch(`/api/posts/${selectedProperty.id}/regenerate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          language: selectedLanguage,
          custom_prompt: customPrompt
        })
      });

      if (!response.ok) {
        throw new Error('Failed to regenerate content');
      }

      const data = await response.json();
      setGeneratedContent(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <SparklesIcon className="h-6 w-6 mr-2 text-blue-600" />
            AI Content Generator
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            Generate engaging social media content for your properties using AI
          </p>
        </div>

        <div className="p-6">
          {/* Property Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Property
            </label>
            <select
              value={selectedProperty?.id || ''}
              onChange={(e) => {
                const property = availableProperties.find(p => p.id === e.target.value);
                setSelectedProperty(property || null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Choose a property...</option>
              {availableProperties.map((property) => (
                <option key={property.id} value={property.id}>
                  {property.title} - {property.location}
                </option>
              ))}
            </select>
          </div>

          {/* Property Details Display */}
          {selectedProperty && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-medium text-gray-900">{selectedProperty.title}</h3>
              <p className="text-sm text-gray-600">{selectedProperty.location}</p>
              <p className="text-sm font-medium text-green-600">{selectedProperty.price}</p>
              {selectedProperty.features && selectedProperty.features.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-gray-600">Features:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedProperty.features.map((feature, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Language Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <LanguageIcon className="h-4 w-4 inline mr-1" />
              Content Language
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          {/* Template Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <DocumentTextIcon className="h-4 w-4 inline mr-1" />
              Template (Optional)
            </label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">No template</option>
              {availableTemplates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>

          {/* Custom Prompt */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Prompt (Optional)
            </label>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Add specific instructions for the AI content generation..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Generate Button */}
          <div className="mb-6">
            <button
              onClick={generateContent}
              disabled={!selectedProperty || isGenerating}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? (
                <>
                  <ArrowPathIcon className="animate-spin h-4 w-4 mr-2" />
                  Generating Content...
                </>
              ) : (
                <>
                  <SparklesIcon className="h-4 w-4 mr-2" />
                  Generate Content
                </>
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <div className="mt-2 text-sm text-red-700">{error}</div>
                </div>
              </div>
            </div>
          )}

          {/* Generated Content Display */}
          {generatedContent && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">Generated Content</h3>
                <button
                  onClick={regenerateContent}
                  disabled={isGenerating}
                  className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  <ArrowPathIcon className="h-4 w-4 mr-1" />
                  Regenerate
                </button>
              </div>

              {/* Main Content */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-sm font-medium text-gray-700">Main Content</h4>
                  <button
                    onClick={() => copyToClipboard(generatedContent.content)}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Copy
                  </button>
                </div>
                <p className="text-gray-900 whitespace-pre-wrap">{generatedContent.content}</p>
              </div>

              {/* Platform-Specific Content */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(generatedContent.optimized_content).map(([platform, content]) => (
                  <div key={platform} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-sm font-medium text-gray-700 capitalize">{platform}</h4>
                      <button
                        onClick={() => copyToClipboard(content)}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        Copy
                      </button>
                    </div>
                    <p className="text-gray-900 text-sm whitespace-pre-wrap">{content}</p>
                  </div>
                ))}
              </div>

              {/* Content Actions */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    // Handle save as draft
                    console.log('Save as draft');
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Save as Draft
                </button>
                <button
                  onClick={() => {
                    // Handle schedule post
                    console.log('Schedule post');
                  }}
                  className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700"
                >
                  Schedule Post
                </button>
                <button
                  onClick={() => {
                    // Handle publish now
                    console.log('Publish now');
                  }}
                  className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                >
                  Publish Now
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIContentGenerator;