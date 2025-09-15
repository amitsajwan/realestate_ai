'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  PlusIcon, 
  SparklesIcon,
  GlobeAltIcon,
  CalendarIcon,
  CheckCircleIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline'

export default function TestPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [postData, setPostData] = useState({
    property: '',
    content: '',
    channels: [] as string[],
    schedule: '',
    aiGenerated: false
  })

  const steps = [
    { id: 1, name: 'Select Property', icon: PlusIcon },
    { id: 2, name: 'Generate Content', icon: SparklesIcon },
    { id: 3, name: 'Choose Channels', icon: GlobeAltIcon },
    { id: 4, name: 'Schedule Post', icon: CalendarIcon },
    { id: 5, name: 'Review & Publish', icon: CheckCircleIcon }
  ]

  const properties = [
    { id: 1, title: 'Luxury Apartment in Mumbai', price: '₹2.5 Cr', type: 'Apartment' },
    { id: 2, title: 'Villa in Bangalore', price: '₹4.2 Cr', type: 'Villa' },
    { id: 3, title: 'Penthouse in Delhi', price: '₹8.5 Cr', type: 'Penthouse' }
  ]

  const channels = [
    { id: 'facebook', name: 'Facebook', color: 'bg-blue-600' },
    { id: 'instagram', name: 'Instagram', color: 'bg-pink-600' },
    { id: 'linkedin', name: 'LinkedIn', color: 'bg-blue-700' },
    { id: 'twitter', name: 'Twitter', color: 'bg-sky-500' }
  ]

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900">Select Property</h3>
            <div className="grid gap-4">
              {properties.map((property) => (
                <motion.div
                  key={property.id}
                  whileHover={{ scale: 1.02 }}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    postData.property === property.id.toString()
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setPostData({...postData, property: property.id.toString()})}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-gray-900">{property.title}</h4>
                      <p className="text-sm text-gray-600">{property.type}</p>
                    </div>
                    <span className="text-lg font-semibold text-blue-600">{property.price}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )
      
      case 2:
        return (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900">Generate Content</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Prompt
                </label>
                <textarea
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={4}
                  placeholder="Describe what kind of content you want to generate..."
                  value={postData.content}
                  onChange={(e) => setPostData({...postData, content: e.target.value})}
                />
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="aiGenerated"
                  checked={postData.aiGenerated}
                  onChange={(e) => setPostData({...postData, aiGenerated: e.target.checked})}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="aiGenerated" className="text-sm text-gray-700">
                  Use AI to generate content
                </label>
              </div>
              {postData.aiGenerated && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200"
                >
                  <div className="flex items-center space-x-2 mb-2">
                    <SparklesIcon className="w-5 h-5 text-purple-600" />
                    <span className="font-medium text-purple-900">AI Generated Content</span>
                  </div>
                  <p className="text-sm text-gray-700">
                    "Discover your dream home! This stunning property offers modern amenities, 
                    prime location, and exceptional value. Perfect for families and investors alike. 
                    Contact us today for a private viewing! 🏠✨"
                  </p>
                </motion.div>
              )}
            </div>
          </div>
        )
      
      case 3:
        return (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900">Choose Publishing Channels</h3>
            <div className="grid grid-cols-2 gap-4">
              {channels.map((channel) => (
                <motion.div
                  key={channel.id}
                  whileHover={{ scale: 1.02 }}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    postData.channels.includes(channel.id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => {
                    const newChannels = postData.channels.includes(channel.id)
                      ? postData.channels.filter(c => c !== channel.id)
                      : [...postData.channels, channel.id]
                    setPostData({...postData, channels: newChannels})
                  }}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 ${channel.color} rounded-lg flex items-center justify-center`}>
                      <span className="text-white text-sm font-bold">
                        {channel.name.charAt(0)}
                      </span>
                    </div>
                    <span className="font-medium text-gray-900">{channel.name}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )
      
      case 4:
        return (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900">Schedule Post</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <button
                  className={`p-4 border-2 rounded-lg text-center transition-all ${
                    postData.schedule === 'now'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setPostData({...postData, schedule: 'now'})}
                >
                  <div className="font-medium">Publish Now</div>
                  <div className="text-sm text-gray-600">Immediately</div>
                </button>
                <button
                  className={`p-4 border-2 rounded-lg text-center transition-all ${
                    postData.schedule === 'later'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setPostData({...postData, schedule: 'later'})}
                >
                  <div className="font-medium">Schedule</div>
                  <div className="text-sm text-gray-600">Choose date & time</div>
                </button>
              </div>
              {postData.schedule === 'later' && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-2"
                >
                  <label className="block text-sm font-medium text-gray-700">
                    Select Date & Time
                  </label>
                  <input
                    type="datetime-local"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </motion.div>
              )}
            </div>
          </div>
        )
      
      case 5:
        return (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900">Review & Publish</h3>
            <div className="bg-gray-50 rounded-lg p-6 space-y-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Property</h4>
                <p className="text-sm text-gray-600">
                  {properties.find(p => p.id.toString() === postData.property)?.title}
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Content</h4>
                <p className="text-sm text-gray-600 bg-white p-3 rounded border">
                  {postData.content || "AI Generated content will appear here..."}
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Channels</h4>
                <div className="flex flex-wrap gap-2">
                  {postData.channels.map(channelId => {
                    const channel = channels.find(c => c.id === channelId)
                    return (
                      <span
                        key={channelId}
                        className={`px-3 py-1 rounded-full text-xs font-medium text-white ${channel?.color}`}
                      >
                        {channel?.name}
                      </span>
                    )
                  })}
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Schedule</h4>
                <p className="text-sm text-gray-600">
                  {postData.schedule === 'now' ? 'Publish immediately' : 'Scheduled for later'}
                </p>
              </div>
            </div>
            <button
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center justify-center space-x-2"
              onClick={() => {
                alert('Post published successfully! 🎉')
                setCurrentStep(1)
                setPostData({ property: '', content: '', channels: [], schedule: '', aiGenerated: false })
              }}
            >
              <span>Publish Post</span>
              <ArrowRightIcon className="w-5 h-5" />
            </button>
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Posting Workflow</h1>
          <p className="text-gray-600">Create and publish content across multiple channels</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className="flex items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    currentStep >= step.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {currentStep > step.id ? (
                      <CheckCircleIcon className="w-6 h-6" />
                    ) : (
                      <step.icon className="w-5 h-5" />
                    )}
                  </div>
                  <span className={`ml-2 text-sm font-medium ${
                    currentStep >= step.id ? 'text-blue-600' : 'text-gray-500'
                  }`}>
                    {step.name}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-4 ${
                    currentStep > step.id ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          {renderStep()}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            onClick={() => setCurrentStep(Math.min(5, currentStep + 1))}
            disabled={currentStep === 5}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}