'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { CogIcon } from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'

interface FacebookPage {
  id: string
  name: string
  access_token?: string
}

export default function FacebookIntegration() {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [facebookPages, setFacebookPages] = useState<FacebookPage[]>([])
  const [selectedPage, setSelectedPage] = useState('')

  useEffect(() => {
    // Check if user is already connected to Facebook
    checkFacebookStatus()
  }, [])

  const checkFacebookStatus = async () => {
    try {
      const response = await fetch('/api/facebook/status')
      const data = await response.json()
      if (data.success && data.status?.connected) {
        setIsConnected(true)
        setFacebookPages(data.status.pages || [])
      }
    } catch (error) {
  console.error('[FacebookIntegration] Facebook status check failed:', error)
    }
  }

  const handleConnectFacebook = async () => {
    setIsLoading(true)
    try {
      // Get Facebook OAuth URL from backend
      const response = await fetch('/api/v1/facebook/oauth')
      const data = await response.json()
      
      if (data.success && data.oauth_url) {
        // Redirect to Facebook OAuth
        window.location.href = data.oauth_url
      } else {
        toast.error('Failed to initiate Facebook connection')
      }
    } catch (error) {
  console.error('[FacebookIntegration] Facebook connection error:', error)
      toast.error('Facebook connection failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="glass-card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <CogIcon className="w-6 h-6 text-blue-500" />
            <h2 className="text-2xl font-bold text-gray-800">Facebook Integration</h2>
          </div>
          
          {!isConnected && (
            <button
              onClick={handleConnectFacebook}
              disabled={isLoading}
              className="btn-primary flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Connecting...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                  <span>Connect Facebook Page</span>
                </>
              )}
            </button>
          )}
          
          {isConnected && (
            <div className="flex items-center space-x-2 text-green-600">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">Connected</span>
            </div>
          )}
        </div>
        
        <p className="text-gray-600 mb-6">
          Connect your Facebook account to automatically post properties and engage with leads.
        </p>

        {!isConnected ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Connect Your Facebook Page</h3>
            <p className="text-gray-500 mb-6">Connect your Facebook page to start posting properties and engaging with leads automatically.</p>
            <button
              onClick={handleConnectFacebook}
              disabled={isLoading}
              className="btn-primary inline-flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Connecting...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                  <span>Connect Facebook Page</span>
                </>
              )}
            </button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-card">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Connected Facebook Pages</h3>
                {facebookPages.length > 0 ? (
                  <div className="space-y-2">
                    {facebookPages.map((page, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                            </svg>
                          </div>
                          <span className="font-medium text-gray-900">{page.name || `Page ${index + 1}`}</span>
                        </div>
                        <span className="text-sm text-green-600 font-medium">Connected</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No Facebook pages found.</p>
                )}
              </div>
              
              <div className="glass-card">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Posts</h3>
                <p className="text-gray-500">No recent posts found.</p>
              </div>
            </div>

            <div className="mt-6">
              <div className="glass-card">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Post</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Select Page</label>
                    <select 
                      className="form-input"
                      value={selectedPage}
                      onChange={(e) => setSelectedPage(e.target.value)}
                    >
                      <option value="">Choose a page...</option>
                      {facebookPages.map((page, index) => (
                        <option key={index} value={page.id || index}>
                          {page.name || `Page ${index + 1}`}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Post Type</label>
                    <select className="form-input">
                      <option>Text Post</option>
                      <option>Image Post</option>
                      <option>Link Post</option>
                    </select>
                  </div>
                  <button 
                    className="btn-primary"
                    disabled={!selectedPage}
                  >
                    Create Post
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </motion.div>
  )
}
