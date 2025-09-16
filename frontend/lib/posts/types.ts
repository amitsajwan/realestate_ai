/**
 * Posts Module Types
 * ==================
 * Centralized type definitions for the posts module
 * Synchronized with backend models
 */

export interface Post {
    id: string;
    propertyId: string;
    agentId: string;
    title: string;
    content: string;
    language: string;

    // Template and AI information
    templateId?: string;
    aiGenerated: boolean;
    aiPrompt?: string;
    aiModel?: string;

    // Publishing information
    status: PostStatus;
    channels: PublishingChannel[];

    // Publishing status per channel
    publishingStatus: Record<PublishingChannel, PublishingStatus>;

    // Platform-specific IDs
    platformIds: Record<PublishingChannel, string>;

    // Scheduling
    scheduledAt?: string;
    publishedAt?: string;

    // Content metadata
    tags: string[];
    hashtags: string[];
    mentions: string[];

    // Media attachments
    mediaUrls: string[];
    mediaTypes: string[];

    // Version control
    version: number;
    parentPostId?: string;

    // Analytics reference
    analyticsId?: string;

    // Timestamps
    createdAt: string;
    updatedAt: string;
}

export interface PostCreate {
    propertyId: string;
    title: string;
    content: string;
    language: string;
    templateId?: string;
    aiGenerated?: boolean;
    aiPrompt?: string;
    channels: PublishingChannel[];
    tags?: string[];
    hashtags?: string[];
    mentions?: string[];
    mediaUrls?: string[];
    scheduledAt?: string;
}

export interface PostUpdate {
    title?: string;
    content?: string;
    language?: string;
    status?: PostStatus;
    channels?: PublishingChannel[];
    tags?: string[];
    hashtags?: string[];
    mentions?: string[];
    mediaUrls?: string[];
    scheduledAt?: string;
}

export interface PostFormData {
    title: string;
    content: string;
    language: string;
    channels: PublishingChannel[];
    tags: string[];
    hashtags: string[];
    mentions: string[];
    mediaUrls: string[];
    scheduledAt?: string;
}

export interface PostResponse {
    success: boolean;
    data?: Post;
    error?: string;
}

export interface PostsResponse {
    success: boolean;
    data?: Post[];
    total?: number;
    error?: string;
}

// Enums
export enum PostStatus {
    DRAFT = 'draft',
    PUBLISHED = 'published',
    ARCHIVED = 'archived',
    SCHEDULED = 'scheduled',
    AI_GENERATED = 'ai_generated'
}

export enum PublishingChannel {
    FACEBOOK = 'facebook',
    INSTAGRAM = 'instagram',
    LINKEDIN = 'linkedin',
    TWITTER = 'twitter',
    WEBSITE = 'website',
    EMAIL = 'email'
}

export enum PublishingStatus {
    PENDING = 'pending',
    PUBLISHED = 'published',
    FAILED = 'failed',
    NOT_SUPPORTED = 'not_supported',
    UNKNOWN = 'unknown'
}

// Analytics
export interface PostAnalytics {
    postId: string;
    platform: string;
    userId: string;

    // Engagement metrics
    views: number;
    likes: number;
    shares: number;
    comments: number;
    clicks: number;
    conversions: number;

    // Calculated metrics
    engagementRate: number;
    reach: number;
    impressions: number;

    // Additional metrics
    costPerClick?: number;
    costPerConversion?: number;
    revenue?: number;

    // Timestamps
    createdAt: string;
    updatedAt: string;
    lastSynced?: string;
}

export interface PostAnalyticsResponse {
    success: boolean;
    data?: PostAnalytics;
    error?: string;
}

// Templates
export interface PostTemplate {
    id: string;
    name: string;
    description: string;
    propertyType: string;
    language: string;

    // Template content
    template: string;
    variables: string[];

    // Publishing settings
    channels: PublishingChannel[];

    // Template metadata
    isActive: boolean;
    isPublic: boolean;
    createdBy: string;

    // Usage statistics
    usageCount: number;
    lastUsed?: string;

    // Timestamps
    createdAt: string;
    updatedAt: string;
}

export interface PostTemplateResponse {
    success: boolean;
    data?: PostTemplate;
    error?: string;
}

export interface PostTemplatesResponse {
    success: boolean;
    data?: PostTemplate[];
    error?: string;
}

// AI Generation
export interface AIPostGenerationRequest {
    propertyId: string;
    templateId?: string;
    language: string;
    channels: PublishingChannel[];
    customPrompt?: string;
    includeHashtags?: boolean;
    includeMentions?: boolean;
}

export interface AIPostGenerationResponse {
    success: boolean;
    data?: {
        title: string;
        content: string;
        hashtags: string[];
        mentions: string[];
        suggestedChannels: PublishingChannel[];
    };
    error?: string;
}

// Publishing
export interface PostPublishingRequest {
    postId: string;
    channels: PublishingChannel[];
    scheduledAt?: string;
    autoTranslate?: boolean;
}

export interface PostPublishingResponse {
    success: boolean;
    data?: {
        postId: string;
        publishingStatus: Record<PublishingChannel, PublishingStatus>;
        platformIds: Record<PublishingChannel, string>;
        publishedAt?: string;
    };
    error?: string;
}
