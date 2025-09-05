/**
 * Color contrast utilities for WCAG 2.1 AA compliance
 * Ensures proper contrast ratios for accessibility
 */

import React from 'react'

// WCAG contrast ratio thresholds
export const CONTRAST_THRESHOLDS = {
  AA_NORMAL: 4.5,
  AA_LARGE: 3.0,
  AAA_NORMAL: 7.0,
  AAA_LARGE: 4.5
}

// Color palette with guaranteed contrast ratios
export const ACCESSIBLE_COLORS = {
  // Primary colors with high contrast
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6', // Primary blue
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a'
  },

  // Neutral grays with proper contrast
  neutral: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827'
  },

  // Semantic colors with accessibility considerations
  success: {
    light: '#dcfce7', // bg-green-100
    DEFAULT: '#16a34a', // text-green-600
    dark: '#14532d' // text-green-800
  },

  warning: {
    light: '#fef3c7', // bg-yellow-100
    DEFAULT: '#ca8a04', // text-yellow-700
    dark: '#92400e' // text-yellow-800
  },

  error: {
    light: '#fee2e2', // bg-red-100
    DEFAULT: '#dc2626', // text-red-600
    dark: '#991b1b' // text-red-800
  }
}

// Contrast calculation utility
export const calculateContrastRatio = (color1: string, color2: string): number => {
  // Convert hex to RGB
  const getRGB = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return [r, g, b]
  }

  // Calculate relative luminance
  const getLuminance = (rgb: number[]) => {
    const [r, g, b] = rgb.map(c => {
      c = c / 255
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    })
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
  }

  const rgb1 = getRGB(color1)
  const rgb2 = getRGB(color2)
  const lum1 = getLuminance(rgb1)
  const lum2 = getLuminance(rgb2)

  const lighter = Math.max(lum1, lum2)
  const darker = Math.min(lum1, lum2)

  return (lighter + 0.05) / (darker + 0.05)
}

// Check if colors meet WCAG standards
export const meetsWCAGStandard = (
  foreground: string,
  background: string,
  level: 'AA' | 'AAA' = 'AA',
  size: 'normal' | 'large' = 'normal'
): boolean => {
  const ratio = calculateContrastRatio(foreground, background)
  const threshold = level === 'AA'
    ? (size === 'large' ? CONTRAST_THRESHOLDS.AA_LARGE : CONTRAST_THRESHOLDS.AA_NORMAL)
    : (size === 'large' ? CONTRAST_THRESHOLDS.AAA_LARGE : CONTRAST_THRESHOLDS.AAA_NORMAL)

  return ratio >= threshold
}

// Accessible text component with automatic contrast adjustment
export const AccessibleText: React.FC<{
  children: React.ReactNode
  color?: string
  backgroundColor?: string
  size?: 'normal' | 'large'
  className?: string
}> = ({
  children,
  color = '#374151', // neutral-700
  backgroundColor = '#ffffff',
  size = 'normal',
  className = ''
}) => {
  const isAccessible = meetsWCAGStandard(color, backgroundColor, 'AA', size)

  // If contrast is insufficient, use a darker color
  const accessibleColor = isAccessible ? color : '#1f2937' // neutral-800

  return (
    <span
      className={className}
      style={{ color: accessibleColor }}
      aria-label={!isAccessible ? 'Text adjusted for better contrast' : undefined}
    >
      {children}
    </span>
  )
}

// High contrast button component
export const HighContrastButton: React.FC<{
  children: React.ReactNode
  onClick: () => void
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  className = ''
}) => {
  const variants = {
    primary: {
      bg: 'bg-blue-600',
      text: 'text-white',
      hover: 'hover:bg-blue-700',
      focus: 'focus:ring-blue-500',
      border: ''
    },
    secondary: {
      bg: 'bg-gray-800',
      text: 'text-white',
      hover: 'hover:bg-gray-900',
      focus: 'focus:ring-gray-500',
      border: ''
    },
    outline: {
      bg: 'bg-transparent',
      text: 'text-gray-900',
      hover: 'hover:bg-gray-100',
      focus: 'focus:ring-gray-500',
      border: 'border-2 border-gray-900'
    }
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  }

  const style = variants[variant]

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${style.bg} ${style.text} ${style.hover} ${style.focus} ${sizes[size]} ${style.border || ''} ${className}`}
    >
      {children}
    </button>
  )
}

// Color scheme validation component
export const ColorSchemeValidator: React.FC<{
  foreground: string
  background: string
  children: React.ReactNode
}> = ({ foreground, background, children }) => {
  const ratio = calculateContrastRatio(foreground, background)
  const meetsAA = ratio >= CONTRAST_THRESHOLDS.AA_NORMAL
  const meetsAAA = ratio >= CONTRAST_THRESHOLDS.AAA_NORMAL

  return (
    <div
      style={{ backgroundColor: background, color: foreground }}
      className="p-4 rounded-lg"
      title={`Contrast ratio: ${ratio.toFixed(2)} - AA: ${meetsAA ? '✓' : '✗'} AAA: ${meetsAAA ? '✓' : '✗'}`}
    >
      {children}
      {!meetsAA && (
        <div className="mt-2 text-xs text-red-600">
          ⚠️ Contrast ratio too low for accessibility standards
        </div>
      )}
    </div>
  )
}
