/**
 * Properties API
 * ==============
 * DEPRECATED: Use apiClient from @/lib/api/unified-client instead
 * This file is kept for backward compatibility
 */

import { authManager } from '@/lib/auth';
import { PropertiesResponse, PropertyResponse, PropertyUpdate, PublishingRequest, PublishingStatusResponse } from './types';

import { fetchWithAuthInterceptor } from '../auth/interceptor';

import { API_BASE_URL } from '../config/api';

class PropertiesAPI {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    private getAuthHeaders(): Record<string, string> {
        const authState = authManager.getState();
        const token = authState.token;
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
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/?skip=${skip}&limit=${limit}`, {
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
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/${propertyId}`, {
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
    async createProperty(propertyData: any): Promise<PropertyResponse> {
        // Transform the data to match backend expectations
        const backendData = {
            ...propertyData,
            // Ensure property_type is used instead of propertyType
            property_type: propertyData.property_type || propertyData.propertyType,
            // Remove propertyType if it exists to avoid confusion
            ...(propertyData.propertyType && !propertyData.property_type ? { propertyType: undefined } : {})
        };

        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(backendData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Create property failed: ${response.status}`);
        }

        const createdProperty = await response.json();
        // Wrap the response to match the expected format
        return {
            success: true,
            data: createdProperty
        };
    }

    /**
     * Update an existing property
     */
    async updateProperty(propertyId: string, propertyData: PropertyUpdate): Promise<PropertyResponse> {
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/${propertyId}`, {
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
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/${propertyId}`, {
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
    async getAIPropertySuggestions(propertyId: string, data: any): Promise<{ success: boolean; suggestions?: any; error?: string; generated_at?: string }> {
        try {
            const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/${propertyId}/ai-suggestions`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));

                // Handle specific error cases
                if (response.status === 401) {
                    throw new Error('Authentication required. Please log in to use AI features.');
                } else if (response.status === 403) {
                    throw new Error('Access denied. You do not have permission to use AI features.');
                } else if (response.status === 500) {
                    throw new Error('Server error. AI service is temporarily unavailable.');
                } else {
                    throw new Error(errorData.detail || `AI suggestions failed: ${response.status}`);
                }
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('AI suggestions API error:', error);

            // Re-throw with better error message
            if (error instanceof Error) {
                throw error;
            } else {
                throw new Error('Network error. Please check your connection and try again.');
            }
        }
    }

    /**
     * Get market insights for a property
     */
    async getMarketInsights(propertyId: string): Promise<{ success: boolean; data?: any; error?: string }> {
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/${propertyId}/market-insights`, {
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
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/${propertyId}/analytics`, {
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

        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/search?${searchParams}`, {
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
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/${publishData.propertyId}/publish`, {
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
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/properties/${propertyId}/status`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get publishing status failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Generate AI content for property
     */
    async generateAIContent(data: any): Promise<any> {
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/ai-unified/generate-unified`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Generate AI content failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Upload images
     */
    async uploadImages(formData: FormData): Promise<any> {
        const response = await fetchWithAuthInterceptor(`${this.baseUrl}/api/v1/uploads/images`, {
            method: 'POST',
            body: formData,
            // Don't set Content-Type for FormData - let browser set it with boundary
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Upload images failed: ${response.status}`);
        }

        return response.json();
    }
}

export const propertiesAPI = new PropertiesAPI();
