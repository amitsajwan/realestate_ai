'use client'

import { useSwipe } from '@/lib/mobile'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'

interface ImageModalProps {
  images: string[]
  initialIndex: number
  isOpen: boolean
  onClose: () => void
}

export default function ImageModal({ images, initialIndex, isOpen, onClose }: ImageModalProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex)

  const handleSwipeLeft = () => {
    if (currentIndex < images.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handleSwipeRight = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  const swipeHandlers = useSwipe(handleSwipeRight, handleSwipeLeft)

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur"
          {...swipeHandlers}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-50 p-2 text-white/75 hover:text-white bg-black/20 hover:bg-black/40 rounded-full transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>

          {/* Image container */}
          <div className="h-full w-full flex items-center justify-center p-4">
            <img
              src={images[currentIndex]}
              alt={`Image ${currentIndex + 1} of ${images.length}`}
              className="max-w-full max-h-[80vh] sm:max-h-[90vh] object-contain"
            />
          </div>

          {/* Image counter */}
          {images.length > 1 && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1 bg-black/50 text-white/75 text-sm rounded-full">
              {currentIndex + 1} / {images.length}
            </div>
          )}

          {/* Navigation arrows */}
          {images.length > 1 && (
            <>
              <button
                onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
                disabled={currentIndex === 0}
                className="absolute left-4 top-1/2 -translate-y-1/2 p-2 text-white/75 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ←
              </button>
              <button
                onClick={() => setCurrentIndex(Math.min(images.length - 1, currentIndex + 1))}
                disabled={currentIndex === images.length - 1}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-2 text-white/75 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                →
              </button>
            </>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}