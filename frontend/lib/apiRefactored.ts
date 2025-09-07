/**
 * Refactored API Service
 * ======================
 * 
 * Enhanced API service with:
 * - Retry logic with exponential backoff
 * - Better error handling
 * - Request/response interceptors
 * - Offline support
 * - Request deduplication
 */

'use client';

import { errorHandler, AppError } from './error-handler';
import { logger } from './logger';

// Types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  status?: number;
}

export interface RequestConfig {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  retryCondition?: (error: any) => boolean;
  headers?: Record<string, string>;
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
}

class APIError extends Error {
  public status: number;
  public response?: any;
  public errorType?: string;
  public isRetryable: boolean;

  constructor(message: string, status: number, response?: any, errorType?: string, isRetryable: boolean = false) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.response = response;
    this.errorType = errorType;
    this.isRetryable = isRetryable;
  }
}

export class APIServiceRefactored {
  private baseURL: string;
  private token: string | null = null;
  private defaultTimeout: number = 30000;
  private retryConfig: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    backoffFactor: 2
  };
  private pendingRequests: Map<string, Promise<any>> = new Map();
  private isOnline: boolean = true;

  constructor(baseURL?: string) {
    this.baseURL = baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    this.setupOnlineListener();
  }

  // Online/Offline detection
  private setupOnlineListener(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        this.isOnline = true;
        logger.info('Network connection restored');
      });

      window.addEventListener('offline', () => {
        this.isOnline = false;
        logger.warn('Network connection lost');
      });
    }
  }

  // Request deduplication
  private getRequestKey(method: string, url: string, data?: any): string {
    return `${method}:${url}:${JSON.stringify(data || {})}`;
  }

  // Retry logic with exponential backoff
  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private calculateRetryDelay(attempt: number): number {
    const delay = this.retryConfig.baseDelay * Math.pow(this.retryConfig.backoffFactor, attempt);
    return Math.min(delay, this.retryConfig.maxDelay);
  }

  private isRetryableError(error: any): boolean {
    if (error instanceof APIError) {
      return error.isRetryable;
    }
    
    // Retry on network errors, timeouts, and 5xx server errors
    return (
      !this.isOnline ||
      error.name === 'NetworkError' ||
      error.name === 'TimeoutError' ||
      (error.status >= 500 && error.status < 600) ||
      error.status === 429 // Rate limiting
    );
  }

  // Core request method with retry logic
  private async makeRequest<T>(
    method: string,
    endpoint: string,
    data?: any,
    config: RequestConfig = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const requestKey = this.getRequestKey(method, url, data);
    
    // Check for pending request
    if (this.pendingRequests.has(requestKey)) {
      logger.info(`Deduplicating request: ${method} ${endpoint}`);
      return this.pendingRequests.get(requestKey)!;
    }

    const requestPromise = this.executeRequestWithRetry<T>(method, url, data, config);
    this.pendingRequests.set(requestKey, requestPromise);

    try {
      const result = await requestPromise;
      return result;
    } finally {
      this.pendingRequests.delete(requestKey);
    }
  }

  private async executeRequestWithRetry<T>(
    method: string,
    url: string,
    data?: any,
    config: RequestConfig = {}
  ): Promise<APIResponse<T>> {
    const maxRetries = config.retries ?? this.retryConfig.maxRetries;
    let lastError: any;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (!this.isOnline && attempt === 0) {
          throw new APIError('Network offline', 0, null, 'NetworkError', true);
        }

        const response = await this.executeSingleRequest<T>(method, url, data, config);
        return response;

      } catch (error) {
        lastError = error;
        
        // Don't retry on last attempt or non-retryable errors
        if (attempt === maxRetries || !this.isRetryableError(error)) {
          break;
        }

        const delay = this.calculateRetryDelay(attempt);
        logger.warn(`Request failed (attempt ${attempt + 1}/${maxRetries + 1}), retrying in ${delay}ms:`, error);
        await this.sleep(delay);
      }
    }

    // All retries failed
    throw lastError;
  }

  private async executeSingleRequest<T>(
    method: string,
    url: string,
    data?: any,
    config: RequestConfig = {}
  ): Promise<APIResponse<T>> {
    const timeout = config.timeout ?? this.defaultTimeout;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...config.headers
    };

    // Add authentication token
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const requestOptions: RequestInit = {
      method,
      headers,
      signal: AbortSignal.timeout(timeout)
    };

    // Add body for non-GET requests
    if (data && method !== 'GET') {
      requestOptions.body = JSON.stringify(data);
    }

    logger.info(`Making ${method} request to ${url}`, { data, timeout });

    try {
      const response = await fetch(url, requestOptions);
      const responseData = await response.json();

      if (!response.ok) {
        const isRetryable = response.status >= 500 || response.status === 429;
        throw new APIError(
          responseData.message || `HTTP ${response.status}`,
          response.status,
          responseData,
          'HTTPError',
          isRetryable
        );
      }

      logger.info(`Request successful: ${method} ${url}`, { status: response.status });
      return {
        success: true,
        data: responseData,
        status: response.status
      };

    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      // Handle network errors
      if (error.name === 'AbortError') {
        throw new APIError('Request timeout', 408, null, 'TimeoutError', true);
      }

      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new APIError('Network error', 0, null, 'NetworkError', true);
      }

      throw new APIError(
        error.message || 'Unknown error',
        0,
        null,
        'UnknownError',
        false
      );
    }
  }

  // Authentication methods
  setToken(token: string | null): void {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  // Property-related methods
  async createProperty(propertyData: any, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('POST', '/api/v1/properties', propertyData, config);
  }

  async getProperties(config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('GET', '/api/v1/properties', undefined, config);
  }

  async getProperty(id: string, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('GET', `/api/v1/properties/${id}`, undefined, config);
  }

  async updateProperty(id: string, propertyData: any, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('PUT', `/api/v1/properties/${id}`, propertyData, config);
  }

  async deleteProperty(id: string, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('DELETE', `/api/v1/properties/${id}`, undefined, config);
  }

  // Smart Property methods
  async createSmartProperty(propertyData: any, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('POST', '/api/v1/smart-properties', propertyData, config);
  }

  async getSmartProperties(config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('GET', '/api/v1/smart-properties', undefined, config);
  }

  // AI-related methods
  async getAIPropertySuggestions(context: any, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('POST', '/api/v1/ai/property-suggestions', context, config);
  }

  async getMarketInsights(data: any, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('POST', '/api/v1/ai/market-insights', data, config);
  }

  // Authentication methods
  async login(credentials: any, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('POST', '/api/v1/auth/login', credentials, config);
  }

  async register(userData: any, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('POST', '/api/v1/auth/register', userData, config);
  }

  async getCurrentUser(config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('GET', '/api/v1/auth/me', undefined, config);
  }

  // Facebook integration methods
  async getFacebookConfig(config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('GET', '/api/v1/facebook/config', undefined, config);
  }

  async optimizeCampaign(campaignData: any, config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('POST', '/api/v1/facebook/optimize', campaignData, config);
  }

  // Utility methods
  async healthCheck(config?: RequestConfig): Promise<APIResponse> {
    return this.makeRequest('GET', '/api/v1/health', undefined, config);
  }

  // Batch requests
  async batchRequest(requests: Array<{ method: string; endpoint: string; data?: any }>): Promise<APIResponse[]> {
    const promises = requests.map(req => 
      this.makeRequest(req.method, req.endpoint, req.data)
    );
    
    return Promise.allSettled(promises).then(results =>
      results.map(result => 
        result.status === 'fulfilled' 
          ? result.value 
          : { success: false, error: result.reason?.message || 'Request failed' }
      )
    );
  }

  // Clear pending requests (useful for cleanup)
  clearPendingRequests(): void {
    this.pendingRequests.clear();
  }

  // Update retry configuration
  updateRetryConfig(config: Partial<RetryConfig>): void {
    this.retryConfig = { ...this.retryConfig, ...config };
  }
}

// Export singleton instance
export const apiServiceRefactored = new APIServiceRefactored();

// Export for backward compatibility
export { APIError };