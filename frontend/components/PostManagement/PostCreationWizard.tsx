import { Property } from '@/lib/properties';
import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Post, Template } from '../../types/post';

interface PostCreationWizardProps {
    propertyId?: string;
    onPostCreated: (post: Post) => void;
    onCancel: () => void;
}

interface PostCreateData {
    property_id: string;
    title: string;
    content: string;
    language: string;
    template_id?: string;
    channels: string[];
    scheduled_at?: string;
    ai_generated: boolean;
    ai_prompt?: string;
}

const steps = [
    { id: 1, title: 'Select Property', description: 'Choose the property for this post' },
    { id: 2, title: 'Select Template', description: 'Choose a template or start from scratch' },
    { id: 3, title: 'Generate Content', description: 'Create content using AI or write manually' },
    { id: 4, title: 'Review & Edit', description: 'Review and edit your content' },
    { id: 5, title: 'Publishing Options', description: 'Choose channels and schedule' }
];

export const PostCreationWizard: React.FC<PostCreationWizardProps> = ({
    propertyId,
    onPostCreated,
    onCancel
}) => {
    const [currentStep, setCurrentStep] = useState(1);
    const [postData, setPostData] = useState<PostCreateData>({
        property_id: propertyId || '',
        title: '',
        content: '',
        language: 'en',
        channels: [],
        ai_generated: false,
        ai_prompt: ''
    });
    const [properties, setProperties] = useState<Property[]>([]);
    const [templates, setTemplates] = useState<Template[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [aiGenerating, setAiGenerating] = useState(false);

    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        try {
            setLoading(true);
            const [propertiesRes, templatesRes] = await Promise.all([
                api.properties.get(),
                api.templates.get()
            ]);
            setProperties(propertiesRes);
            setTemplates(templatesRes);
        } catch (error) {
            setError('Failed to load data');
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleNext = () => {
        if (currentStep < steps.length) {
            setCurrentStep(currentStep + 1);
        }
    };

    const handlePrevious = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleCreatePost = async () => {
        try {
            setLoading(true);
            setError(null);

            const post = await api.posts.create(postData);
            onPostCreated(post);
        } catch (error) {
            setError('Failed to create post');
            console.error('Error creating post:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateAIContent = async () => {
        if (!postData.property_id || !postData.ai_prompt) return;

        try {
            setAiGenerating(true);
            setError(null);

            const property = properties.find(p => p.id === postData.property_id);
            if (!property) return;

            const propertyData = {
                title: property.title,
                description: property.description,
                price: property.price,
                location: property.location,
                property_type: property.propertyType,
                features: property.features || []
            };

            const content = await api.posts.generateAIContent({
                property_data: propertyData,
                prompt: postData.ai_prompt,
                language: postData.language
            });

            setPostData(prev => ({
                ...prev,
                content: content,
                ai_generated: true
            }));
        } catch (error) {
            setError('Failed to generate AI content');
            console.error('Error generating AI content:', error);
        } finally {
            setAiGenerating(false);
        }
    };

    const handleTemplateSelect = (template: Template) => {
        setPostData(prev => ({
            ...prev,
            template_id: template.id,
            content: template.template,
            language: template.language,
            channels: template.channels
        }));
    };

    const renderStepContent = () => {
        switch (currentStep) {
            case 1:
                return (
                    <PropertySelectionStep
                        properties={properties}
                        selectedPropertyId={postData.property_id}
                        onPropertySelect={(propertyId) =>
                            setPostData(prev => ({ ...prev, property_id: propertyId }))
                        }
                    />
                );
            case 2:
                return (
                    <TemplateSelectionStep
                        templates={templates}
                        selectedTemplateId={postData.template_id}
                        onTemplateSelect={handleTemplateSelect}
                        onSkipTemplate={() => setPostData(prev => ({ ...prev, template_id: undefined }))}
                    />
                );
            case 3:
                return (
                    <ContentGenerationStep
                        postData={postData}
                        onDataChange={setPostData}
                        onGenerateAI={handleGenerateAIContent}
                        aiGenerating={aiGenerating}
                    />
                );
            case 4:
                return (
                    <ContentReviewStep
                        postData={postData}
                        onDataChange={setPostData}
                    />
                );
            case 5:
                return (
                    <PublishingOptionsStep
                        postData={postData}
                        onDataChange={setPostData}
                    />
                );
            default:
                return null;
        }
    };

    const canProceed = () => {
        switch (currentStep) {
            case 1:
                return !!postData.property_id;
            case 2:
                return true; // Template selection is optional
            case 3:
                return !!postData.title && !!postData.content;
            case 4:
                return !!postData.title && !!postData.content;
            case 5:
                return postData.channels.length > 0;
            default:
                return false;
        }
    };

    if (loading && currentStep === 1) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold text-gray-900">Create New Post</h2>
                        <button
                            onClick={onCancel}
                            className="text-gray-400 hover:text-gray-600"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Progress Steps */}
                    <div className="mt-4">
                        <div className="flex items-center justify-between">
                            {steps.map((step, index) => (
                                <div key={step.id} className="flex items-center">
                                    <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${currentStep >= step.id
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-200 text-gray-600'
                                        }`}>
                                        {step.id}
                                    </div>
                                    <div className="ml-2 hidden sm:block">
                                        <p className={`text-sm font-medium ${currentStep >= step.id ? 'text-blue-600' : 'text-gray-500'
                                            }`}>
                                            {step.title}
                                        </p>
                                        <p className="text-xs text-gray-500">{step.description}</p>
                                    </div>
                                    {index < steps.length - 1 && (
                                        <div className={`hidden sm:block w-16 h-0.5 mx-4 ${currentStep > step.id ? 'bg-blue-600' : 'bg-gray-200'
                                            }`} />
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[60vh]">
                    {error && (
                        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
                            <div className="flex">
                                <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                <div className="ml-3">
                                    <p className="text-sm text-red-800">{error}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {renderStepContent()}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
                    <div className="flex items-center justify-between">
                        <button
                            onClick={handlePrevious}
                            disabled={currentStep === 1}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>

                        <div className="flex items-center space-x-3">
                            <button
                                onClick={onCancel}
                                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                Cancel
                            </button>

                            {currentStep === steps.length ? (
                                <button
                                    onClick={handleCreatePost}
                                    disabled={!canProceed() || loading}
                                    className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'Creating...' : 'Create Post'}
                                </button>
                            ) : (
                                <button
                                    onClick={handleNext}
                                    disabled={!canProceed()}
                                    className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Next
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Step Components
const PropertySelectionStep: React.FC<{
    properties: Property[];
    selectedPropertyId: string;
    onPropertySelect: (propertyId: string) => void;
}> = ({ properties, selectedPropertyId, onPropertySelect }) => (
    <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Select Property</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {properties.map((property) => (
                <div
                    key={property.id}
                    onClick={() => onPropertySelect(property.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${selectedPropertyId === property.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                        }`}
                >
                    <h4 className="font-medium text-gray-900">{property.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{property.location}</p>
                    <p className="text-sm text-gray-500 mt-1">₹{property.price?.toLocaleString()}</p>
                </div>
            ))}
        </div>
    </div>
);

const TemplateSelectionStep: React.FC<{
    templates: Template[];
    selectedTemplateId?: string;
    onTemplateSelect: (template: Template) => void;
    onSkipTemplate: () => void;
}> = ({ templates, selectedTemplateId, onTemplateSelect, onSkipTemplate }) => (
    <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Select Template (Optional)</h3>

        <div className="mb-4">
            <button
                onClick={onSkipTemplate}
                className={`w-full p-4 border rounded-lg text-left transition-colors ${!selectedTemplateId
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                    }`}
            >
                <h4 className="font-medium text-gray-900">Start from scratch</h4>
                <p className="text-sm text-gray-600">Create a custom post without using a template</p>
            </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map((template) => (
                <div
                    key={template.id}
                    onClick={() => onTemplateSelect(template)}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${selectedTemplateId === template.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                        }`}
                >
                    <h4 className="font-medium text-gray-900">{template.name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                    <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {template.property_type}
                        </span>
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {template.language.toUpperCase()}
                        </span>
                    </div>
                </div>
            ))}
        </div>
    </div>
);

const ContentGenerationStep: React.FC<{
    postData: PostCreateData;
    onDataChange: (data: PostCreateData) => void;
    onGenerateAI: () => void;
    aiGenerating: boolean;
}> = ({ postData, onDataChange, onGenerateAI, aiGenerating }) => (
    <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Generate Content</h3>

        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Post Title
                </label>
                <input
                    type="text"
                    value={postData.title}
                    onChange={(e) => onDataChange({ ...postData, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter post title"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Language
                </label>
                <select
                    value={postData.language}
                    onChange={(e) => onDataChange({ ...postData, language: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="ta">Tamil</option>
                    <option value="te">Telugu</option>
                    <option value="bn">Bengali</option>
                    <option value="gu">Gujarati</option>
                    <option value="kn">Kannada</option>
                    <option value="ml">Malayalam</option>
                    <option value="mr">Marathi</option>
                    <option value="pa">Punjabi</option>
                    <option value="ur">Urdu</option>
                </select>
            </div>

            <div>
                <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                        Content
                    </label>
                    <div className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            id="ai-generated"
                            checked={postData.ai_generated}
                            onChange={(e) => onDataChange({ ...postData, ai_generated: e.target.checked })}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <label htmlFor="ai-generated" className="text-sm text-gray-700">
                            AI Generated
                        </label>
                    </div>
                </div>

                {postData.ai_generated && (
                    <div className="mb-3">
                        <textarea
                            value={postData.ai_prompt || ''}
                            onChange={(e) => onDataChange({ ...postData, ai_prompt: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Enter AI prompt for content generation"
                            rows={3}
                        />
                        <button
                            onClick={onGenerateAI}
                            disabled={aiGenerating || !postData.ai_prompt}
                            className="mt-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                        >
                            {aiGenerating ? 'Generating...' : 'Generate AI Content'}
                        </button>
                    </div>
                )}

                <textarea
                    value={postData.content}
                    onChange={(e) => onDataChange({ ...postData, content: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter post content"
                    rows={6}
                />
            </div>
        </div>
    </div>
);

const ContentReviewStep: React.FC<{
    postData: PostCreateData;
    onDataChange: (data: PostCreateData) => void;
}> = ({ postData, onDataChange }) => (
    <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Review & Edit</h3>

        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Post Title
                </label>
                <input
                    type="text"
                    value={postData.title}
                    onChange={(e) => onDataChange({ ...postData, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content
                </label>
                <textarea
                    value={postData.content}
                    onChange={(e) => onDataChange({ ...postData, content: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={8}
                />
            </div>
        </div>
    </div>
);

const PublishingOptionsStep: React.FC<{
    postData: PostCreateData;
    onDataChange: (data: PostCreateData) => void;
}> = ({ postData, onDataChange }) => {
    const channels = [
        { id: 'facebook', name: 'Facebook', icon: '📘' },
        { id: 'instagram', name: 'Instagram', icon: '📷' },
        { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
        { id: 'website', name: 'Website', icon: '🌐' },
        { id: 'email', name: 'Email', icon: '📧' }
    ];

    const toggleChannel = (channelId: string) => {
        const newChannels = postData.channels.includes(channelId)
            ? postData.channels.filter(id => id !== channelId)
            : [...postData.channels, channelId];
        onDataChange({ ...postData, channels: newChannels });
    };

    return (
        <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Publishing Options</h3>

            <div className="space-y-6">
                <div>
                    <h4 className="text-md font-medium text-gray-700 mb-3">Select Channels</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {channels.map((channel) => (
                            <div
                                key={channel.id}
                                onClick={() => toggleChannel(channel.id)}
                                className={`p-3 border rounded-lg cursor-pointer transition-colors ${postData.channels.includes(channel.id)
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-200 hover:border-gray-300'
                                    }`}
                            >
                                <div className="flex items-center space-x-2">
                                    <span className="text-lg">{channel.icon}</span>
                                    <span className="text-sm font-medium">{channel.name}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div>
                    <h4 className="text-md font-medium text-gray-700 mb-3">Schedule</h4>
                    <div className="space-y-3">
                        <div className="flex items-center">
                            <input
                                type="radio"
                                id="publish-now"
                                name="schedule"
                                checked={!postData.scheduled_at}
                                onChange={() => onDataChange({ ...postData, scheduled_at: undefined })}
                                className="mr-2"
                            />
                            <label htmlFor="publish-now" className="text-sm text-gray-700">
                                Publish immediately
                            </label>
                        </div>
                        <div className="flex items-center">
                            <input
                                type="radio"
                                id="schedule-later"
                                name="schedule"
                                checked={!!postData.scheduled_at}
                                onChange={() => onDataChange({ ...postData, scheduled_at: new Date().toISOString() })}
                                className="mr-2"
                            />
                            <label htmlFor="schedule-later" className="text-sm text-gray-700">
                                Schedule for later
                            </label>
                        </div>
                        {postData.scheduled_at && (
                            <input
                                type="datetime-local"
                                value={postData.scheduled_at}
                                onChange={(e) => onDataChange({ ...postData, scheduled_at: e.target.value })}
                                className="ml-6 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PostCreationWizard;
