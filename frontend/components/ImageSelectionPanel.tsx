'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckIcon, XMarkIcon, EyeIcon, PlusIcon } from '@heroicons/react/24/outline'
import { CheckIcon as CheckSolidIcon } from '@heroicons/react/24/solid'
import Image from 'next/image'

interface ImageSelectionPanelProps {
  propertyImages: string[]
  selectedImages: string[]
  onImageSelect: (images: string[]) => void
  platforms: string[]
  maxImagesPerPlatform?: Record<string, number>
  className?: string
}

// Platform-specific image limits
const PLATFORM_IMAGE_LIMITS = {
  instagram: 10,
  facebook: 20,
  linkedin: 9,
  twitter: 4,
  website: 50
} as const

export default function ImageSelectionPanel({
  propertyImages,
  selectedImages,
  onImageSelect,
  platforms,
  maxImagesPerPlatform,
  className = ''
}: ImageSelectionPanelProps) {
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [hoveredImage, setHoveredImage] = useState<string | null>(null)

  // Calculate max images based on selected platforms
  const maxImages = platforms.reduce((max, platform) => {
    const platformLimit = maxImagesPerPlatform?.[platform] || PLATFORM_IMAGE_LIMITS[platform as keyof typeof PLATFORM_IMAGE_LIMITS] || 10
    return Math.min(max, platformLimit)
  }, Math.min(...platforms.map(p => PLATFORM_IMAGE_LIMITS[p as keyof typeof PLATFORM_IMAGE_LIMITS] || 10)))

  const handleImageToggle = useCallback((imageUrl: string) => {
    const isSelected = selectedImages.includes(imageUrl)
    
    if (isSelected) {
      // Remove image
      onImageSelect(selectedImages.filter(img => img !== imageUrl))
    } else {
      // Add image (if under limit)
      if (selectedImages.length < maxImages) {
        onImageSelect([...selectedImages, imageUrl])
      } else {
        // Show limit reached message
        console.warn(`Maximum ${maxImages} images allowed for selected platforms`)
      }
    }
  }, [selectedImages, onImageSelect, maxImages])

  const handleSelectAll = useCallback(() => {
    const imagesToSelect = propertyImages.slice(0, maxImages)
    onImageSelect(imagesToSelect)
  }, [propertyImages, maxImages, onImageSelect])

  const handleClearAll = useCallback(() => {
    onImageSelect([])
  }, [onImageSelect])

  const isImageSelected = (imageUrl: string) => selectedImages.includes(imageUrl)
  const canSelectMore = selectedImages.length < maxImages

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Select Images</h3>
          <p className="text-sm text-gray-600">
            {selectedImages.length} of {maxImages} images selected
            {platforms.length > 1 && (
              <span className="ml-2 text-xs text-blue-600">
                (Limited by {platforms.join(', ')})
              </span>
            )}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleSelectAll}
            disabled={propertyImages.length === 0}
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Select All
          </button>
          <button
            onClick={handleClearAll}
            disabled={selectedImages.length === 0}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Image grid */}
      {propertyImages.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {propertyImages.map((imageUrl, index) => {
            const isSelected = isImageSelected(imageUrl)
            const isHovered = hoveredImage === imageUrl
            
            return (
              <motion.div
                key={`${imageUrl}-${index}`}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className={`relative aspect-square rounded-lg overflow-hidden cursor-pointer group ${
                  isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : 'hover:ring-2 hover:ring-gray-300'
                } ${!canSelectMore && !isSelected ? 'opacity-50' : ''}`}
                onClick={() => handleImageToggle(imageUrl)}
                onMouseEnter={() => setHoveredImage(imageUrl)}
                onMouseLeave={() => setHoveredImage(null)}
              >
                <Image
                  src={imageUrl}
                  alt={`Property image ${index + 1}`}
                  fill
                  className="object-cover transition-transform group-hover:scale-105"
                  sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 20vw"
                />
                
                {/* Selection overlay */}
                <AnimatePresence>
                  {(isSelected || isHovered) && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center"
                    >
                      {isSelected ? (
                        <CheckSolidIcon className="w-6 h-6 text-white" />
                      ) : (
                        <CheckIcon className="w-6 h-6 text-white" />
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Selection indicator */}
                {isSelected && (
                  <div className="absolute top-2 right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                    <CheckSolidIcon className="w-4 h-4 text-white" />
                  </div>
                )}

                {/* Image number */}
                <div className="absolute bottom-2 left-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                  {index + 1}
                </div>
              </motion.div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <PlusIcon className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-600">No images available for this property</p>
          <p className="text-sm text-gray-500 mt-1">Add images to the property first</p>
        </div>
      )}

      {/* Platform limits info */}
      {platforms.length > 1 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Platform Limits</h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
            {platforms.map(platform => (
              <div key={platform} className="flex items-center justify-between">
                <span className="text-blue-700 capitalize">{platform}</span>
                <span className="text-blue-600 font-medium">
                  {maxImagesPerPlatform?.[platform] || PLATFORM_IMAGE_LIMITS[platform as keyof typeof PLATFORM_IMAGE_LIMITS] || 10}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Image preview modal */}
      <AnimatePresence>
        {previewImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black bg-opacity-75 flex items-center justify-center p-4"
            onClick={() => setPreviewImage(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="relative max-w-4xl max-h-full"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setPreviewImage(null)}
                className="absolute -top-10 right-0 text-white hover:text-gray-300"
              >
                <XMarkIcon className="w-8 h-8" />
              </button>
              <Image
                src={previewImage}
                alt="Preview"
                width={800}
                height={600}
                className="rounded-lg"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}