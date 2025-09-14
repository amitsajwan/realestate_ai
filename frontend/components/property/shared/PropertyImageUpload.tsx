'use client'

import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { PhotoIcon, XMarkIcon, CloudArrowUpIcon } from '@heroicons/react/24/outline'
import { apiService } from '@/lib/api'
import toast from 'react-hot-toast'

interface PropertyImageUploadProps {
  propertyId?: string
  onImagesUploaded?: (images: any[]) => void
  maxImages?: number
  className?: string
}

interface UploadedImage {
  id: string
  filename: string
  original_name: string
  url: string
  thumbnail_url?: string
  content_type: string
  size: number
}

export default function PropertyImageUpload({
  propertyId,
  onImagesUploaded,
  maxImages = 20,
  className = ""
}: PropertyImageUploadProps) {
  const [uploadedImages, setUploadedImages] = useState<UploadedImage[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({})

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (uploadedImages.length + acceptedFiles.length > maxImages) {
      toast.error(`Maximum ${maxImages} images allowed`)
      return
    }

    setIsUploading(true)

    try {
      const formData = new FormData()

      acceptedFiles.forEach((file, index) => {
        formData.append('files', file)
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }))
      })

      if (propertyId) {
        formData.append('property_id', propertyId)
      }

      // Support both uploadImages (current) and uploadPropertyImages (legacy in tests)
      const uploader = (apiService as any).uploadPropertyImages || apiService.uploadImages
      const response = await uploader.call(apiService, formData, propertyId)

      if (response.success || Array.isArray(response)) {
        const files = Array.isArray(response) ? response : (response.files ?? [])
        const newImages = (files ?? []) as UploadedImage[]
        setUploadedImages(prev => [...prev, ...newImages])
        onImagesUploaded?.(newImages)

        // Clear progress
        acceptedFiles.forEach(file => {
          setUploadProgress(prev => {
            const updated = { ...prev }
            delete updated[file.name]
            return updated
          })
        })

        toast.success('Images uploaded successfully!')
      } else {
        throw new Error(response.message || 'Upload failed')
      }
    } catch (error: any) {
      console.error('Upload error:', error)
      toast.error(error.message || 'Failed to upload images')
    } finally {
      setIsUploading(false)
    }
  }, [uploadedImages.length, maxImages, propertyId, onImagesUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp', '.gif']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true,
    disabled: isUploading
  })

  const removeImage = (imageId: string) => {
    setUploadedImages(prev => prev.filter(img => img.id !== imageId))
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragActive
            ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
        <div className="mt-4">
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            {isDragActive ? 'Drop images here' : 'Upload Property Images'}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Drag & drop images here, or click to select files
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
            Supports: JPEG, PNG, WebP, GIF (max 10MB each)
          </p>
        </div>
      </div>

      {/* Upload Progress */}
      {isUploading && Object.keys(uploadProgress).length > 0 && (
        <div className="space-y-2">
          {Object.entries(uploadProgress).map(([filename, progress]) => (
            <div key={filename} className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {filename}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Uploaded Images Grid */}
      {uploadedImages.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
            Uploaded Images ({uploadedImages.length}/{maxImages})
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {uploadedImages.map((image) => (
              <div key={image.id} className="relative group">
                <div className="aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
                  <img
                    src={image.thumbnail_url || image.url}
                    alt={image.original_name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <button
                  onClick={() => removeImage(image.id)}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
                <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-2 truncate">
                  {image.original_name}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Helper Text */}
      <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
        <p>• Upload high-quality images to attract more buyers</p>
        <p>• First image will be used as the main property photo</p>
        <p>• Images are automatically optimized for web viewing</p>
      </div>
    </div>
  )
}
