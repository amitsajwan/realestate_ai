export interface Post {
    id: string;
    property_id: string;
    agent_id: string;
    title: string;
    content: string;
    language: string;
    template_id?: string;
    status: PostStatus;
    channels: string[];
    scheduled_at?: string;
    published_at?: string;
    facebook_post_id?: string;
    instagram_post_id?: string;
    linkedin_post_id?: string;
    website_post_id?: string;
    email_campaign_id?: string;
    ai_generated: boolean;
    ai_prompt?: string;
    version: number;
    created_at: string;
    updated_at: string;
    analytics?: PostAnalytics;
}

export interface PostAnalytics {
    views: number;
    likes: number;
    shares: number;
    comments: number;
    clicks: number;
    conversions: number;
    engagement_rate: number;
    reach: number;
    impressions: number;
}

export interface Template {
    id: string;
    name: string;
    description: string;
    property_type: string;
    language: string;
    template: string;
    variables: string[];
    channels: string[];
    is_active: boolean;
    created_by: string;
    created_at: string;
    updated_at: string;
}

export type PostStatus = 'draft' | 'published' | 'scheduled' | 'archived';

export interface PostFilters {
    property_id?: string;
    agent_id?: string;
    status?: PostStatus;
    language?: string;
    channels?: string[];
    ai_generated?: boolean;
    template_id?: string;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
}

export interface PostCreateRequest {
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

export interface PostUpdateRequest {
    title?: string;
    content?: string;
    language?: string;
    template_id?: string;
    channels?: string[];
    scheduled_at?: string;
    status?: PostStatus;
}

export interface TemplateCreateRequest {
    name: string;
    description: string;
    property_type: string;
    language: string;
    template: string;
    variables: string[];
    channels: string[];
}

export interface TemplateUpdateRequest {
    name?: string;
    description?: string;
    property_type?: string;
    language?: string;
    template?: string;
    variables?: string[];
    channels?: string[];
    is_active?: boolean;
}

export interface TemplateFilters {
    property_type?: string;
    language?: string;
    is_active?: boolean;
    created_by?: string;
    skip?: number;
    limit?: number;
}

export interface PublishingRequest {
    channels: string[];
    scheduled_at?: string;
}

export interface PublishingResult {
    success: boolean;
    channel: string;
    external_id?: string;
    error?: string;
    published_at?: string;
}

export interface PublishingResponse {
    post_id: string;
    results: PublishingResult[];
    success_count: number;
    failure_count: number;
}

export interface AnalyticsResponse {
    post_id: string;
    total_views: number;
    total_likes: number;
    total_shares: number;
    total_comments: number;
    total_clicks: number;
    total_conversions: number;
    engagement_rate: number;
    reach: number;
    impressions: number;
    channel_breakdown: Record<string, Record<string, number>>;
    time_series: Array<Record<string, any>>;
}

export interface PropertyAnalyticsResponse {
    property_id: string;
    total_posts: number;
    total_views: number;
    total_engagement: number;
    average_engagement_rate: number;
    top_performing_post?: Post;
    channel_performance: Record<string, Record<string, number>>;
    posts: Post[];
}
