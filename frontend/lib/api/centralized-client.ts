/**
 * Centralized API Client
 * ======================
 * Single source of truth for all API calls with automatic token handling
 */

import { fetchWithAuthInterceptor } from '../auth/interceptor';
import { authManager } from '../auth/manager';
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
  private async request<T>(
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
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
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
  async generateAIContent(data: any): Promise<any> {
    return this.request('/api/v1/ai-unified/generate-unified', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAIPropertySuggestions(propertyId: string, data: any): Promise<any> {
    return this.request(`/api/v1/properties/${propertyId}/ai-suggestions`, {
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

  async getPublishingLogs(): Promise<any[]> {
    return this.request('/api/v1/publishing-logs/');
  }

  // File Upload
  async uploadImages(formData: FormData): Promise<any> {
    const url = `${this.baseUrl}/api/v1/uploads/images`;
    
    // For file uploads, we need to handle FormData differently
    const config: RequestInit = {
      method: 'POST',
      body: formData,
      // Don't set Content-Type for FormData - let browser set it with boundary
    };

    const response = await fetchWithAuthInterceptor(url, config);
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }
    
    return response.json();
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

// Export the class for testing
export { CentralizedAPIClient };