/**
 * Accessibility utilities and focus management
 * Implements WCAG 2.1 AA compliance and keyboard navigation
 */

'use client'

import React, { useEffect, useRef, useState } from 'react'

// Focus trap utility for modals and dropdowns
export const useFocusTrap = (isActive: boolean) => {
  const containerRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!isActive || !containerRef.current) return

    const container = containerRef.current
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    const firstElement = focusableElements[0] as HTMLElement
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault()
            lastElement?.focus()
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault()
            firstElement?.focus()
          }
        }
      }

      if (e.key === 'Escape') {
        // Close modal/dropdown - implement in parent component
        const closeEvent = new CustomEvent('close')
        container.dispatchEvent(closeEvent)
      }
    }

    container.addEventListener('keydown', handleKeyDown)
    firstElement?.focus()

    return () => {
      container.removeEventListener('keydown', handleKeyDown)
    }
  }, [isActive])

  return containerRef
}

// Skip link component for keyboard navigation
export const SkipLink: React.FC<{
  href: string
  children: React.ReactNode
}> = ({ href, children }) => (
  <a
    href={href}
    className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
  >
    {children}
  </a>
)

// Screen reader only text
export const ScreenReaderOnly: React.FC<{
  children: React.ReactNode
  className?: string
}> = ({ children, className = '' }) => (
  <span className={`sr-only ${className}`}>
    {children}
  </span>
)

// Accessible button with proper focus management
export const AccessibleButton: React.FC<{
  onClick: () => void
  children: React.ReactNode
  disabled?: boolean
  'aria-label'?: string
  'aria-describedby'?: string
  className?: string
}> = ({
  onClick,
  children,
  disabled = false,
  'aria-label': ariaLabel,
  'aria-describedby': ariaDescribedBy,
  className = ''
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    aria-label={ariaLabel}
    aria-describedby={ariaDescribedBy}
    className={`focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
  >
    {children}
  </button>
)

// Live region for dynamic content announcements
export const LiveRegion: React.FC<{
  children: React.ReactNode
  priority?: 'off' | 'polite' | 'assertive'
  className?: string
}> = ({ children, priority = 'polite', className = '' }) => (
  <div
    aria-live={priority}
    aria-atomic="true"
    className={`sr-only ${className}`}
  >
    {children}
  </div>
)

// Enhanced focus styles utility
export const focusStyles = {
  default: 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
  inset: 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset',
  visible: 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus-visible:ring-2 focus-visible:ring-blue-500',
}

// Color contrast utilities for better accessibility
export const contrastColors = {
  high: {
    text: 'text-gray-900',
    bg: 'bg-white',
    border: 'border-gray-300',
  },
  medium: {
    text: 'text-gray-700',
    bg: 'bg-gray-50',
    border: 'border-gray-200',
  },
}

// Keyboard navigation hook
export const useKeyboardNavigation = (
  items: any[],
  onSelect: (item: any) => void,
  isOpen: boolean
) => {
  const [focusedIndex, setFocusedIndex] = useState(-1)

  useEffect(() => {
    if (!isOpen) {
      setFocusedIndex(-1)
      return
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setFocusedIndex(prev =>
            prev < items.length - 1 ? prev + 1 : 0
          )
          break
        case 'ArrowUp':
          e.preventDefault()
          setFocusedIndex(prev =>
            prev > 0 ? prev - 1 : items.length - 1
          )
          break
        case 'Enter':
          e.preventDefault()
          if (focusedIndex >= 0 && items[focusedIndex]) {
            onSelect(items[focusedIndex])
          }
          break
        case 'Escape':
          e.preventDefault()
          setFocusedIndex(-1)
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [items, onSelect, isOpen, focusedIndex])

  return focusedIndex
}
