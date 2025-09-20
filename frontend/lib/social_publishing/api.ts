/**
 * Social Publishing API Service
 * =============================
 * API service for social media publishing workflow
 */

import { authManager } from '@/lib/auth';
import {
    AIDraft,
    DraftsResponse,
    GenerateContentRequest,
    GenerateContentResponse,
    MarkReadyRequest,
    PublishRequest,
    PublishResponse,
    UpdateDraftRequest
} from '@/types/social_publishing';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class SocialPublishingAPI {
    private baseUrl: string;

    constructor() {
        this.baseUrl = `${API_BASE_URL}/api/v1/social-publishing`;
    }

    private getHeaders(): HeadersInit {
        const authState = authManager.getState();
        const token = authState.token;

        return {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        };
    }

    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        const data = await response.json();
        return this.snakeToCamel(data);
    }

    private camelToSnake(obj: any): any {
        if (obj === null || obj === undefined) return obj;
        if (Array.isArray(obj)) return obj.map(item => this.camelToSnake(item));
        if (typeof obj !== 'object') return obj;

        const result: any = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
                result[snakeKey] = this.camelToSnake(obj[key]);
            }
        }
        return result;
    }

    private snakeToCamel(obj: any): any {
        if (obj === null || obj === undefined) return obj;
        if (Array.isArray(obj)) return obj.map(item => this.snakeToCamel(item));
        if (typeof obj !== 'object') return obj;

        const result: any = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                const camelKey = key.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
                result[camelKey] = this.snakeToCamel(obj[key]);
            }
        }
        return result;
    }

    async generateContent(request: GenerateContentRequest): Promise<GenerateContentResponse> {
        const snakeCaseRequest = this.camelToSnake(request);
        const response = await fetch(`${this.baseUrl}/generate`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(snakeCaseRequest)
        });
        return this.handleResponse<GenerateContentResponse>(response);
    }

    async updateDraft(draftId: string, request: UpdateDraftRequest): Promise<AIDraft> {
        const snakeCaseRequest = this.camelToSnake(request);
        const response = await fetch(`${this.baseUrl}/draft/${draftId}`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(snakeCaseRequest)
        });
        return this.handleResponse<AIDraft>(response);
    }

    async markDraftsReady(request: MarkReadyRequest): Promise<{ message: string }> {
        const snakeCaseRequest = this.camelToSnake(request);
        const response = await fetch(`${this.baseUrl}/mark-ready`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(snakeCaseRequest)
        });
        return this.handleResponse<{ message: string }>(response);
    }

    async publishDrafts(request: PublishRequest): Promise<PublishResponse> {
        const snakeCaseRequest = this.camelToSnake(request);
        const response = await fetch(`${this.baseUrl}/publish`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(snakeCaseRequest)
        });
        return this.handleResponse<PublishResponse>(response);
    }

    async getDrafts(propertyId: string, language?: string): Promise<DraftsResponse[]> {
        const params = new URLSearchParams({ property_id: propertyId });
        if (language) {
            params.append('language', language);
        }

        const response = await fetch(`${this.baseUrl}/drafts?${params}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse<DraftsResponse[]>(response);
    }
}

export const socialPublishingAPI = new SocialPublishingAPI();
