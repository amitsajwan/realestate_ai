/**
 * Mobile optimization utilities
 * Ensures proper touch targets and responsive design
 */

'use client'

import { useEffect, useState } from 'react'

// Touch target minimum size (44px as per WCAG)
export const TOUCH_TARGET_MIN = 44

// Mobile viewport detection
export const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  return isMobile
}

// Touch-friendly button component
export const TouchButton: React.FC<{
  onClick: () => void
  children: React.ReactNode
  disabled?: boolean
  className?: string
  size?: 'sm' | 'md' | 'lg'
}> = ({
  onClick,
  children,
  disabled = false,
  className = '',
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'min-h-[44px] min-w-[44px] px-3 py-2',
    md: 'min-h-[48px] min-w-[48px] px-4 py-3',
    lg: 'min-h-[52px] min-w-[52px] px-6 py-4'
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`touch-manipulation select-none ${sizeClasses[size]} ${className}`}
    >
      {children}
    </button>
  )
}

// Swipe gesture detection
export const useSwipeGesture = (
  onSwipeLeft?: () => void,
  onSwipeRight?: () => void,
  threshold = 50
) => {
  const [touchStart, setTouchStart] = useState<number | null>(null)
  const [touchEnd, setTouchEnd] = useState<number | null>(null)

  const minSwipeDistance = threshold

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null)
    setTouchStart(e.targetTouches[0].clientX)
  }

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX)
  }

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return

    const distance = touchStart - touchEnd
    const isLeftSwipe = distance > minSwipeDistance
    const isRightSwipe = distance < -minSwipeDistance

    if (isLeftSwipe && onSwipeLeft) {
      onSwipeLeft()
    }
    if (isRightSwipe && onSwipeRight) {
      onSwipeRight()
    }
  }

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd
  }
}

// Mobile-optimized form inputs
export const MobileInput: React.FC<{
  type?: string
  placeholder?: string
  value: string
  onChange: (value: string) => void
  className?: string
  autoComplete?: string
  inputMode?: 'text' | 'numeric' | 'email' | 'tel' | 'url' | 'search'
}> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  className = '',
  autoComplete,
  inputMode = 'text'
}) => (
  <input
    type={type}
    placeholder={placeholder}
    value={value}
    onChange={(e) => onChange(e.target.value)}
    autoComplete={autoComplete}
    inputMode={inputMode}
    className={`min-h-[44px] px-4 py-3 text-base border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${className}`}
  />
)

// Prevent zoom on input focus for iOS
export const usePreventZoom = () => {
  useEffect(() => {
    const viewport = document.querySelector('meta[name=viewport]')
    if (viewport) {
      const content = viewport.getAttribute('content') || ''
      if (!content.includes('user-scalable=no')) {
        viewport.setAttribute('content', content + ', user-scalable=no')
      }
    }

    return () => {
      const viewport = document.querySelector('meta[name=viewport]')
      if (viewport) {
        const content = viewport.getAttribute('content') || ''
        viewport.setAttribute('content', content.replace(', user-scalable=no', ''))
      }
    }
  }, [])
}

// Mobile keyboard detection
export const useKeyboardVisibility = () => {
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false)

  useEffect(() => {
    const handleResize = () => {
      const viewportHeight = window.visualViewport?.height || window.innerHeight
      const windowHeight = window.innerHeight
      setIsKeyboardVisible(viewportHeight < windowHeight * 0.8)
    }

    window.visualViewport?.addEventListener('resize', handleResize)
    return () => {
      window.visualViewport?.removeEventListener('resize', handleResize)
    }
  }, [])

  return isKeyboardVisible
}

// Mobile-optimized modal positioning
export const MobileModal: React.FC<{
  isOpen: boolean
  onClose: () => void
  children: React.ReactNode
  className?: string
}> = ({ isOpen, onClose, children, className = '' }) => {
  const isMobile = useIsMobile()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black bg-opacity-50">
      <div
        className={`bg-white rounded-t-lg shadow-lg w-full max-w-md mx-4 mb-4 max-h-[80vh] overflow-y-auto ${
          isMobile ? 'rounded-b-none' : 'rounded-lg'
        } ${className}`}
      >
        {children}
      </div>
    </div>
  )
}
