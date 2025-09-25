'use client'

import { useState } from 'react'
import UnifiedPostingHub from './UnifiedPostingHub'

// Example usage of UnifiedPostingHub to replace all existing posting components

export default function UnifiedPostingHubExamples() {
  const [showQuickPost, setShowQuickPost] = useState(false)
  const [showStandalone, setShowStandalone] = useState(false)
  const [showMarketingHub, setShowMarketingHub] = useState(false)
  const [showPropertyCreation, setShowPropertyCreation] = useState(false)

  // Example property data
  const exampleProperty = {
    id: '1',
    title: 'Beautiful 3BR Apartment in Downtown',
    location: 'New York, NY',
    price: 750000,
    bedrooms: 3,
    bathrooms: 2,
    propertyType: 'Apartment',
    area: 1200,
    description: 'Modern apartment with stunning city views',
    images: ['image1.jpg', 'image2.jpg']
  }

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">
        Unified Posting Hub Examples
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Quick Post Generator (replaces QuickPostGenerator.tsx) */}
        <div className="border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Post Generator</h2>
          <p className="text-gray-600 mb-4">
            Replaces: QuickPostGenerator.tsx
          </p>
          <button
            onClick={() => setShowQuickPost(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Open Quick Post Generator
          </button>
        </div>

        {/* Standalone AI Generator (replaces UnifiedAIContentGenerator.tsx) */}
        <div className="border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Standalone AI Generator</h2>
          <p className="text-gray-600 mb-4">
            Replaces: UnifiedAIContentGenerator.tsx
          </p>
          <button
            onClick={() => setShowStandalone(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Open Standalone Generator
          </button>
        </div>

        {/* Marketing Hub (replaces EnhancedPropertyMarketingHub.tsx) */}
        <div className="border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Marketing Content Hub</h2>
          <p className="text-gray-600 mb-4">
            Replaces: EnhancedPropertyMarketingHub.tsx
          </p>
          <button
            onClick={() => setShowMarketingHub(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
          >
            Open Marketing Hub
          </button>
        </div>

        {/* Property Creation (replaces SmartPropertyForm content generation) */}
        <div className="border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Property Content Creator</h2>
          <p className="text-gray-600 mb-4">
            Replaces: SmartPropertyForm.tsx content generation
          </p>
          <button
            onClick={() => setShowPropertyCreation(true)}
            className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700"
          >
            Open Property Creator
          </button>
        </div>
      </div>

      {/* Unified Posting Hub Instances */}
      
      {/* Quick Post Mode */}
      <UnifiedPostingHub
        mode="quick-post"
        propertyData={exampleProperty}
        isOpen={showQuickPost}
        onClose={() => setShowQuickPost(false)}
        preselectedLanguage="en"
        preselectedPlatforms={['website', 'facebook', 'instagram']}
        onContentGenerated={(content) => {
          console.log('Quick post content generated:', content)
        }}
        onPublish={(content, language) => {
          console.log('Quick post published:', content, language)
          setShowQuickPost(false)
        }}
      />

      {/* Standalone Mode */}
      <UnifiedPostingHub
        mode="standalone"
        isOpen={showStandalone}
        onClose={() => setShowStandalone(false)}
        preselectedLanguage="en"
        preselectedPlatforms={['website', 'facebook', 'instagram', 'linkedin']}
        onContentGenerated={(content) => {
          console.log('Standalone content generated:', content)
        }}
        onPublish={(content, language) => {
          console.log('Standalone content published:', content, language)
          setShowStandalone(false)
        }}
      />

      {/* Marketing Hub Mode */}
      <UnifiedPostingHub
        mode="marketing-hub"
        isOpen={showMarketingHub}
        onClose={() => setShowMarketingHub(false)}
        preselectedLanguage="en"
        preselectedPlatforms={['website', 'facebook', 'instagram', 'linkedin', 'twitter']}
        onContentGenerated={(content) => {
          console.log('Marketing hub content generated:', content)
        }}
        onPublish={(content, language) => {
          console.log('Marketing hub content published:', content, language)
          setShowMarketingHub(false)
        }}
      />

      {/* Property Creation Mode */}
      <UnifiedPostingHub
        mode="property-creation"
        propertyData={exampleProperty}
        isOpen={showPropertyCreation}
        onClose={() => setShowPropertyCreation(false)}
        preselectedLanguage="en"
        preselectedPlatforms={['website']}
        onContentGenerated={(content) => {
          console.log('Property creation content generated:', content)
        }}
        onPublish={(content, language) => {
          console.log('Property creation content published:', content, language)
          setShowPropertyCreation(false)
        }}
      />
    </div>
  )
}

/* 
MIGRATION GUIDE:

1. Replace QuickPostGenerator.tsx:
   <QuickPostGenerator 
     isOpen={showQuickPost}
     onClose={() => setShowQuickPost(false)}
     propertyData={property}
     onPublish={handlePublish}
   />
   
   WITH:
   <UnifiedPostingHub
     mode="quick-post"
     propertyData={property}
     isOpen={showQuickPost}
     onClose={() => setShowQuickPost(false)}
     onPublish={handlePublish}
   />

2. Replace UnifiedAIContentGenerator.tsx:
   <UnifiedAIContentGenerator
     context="standalone"
     onContentGenerated={handleContent}
     onClose={handleClose}
   />
   
   WITH:
   <UnifiedPostingHub
     mode="standalone"
     isOpen={true}
     onClose={handleClose}
     onContentGenerated={handleContent}
   />

3. Replace EnhancedPropertyMarketingHub.tsx:
   <EnhancedPropertyMarketingHub
     preselectedPropertyId={propertyId}
     onClearPreselectedProperty={handleClear}
   />
   
   WITH:
   <UnifiedPostingHub
     mode="marketing-hub"
     isOpen={true}
     preselectedProperty={propertyId}
     onClose={handleClear}
   />

4. Replace AIContentGenerator.tsx:
   <AIContentGenerator
     propertyData={property}
     onContentGenerated={handleContent}
   />
   
   WITH:
   <UnifiedPostingHub
     mode="standalone"
     propertyData={property}
     isOpen={true}
     onContentGenerated={handleContent}
   />

BENEFITS:
- ✅ Single component handles all posting scenarios
- ✅ Consistent UI/UX across all modes
- ✅ Centralized API calls
- ✅ Unified error handling
- ✅ Single source of truth for posting logic
- ✅ Easy to maintain and extend
- ✅ Reduced code duplication
*/