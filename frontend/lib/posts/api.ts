/**
 * Posts API
 * =========
 * DEPRECATED: Use apiClient from @/lib/api/unified-client instead
 * This file is kept for backward compatibility
 */

import { apiClient } from '../api/unified-client';
import {
    AIPostGenerationRequest,
    AIPostGenerationResponse,
    PostAnalyticsResponse,
    PostCreate,
    PostPublishingResponse,
    PostResponse,
    PostsResponse,
    PostTemplateResponse,
    PostTemplatesResponse,
    PostUpdate
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class PostsAPI {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    private getAuthHeaders(): Record<string, string> {
        const token = localStorage.getItem('auth_token');
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
            'Origin': 'http://localhost:3000'
        };
    }

    /**
     * Get all posts for the current user
     */
    async getPosts(skip: number = 0, limit: number = 100): Promise<PostsResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/?skip=${skip}&limit=${limit}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get posts failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get posts by property ID
     */
    async getPostsByProperty(propertyId: string): Promise<PostsResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/property/${propertyId}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get posts by property failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get a specific post by ID
     */
    async getPost(postId: string): Promise<PostResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/${postId}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get post failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Create a new post
     */
    async createPost(postData: PostCreate): Promise<PostResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(postData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Create post failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Update an existing post
     */
    async updatePost(postId: string, postData: PostUpdate): Promise<PostResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/${postId}`, {
            method: 'PUT',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(postData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Update post failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Delete a post
     */
    async deletePost(postId: string): Promise<{ success: boolean; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/${postId}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Delete post failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Publish a post
     */
    async publishPost(postId: string): Promise<PostPublishingResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/${postId}/publish`, {
            method: 'POST',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Publish post failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Unpublish a post
     */
    async unpublishPost(postId: string): Promise<{ success: boolean; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/${postId}/unpublish`, {
            method: 'POST',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Unpublish post failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get post analytics
     */
    async getPostAnalytics(postId: string): Promise<PostAnalyticsResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/${postId}/analytics`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get post analytics failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get AI suggestions for a post
     */
    async getAIPostSuggestions(postId: string): Promise<{ success: boolean; data?: any; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/${postId}/ai-suggestions`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get AI suggestions failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Enhance post with AI
     */
    async enhancePost(postId: string, enhancementData: any): Promise<PostResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/${postId}/enhance`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(enhancementData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Enhance post failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get post templates
     */
    async getPostTemplates(propertyType?: string, language?: string): Promise<PostTemplatesResponse> {
        const params = new URLSearchParams();
        if (propertyType) params.append('property_type', propertyType);
        if (language) params.append('language', language);

        const response = await fetch(`${this.baseUrl}/api/v1/templates/?${params}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get post templates failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get a specific post template
     */
    async getPostTemplate(templateId: string): Promise<PostTemplateResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/templates/${templateId}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get post template failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Generate AI post content
     */
    async generateAIPost(generationData: AIPostGenerationRequest): Promise<AIPostGenerationResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/generate`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(generationData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Generate AI post failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get supported languages
     */
    async getSupportedLanguages(): Promise<{ success: boolean; data?: string[]; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/posts/languages/supported`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get supported languages failed: ${response.status}`);
        }

        return response.json();
    }
}

export const postsAPI = new PostsAPI();
