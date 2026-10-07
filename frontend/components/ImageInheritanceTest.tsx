'use client'

import { useState } from 'react'
import ImageSelectionPanel from './ImageSelectionPanel'
import { calculateMaxImages, validateImageCount } from '@/lib/imageUtils'

/**
 * Test component for Phase 1 Image Inheritance
 * This component demonstrates the basic image inheritance functionality
 */
export default function ImageInheritanceTest() {
  const [selectedImages, setSelectedImages] = useState<string[]>([])
  const [platforms, setPlatforms] = useState<string[]>(['instagram', 'facebook'])
  
  // Mock property images
  const propertyImages = [
    'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800',
    'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800',
    'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800',
    'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800',
    'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800',
    'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800'
  ]

  const maxImages = calculateMaxImages(platforms)
  const validation = validateImageCount(selectedImages.length, platforms)

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h2 className="text-xl font-semibold text-blue-900 mb-2">
          Phase 1: Basic Image Inheritance Test
        </h2>
        <p className="text-blue-700">
          This component tests the basic image inheritance functionality including:
        </p>
        <ul className="list-disc list-inside text-blue-700 mt-2 space-y-1">
          <li>✅ Auto-copy property images to posts</li>
          <li>✅ Basic image selection UI</li>
          <li>✅ Platform-specific image limits</li>
          <li>✅ Image preview functionality</li>
        </ul>
      </div>

      {/* Platform Selection */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Platform Selection</h3>
        <div className="flex flex-wrap gap-2">
          {['instagram', 'facebook', 'linkedin', 'twitter', 'website'].map(platform => (
            <button
              key={platform}
              onClick={() => {
                if (platforms.includes(platform)) {
                  setPlatforms(platforms.filter(p => p !== platform))
                } else {
                  setPlatforms([...platforms, platform])
                }
              }}
              className={`px-3 py-1 rounded-md text-sm font-medium ${
                platforms.includes(platform)
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              {platform}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-600 mt-2">
          Max images: {maxImages} (limited by most restrictive platform)
        </p>
      </div>

      {/* Image Selection Panel */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <ImageSelectionPanel
          propertyImages={propertyImages}
          selectedImages={selectedImages}
          onImageSelect={setSelectedImages}
          platforms={platforms}
        />
      </div>

      {/* Validation Results */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Validation Results</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Selected Images:</span>
            <span className="font-medium">{selectedImages.length}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Max Allowed:</span>
            <span className="font-medium">{maxImages}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Valid:</span>
            <span className={`font-medium ${validation.isValid ? 'text-green-600' : 'text-red-600'}`}>
              {validation.isValid ? 'Yes' : 'No'}
            </span>
          </div>
          {validation.message && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
              {validation.message}
            </div>
          )}
        </div>
      </div>

      {/* Selected Images Preview */}
      {selectedImages.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Selected Images Preview</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {selectedImages.map((imageUrl, index) => (
              <div key={index} className="aspect-square rounded-lg overflow-hidden">
                <img
                  src={imageUrl}
                  alt={`Selected image ${index + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}