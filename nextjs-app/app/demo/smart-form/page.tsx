'use client'

import React from 'react'
import { Toaster } from 'react-hot-toast'
import { useRouter } from 'next/navigation'
import ConsolidatedPropertyForm from '@/components/property/ConsolidatedPropertyForm'

export default function SmartFormDemoPage() {
   const router = useRouter()
 
  const handleSuccess = (_response?: any) => {
     // Handle successful property creation
     console.log('Property created successfully!')
     // In a real app, you might redirect to the properties list
     // router.push('/properties')
   }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
      {/* Demo Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.back()}
                className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                ← Back
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Smart Property Form Demo
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  AI-Enhanced Property Addition with Progressive Disclosure
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                Demo Mode
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Demo Features Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="text-center">
            <h2 className="text-lg font-semibold mb-2">🚀 New Features Showcase</h2>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <div className="flex items-center space-x-1">
                <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                <span>Progressive Multi-Step Form</span>
              </div>
              <div className="flex items-center space-x-1">
                <span className="w-2 h-2 bg-yellow-400 rounded-full"></span>
                <span>AI Content Generation</span>
              </div>
              <div className="flex items-center space-x-1">
                <span className="w-2 h-2 bg-pink-400 rounded-full"></span>
                <span>Real-time Market Insights</span>
              </div>
              <div className="flex items-center space-x-1">
                <span className="w-2 h-2 bg-cyan-400 rounded-full"></span>
                <span>Smart Validation</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Instructions Panel */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 mb-6 border border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
            💡 How to Test the Smart Form
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800 dark:text-blue-200">
            <div>
              <h4 className="font-semibold mb-2">Step 1: Location Intelligence</h4>
              <ul className="space-y-1 list-disc list-inside">
                <li>Enter any address (e.g., &quot;123 Marine Drive, Mumbai&quot;)</li>
                <li>Watch AI detect property type and market trends</li>
                <li>Notice the contextual guidance and validation</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Step 2: Smart Suggestions</h4>
              <ul className="space-y-1 list-disc list-inside">
                <li>Fill basic property details</li>
                <li>See real-time market insights appear</li>
                <li>Get pricing recommendations based on area</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Step 3: AI Content Generation</h4>
              <ul className="space-y-1 list-disc list-inside">
                <li>Click &quot;Generate AI Content&quot; in the final step</li>
                <li>Review AI-generated title and description</li>
                <li>See quality scores and apply suggestions</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Step 4: Progressive Experience</h4>
              <ul className="space-y-1 list-disc list-inside">
                <li>Notice step-by-step validation</li>
                <li>Experience smooth transitions</li>
                <li>Test mobile responsiveness</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Smart Property Form (Consolidated) */}
      <ConsolidatedPropertyForm
        variant="wizard"
        enableAI={true}
        enableMarketInsights={true}
        enableQualityScoring={true}
        onSuccess={handleSuccess}
      />

      {/* Demo Footer */}
      <div className="bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              🎯 Key Improvements Demonstrated
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
              <div className="bg-gray-50 dark:bg-slate-700 rounded-lg p-4">
                <div className="text-2xl mb-2">🧠</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">AI-Powered UX</h4>
                <p className="text-gray-600 dark:text-gray-400">
                  Intelligent suggestions reduce cognitive load and improve form completion rates
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-slate-700 rounded-lg p-4">
                <div className="text-2xl mb-2">📊</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Market Intelligence</h4>
                <p className="text-gray-600 dark:text-gray-400">
                  Real-time market data helps users make informed pricing decisions
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-slate-700 rounded-lg p-4">
                <div className="text-2xl mb-2">🎨</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Progressive Disclosure</h4>
                <p className="text-gray-600 dark:text-gray-400">
                  Step-by-step approach reduces overwhelm and increases completion
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 4000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  )
}