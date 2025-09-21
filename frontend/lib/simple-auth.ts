/**
 * Simple Authentication Helper
 * ===========================
 * Lightweight authentication utilities for simple forms
 */

export interface AuthUser {
  email: string;
  first_name?: string;
  last_name?: string;
  id?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  token: string | null;
}

class SimpleAuthManager {
  private static instance: SimpleAuthManager;
  private state: AuthState = {
    isAuthenticated: false,
    user: null,
    token: null,
  };

  private constructor() {
    this.loadAuthState();
  }

  static getInstance(): SimpleAuthManager {
    if (!SimpleAuthManager.instance) {
      SimpleAuthManager.instance = new SimpleAuthManager();
    }
    return SimpleAuthManager.instance;
  }

  /**
   * Load authentication state from localStorage
   */
  private loadAuthState(): void {
    // Only access localStorage in browser environment
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      const stored = localStorage.getItem('simple_auth_state');
      if (stored) {
        this.state = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load auth state:', error);
      this.clearAuthState();
    }
  }

  /**
   * Save authentication state to localStorage
   */
  private saveAuthState(): void {
    // Only access localStorage in browser environment
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      localStorage.setItem('simple_auth_state', JSON.stringify(this.state));
    } catch (error) {
      console.error('Failed to save auth state:', error);
    }
  }

  /**
   * Get current authentication state
   */
  getState(): AuthState {
    return { ...this.state };
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.state.isAuthenticated && !!this.state.token;
  }

  /**
   * Get authentication token
   */
  getToken(): string | null {
    return this.state.token;
  }

  /**
   * Set authentication state
   */
  setAuthState(user: AuthUser, token: string): void {
    this.state = {
      isAuthenticated: true,
      user,
      token,
    };
    this.saveAuthState();
  }

  /**
   * Clear authentication state
   */
  clearAuthState(): void {
    this.state = {
      isAuthenticated: false,
      user: null,
      token: null,
    };
    
    // Only access localStorage in browser environment
    if (typeof window !== 'undefined') {
      localStorage.removeItem('simple_auth_state');
    }
  }

  /**
   * Make authenticated API request
   */
  async makeAuthenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const token = this.getToken();
    
    if (!token) {
      throw new Error('No authentication token available');
    }

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    return fetch(url, {
      ...options,
      headers,
    });
  }

  /**
   * Get current user data
   */
  async getCurrentUser(): Promise<AuthUser | null> {
    if (!this.isAuthenticated()) {
      return null;
    }

    try {
      const response = await this.makeAuthenticatedRequest('http://localhost:8000/api/v1/auth/me');
      
      if (response.ok) {
        const userData = await response.json();
        return userData;
      } else {
        // Token might be invalid, clear auth state
        this.clearAuthState();
        return null;
      }
    } catch (error) {
      console.error('Failed to get current user:', error);
      return null;
    }
  }
}

// Export singleton instance
export const simpleAuth = SimpleAuthManager.getInstance();

// Export helper functions
export const isAuthenticated = () => simpleAuth.isAuthenticated();
export const getAuthToken = () => simpleAuth.getToken();
export const getCurrentUser = () => simpleAuth.getCurrentUser();
export const clearAuth = () => simpleAuth.clearAuthState();