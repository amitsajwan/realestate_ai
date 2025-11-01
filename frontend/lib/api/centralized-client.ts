/**
 * Centralized API Client
 * ======================
 * Single source of truth for all API calls with automatic token handling
 */

import { fetchWithAuthInterceptor } from '../auth/interceptor';
import { API_BASE_URL } from '../config/api';

export class CentralizedAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Centralized request method that automatically handles:
   * - Token injection
   * - Error handling
   * - Response parsing
   * - Authentication state management
   */
  public async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // All requests automatically get token via fetchWithAuthInterceptor
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000',
        ...options.headers,
      },
    };

    try {
      const response = await fetchWithAuthInterceptor(url, config);

      if (!response.ok) {
        let errorData: any = {};
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: `HTTP ${response.status}: ${response.statusText}` };
        }
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      // Handle 204 No Content responses
      if (response.status === 204) {
        return {} as T;
      }

      return response.json();
    } catch (error) {
      console.error(`API request failed:`, error);
      throw error;
    }
  }

  /**
   * Delete an image from storage
   */
  async deleteImage(imageUrl: string): Promise<void> {
    const encodedUrl = encodeURIComponent(imageUrl);
    await this.request<void>(`/api/v1/images/${encodedUrl}`, {
      method: 'DELETE',
    });
  }

  // Authentication methods
  async login(credentials: { email: string; password: string }): Promise<any> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    return this.request('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
  }

  async register(userData: any): Promise<any> {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser(): Promise<any> {
    return this.request('/api/v1/auth/me');
  }

  async updateCurrentUser(data: any): Promise<any> {
    return this.request('/api/v1/user/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Facebook Integration
  async getFacebookStatus(): Promise<any> {
    return this.request('/api/v1/facebook/status');
  }

  async connectFacebook(): Promise<any> {
    return this.request('/api/v1/facebook/connect', {
      method: 'POST',
    });
  }

  async disconnectFacebook(): Promise<any> {
    return this.request('/api/v1/facebook/disconnect', {
      method: 'POST',
    });
  }

  async getFacebookLoginUrl(): Promise<any> {
    return this.request('/api/v1/facebook/auth-url');
  }

  async getUserProfile(userId: string): Promise<any> {
    return this.request(`/api/v1/user/profile/${userId}`);
  }

  async updateUserProfile(userId: string, data: any): Promise<any> {
    return this.request(`/api/v1/user/profile/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getAgentPublicStats(): Promise<any> {
    return this.request('/api/v1/agent/public/stats');
  }

  // Team Management
  async getTeam(teamId?: string): Promise<any> {
    const endpoint = teamId ? `/api/v1/teams/${teamId}` : '/api/v1/teams/current';
    return this.request(endpoint);
  }

  async inviteTeamMember(teamId: string, data: any): Promise<any> {
    return this.request(`/api/v1/teams/${teamId}/invite`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async removeTeamMember(teamId: string, memberId: string): Promise<any> {
    return this.request(`/api/v1/teams/${teamId}/members/${memberId}`, {
      method: 'DELETE',
    });
  }

  async updateUser(userData: any): Promise<any> {
    return this.request('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async logout(): Promise<void> {
    await this.request('/api/v1/auth/logout', {
      method: 'POST',
    });
  }

  // Property methods
  async getProperties(skip: number = 0, limit: number = 100): Promise<any[]> {
    return this.request(`/api/v1/ai-unified/properties?skip=${skip}&limit=${limit}`);
  }

  async getPropertiesLegacy(skip: number = 0, limit: number = 100): Promise<any[]> {
    return this.request(`/api/v1/properties/?skip=${skip}&limit=${limit}`);
  }

  async getProperty(propertyId: string): Promise<any> {
    return this.request(`/api/v1/properties/${propertyId}`);
  }

  async createProperty(propertyData: any): Promise<any> {
    return this.request('/api/v1/properties/', {
      method: 'POST',
      body: JSON.stringify(propertyData),
    });
  }

  async updateProperty(propertyId: string, propertyData: any): Promise<any> {
    return this.request(`/api/v1/properties/${propertyId}`, {
      method: 'PUT',
      body: JSON.stringify(propertyData),
    });
  }

  async deleteProperty(propertyId: string): Promise<any> {
    return this.request(`/api/v1/properties/${propertyId}`, {
      method: 'DELETE',
    });
  }

  // AI Content Generation
  async getAIPropertySuggestions(propertyId: string, data: any): Promise<any> {
    return this.request(`/api/v1/properties/${propertyId}/ai-suggestions`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Legacy AI Content Generation (for backward compatibility)
  async generateLegacyAIContent(data: any): Promise<any> {
    return this.request('/api/v1/ai-content/generate-content', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async regenerateLegacyAIContent(propertyId: string, data: any): Promise<any> {
    return this.request(`/api/v1/ai-content/regenerate/${propertyId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Social Publishing
  async publishToSocialMedia(data: any): Promise<any> {
    return this.request('/api/v1/social-publishing/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async publishContent(publishData: any): Promise<any> {
    console.log('[CentralizedAPIClient] Publishing with data:', JSON.stringify(publishData, null, 2))
    return this.request('/api/v1/publishing/publish', {
      method: 'POST',
      body: JSON.stringify(publishData),
    });
  }

  async getPublishingStatus(propertyId: string): Promise<any> {
    return this.request(`/api/v1/properties/${propertyId}/publishing-status`);
  }

  // Agent Profile
  async getAgentProfile(): Promise<any> {
    return this.request('/api/v1/agent/profile');
  }

  async getAgentPublicProfile(): Promise<any> {
    return this.request('/api/v1/agent/public/profile');
  }

  async updateAgentPublicProfile(data: any): Promise<any> {
    return this.request('/api/v1/agent/public/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Content Management
  async getContentItems(): Promise<any[]> {
    return this.request('/api/v1/content/');
  }

  async getContent(query?: string): Promise<any> {
    return this.request(`/api/v1/content/${query || ''}`);
  }

  async getPublishingLogs(query?: string): Promise<any> {
    return this.request(`/api/v1/publishing-logs/${query || ''}`);
  }

  async createPost(postData: any): Promise<any> {
    console.log('[CentralizedAPIClient] Creating post with data:', JSON.stringify(postData, null, 2))
    console.log('[CentralizedAPIClient] Data type:', typeof postData)
    console.log('[CentralizedAPIClient] Data keys:', Object.keys(postData))
    console.log('[CentralizedAPIClient] Channels field:', postData.channels, 'Type:', typeof postData.channels)

    return this.request('/api/v1/enhanced-posts/posts/', {
      method: 'POST',
      body: JSON.stringify(postData),
    });
  }

  // Onboarding
  async updateOnboarding(userId: string, data: any): Promise<any> {
    return this.request(`/api/v1/onboarding/${userId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async completeOnboarding(userId: string): Promise<any> {
    return this.request(`/api/v1/onboarding/${userId}/complete`, {
      method: 'POST',
    });
  }

  // Dashboard
  async getDashboardStats(): Promise<any> {
    return this.request('/api/v1/dashboard/stats');
  }

  async getAnalytics(): Promise<any> {
    return this.request('/api/analytics/dashboard');
  }

  // Branding
  async getBrandingSuggestions(data: any): Promise<any> {
    return this.request('/api/v1/branding/suggestions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

// Export singleton instance
export const apiService = new CentralizedAPIClient();