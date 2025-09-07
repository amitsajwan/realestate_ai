'use client';

// Enhanced API service with comprehensive error handling and logging
import { errorHandler, AppError } from './error-handler';
import { logger, logApiCall } from './logger';
import {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  RefreshTokenResponse,
  BrandingSuggestionRequest,
  BrandingSuggestion,
  BrandingSuggestionResponse,
  OnboardingUpdateRequest,
  OnboardingFormData,
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
    const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    
    // If environment variable is explicitly defined (including empty string), use it
    if (envUrl !== undefined) {
      return envUrl;
    }
    
    // Default behavior when no environment variable is set: detect environment
    // In development (localhost), use direct backend connection
    // In production/container, use relative paths through nginx proxy
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000';
      }
      // In production/container, use relative paths through nginx proxy
      return '';
    }
    
    // Server-side: use relative paths by default (works with nginx proxy)
    return '';
  }

  /**
   * Log API configuration for debugging
   */
  private logConfiguration(): void {
    logger.info('APIService initialized', {
      component: 'APIService',
      action: 'initialization',
      metadata: {
        baseURL: this.baseURL,
        timeout: this.requestTimeout,
        environment: process.env.NODE_ENV
      }
    });
  }

  /**
   * Set authentication token
   */
  setToken(token: string | null): void {
    this.token = token;
    logger.debug('Token updated', {
      component: 'APIService',
      action: 'token_update',
      metadata: { hasToken: !!token }
    });
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    this.token = null;
    logger.debug('Token cleared', {
      component: 'APIService',
      action: 'token_clear'
    });
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
    const method = options.method || 'GET';
    const startTime = Date.now();
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Initialize API call logging
    const apiLog = logApiCall(method, endpoint);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Request-ID': requestId,
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

      // Log request details
      logger.debug('Making API request', {
        component: 'APIService',
        action: 'api_request',
        requestId,
        method,
        endpoint,
        metadata: {
          url,
          requiresAuth,
          retryCount,
          headers: this.sanitizeHeaders(headers),
          bodySize: options.body ? (options.body as string).length : 0
        }
      });

      const response = await fetch(url, requestOptions);
      clearTimeout(timeoutId);

      const responseTime = Date.now() - startTime;
      const responseId = response.headers.get('X-Response-ID') || 'unknown';

      // Log response details
      logger.debug('Received API response', {
        component: 'APIService',
        action: 'api_response',
        requestId,
        method,
        endpoint,
        statusCode: response.status,
        duration: responseTime,
        metadata: {
          url,
          statusText: response.statusText,
          responseId,
          contentType: response.headers.get('content-type')
        }
      });

      let responseData: any;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        responseData = await response.json();
      } else {
        responseData = await response.text();
      }

      if (!response.ok) {
        // Log API call as error
        apiLog.error({
          status: response.status,
          response: responseData,
          message: this.extractErrorMessage(responseData)
        }, {
          requestId,
          statusCode: response.status,
          duration: responseTime,
          metadata: {
            statusText: response.statusText,
            responseData: typeof responseData === 'object' ? responseData : { raw: responseData }
          }
        });

        // Handle 401 Unauthorized - attempt token refresh and retry
        if (response.status === 401 && requiresAuth && retryCount === 0) {
          logger.info('401 Unauthorized detected, attempting token refresh', {
            component: 'APIService',
            action: 'token_refresh_attempt',
            requestId,
            method,
            endpoint
          });
          
          // Import authManager dynamically to avoid circular dependency
          const { authManager } = await import('./auth');
          const refreshSuccess = await authManager.refreshAccessToken();
          
          if (refreshSuccess) {
            logger.info('Token refreshed successfully, retrying request', {
              component: 'APIService',
              action: 'token_refresh_success',
              requestId,
              method,
              endpoint
            });
            // Update token and retry the request
            this.setToken(authManager.getToken());
            return this.makeRequest<T>(endpoint, options, requiresAuth, retryCount + 1);
          } else {
            logger.warn('Token refresh failed, request will fail', {
              component: 'APIService',
              action: 'token_refresh_failed',
              requestId,
              method,
              endpoint
            });
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

      // Log successful API call
      apiLog.success(response.status, {
        requestId,
        duration: responseTime,
        metadata: {
          responseSize: JSON.stringify(responseData).length,
          contentType: response.headers.get('content-type')
        }
      });

      return responseData as T;
    } catch (error: any) {
      const responseTime = Date.now() - startTime;

      if (error.name === 'AbortError') {
        const timeoutError = {
          code: 'TIMEOUT_ERROR',
          message: 'Request timed out'
        };
        
        apiLog.error(timeoutError, {
          requestId,
          duration: responseTime,
          metadata: {
            errorType: 'timeout',
            timeout: this.requestTimeout
          }
        });
        
        logger.error('API request timed out', {
          component: 'APIService',
          action: 'api_timeout',
          requestId,
          method,
          endpoint,
          duration: responseTime,
          metadata: {
            url,
            timeout: this.requestTimeout
          }
        }, error);
        
        throw timeoutError;
      }
      
      // If it's already a structured error, re-throw it
      if (error.response || error.code) {
        apiLog.error(error, {
          requestId,
          duration: responseTime,
          metadata: {
            errorType: 'structured_error',
            hasResponse: !!error.response,
            hasCode: !!error.code
          }
        });
        throw error;
      }

      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = {
          code: 'NETWORK_ERROR',
          message: error.message
        };
        
        apiLog.error(networkError, {
          requestId,
          duration: responseTime,
          metadata: {
            errorType: 'network_error',
            originalMessage: error.message
          }
        });
        
        logger.error('Network error during API request', {
          component: 'APIService',
          action: 'api_network_error',
          requestId,
          method,
          endpoint,
          duration: responseTime,
          metadata: {
            url,
            originalError: error.message
          }
        }, error);
        
        throw networkError;
      }

      // Handle unexpected errors
      const unexpectedError = {
        code: 'UNEXPECTED_ERROR',
        message: 'Unexpected error occurred'
      };
      
      apiLog.error(unexpectedError, {
        requestId,
        duration: responseTime,
        metadata: {
          errorType: 'unexpected_error',
          originalMessage: error.message,
          errorName: error.name
        }
      });
      
      logger.error('Unexpected error during API request', {
        component: 'APIService',
        action: 'api_unexpected_error',
        requestId,
        method,
        endpoint,
        duration: responseTime,
        metadata: {
          url,
          originalError: error.message,
          errorName: error.name,
          stack: error.stack
        }
      }, error);
      
      throw unexpectedError;
    }
  }

  private extractErrorMessage(responseData: any): string {
    // Handle string responses
    if (typeof responseData === 'string') {
      return responseData;
    }
    
    // Handle array responses directly
    if (Array.isArray(responseData)) {
      return responseData.map(item => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') return this.extractErrorMessage(item);
        return String(item);
      }).join(', ');
    }
    
    // Handle object responses
    if (responseData && typeof responseData === 'object') {
      const message = responseData.detail || responseData.message || responseData.error;
      
      // Handle array messages (common in validation errors)
      if (Array.isArray(message)) {
        return message.join(', ');
      }
      
      // Handle object messages (which might be causing the [object Object] issue)
      if (message && typeof message === 'object') {
        return this.extractErrorMessage(message);
      }
      
      return message || 'An error occurred';
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
    
    // Backend returns only tokens for /login; fetch user afterwards
    const tokenResp = await this.makeRequest<any>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    console.log('[APIService] Login tokens received');

    const accessToken = tokenResp.access_token || tokenResp.accessToken;
    const refreshToken = tokenResp.refresh_token || tokenResp.refreshToken;

    if (!accessToken) {
      // Unexpected shape; just pass through whatever came back
      return {
        // @ts-ignore - provide best-effort mapping
        user: tokenResp.user ? UserDataTransformer.fromBackend(tokenResp.user) : undefined,
        // expose both key styles for compatibility
        // @ts-ignore
        access_token: tokenResp.access_token,
        // @ts-ignore
        refresh_token: tokenResp.refresh_token,
        accessToken: tokenResp.accessToken,
        refreshToken: tokenResp.refreshToken
      } as any;
    }

    // Set token so that authenticated requests include Authorization header
    this.setToken(accessToken);

    // Fetch current user info
    const rawUser = await this.makeRequest<any>('/api/v1/auth/me', { method: 'GET' }, true);
    const user = UserDataTransformer.fromBackend(rawUser);
    
    console.log('[APIService] Login successful');
    
    // Return with both snake_case and camelCase token keys for compatibility
    return {
      // @ts-ignore - allow additional fields
      user,
      // @ts-ignore
      access_token: accessToken,
      // @ts-ignore
      refresh_token: refreshToken,
      accessToken,
      refreshToken
    } as any;
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    console.log('[APIService] Attempting registration for:', userData.email);
    
    const response = await this.makeRequest<any>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    
    console.log('[APIService] Registration successful');
    
    // Backend returns the created user object directly (no tokens). Also support legacy { user: {...} }
    const backendUser = response?.user ?? response;
    const user = UserDataTransformer.fromBackend(backendUser);

    const accessToken = response.access_token || response.accessToken;
    const refreshToken = response.refresh_token || response.refreshToken;
    
    // Return with both token key styles (tokens may be undefined, which is fine)
    return {
      // @ts-ignore
      user,
      // @ts-ignore
      access_token: accessToken,
      // @ts-ignore
      refresh_token: refreshToken,
      accessToken,
      refreshToken
    } as any;
  }

  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    return this.makeRequest<RefreshTokenResponse>('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken })
    });
  }

  async getCurrentUser(): Promise<User> {
    const raw = await this.makeRequest<any>('/api/v1/auth/me', { method: 'GET' }, true);
    return UserDataTransformer.fromBackend(raw);
  }

  async updateProfile(userData: Partial<User>): Promise<User> {
    const raw = await this.makeRequest<any>('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify(userData)
    }, true);
    return UserDataTransformer.fromBackend(raw);
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

  async deleteProperty(propertyId: string): Promise<{ message?: string } | any> {
    return this.delete(`/api/v1/properties/${propertyId}`, true);
  }

  async getAIPropertySuggestions(data: any): Promise<any> {
    return this.makeRequest('/api/v1/property/ai_suggest', {
      method: 'POST',
      body: JSON.stringify(data)
    }, true);
  }

  async getAgentProfile(): Promise<any> {
    return this.makeRequest('/api/v1/agent/profile', {
      method: 'GET'
    }, true);
  }

  async getBrandingSuggestions(data: { company_name: string; agent_name?: string; position?: string }): Promise<any> {
    return this.post('/api/v1/agent/branding-suggest', data, false);
  }

  async getMarketInsights(params: { location: string; propertyType: string; price: string | number }): Promise<any> {
    const query = new URLSearchParams({
      location: String(params.location || ''),
      property_type: String(params.propertyType || ''),
      price: String(params.price ?? '')
    }).toString();
    return this.get(`/api/v1/properties/market-insights?${query}`, false);
  }

  async updateOnboarding(userId: string, data: OnboardingUpdateRequest): Promise<ApiResponse<User>> {
    console.log('[APIService] Updating onboarding for user:', userId);
    
    if (!userId || userId === 'undefined') {
      console.error('[APIService] Invalid user ID for onboarding update:', userId);
      throw new Error('Invalid user ID for onboarding update');
    }
    
    // If completing onboarding, use the dedicated complete endpoint
    if (data.completed) {
      console.log('[APIService] Completing onboarding via /complete endpoint');
      const response = await this.makeRequest<any>(`/api/v1/onboarding/${userId}/complete`, {
        method: 'POST'
      }, true);
      
      console.log('[APIService] Onboarding completion successful');
      
      // After completion, get fresh user data to ensure onboarding_completed is updated
      const updatedUser = await this.getCurrentUser();
      
      return {
        success: true,
        data: updatedUser,
        message: response.message || 'Onboarding completed successfully'
      };
    }
    
    // For regular step updates, use the existing endpoint
    const backendData = data.data ? UserDataTransformer.transformOnboardingData(data.data as OnboardingFormData) : {};
    
    console.log('[APIService] Making onboarding request with data:', {
      userId,
      step_number: data.step,
      data: backendData,
      completed: data.completed
    });
    
    const response = await this.makeRequest<any>(`/api/v1/onboarding/${userId}`, {
      method: 'POST',
      body: JSON.stringify({
        step_number: data.step, // Map 'step' to 'step_number' as expected by backend
        data: backendData, // Ensure 'data' field is included as expected by backend
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

  async generatePropertyContent(propertyData: any): Promise<any> {
    const apiLog = logApiCall('POST', '/api/generate-property');
    
    try {
      logger.info('Generating property content', {
        metadata: { propertyData }
      });
      
      const response = await this.makeRequest('/api/generate-property', {
        method: 'POST',
        body: JSON.stringify(propertyData)
      });
      
      apiLog.success(200);
      
      return {
        success: true,
        data: response,
        message: 'Property content generated successfully'
      };
    } catch (error) {
      apiLog.error(error);
      
      logger.error('Failed to generate property content', {
        errorDetails: error,
        metadata: { propertyData }
      });
      throw error;
    }
  }

  async uploadImages(formData: FormData): Promise<{success: boolean, files?: any[], message?: string, error?: string}> {
    const apiLog = logApiCall('POST', '/api/v1/uploads/images');

    try {
      logger.info('Uploading property images', {
        metadata: { fileCount: formData.getAll('files').length }
      });

      // Create request with FormData (no JSON headers)
      const response: any = await this.makeRequest('/api/v1/uploads/images', {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type, let browser set it with boundary
        }
      }, true);

      apiLog.success(200);

      return {
        success: true,
        files: (response as any).files,
        message: (response as any).message
      };
    } catch (error) {
      apiLog.error(error);

      logger.error('Failed to upload images', {
        errorDetails: error
      });
      throw error;
    }
  }

  async uploadDocuments(formData: FormData): Promise<{success: boolean, files?: any[], message?: string, error?: string}> {
    const apiLog = logApiCall('POST', '/api/v1/uploads/documents');

    try {
      logger.info('Uploading documents', {
        metadata: { fileCount: formData.getAll('files').length }
      });

      const response: any = await this.makeRequest('/api/v1/uploads/documents', {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type, let browser set it with boundary
        }
      }, true);

      apiLog.success(200);

      return {
        success: true,
        files: (response as any).files,
        message: (response as any).message
      };
    } catch (error) {
      apiLog.error(error);

      logger.error('Failed to upload documents', {
        errorDetails: error
      });
      throw error;
    }
  }
}

export { APIError };
export const apiService = new APIService();
