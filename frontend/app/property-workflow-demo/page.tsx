'use client'

import PublishingWorkflowManager from '@/components/PublishingWorkflowManager'
import SmartPropertyForm from '@/components/SmartPropertyForm'
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

export default function PropertyWorkflowDemo() {
    const [showWorkflow, setShowWorkflow] = useState(false)
    const [propertyData, setPropertyData] = useState<PropertyData | null>(null)
    const [workflowStep, setWorkflowStep] = useState<'form' | 'workflow' | 'complete'>('form')

    const handlePropertySuccess = (data: PropertyData) => {
        console.log('Property created successfully:', data)
        setPropertyData(data)
        setShowWorkflow(true)
        setWorkflowStep('workflow')
    }

    const handleWorkflowComplete = () => {
        setShowWorkflow(false)
        setWorkflowStep('complete')
        setPropertyData(null)
    }

    const handleWorkflowClose = () => {
        setShowWorkflow(false)
        setWorkflowStep('complete')
    }

    const resetDemo = () => {
        setWorkflowStep('form')
        setPropertyData(null)
        setShowWorkflow(false)
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">
                                Property-to-Post Workflow Demo
                            </h1>
                            <p className="text-gray-600 mt-1">
                                Experience the seamless AI-powered property creation and social media publishing workflow
                            </p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="text-sm text-gray-500">
                                Step: {workflowStep === 'form' ? '1' : workflowStep === 'workflow' ? '2-4' : 'Complete'}
                            </div>
                            <button
                                onClick={resetDemo}
                                className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                            >
                                Reset Demo
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Progress Indicator */}
            <div className="bg-white border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-center">
                        <div className="flex items-center space-x-8">
                            {/* Step 1: Property Creation */}
                            <div className={`flex items-center ${workflowStep === 'form' ? 'text-blue-600' : workflowStep === 'workflow' || workflowStep === 'complete' ? 'text-green-600' : 'text-gray-400'}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${workflowStep === 'form' ? 'bg-blue-100 text-blue-600' :
                                        workflowStep === 'workflow' || workflowStep === 'complete' ? 'bg-green-100 text-green-600' :
                                            'bg-gray-100 text-gray-400'
                                    }`}>
                                    {workflowStep === 'form' ? '1' : '✓'}
                                </div>
                                <span className="ml-2 text-sm font-medium">Create Property</span>
                            </div>

                            <div className={`w-16 h-0.5 ${workflowStep === 'workflow' || workflowStep === 'complete' ? 'bg-green-600' : 'bg-gray-300'}`}></div>

                            {/* Step 2: Success Modal */}
                            <div className={`flex items-center ${workflowStep === 'workflow' ? 'text-blue-600' : workflowStep === 'complete' ? 'text-green-600' : 'text-gray-400'}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${workflowStep === 'workflow' ? 'bg-blue-100 text-blue-600' :
                                        workflowStep === 'complete' ? 'bg-green-100 text-green-600' :
                                            'bg-gray-100 text-gray-400'
                                    }`}>
                                    {workflowStep === 'workflow' ? '2' : workflowStep === 'complete' ? '✓' : '2'}
                                </div>
                                <span className="ml-2 text-sm font-medium">Success Modal</span>
                            </div>

                            <div className={`w-16 h-0.5 ${workflowStep === 'complete' ? 'bg-green-600' : 'bg-gray-300'}`}></div>

                            {/* Step 3: AI Generation */}
                            <div className={`flex items-center ${workflowStep === 'workflow' ? 'text-blue-600' : workflowStep === 'complete' ? 'text-green-600' : 'text-gray-400'}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${workflowStep === 'workflow' ? 'bg-blue-100 text-blue-600' :
                                        workflowStep === 'complete' ? 'bg-green-100 text-green-600' :
                                            'bg-gray-100 text-gray-400'
                                    }`}>
                                    {workflowStep === 'workflow' ? '3' : workflowStep === 'complete' ? '✓' : '3'}
                                </div>
                                <span className="ml-2 text-sm font-medium">AI Generation</span>
                            </div>

                            <div className={`w-16 h-0.5 ${workflowStep === 'complete' ? 'bg-green-600' : 'bg-gray-300'}`}></div>

                            {/* Step 4: Publishing */}
                            <div className={`flex items-center ${workflowStep === 'complete' ? 'text-green-600' : 'text-gray-400'}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${workflowStep === 'complete' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                                    }`}>
                                    {workflowStep === 'complete' ? '✓' : '4'}
                                </div>
                                <span className="ml-2 text-sm font-medium">Publishing</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {workflowStep === 'form' && (
                    <div className="space-y-8">
                        {/* Demo Instructions */}
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                            <h2 className="text-lg font-semibold text-blue-900 mb-2">
                                🎯 Demo Instructions
                            </h2>
                            <p className="text-blue-800 mb-4">
                                This demo showcases the complete property-to-post workflow as recommended by the Architecture team.
                                Follow these steps to experience the seamless AI-powered workflow:
                            </p>
                            <ol className="list-decimal list-inside space-y-2 text-blue-800">
                                <li>Fill out the property form below with sample data</li>
                                <li>After successful creation, you'll see the new success modal with "Create Social Posts" CTA</li>
                                <li>Experience the AI content generation interface with property context</li>
                                <li>See the publishing confirmation with analytics preview</li>
                            </ol>
                        </div>

                        {/* Property Form */}
                        <div className="bg-white rounded-lg shadow-sm border">
                            <div className="p-6 border-b border-gray-200">
                                <h2 className="text-xl font-semibold text-gray-900">
                                    Step 1: Create Your Property
                                </h2>
                                <p className="text-gray-600 mt-1">
                                    Fill out the form below to create a new property listing
                                </p>
                            </div>
                            <div className="p-6">
                                <SmartPropertyForm onSuccess={handlePropertySuccess} />
                            </div>
                        </div>
                    </div>
                )}

                {workflowStep === 'complete' && (
                    <div className="text-center py-16">
                        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            Workflow Complete! 🎉
                        </h2>
                        <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
                            You've successfully experienced the complete property-to-post workflow.
                            The new seamless experience transforms property creation into an AI-powered
                            social media marketing journey.
                        </p>
                        <div className="space-y-4">
                            <button
                                onClick={resetDemo}
                                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Workflow Manager */}
            <PublishingWorkflowManager
                propertyData={propertyData}
                isOpen={showWorkflow}
                onClose={handleWorkflowClose}
                onComplete={handleWorkflowComplete}
            />
        </div>
    )
}
