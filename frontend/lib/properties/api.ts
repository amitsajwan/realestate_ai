/**
 * Properties API
 * ==============
 * API calls for property operations
 */

import { AIPropertySuggestion, PropertiesResponse, PropertyCreate, PropertyResponse, PropertyUpdate, PublishingRequest, PublishingStatusResponse } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class PropertiesAPI {
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
     * Get all properties for the current user
     */
    async getProperties(skip: number = 0, limit: number = 100): Promise<PropertiesResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/?skip=${skip}&limit=${limit}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get properties failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get a specific property by ID
     */
    async getProperty(propertyId: string): Promise<PropertyResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/${propertyId}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get property failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Create a new property
     */
    async createProperty(propertyData: PropertyCreate): Promise<PropertyResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(propertyData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Create property failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Update an existing property
     */
    async updateProperty(propertyId: string, propertyData: PropertyUpdate): Promise<PropertyResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/${propertyId}`, {
            method: 'PUT',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(propertyData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Update property failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Delete a property
     */
    async deleteProperty(propertyId: string): Promise<{ success: boolean; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/${propertyId}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Delete property failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get AI suggestions for a property
     */
    async getAIPropertySuggestions(propertyId: string, data: any): Promise<{ success: boolean; data?: AIPropertySuggestion; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/${propertyId}/ai-suggestions`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get AI suggestions failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get market insights for a property
     */
    async getMarketInsights(propertyId: string): Promise<{ success: boolean; data?: any; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/${propertyId}/market-insights`, {
            method: 'POST',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get market insights failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get property analytics
     */
    async getPropertyAnalytics(propertyId: string): Promise<{ success: boolean; data?: any; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/${propertyId}/analytics`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get property analytics failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Search properties
     */
    async searchProperties(query: string, filters?: any): Promise<PropertiesResponse> {
        const searchParams = new URLSearchParams({ q: query });
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value) searchParams.append(key, String(value));
            });
        }

        const response = await fetch(`${this.baseUrl}/api/v1/properties/search?${searchParams}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Search properties failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Publish property to channels
     */
    async publishProperty(publishData: PublishingRequest): Promise<PublishingStatusResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/${publishData.propertyId}/publish`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(publishData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Publish property failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get publishing status
     */
    async getPublishingStatus(propertyId: string): Promise<PublishingStatusResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/${propertyId}/status`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get publishing status failed: ${response.status}`);
        }

        return response.json();
    }
}

export const propertiesAPI = new PropertiesAPI();
