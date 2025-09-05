'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { SparklesIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function AIContentGenerator() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedContent, setGeneratedContent] = useState('')
  const [formData, setFormData] = useState({
    propertyType: 'Apartment',
    contentStyle: 'Professional',
    aiPrompt: ''
  })

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const generateContent = async () => {
    if (!formData.aiPrompt.trim()) {
      toast.error('Please describe your property first.')
      return
    }

    setIsGenerating(true)
    try {
      // Simulate AI content generation
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const mockContent = `🏠 **${formData.propertyType} in Prime Location**

💰 **Price**: ₹75,00,000
📍 **Location**: City Center
🛏️ **Bedrooms**: 3 | 🚿 **Bathrooms**: 2

**Description:**
${formData.aiPrompt}

**Key Features:**
• Modern ${formData.contentStyle.toLowerCase()} design
• Prime location with excellent connectivity
• High-quality finishes and amenities
• Perfect for families and professionals

**Amenities:**
• 24/7 Security
• Parking Space
• Gym & Swimming Pool
• Children's Play Area
• Power Backup

📞 **Contact us today for a viewing!**
#RealEstate #PropertyForSale #${formData.propertyType}`

      setGeneratedContent(mockContent)
      toast.success('AI content generated successfully!')
    } catch (error) {
      toast.error('Failed to generate content. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedContent)
    toast.success('Content copied to clipboard!')
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="glass-card">
        <div className="flex items-center space-x-3 mb-6">
          <SparklesIcon className="w-6 h-6 text-purple-500" />
          <h2 className="text-2xl font-bold text-gray-800">AI Content Generation</h2>
        </div>
        
        <p className="text-gray-600 mb-6">
          Generate engaging content for your properties using AI assistance.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Property Type
                </label>
                <select
                  name="propertyType"
                  value={formData.propertyType}
                  onChange={handleInputChange}
                  className="form-input"
                >
                  <option value="Apartment">Apartment</option>
                  <option value="House">House</option>
                  <option value="Villa">Villa</option>
                  <option value="Commercial">Commercial</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content Style
                </label>
                <select
                  name="contentStyle"
                  value={formData.contentStyle}
                  onChange={handleInputChange}
                  className="form-input"
                >
                  <option value="Professional">Professional</option>
                  <option value="Casual">Casual</option>
                  <option value="Luxury">Luxury</option>
                  <option value="Family-friendly">Family-friendly</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Describe your property
              </label>
              <textarea
                name="aiPrompt"
                value={formData.aiPrompt}
                onChange={handleInputChange}
                rows={4}
                className="form-input"
                placeholder="Describe the property features, location, amenities..."
              />
            </div>

            <button
              onClick={generateContent}
              disabled={isGenerating}
              className="btn-secondary w-full flex items-center justify-center space-x-2"
            >
              {isGenerating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Generating Content...</span>
                </>
              ) : (
                <>
                  <SparklesIcon className="w-5 h-5" />
                  <span>Generate Content</span>
                </>
              )}
            </button>
          </div>

          {/* Generated Content */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Generated Content</h3>
            
            {generatedContent ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                  {generatedContent}
                </pre>
                <button
                  onClick={copyToClipboard}
                  className="mt-4 btn-outline w-full"
                >
                  Copy to Clipboard
                </button>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <SparklesIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">
                  Generated content will appear here after you click &quot;Generate Content&quot;
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <button className="btn-outline flex items-center space-x-2">
            <ArrowLeftIcon className="w-5 h-5" />
            <span>Back to Dashboard</span>
          </button>
        </div>
      </div>
    </motion.div>
  )
}
