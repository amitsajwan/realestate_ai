/**
 * Agent API
 * =========
 * API calls for agent operations
 */

import {
    AgentCreate,
    AgentDashboardResponse,
    AgentInquiriesResponse,
    AgentLanguagePreferences,
    AgentLanguagePreferencesResponse,
    AgentPublicProfileResponse,
    AgentResponse,
    AgentUpdate,
    BrandingSuggestion
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class AgentAPI {
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
     * Get current agent profile
     */
    async getAgentProfile(): Promise<AgentResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/dashboard/profile`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get agent profile failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Update agent profile
     */
    async updateAgentProfile(agentData: AgentUpdate): Promise<AgentResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/dashboard/profile`, {
            method: 'PUT',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(agentData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Update agent profile failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Create agent profile
     */
    async createAgentProfile(agentData: AgentCreate): Promise<AgentResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/dashboard/create-profile`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(agentData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Create agent profile failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get agent dashboard data
     */
    async getAgentDashboard(): Promise<AgentDashboardResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/dashboard/stats`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get agent dashboard failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get agent inquiries
     */
    async getAgentInquiries(skip: number = 0, limit: number = 100): Promise<AgentInquiriesResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/dashboard/inquiries?skip=${skip}&limit=${limit}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get agent inquiries failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get public agent profile by slug
     */
    async getPublicAgentProfile(agentSlug: string): Promise<AgentPublicProfileResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/public/${agentSlug}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get public agent profile failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get public agent properties
     */
    async getPublicAgentProperties(agentSlug: string, filters?: any): Promise<{ success: boolean; data?: any[]; error?: string }> {
        const params = new URLSearchParams();
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value) params.append(key, String(value));
            });
        }

        const response = await fetch(`${this.baseUrl}/api/v1/agent/public/${agentSlug}/properties?${params}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get public agent properties failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get public agent stats
     */
    async getPublicAgentStats(agentSlug: string): Promise<{ success: boolean; data?: any; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/public/${agentSlug}/stats`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get public agent stats failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Submit contact inquiry
     */
    async submitContactInquiry(agentSlug: string, inquiryData: any): Promise<{ success: boolean; data?: any; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/public/${agentSlug}/contact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            },
            body: JSON.stringify(inquiryData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Submit contact inquiry failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Track contact inquiry
     */
    async trackContactInquiry(agentSlug: string, trackingData: any): Promise<{ success: boolean; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/public/${agentSlug}/track-contact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            },
            body: JSON.stringify(trackingData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Track contact inquiry failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get agent language preferences
     */
    async getAgentLanguagePreferences(): Promise<AgentLanguagePreferencesResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/publishing/agents/me/language-preferences`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get agent language preferences failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Update agent language preferences
     */
    async updateAgentLanguagePreferences(preferences: Partial<AgentLanguagePreferences>): Promise<AgentLanguagePreferencesResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/properties/publishing/agents/me/language-preferences`, {
            method: 'PUT',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(preferences)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Update agent language preferences failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get branding suggestions
     */
    async getBrandingSuggestions(agentData: any): Promise<{ success: boolean; data?: BrandingSuggestion; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/onboarding/branding-suggest`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(agentData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get branding suggestions failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Complete agent onboarding
     */
    async completeAgentOnboarding(onboardingData: any): Promise<{ success: boolean; data?: any; error?: string }> {
        const response = await fetch(`${this.baseUrl}/api/v1/agent/onboarding/onboard`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(onboardingData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Complete agent onboarding failed: ${response.status}`);
        }

        return response.json();
    }
}

export const agentAPI = new AgentAPI();
