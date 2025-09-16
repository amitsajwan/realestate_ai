/**
 * Posts Module
 * ============
 * Centralized posts functionality
 */

// Export types
export type {
    AIPostGenerationRequest,
    AIPostGenerationResponse, Post, PostAnalytics,
    PostAnalyticsResponse, PostCreate, PostFormData, PostPublishingRequest,
    PostPublishingResponse, PostResponse, PostsResponse, PostTemplate,
    PostTemplateResponse,
    PostTemplatesResponse, PostUpdate
} from './types';

export { PostStatus, PublishingChannel, PublishingStatus } from './types';

// Export API
export { postsAPI } from './api';

// Export manager
export { PostsManager, postsManager } from './manager';
export type { PostsResult, PostsState } from './manager';

