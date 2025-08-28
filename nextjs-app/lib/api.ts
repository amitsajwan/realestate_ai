'use client';

// Enhanced API service with comprehensive error handling and logging

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phone?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in?: number;
  user: {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    phone?: string;
    onboardingCompleted: boolean;
    createdAt: string;
    updatedAt: string;
  };
}

export interface RegisterResponse {
  user: {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    phone?: string;
    onboardingCompleted: boolean;
    createdAt: string;
    updatedAt: string;
  };
  message: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in?: number;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface APIError {
  detail: string;
  status_code: number;
  error_type?: string;
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  onboardingCompleted: boolean;
  createdAt: string;
  updatedAt: string;
}

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
      // Client-side: use Next.js public environment variables
      return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    } else {
      // Server-side: use regular environment variables
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
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    requiresAuth: boolean = false
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const startTime = Date.now();

    try {
      // Prepare headers
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers
      };

      // Add authentication header if required
      if (requiresAuth && this.token) {
        headers['Authorization'] = `Bearer ${this.token}`;
      }

      // Create AbortController for timeout
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

      // Handle different response types
      let responseData: any;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        responseData = await response.json();
      } else {
        responseData = await response.text();
      }

      if (!response.ok) {
        const errorMessage = this.extractErrorMessage(responseData);
        const errorType = this.getErrorType(response.status);
        
        if (process.env.NODE_ENV === 'development') {
          console.error('[APIService] Error Response:', {
            status: response.status,
            statusText: response.statusText,
            data: responseData,
            url
          });
        }

        throw new APIError(
          errorMessage,
          response.status,
          responseData,
          errorType
        );
      }

      return responseData as T;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      
      if (error instanceof APIError) {
        throw error;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('[APIService] Network Error:', {
          message: error.message,
          url,
          responseTime: `${responseTime}ms`
        });
        throw new APIError(
          'Network error. Please check your internet connection.',
          0,
          null,
          'NETWORK_ERROR'
        );
      }

      // Handle timeout errors
      if (error.name === 'AbortError') {
        console.error('[APIService] Timeout Error:', {
          url,
          timeout: this.requestTimeout,
          responseTime: `${responseTime}ms`
        });
        throw new APIError(
          'Request timeout. Please try again.',
          408,
          null,
          'TIMEOUT_ERROR'
        );
      }

      console.error('[APIService] Unexpected Error:', {
        error: error.message,
        url,
        responseTime: `${responseTime}ms`
      });

      throw new APIError(
        'An unexpected error occurred. Please try again.',
        500,
        null,
        'UNKNOWN_ERROR'
      );
    }
  }

  /**
   * Extract error message from response
   */
  private extractErrorMessage(responseData: any): string {
    if (typeof responseData === 'string') {
      return responseData;
    }

    if (responseData && typeof responseData === 'object') {
      return responseData.detail || 
             responseData.message || 
             responseData.error || 
             'An error occurred';
    }

    return 'An error occurred';
  }

  /**
   * Get error type based on status code
   */
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

  /**
   * Sanitize headers for logging (remove sensitive data)
   */
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

  /**
   * Test API connection
   */
  async testConnection(): Promise<{ success: boolean; message: string; responseTime: number }> {
    const startTime = Date.now();
    
    try {
      await this.makeRequest('/health', { method: 'GET' });
      const responseTime = Date.now() - startTime;
      
      return {
        success: true,
        message: 'API connection successful',
        responseTime
      };
    } catch (error) {
      const responseTime = Date.now() - startTime;
      
      return {
        success: false,
        message: error instanceof APIError ? error.message : 'Connection failed',
        responseTime
      };
    }
  }

  /**
   * Login user
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    return this.makeRequest<LoginResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  }

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    return this.makeRequest<RegisterResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    return this.makeRequest<RefreshTokenResponse>('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken })
    });
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    return this.makeRequest<User>('/api/v1/auth/me', {
      method: 'GET'
    }, true);
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<User> {
    return this.makeRequest<User>('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify(userData)
    }, true);
  }

  /**
   * Change user password
   */
  async changePassword(passwordData: PasswordChangeRequest): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData)
    }, true);
  }

  /**
   * Logout user
   */
  async logout(): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/auth/logout', {
      method: 'POST'
    }, true);
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/auth/password-reset-request', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  }

  /**
   * Confirm password reset
   */
  async confirmPasswordReset(token: string, newPassword: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/auth/password-reset-confirm', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword })
    });
  }

  /**
   * Get dashboard statistics
   */
  async getDashboardStats(): Promise<any> {
    return this.makeRequest('/api/v1/dashboard/stats', {
      method: 'GET'
    }, true);
  }

  /**
   * Search users (admin)
   */
  async searchUsers(query: string, page: number = 1, limit: number = 10): Promise<any> {
    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      limit: limit.toString()
    });
    
    return this.makeRequest(`/api/v1/auth/search?${params}`, {
      method: 'GET'
    }, true);
  }

  /**
   * Generic GET request
   */
  async get<T>(endpoint: string, requiresAuth: boolean = false): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'GET' }, requiresAuth);
  }

  /**
   * Generic POST request
   */
  async post<T>(endpoint: string, data?: any, requiresAuth: boolean = false): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    }, requiresAuth);
  }

  /**
   * Generic PUT request
   */
  async put<T>(endpoint: string, data?: any, requiresAuth: boolean = false): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    }, requiresAuth);
  }

  /**
   * Generic DELETE request
   */
  async delete<T>(endpoint: string, requiresAuth: boolean = false): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE' }, requiresAuth);
  }

  /**
   * Upload file
   */
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
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new APIError(
        this.extractErrorMessage(errorData),
        response.status,
        errorData,
        this.getErrorType(response.status)
      );
    }

    return response.json();
  }

  /**
   * Set request timeout
   */
  setTimeout(timeout: number): void {
    this.requestTimeout = timeout;
    if (process.env.NODE_ENV === 'development') {
      console.log('[APIService] Timeout updated:', timeout);
    }
  }

  /**
   * Get current configuration
   */
  getConfig(): { baseURL: string; timeout: number; hasToken: boolean } {
    return {
      baseURL: this.baseURL,
      timeout: this.requestTimeout,
      hasToken: !!this.token
    };
  }
}

// Export error class and singleton instance
export { APIError };
export const apiService = new APIService();
