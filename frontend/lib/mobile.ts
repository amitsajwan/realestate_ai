'use client'

import { useEffect, useState } from 'react'

const SWIPE_THRESHOLD = 100

export interface TouchHandlers {
  onTouchStart: (e: React.TouchEvent) => void
  onTouchMove: (e: React.TouchEvent) => void
  onTouchEnd: () => void
}

interface Point {
  x: number
  y: number
}

interface SwipeHandlers {
  onSwipeLeft?: () => void
  onSwipeRight?: () => void
  onSwipeUp?: () => void
  onSwipeDown?: () => void
}

/**
 * A hook that detects swipe gestures on mobile devices
 * @param handlers Object containing swipe event handlers
 * @returns Touch event handlers for use in a component
 */
export const useSwipe = ({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown
}: SwipeHandlers): TouchHandlers => {
  const [touchStart, setTouchStart] = useState<Point | null>(null)
  const [touchEnd, setTouchEnd] = useState<Point | null>(null)

  const onTouchStart = (event: React.TouchEvent) => {
    const touch = event.touches[0]
    setTouchEnd(null) // Reset
    setTouchStart({
      x: touch.clientX,
      y: touch.clientY
    })
  }

  const onTouchMove = (event: React.TouchEvent) => {
    const touch = event.touches[0]
    setTouchEnd({
      x: touch.clientX,
      y: touch.clientY
    })
  }

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return

    const distanceX = touchEnd.x - touchStart.x
    const distanceY = touchEnd.y - touchStart.y
    const isHorizontalSwipe = Math.abs(distanceX) > Math.abs(distanceY)

    if (isHorizontalSwipe) {
      if (Math.abs(distanceX) >= SWIPE_THRESHOLD) {
        if (distanceX > 0) {
          onSwipeRight?.()
        } else {
          onSwipeLeft?.()
        }
      }
    } else {
      if (Math.abs(distanceY) >= SWIPE_THRESHOLD) {
        if (distanceY > 0) {
          onSwipeDown?.()
        } else {
          onSwipeUp?.()
        }
      }
    }

    setTouchEnd(null)
    setTouchStart(null)
  }

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd
  }
}

/**
 * A hook that detects if the current viewport is mobile-sized
 * @returns boolean indicating if viewport is mobile-sized
 */
export const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkMobile() // Check on initial render
    window.addEventListener('resize', checkMobile)

    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  return isMobile
}

/**
 * Prevent default zoom behavior on iOS when focusing inputs
 */
export const usePreventZoom = () => {
  useEffect(() => {
    const originalContent = document
      .querySelector('meta[name="viewport"]')
      ?.getAttribute('content')

    document
      .querySelector('meta[name="viewport"]')
      ?.setAttribute('content', 'width=device-width, initial-scale=1, maximum-scale=1')

    return () => {
      if (originalContent) {
        document
          .querySelector('meta[name="viewport"]')
          ?.setAttribute('content', originalContent)
      }
    }
  }, [])
}