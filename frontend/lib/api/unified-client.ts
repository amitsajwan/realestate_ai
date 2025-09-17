/**
 * Unified API Client
 * ==================
 * Centralized API client that handles all frontend-backend communication
 * with consistent error handling, authentication, and type safety.
 */

import { User, AuthResponse, LoginData, RegisterData } from '../auth/types';
import { Post, PostCreateRequest, PostUpdateRequest, PostFilters, PostAnalyticsResponse } from '../types/post';
import { PropertyCreate, PropertyUpdate, PropertyResponse } from '../types/property';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Response wrapper
interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Error class for API errors
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

class UnifiedAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    return {
      'Content-Type': 'application/json',
      'Origin': 'http://localhost:3000',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorData: any = {};
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: `HTTP ${response.status}: ${response.statusText}` };
      }
      
      throw new APIError(
        errorData.detail || errorData.message || `HTTP ${response.status}`,
        response.status,
        errorData
      );
    }

    // Handle 204 No Content responses
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      return await this.handleResponse<T>(response);
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(
        error instanceof Error ? error.message : 'Network error',
        0
      );
    }
  }

  // Authentication methods
  async login(credentials: LoginData): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    return this.request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
  }

  async register(userData: RegisterData): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/api/v1/auth/me');
  }

  async updateUser(userData: Partial<User>): Promise<User> {
    return this.request<User>('/api/v1/auth/me', {
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
  async getProperties(skip: number = 0, limit: number = 100): Promise<PropertyResponse[]> {
    return this.request<PropertyResponse[]>(`/api/v1/properties/?skip=${skip}&limit=${limit}`);
  }

  async getProperty(propertyId: string): Promise<PropertyResponse> {
    return this.request<PropertyResponse>(`/api/v1/properties/${propertyId}`);
  }

  async createProperty(propertyData: PropertyCreate): Promise<PropertyResponse> {
    return this.request<PropertyResponse>('/api/v1/properties/', {
      method: 'POST',
      body: JSON.stringify(propertyData),
    });
  }

  async updateProperty(propertyId: string, propertyData: PropertyUpdate): Promise<PropertyResponse> {
    return this.request<PropertyResponse>(`/api/v1/properties/${propertyId}`, {
      method: 'PUT',
      body: JSON.stringify(propertyData),
    });
  }

  async deleteProperty(propertyId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/v1/properties/${propertyId}`, {
      method: 'DELETE',
    });
  }

  async getAIPropertySuggestions(propertyId: string, data: any): Promise<any> {
    return this.request<any>(`/api/v1/properties/${propertyId}/ai-suggestions`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMarketInsights(propertyId: string): Promise<any> {
    return this.request<any>(`/api/v1/properties/${propertyId}/market-insights`, {
      method: 'POST',
    });
  }

  async getPropertyAnalytics(propertyId: string): Promise<any> {
    return this.request<any>(`/api/v1/properties/${propertyId}/analytics`);
  }

  async searchProperties(query: string, filters?: any): Promise<PropertyResponse[]> {
    const searchParams = new URLSearchParams({ q: query });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) searchParams.append(key, String(value));
      });
    }
    return this.request<PropertyResponse[]>(`/api/v1/properties/search?${searchParams}`);
  }

  // Post methods (using enhanced posts endpoint)
  async getPosts(filters: PostFilters = {}): Promise<Post[]> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          params.append(key, value.join(','));
        } else {
          params.append(key, String(value));
        }
      }
    });
    return this.request<Post[]>(`/api/v1/enhanced-posts/posts/?${params.toString()}`);
  }

  async getPost(postId: string): Promise<Post> {
    return this.request<Post>(`/api/v1/enhanced-posts/posts/${postId}`);
  }

  async createPost(postData: PostCreateRequest): Promise<Post> {
    return this.request<Post>('/api/v1/enhanced-posts/posts/', {
      method: 'POST',
      body: JSON.stringify(postData),
    });
  }

  async updatePost(postId: string, postData: PostUpdateRequest): Promise<Post> {
    return this.request<Post>(`/api/v1/enhanced-posts/posts/${postId}`, {
      method: 'PUT',
      body: JSON.stringify(postData),
    });
  }

  async deletePost(postId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/v1/enhanced-posts/posts/${postId}`, {
      method: 'DELETE',
    });
  }

  async publishPost(postId: string, channels: string[] = []): Promise<any> {
    return this.request<any>(`/api/v1/enhanced-posts/posts/${postId}/publish`, {
      method: 'POST',
      body: JSON.stringify({ channels }),
    });
  }

  async schedulePost(postId: string, scheduledAt: string): Promise<Post> {
    return this.request<Post>(`/api/v1/enhanced-posts/posts/${postId}/schedule`, {
      method: 'POST',
      body: JSON.stringify({ scheduled_at: scheduledAt }),
    });
  }

  async getPostAnalytics(postId: string): Promise<PostAnalyticsResponse> {
    return this.request<PostAnalyticsResponse>(`/api/v1/enhanced-posts/posts/${postId}/analytics`);
  }

  async getAIPostSuggestions(postId: string): Promise<any> {
    return this.request<any>(`/api/v1/posts/${postId}/ai-suggestions`);
  }

  async enhancePost(postId: string, enhancementData: any): Promise<Post> {
    return this.request<Post>(`/api/v1/posts/${postId}/enhance`, {
      method: 'POST',
      body: JSON.stringify(enhancementData),
    });
  }

  // Template methods
  async getTemplates(filters: any = {}): Promise<any[]> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
    return this.request<any[]>(`/api/v1/enhanced-posts/posts/templates/?${params.toString()}`);
  }

  async createTemplate(templateData: any): Promise<any> {
    return this.request<any>('/api/v1/enhanced-posts/posts/templates/', {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  // Dashboard methods
  async getDashboardStats(): Promise<any> {
    return this.request<any>('/api/v1/dashboard/stats');
  }

  // Upload methods
  async uploadImages(formData: FormData): Promise<any> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    return this.request<any>('/api/v1/uploads/images', {
      method: 'POST',
      headers: {
        'Origin': 'http://localhost:3000',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: formData,
    });
  }

  // Onboarding methods
  async updateOnboarding(userId: string, data: any): Promise<any> {
    return this.request<any>(`/api/v1/onboarding/${userId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async completeOnboarding(userId: string): Promise<any> {
    return this.request<any>(`/api/v1/onboarding/${userId}/complete`, {
      method: 'POST',
    });
  }

  // Facebook methods
  async getFacebookStatus(): Promise<any> {
    return this.request<any>('/api/v1/facebook/status');
  }

  async getFacebookLoginUrl(): Promise<any> {
    return this.request<any>('/api/v1/facebook/login');
  }

  // Branding methods
  async getBrandingSuggestions(data: any): Promise<any> {
    return this.request<any>('/api/v1/branding/suggestions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

// Export singleton instance
export const apiClient = new UnifiedAPIClient();

// Export types
export type { APIResponse, APIError };