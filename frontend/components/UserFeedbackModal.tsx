/**
 * User Feedback Modal Component
 * =============================
 * 
 * A modal component for collecting user feedback after form completion
 * or abandonment, with comprehensive rating and feedback collection.
 */

'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  XMarkIcon,
  StarIcon,
  ThumbUpIcon,
  ThumbDownIcon,
  ChatBubbleLeftRightIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline'
import { useUserTesting } from '@/utils/userTesting'
import { FormVariant } from '@/types/PropertyFormTypes'

interface UserFeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  variant: FormVariant
  sessionId: string
  completed: boolean
  abandonmentPoint?: string
}

export default function UserFeedbackModal({
  isOpen,
  onClose,
  variant,
  sessionId,
  completed,
  abandonmentPoint
}: UserFeedbackModalProps) {
  const [rating, setRating] = useState(0)
  const [comments, setComments] = useState('')
  const [difficulty, setDifficulty] = useState<'very-easy' | 'easy' | 'moderate' | 'difficult' | 'very-difficult'>('moderate')
  const [features, setFeatures] = useState({
    ai: false,
    marketInsights: false,
    wizard: false,
    autoSave: false
  })
  const [suggestions, setSuggestions] = useState('')
  const [wouldRecommend, setWouldRecommend] = useState<boolean | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { collectFeedback } = useUserTesting(variant)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (rating === 0) {
      alert('Please provide a rating')
      return
    }

    setIsSubmitting(true)

    try {
      collectFeedback({
        rating,
        comments,
        difficulty,
        features,
        suggestions,
        wouldRecommend: wouldRecommend || false
      })

      // Close modal after successful submission
      setTimeout(() => {
        onClose()
      }, 1000)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      alert('Failed to submit feedback. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleFeatureToggle = (feature: keyof typeof features) => {
    setFeatures(prev => ({
      ...prev,
      [feature]: !prev[feature]
    }))
  }

  const renderStars = () => {
    return (
      <div className="flex space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => setRating(star)}
            className="focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
          >
            <StarIcon
              className={`h-8 w-8 ${
                star <= rating
                  ? 'text-yellow-400 fill-current'
                  : 'text-gray-300'
              }`}
            />
          </button>
        ))}
      </div>
    )
  }

  const getDifficultyLabel = (level: string) => {
    switch (level) {
      case 'very-easy': return 'Very Easy'
      case 'easy': return 'Easy'
      case 'moderate': return 'Moderate'
      case 'difficult': return 'Difficult'
      case 'very-difficult': return 'Very Difficult'
      default: return 'Moderate'
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 overflow-y-auto"
        >
          <div className="flex min-h-full items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
              onClick={onClose}
            />

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <ChatBubbleLeftRightIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {completed ? 'How was your experience?' : 'Help us improve'}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {completed 
                        ? 'Your feedback helps us make the form better for everyone'
                        : 'We\'d love to know what went wrong so we can fix it'
                      }
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {/* Content */}
              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                {/* Rating */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Overall Rating *
                  </label>
                  <div className="flex items-center space-x-4">
                    {renderStars()}
                    <span className="text-sm text-gray-600">
                      {rating > 0 && `${rating} out of 5 stars`}
                    </span>
                  </div>
                </div>

                {/* Difficulty */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    How difficult was it to complete the form?
                  </label>
                  <div className="grid grid-cols-5 gap-2">
                    {(['very-easy', 'easy', 'moderate', 'difficult', 'very-difficult'] as const).map((level) => (
                      <button
                        key={level}
                        type="button"
                        onClick={() => setDifficulty(level)}
                        className={`p-3 text-sm font-medium rounded-lg border transition-colors ${
                          difficulty === level
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        {getDifficultyLabel(level)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Features Used */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Which features did you use? (Select all that apply)
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { key: 'ai', label: 'AI Suggestions', icon: '🤖' },
                      { key: 'marketInsights', label: 'Market Insights', icon: '📊' },
                      { key: 'wizard', label: 'Step-by-step Wizard', icon: '🧙‍♂️' },
                      { key: 'autoSave', label: 'Auto-save', icon: '💾' }
                    ].map((feature) => (
                      <button
                        key={feature.key}
                        type="button"
                        onClick={() => handleFeatureToggle(feature.key as keyof typeof features)}
                        className={`p-3 text-sm font-medium rounded-lg border transition-colors flex items-center space-x-2 ${
                          features[feature.key as keyof typeof features]
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        <span>{feature.icon}</span>
                        <span>{feature.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Comments */}
                <div>
                  <label htmlFor="comments" className="block text-sm font-medium text-gray-700 mb-2">
                    {completed ? 'What did you like most?' : 'What went wrong?'}
                  </label>
                  <textarea
                    id="comments"
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder={completed 
                      ? 'Tell us what worked well...'
                      : 'Describe what was confusing or difficult...'
                    }
                  />
                </div>

                {/* Suggestions */}
                <div>
                  <label htmlFor="suggestions" className="block text-sm font-medium text-gray-700 mb-2">
                    Suggestions for improvement
                  </label>
                  <textarea
                    id="suggestions"
                    value={suggestions}
                    onChange={(e) => setSuggestions(e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Any ideas on how we can make this better?"
                  />
                </div>

                {/* Recommendation */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Would you recommend this form to other real estate agents?
                  </label>
                  <div className="flex space-x-4">
                    <button
                      type="button"
                      onClick={() => setWouldRecommend(true)}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
                        wouldRecommend === true
                          ? 'bg-green-600 text-white border-green-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      <ThumbUpIcon className="h-5 w-5" />
                      <span>Yes</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setWouldRecommend(false)}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
                        wouldRecommend === false
                          ? 'bg-red-600 text-white border-red-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      <ThumbDownIcon className="h-5 w-5" />
                      <span>No</span>
                    </button>
                  </div>
                </div>

                {/* Abandonment Point (if applicable) */}
                {!completed && abandonmentPoint && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <LightBulbIcon className="h-5 w-5 text-yellow-600" />
                      <span className="text-sm font-medium text-yellow-800">
                        We noticed you left at: {abandonmentPoint}
                      </span>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Skip
                  </button>
                  <button
                    type="submit"
                    disabled={rating === 0 || isSubmitting}
                    className="px-6 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Submitting...</span>
                      </>
                    ) : (
                      <span>Submit Feedback</span>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}