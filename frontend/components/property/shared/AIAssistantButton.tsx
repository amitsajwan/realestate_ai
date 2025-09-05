'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { SparklesIcon, LightBulbIcon, CommandLineIcon } from '@heroicons/react/24/outline'

interface AIAssistantButtonProps {
  onGenerate: () => Promise<void>
  isLoading: boolean
  variant: 'auto-fill' | 'suggestions' | 'generate' | 'insights'
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
  children?: React.ReactNode
}

const variantConfig = {
  'auto-fill': {
    icon: SparklesIcon,
    text: 'AI Auto-Fill',
    loadingText: 'Filling...',
    gradient: 'from-purple-600 to-blue-600',
    hoverGradient: 'from-purple-700 to-blue-700'
  },
  'suggestions': {
    icon: LightBulbIcon,
    text: 'Get AI Suggestions',
    loadingText: 'Generating...',
    gradient: 'from-emerald-600 to-teal-600',
    hoverGradient: 'from-emerald-700 to-teal-700'
  },
  'generate': {
    icon: SparklesIcon,
    text: 'Generate Content',
    loadingText: 'Creating...',
    gradient: 'from-violet-600 to-purple-600',
    hoverGradient: 'from-violet-700 to-purple-700'
  },
  'insights': {
    icon: LightBulbIcon,
    text: 'Market Insights',
    loadingText: 'Analyzing...',
    gradient: 'from-orange-600 to-red-600',
    hoverGradient: 'from-orange-700 to-red-700'
  }
}

const sizeConfig = {
  sm: {
    padding: 'px-3 py-2',
    text: 'text-sm',
    icon: 'w-4 h-4'
  },
  md: {
    padding: 'px-4 py-2',
    text: 'text-sm',
    icon: 'w-5 h-5'
  },
  lg: {
    padding: 'px-6 py-3',
    text: 'text-base',
    icon: 'w-6 h-6'
  }
}

export default function AIAssistantButton({
  onGenerate,
  isLoading,
  variant,
  disabled = false,
  size = 'md',
  className = '',
  children
}: AIAssistantButtonProps) {
  const config = variantConfig[variant]
  const sizeStyles = sizeConfig[size]
  const Icon = config.icon

  const handleClick = async () => {
    if (!disabled && !isLoading) {
      await onGenerate()
    }
  }

  const isDisabled = disabled || isLoading

  return (
    <motion.button
      type="button"
      onClick={handleClick}
      disabled={isDisabled}
      className={`
        relative overflow-hidden
        ${sizeStyles.padding} ${sizeStyles.text}
        bg-gradient-to-r ${config.gradient}
        hover:${config.hoverGradient}
        text-white font-medium rounded-xl
        transition-all duration-200
        shadow-lg hover:shadow-xl
        transform hover:scale-[1.02]
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
        flex items-center gap-2
        ${className}
      `}
      whileHover={!isDisabled ? { scale: 1.02 } : {}}
      whileTap={!isDisabled ? { scale: 0.98 } : {}}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      {/* Background animation */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent"
        initial={{ x: '-100%' }}
        animate={isLoading ? { x: '100%' } : { x: '-100%' }}
        transition={{
          duration: 1.5,
          repeat: isLoading ? Infinity : 0,
          ease: 'linear'
        }}
      />
      
      {/* Content */}
      <div className="relative flex items-center gap-2">
        {isLoading ? (
          <div className={`${sizeStyles.icon} border-2 border-white border-t-transparent rounded-full animate-spin`} />
        ) : (
          <Icon className={sizeStyles.icon} />
        )}
        
        <span>
          {children || (isLoading ? config.loadingText : config.text)}
        </span>
      </div>
      
      {/* Glow effect */}
      {!isDisabled && (
        <motion.div
          className="absolute inset-0 rounded-xl bg-gradient-to-r from-white/10 to-white/5 opacity-0"
          whileHover={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        />
      )}
    </motion.button>
  )
}

// Convenience components for specific use cases
export const AIAutoFillButton = (props: Omit<AIAssistantButtonProps, 'variant'>) => (
  <AIAssistantButton {...props} variant="auto-fill" />
)

export const AISuggestionsButton = (props: Omit<AIAssistantButtonProps, 'variant'>) => (
  <AIAssistantButton {...props} variant="suggestions" />
)

export const AIGenerateButton = (props: Omit<AIAssistantButtonProps, 'variant'>) => (
  <AIAssistantButton {...props} variant="generate" />
)

export const AIInsightsButton = (props: Omit<AIAssistantButtonProps, 'variant'>) => (
  <AIAssistantButton {...props} variant="insights" />
)