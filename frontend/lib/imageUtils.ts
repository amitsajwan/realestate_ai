/**
 * Image Utilities for Property-Post Integration
 * ============================================
 * Utilities for handling image inheritance, platform limits, and optimization
 */

export interface PlatformImageLimits {
  maxImages: number
  preferredAspectRatio: string
  maxFileSize: string
  supportedFormats: string[]
  dimensions: {
    min: number
    max: number
  }
}

export const PLATFORM_IMAGE_CONFIG: Record<string, PlatformImageLimits> = {
  instagram: {
    maxImages: 10,
    preferredAspectRatio: '1:1',
    maxFileSize: '8MB',
    supportedFormats: ['jpg', 'jpeg', 'png'],
    dimensions: { min: 1080, max: 1080 }
  },
  facebook: {
    maxImages: 20,
    preferredAspectRatio: '16:9',
    maxFileSize: '10MB',
    supportedFormats: ['jpg', 'jpeg', 'png', 'gif'],
    dimensions: { min: 1200, max: 1920 }
  },
  linkedin: {
    maxImages: 9,
    preferredAspectRatio: '4:3',
    maxFileSize: '5MB',
    supportedFormats: ['jpg', 'jpeg', 'png'],
    dimensions: { min: 1200, max: 1920 }
  },
  twitter: {
    maxImages: 4,
    preferredAspectRatio: '16:9',
    maxFileSize: '5MB',
    supportedFormats: ['jpg', 'jpeg', 'png', 'gif'],
    dimensions: { min: 1200, max: 1920 }
  },
  website: {
    maxImages: 50,
    preferredAspectRatio: 'any',
    maxFileSize: '20MB',
    supportedFormats: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    dimensions: { min: 800, max: 4000 }
  }
}

/**
 * Calculate the maximum number of images allowed based on selected platforms
 */
export function calculateMaxImages(platforms: string[]): number {
  if (platforms.length === 0) return 0
  
  return Math.min(
    ...platforms.map(platform => 
      PLATFORM_IMAGE_CONFIG[platform]?.maxImages || 10
    )
  )
}

/**
 * Get platform-specific image limits
 */
export function getPlatformLimits(platform: string): PlatformImageLimits {
  return PLATFORM_IMAGE_CONFIG[platform] || PLATFORM_IMAGE_CONFIG.website
}

/**
 * Validate if image count is within platform limits
 */
export function validateImageCount(
  imageCount: number, 
  platforms: string[]
): { isValid: boolean; maxAllowed: number; message?: string } {
  const maxAllowed = calculateMaxImages(platforms)
  
  if (imageCount <= maxAllowed) {
    return { isValid: true, maxAllowed }
  }
  
  return {
    isValid: false,
    maxAllowed,
    message: `Maximum ${maxAllowed} images allowed for selected platforms: ${platforms.join(', ')}`
  }
}

/**
 * Auto-select images from property based on platform requirements
 */
export function autoSelectImages(
  propertyImages: string[],
  platforms: string[],
  maxImages?: number
): string[] {
  const maxAllowed = maxImages || calculateMaxImages(platforms)
  
  if (propertyImages.length === 0) return []
  
  // For now, just take the first N images
  // TODO: In Phase 2, implement AI-powered smart selection
  return propertyImages.slice(0, maxAllowed)
}

/**
 * Check if image URL is valid
 */
export function isValidImageUrl(url: string): boolean {
  try {
    const urlObj = new URL(url)
    return ['http:', 'https:'].includes(urlObj.protocol)
  } catch {
    return false
  }
}

/**
 * Get image dimensions from URL (placeholder - would need actual implementation)
 */
export function getImageDimensions(url: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight })
    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = url
  })
}

/**
 * Generate image selection summary for UI
 */
export function generateImageSummary(
  selectedImages: string[],
  platforms: string[]
): {
  count: number
  maxAllowed: number
  platforms: string[]
  canAddMore: boolean
  message: string
} {
  const maxAllowed = calculateMaxImages(platforms)
  const canAddMore = selectedImages.length < maxAllowed
  
  let message = `${selectedImages.length} of ${maxAllowed} images selected`
  if (platforms.length > 1) {
    message += ` (limited by ${platforms.join(', ')})`
  }
  
  return {
    count: selectedImages.length,
    maxAllowed,
    platforms,
    canAddMore,
    message
  }
}