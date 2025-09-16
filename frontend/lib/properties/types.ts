/**
 * Properties Module Types
 * =======================
 * Centralized type definitions for the properties module
 * Synchronized with backend models
 */

export interface Property {
    id: string;
    title: string;
    description: string;
    propertyType: string; // apartment, house, commercial, etc.
    price: number;
    location: string;
    bedrooms: number;
    bathrooms: number; // Can be decimal (1.5, 2.5, etc.)
    areaSqft?: number;
    features: string[];
    amenities?: string;
    status: PropertyStatus;
    agentId: string;
    images: string[];

    // Smart property features (optional)
    smartFeatures?: Record<string, any>;
    aiInsights?: Record<string, any>;
    marketAnalysis?: Record<string, any>;

    // Publishing information
    publishingStatus: PublishingStatus;
    publishedAt?: string;
    targetLanguages: string[];
    publishingChannels: string[];
    facebookPageMappings: Record<string, string>;

    // Timestamps
    createdAt: string;
    updatedAt: string;
}

export interface PropertyCreate {
    title: string;
    description: string;
    propertyType: string;
    price: number;
    location: string;
    bedrooms: number;
    bathrooms: number;
    areaSqft?: number;
    features: string[];
    amenities?: string;
    images: string[];
    smartFeatures?: Record<string, any>;
}

export interface PropertyUpdate {
    title?: string;
    description?: string;
    propertyType?: string;
    price?: number;
    location?: string;
    bedrooms?: number;
    bathrooms?: number;
    areaSqft?: number;
    features?: string[];
    amenities?: string;
    images?: string[];
    status?: PropertyStatus;
    smartFeatures?: Record<string, any>;
    aiInsights?: Record<string, any>;
    marketAnalysis?: Record<string, any>;
}

export interface PropertyFormData {
    title: string;
    description: string;
    propertyType: string;
    price: number;
    location: string;
    bedrooms: number;
    bathrooms: number;
    areaSqft?: number;
    features: string[];
    amenities?: string;
    images: string[];
}

export interface PropertyResponse {
    success: boolean;
    data?: Property;
    error?: string;
}

export interface PropertiesResponse {
    success: boolean;
    data?: Property[];
    total?: number;
    error?: string;
}

// Enums
export enum PropertyStatus {
    ACTIVE = 'active',
    SOLD = 'sold',
    PENDING = 'pending',
    INACTIVE = 'inactive',
    DRAFT = 'draft'
}

export enum PublishingStatus {
    DRAFT = 'draft',
    PUBLISHED = 'published',
    ARCHIVED = 'archived',
    SCHEDULED = 'scheduled'
}

// AI and Analytics
export interface AIPropertySuggestion {
    title: string;
    description: string;
    price: string;
    amenities: string[];
    features: string[];
    marketInsights: string;
}

export interface PropertyAnalytics {
    views: number;
    likes: number;
    shares: number;
    comments: number;
    clicks: number;
    conversions: number;
    engagementRate: number;
    reach: number;
    impressions: number;
}

export interface MarketInsight {
    trend: string;
    recommendation: string;
    confidence: number;
    dataPoints: string[];
}

// Publishing
export interface PublishingRequest {
    propertyId: string;
    targetLanguages: string[];
    publishingChannels: string[];
    facebookPageMappings: Record<string, string>;
    autoTranslate: boolean;
}

export interface PublishingStatusResponse {
    propertyId: string;
    publishingStatus: string;
    publishedAt?: string;
    publishedChannels: string[];
    languageStatus: Record<string, string>;
    facebookPosts: Record<string, string>;
    analyticsData: Record<string, any>;
}
