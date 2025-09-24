'use client'

import PublishingWorkflowManager from '@/components/PublishingWorkflowManager'
import { useState } from 'react'

interface PropertyData {
    id: string
    title: string
    location: string
    price: number
    bedrooms: number
    bathrooms: number
    propertyType: string
    area?: number
    description?: string
    images?: string[]
}

export default function TestWorkflowPage() {
    const [showWorkflow, setShowWorkflow] = useState(false)
    const [propertyData, setPropertyData] = useState<PropertyData | null>(null)

    const handleCreateProperty = () => {
        // Simulate property creation
        const mockProperty: PropertyData = {
            id: 'test-property-1',
            title: 'Beautiful 3BHK Apartment',
            location: 'Bandra West, Mumbai',
            price: 7500000,
            bedrooms: 3,
            bathrooms: 2,
            propertyType: 'Apartment',
            area: 1200,
            description: 'Spacious 3BHK apartment in prime location with modern amenities and great connectivity.',
            images: ['/images/sample-property-1.jpg', '/images/sample-property-2.jpg']
        }

        setPropertyData(mockProperty)
        setShowWorkflow(true)
    }

    const handleWorkflowComplete = () => {
        setShowWorkflow(false)
        setPropertyData(null)
        alert('Workflow completed successfully! 🎉')
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-4xl mx-auto">
                <div className="bg-white rounded-lg shadow-lg p-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-4">
                        Property-to-Post Workflow Test
                    </h1>

                    <p className="text-gray-600 mb-8">
                        This is a simplified test of the new property-to-post workflow.
                        Click the button below to simulate property creation and see the workflow in action.
                    </p>

                    {!showWorkflow ? (
                        <div className="space-y-6">
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                                <h2 className="text-lg font-semibold text-blue-900 mb-2">
                                    🎯 Test Instructions
                                </h2>
                                <p className="text-blue-800">
                                    Click the button below to simulate creating a property and experience the new workflow:
                                </p>
                                <ol className="list-decimal list-inside space-y-1 text-blue-800 mt-2">
                                    <li>Property creation success modal</li>
                                    <li>AI content generation interface</li>
                                    <li>Publishing confirmation with analytics</li>
                                </ol>
                            </div>

                            <button
                                onClick={handleCreateProperty}
                                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                            >
                                🏠 Create Test Property & Start Workflow
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                                <h2 className="text-lg font-semibold text-green-900 mb-2">
                                    ✅ Property Created Successfully!
                                </h2>
                                <div className="bg-white rounded-lg p-4 mb-4">
                                    <h3 className="font-semibold text-gray-900">{propertyData?.title}</h3>
                                    <p className="text-gray-600">{propertyData?.location}</p>
                                    <div className="flex gap-4 text-sm text-gray-500 mt-2">
                                        <span>{propertyData?.bedrooms} bed</span>
                                        <span>{propertyData?.bathrooms} bath</span>
                                        <span>{propertyData?.propertyType}</span>
                                    </div>
                                    <div className="mt-2">
                                        <span className="text-2xl font-bold text-green-600">
                                            ₹{(propertyData?.price || 0) / 100000}L
                                        </span>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <h4 className="font-semibold text-gray-900">Next Steps:</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                                            <h5 className="font-medium text-gray-700 mb-2">Step 1: Success Modal</h5>
                                            <p className="text-sm text-gray-600">✅ Property created with success modal</p>
                                        </div>
                                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                                            <h5 className="font-medium text-gray-700 mb-2">Step 2: AI Generation</h5>
                                            <p className="text-sm text-gray-600">🤖 AI content generation interface</p>
                                        </div>
                                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                                            <h5 className="font-medium text-gray-700 mb-2">Step 3: Publishing</h5>
                                            <p className="text-sm text-gray-600">📱 Multi-platform publishing</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-4">
                                <button
                                    onClick={handleWorkflowComplete}
                                    className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all duration-200"
                                >
                                    🚀 Complete Workflow
                                </button>
                                <button
                                    onClick={() => setShowWorkflow(false)}
                                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    Reset
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Workflow Manager */}
            <PublishingWorkflowManager
                propertyData={propertyData}
                isOpen={showWorkflow}
                onClose={() => setShowWorkflow(false)}
                onComplete={handleWorkflowComplete}
            />
        </div>
    )
}
