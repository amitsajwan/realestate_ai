'use client';

// Enhanced API service with comprehensive error handling and logging
import { errorHandler, AppError } from './error-handler';
import {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  RefreshTokenResponse,
  BrandingSuggestionRequest,
  BrandingSuggestion,
  BrandingSuggestionResponse,
  OnboardingUpdateRequest,
  User,
  UserDataTransformer,
  ApiResponse
} from '../types/user';

// Legacy type aliases for backward compatibility
type LoginResponse = AuthResponse;
type RegisterResponse = AuthResponse;

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

// Re-exports removed to fix build issues - import directly from types/user

class APIError extends Error {
  public status: number;
  public response?: any;
  public errorType?: string;

  constructor(message: string, status: number, response?: any, errorType?: string) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.response = response;
    this.errorType = errorType;
  }
}

export class APIService {
  private baseURL: string;
  private token: string | null = null;
  private requestTimeout: number = 30000; // 30 seconds

  constructor() {
    // Use environment variables with fallbacks
    this.baseURL = this.getAPIBaseURL();
    this.logConfiguration();
  }

  /**
   * Get API base URL from environment variables
   */
  private getAPIBaseURL(): string {
    if (typeof window !== 'undefined') {
      return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    } else {
      return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    }
  }

  /**
   * Log API configuration for debugging
   */
  private logConfiguration(): void {
    if (process.env.NODE_ENV === 'development') {
      console.log('[APIService] Configuration:', {
        baseURL: this.baseURL,
        timeout: this.requestTimeout,
        environment: process.env.NODE_ENV
      });
    }
  }

  /**
   * Set authentication token
   */
  setToken(token: string | null): void {
    this.token = token;
    if (process.env.NODE_ENV === 'development') {
      console.log('[APIService] Token updated:', !!token);
    }
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    this.token = null;
    if (process.env.NODE_ENV === 'development') {
      console.log('[APIService] Token cleared');
    }
  }

  /**
   * Get current token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * Make HTTP request with comprehensive error handling
   */
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}, requiresAuth: boolean = false, retryCount: number = 0): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const startTime = Date.now();

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(options.headers as Record<string, string> || {})
      };

      if (requiresAuth && this.token) {
        headers['Authorization'] = `Bearer ${this.token}`;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);

      const requestOptions: RequestInit = {
        ...options,
        headers,
        signal: controller.signal
      };

      if (process.env.NODE_ENV === 'development') {
        console.log('[APIService] Request:', {
          method: options.method || 'GET',
          url,
          headers: this.sanitizeHeaders(headers),
          body: options.body ? JSON.parse(options.body as string) : undefined
        });
      }

      const response = await fetch(url, requestOptions);
      clearTimeout(timeoutId);

      const responseTime = Date.now() - startTime;

      if (process.env.NODE_ENV === 'development') {
        console.log('[APIService] Response:', {
          status: response.status,
          statusText: response.statusText,
          responseTime: `${responseTime}ms`,
          url
        });
      }

      let responseData: any;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        responseData = await response.json();
      } else {
        responseData = await response.text();
      }

      if (!response.ok) {
        if (process.env.NODE_ENV === 'development') {
          console.error('[APIService] Error Response:', {
            status: response.status,
            statusText: response.statusText,
            data: responseData,
            url
          });
        }

        // Handle 401 Unauthorized - attempt token refresh and retry
        if (response.status === 401 && requiresAuth && retryCount === 0) {
          console.log('[APIService] 401 detected, attempting token refresh...');
          
          // Import authManager dynamically to avoid circular dependency
          const { authManager } = await import('./auth');
          const refreshSuccess = await authManager.refreshAccessToken();
          
          if (refreshSuccess) {
            console.log('[APIService] Token refreshed, retrying request...');
            // Update token and retry the request
            this.setToken(authManager.getToken());
            return this.makeRequest<T>(endpoint, options, requiresAuth, retryCount + 1);
          } else {
            console.log('[APIService] Token refresh failed, request will fail');
          }
        }

        // Create error object for centralized error handler
        const apiError = {
          response: {
            status: response.status,
            data: responseData
          },
          message: this.extractErrorMessage(responseData)
        };
        
        throw apiError;
      }

      return responseData as T;
    } catch (error: any) {
      const responseTime = Date.now() - startTime;

      if (error.name === 'AbortError') {
        console.error('[APIService] Timeout Error:', {
          message: 'Request timed out.',
          url,
          responseTime: `${responseTime}ms`
        });
        const timeoutError = {
          code: 'TIMEOUT_ERROR',
          message: 'Request timed out'
        };
        throw timeoutError;
      }
      
      // If it's already a structured error, re-throw it
      if (error.response || error.code) {
        throw error;
      }

      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('[APIService] Network Error:', {
          message: error.message,
          url,
          responseTime: `${responseTime}ms`
        });
        const networkError = {
          code: 'NETWORK_ERROR',
          message: 'Network connection error'
        };
        throw networkError;
      }

      console.error('[APIService] Unexpected Error:', {
        message: error.message,
        url,
        responseTime: `${responseTime}ms`
      });
      const unexpectedError = {
        code: 'UNEXPECTED_ERROR',
        message: 'Unexpected error occurred'
      };
      throw unexpectedError;
    }
  }

  private extractErrorMessage(responseData: any): string {
    if (typeof responseData === 'string') {
      return responseData;
    }
    if (responseData && typeof responseData === 'object') {
      return responseData.detail || responseData.message || responseData.error || 'An error occurred';
    }
    return 'An error occurred';
  }

  private getErrorType(status: number): string {
    switch (status) {
      case 400: return 'BAD_REQUEST';
      case 401: return 'UNAUTHORIZED';
      case 403: return 'FORBIDDEN';
      case 404: return 'NOT_FOUND';
      case 409: return 'CONFLICT';
      case 422: return 'VALIDATION_ERROR';
      case 429: return 'RATE_LIMIT';
      case 500: return 'INTERNAL_SERVER_ERROR';
      case 502: return 'BAD_GATEWAY';
      case 503: return 'SERVICE_UNAVAILABLE';
      case 504: return 'GATEWAY_TIMEOUT';
      default: return 'UNKNOWN_ERROR';
    }
  }

  private sanitizeHeaders(headers: HeadersInit): Record<string, string> {
    const sanitized: Record<string, string> = {};
    if (headers instanceof Headers) {
      headers.forEach((value, key) => {
        sanitized[key] = key.toLowerCase() === 'authorization' ? '[REDACTED]' : value;
      });
    } else if (Array.isArray(headers)) {
      headers.forEach(([key, value]) => {
        sanitized[key] = key.toLowerCase() === 'authorization' ? '[REDACTED]' : value;
      });
    } else {
      Object.entries(headers).forEach(([key, value]) => {
        sanitized[key] = key.toLowerCase() === 'authorization' ? '[REDACTED]' : value;
      });
    }
    return sanitized;
  }

  async testConnection(): Promise<{ success: boolean; message: string; responseTime: number }> {
    const startTime = Date.now();
    try {
      await this.makeRequest('/health', { method: 'GET' });
      const responseTime = Date.now() - startTime;
      return { success: true, message: 'API connection successful', responseTime };
    } catch (error) {
      const responseTime = Date.now() - startTime;
      return {
        success: false,
        message: error instanceof APIError ? error.message : 'Connection failed',
        responseTime
      };
    }
  }

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    console.log('[APIService] Attempting login for:', credentials.email);
    
    const response = await this.makeRequest<any>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    console.log('[APIService] Login successful');
    
    // Transform backend response to frontend format
    return {
      user: UserDataTransformer.fromBackend(response.user),
      accessToken: response.access_token || response.accessToken,
      refreshToken: response.refresh_token || response.refreshToken
    };
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    console.log('[APIService] Attempting registration for:', userData.email);
    
    const response = await this.makeRequest<any>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    
    console.log('[APIService] Registration successful');
    
    // Transform backend response to frontend format
    return {
      user: UserDataTransformer.fromBackend(response.user),
      accessToken: response.access_token || response.accessToken,
      refreshToken: response.refresh_token || response.refreshToken
    };
  }

  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    return this.makeRequest<RefreshTokenResponse>('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken })
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.makeRequest<User>('/api/v1/auth/me', { method: 'GET' }, true);
  }

  async updateProfile(userData: Partial<User>): Promise<User> {
    return this.makeRequest<User>('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify(userData)
    }, true);
  }

  async changePassword(passwordData: PasswordChangeRequest): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData)
    }, true);
  }

  async logout(): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/auth/logout', { method: 'POST' }, true);
  }

  async requestPasswordReset(email: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/auth/password-reset-request', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  }

  async confirmPasswordReset(token: string, newPassword: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/auth/password-reset-confirm', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword })
    });
  }

  async getDashboardStats(): Promise<any> {
    return this.makeRequest('/api/v1/dashboard/stats', { method: 'GET' }, true);
  }

  async searchUsers(query: string, page: number = 1, limit: number = 10): Promise<any> {
    const params = new URLSearchParams({ q: query, page: page.toString(), limit: limit.toString() });
    return this.makeRequest(`/api/v1/auth/search?${params}`, { method: 'GET' }, true);
  }

  async get<T>(endpoint: string, requiresAuth: boolean = false): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'GET' }, requiresAuth);
  }

  async post<T>(endpoint: string, data?: any, requiresAuth: boolean = false): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'POST', body: data ? JSON.stringify(data) : undefined }, requiresAuth);
  }

  async put<T>(endpoint: string, data?: any, requiresAuth: boolean = false): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'PUT', body: data ? JSON.stringify(data) : undefined }, requiresAuth);
  }

  async delete<T>(endpoint: string, requiresAuth: boolean = false): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE' }, requiresAuth);
  }

  async uploadFile(endpoint: string, file: File, additionalData?: Record<string, string>): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {};
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

    const response = await fetch(url, { method: 'POST', headers, body: formData });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new APIError(this.extractErrorMessage(errorData), response.status, errorData, this.getErrorType(response.status));
    }

    return response.json();
  }

  setTimeout(timeout: number): void {
    this.requestTimeout = timeout;
    if (process.env.NODE_ENV === 'development') {
      console.log('[APIService] Timeout updated:', timeout);
    }
  }

  getConfig(): { baseURL: string; timeout: number; hasToken: boolean } {
    return { baseURL: this.baseURL, timeout: this.requestTimeout, hasToken: !!this.token };
  }

  /**
   * Get default user profile
   */
  async getDefaultUserProfile(): Promise<User> {
    return await this.makeRequest<User>("/api/v1/auth/default-profile", { method: "GET" });
  }

  async createProperty(propertyData: any): Promise<any> {
    return this.makeRequest('/api/v1/properties/', {
      method: 'POST',
      body: JSON.stringify(propertyData)
    }, true);
  }

  async getAIPropertySuggestions(data: any): Promise<any> {
    return this.makeRequest('/api/v1/property/ai_suggest', {
      method: 'POST',
      body: JSON.stringify(data)
    }, true);
  }

  async getBrandingSuggestions(data: { company_name: string; agent_name?: string; position?: string }): Promise<any> {
    return this.post('/api/v1/agent/branding-suggest', data, false);
  }

  async updateOnboarding(userId: string, data: OnboardingUpdateRequest): Promise<ApiResponse<User>> {
    console.log('[APIService] Updating onboarding for user:', userId);
    
    // Transform frontend data to backend format
    const backendData = data.data ? UserDataTransformer.transformOnboardingData(data.data) : data;
    
    const response = await this.makeRequest<any>(`/api/v1/onboarding/${userId}`, {
      method: 'POST',
      body: JSON.stringify({
        ...backendData,
        step: data.step,
        completed: data.completed
      })
    }, true);
    
    console.log('[APIService] Onboarding update successful');
    
    // Transform response if it contains user data
    if (response.user) {
      return {
        success: true,
        data: UserDataTransformer.fromBackend(response.user),
        message: response.message
      };
    }
    
    return {
      success: true,
      data: response.data,
      message: response.message
    };
  }
}

export { APIError };
export const apiService = new APIService();
