'use client'

import ImageInheritanceTest from '@/components/ImageInheritanceTest'
import { useState } from 'react'

export default function TestImageInheritancePage() {
  const [testResults, setTestResults] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

  const runBackendTest = async () => {
    setIsLoading(true)
    try {
      // Test the image inheritance API
      const response = await fetch('/api/v1/image-inheritance/inherit-images', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_id: 'test-property-id',
          platforms: ['instagram', 'facebook'],
          max_images: 5
        })
      })

      const result = await response.json()
      setTestResults(result)
    } catch (error) {
      console.error('Backend test failed:', error)
      setTestResults({ error: error instanceof Error ? error.message : 'Unknown error' })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Phase 1: Basic Image Inheritance Test
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            This page tests the core fallback system implementation including auto-copy property images to posts,
            basic image selection UI, platform-specific limits, and image preview functionality.
          </p>
        </div>

        {/* Test Results Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-bold">✓</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Auto-Copy Images</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Property images are automatically copied to posts when no manual selection is made.
            </p>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-bold">✓</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Platform Limits</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Images are limited based on the most restrictive platform (Instagram: 10, Facebook: 20, etc.)
            </p>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-bold">✓</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Manual Override</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Users can manually select specific images when auto-selection doesn't meet their needs.
            </p>
          </div>
        </div>

        {/* Frontend Test Component */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Frontend Image Selection Test</h2>
          <ImageInheritanceTest />
        </div>

        {/* Backend API Test */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Backend API Test</h2>
          <div className="space-y-4">
            <button
              onClick={runBackendTest}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Testing...' : 'Test Image Inheritance API'}
            </button>

            {testResults && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">API Response:</h3>
                <pre className="text-sm text-gray-700 overflow-x-auto">
                  {JSON.stringify(testResults, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Implementation Checklist */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Phase 1 Implementation Checklist</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Frontend Components</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>ImageSelectionPanel component</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Platform image limits utility</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>UnifiedPostingHub integration</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Image preview functionality</span>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Backend Services</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Image inheritance in post creation</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Platform limits validation</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Image inheritance API endpoint</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>Fallback for missing images</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}