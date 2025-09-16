/**
 * Agent Module Types
 * ==================
 * Centralized type definitions for the agent module
 * Synchronized with backend models
 */

export interface Agent {
    id: string;
    userId: string;
    name: string;
    email: string;
    phone?: string;
    company?: string;
    licenseNumber?: string;
    bio?: string;
    profileImage?: string;

    // Agent website settings
    websiteUrl?: string;
    domain?: string;
    isPublic: boolean;

    // Branding
    branding: AgentBranding;

    // Social media
    socialMedia: AgentSocialMedia;

    // Contact information
    contactInfo: AgentContactInfo;

    // Statistics
    stats: AgentStats;

    // Timestamps
    createdAt: string;
    updatedAt: string;
}

export interface AgentCreate {
    name: string;
    email: string;
    phone?: string;
    company?: string;
    licenseNumber?: string;
    bio?: string;
    profileImage?: string;
    websiteUrl?: string;
    domain?: string;
    isPublic?: boolean;
    branding?: Partial<AgentBranding>;
    socialMedia?: Partial<AgentSocialMedia>;
    contactInfo?: Partial<AgentContactInfo>;
}

export interface AgentUpdate {
    name?: string;
    email?: string;
    phone?: string;
    company?: string;
    licenseNumber?: string;
    bio?: string;
    profileImage?: string;
    websiteUrl?: string;
    domain?: string;
    isPublic?: boolean;
    branding?: Partial<AgentBranding>;
    socialMedia?: Partial<AgentSocialMedia>;
    contactInfo?: Partial<AgentContactInfo>;
}

export interface AgentFormData {
    name: string;
    email: string;
    phone: string;
    company: string;
    licenseNumber: string;
    bio: string;
    profileImage: string;
    websiteUrl: string;
    domain: string;
    isPublic: boolean;
}

export interface AgentResponse {
    success: boolean;
    data?: Agent;
    error?: string;
}

export interface AgentsResponse {
    success: boolean;
    data?: Agent[];
    total?: number;
    error?: string;
}

// Agent Branding
export interface AgentBranding {
    primaryColor: string;
    secondaryColor: string;
    accentColor: string;
    fontFamily: string;
    logoUrl?: string;
    tagline?: string;
    about?: string;
    colorPalette: {
        primary: string;
        secondary: string;
        accent: string;
    };
}

export interface BrandingSuggestion {
    tagline: string;
    about: string;
    primaryColor: string;
    secondaryColor: string;
    fontFamily: string;
    logoStyle: string;
    colorPalette: {
        primary: string;
        secondary: string;
        accent: string;
    };
}

// Agent Social Media
export interface AgentSocialMedia {
    facebook?: string;
    instagram?: string;
    linkedin?: string;
    twitter?: string;
    youtube?: string;
    website?: string;
}

// Agent Contact Information
export interface AgentContactInfo {
    address?: string;
    city?: string;
    state?: string;
    zipCode?: string;
    country?: string;
    officePhone?: string;
    mobilePhone?: string;
    email?: string;
    website?: string;
    officeHours?: string;
}

// Agent Statistics
export interface AgentStats {
    propertiesCount: number;
    postsCount: number;
    viewsCount: number;
    leadsCount: number;
    conversionsCount: number;
    averageResponseTime: number; // in minutes
    rating: number; // 1-5 stars
    reviewsCount: number;
    lastActiveAt?: string;
}

// Public Agent Profile (for public website)
export interface AgentPublicProfile {
    id: string;
    name: string;
    company?: string;
    bio?: string;
    profileImage?: string;
    websiteUrl?: string;
    domain?: string;

    // Branding
    branding: AgentBranding;

    // Social media
    socialMedia: AgentSocialMedia;

    // Contact information
    contactInfo: AgentContactInfo;

    // Statistics (public only)
    stats: {
        propertiesCount: number;
        yearsExperience?: number;
        rating: number;
        reviewsCount: number;
    };

    // Properties (public only)
    featuredProperties: any[]; // Will be Property[] from properties module

    // Timestamps
    createdAt: string;
    updatedAt: string;
}

export interface AgentPublicProfileResponse {
    success: boolean;
    data?: AgentPublicProfile;
    error?: string;
}

// Agent Dashboard
export interface AgentDashboard {
    agent: Agent;
    stats: AgentDashboardStats;
    recentActivity: AgentActivity[];
    upcomingTasks: AgentTask[];
    performanceMetrics: AgentPerformanceMetrics;
}

export interface AgentDashboardStats {
    totalProperties: number;
    activeProperties: number;
    totalPosts: number;
    publishedPosts: number;
    totalViews: number;
    totalLeads: number;
    conversionRate: number;
    averageResponseTime: number;
    monthlyGrowth: {
        properties: number;
        posts: number;
        views: number;
        leads: number;
    };
}

export interface AgentActivity {
    id: string;
    type: 'property_created' | 'post_published' | 'lead_received' | 'profile_updated';
    title: string;
    description: string;
    timestamp: string;
    metadata?: Record<string, any>;
}

export interface AgentTask {
    id: string;
    title: string;
    description: string;
    type: 'property_review' | 'post_schedule' | 'lead_followup' | 'profile_update';
    priority: 'low' | 'medium' | 'high';
    dueDate?: string;
    completed: boolean;
    createdAt: string;
}

export interface AgentPerformanceMetrics {
    responseTime: {
        average: number;
        trend: 'up' | 'down' | 'stable';
    };
    conversionRate: {
        current: number;
        trend: 'up' | 'down' | 'stable';
    };
    engagementRate: {
        current: number;
        trend: 'up' | 'down' | 'stable';
    };
    leadQuality: {
        score: number;
        trend: 'up' | 'down' | 'stable';
    };
}

export interface AgentDashboardResponse {
    success: boolean;
    data?: AgentDashboard;
    error?: string;
}

// Agent Inquiries
export interface AgentInquiry {
    id: string;
    agentId: string;
    propertyId?: string;
    name: string;
    email: string;
    phone?: string;
    message: string;
    inquiryType: 'property_inquiry' | 'general_inquiry' | 'appointment_request';
    status: 'new' | 'contacted' | 'qualified' | 'converted' | 'closed';
    priority: 'low' | 'medium' | 'high';
    source: string; // website, facebook, referral, etc.
    metadata?: Record<string, any>;
    createdAt: string;
    updatedAt: string;
}

export interface AgentInquiriesResponse {
    success: boolean;
    data?: AgentInquiry[];
    total?: number;
    error?: string;
}

// Agent Language Preferences
export interface AgentLanguagePreferences {
    agentId: string;
    primaryLanguage: string;
    supportedLanguages: string[];
    autoTranslate: boolean;
    translationProvider?: string;
    customTranslations?: Record<string, Record<string, string>>;
    createdAt: string;
    updatedAt: string;
}

export interface AgentLanguagePreferencesResponse {
    success: boolean;
    data?: AgentLanguagePreferences;
    error?: string;
}
