'use client';

import { APIService } from './api';

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

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface AuthResult {
  success: boolean;
  user?: User;
  error?: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phone?: string;
}

class AuthManager {
  private state: AuthState = {
    isAuthenticated: false,
    user: null,
    token: null,
    refreshToken: null,
    isLoading: false,
    error: null
  };

  private listeners: Array<(state: AuthState) => void> = [];
  private apiService: APIService;
  private refreshTimer: NodeJS.Timeout | null = null;
  private isRefreshing = false;
  private refreshPromise: Promise<boolean> | null = null;

  constructor() {
    this.apiService = new APIService();
    if (typeof window !== 'undefined') {
      this.init();
    }
  }

  /**
   * Initialize auth manager - load tokens from storage and validate
   */
  async init(): Promise<void> {
    try {
      this.setState({ isLoading: true, error: null });
      
      const token = this.getStoredToken();
      const refreshToken = this.getStoredRefreshToken();
      
      if (!token) {
        this.setState({ isLoading: false });
        return;
      }

      // Check if token is expired
      if (this.isTokenExpired(token)) {
        if (refreshToken && !this.isTokenExpired(refreshToken)) {
          const refreshed = await this.refreshAccessToken();
          if (!refreshed) {
            this.clearAuth();
            this.setState({ isLoading: false });
            return;
          }
        } else {
          this.clearAuth();
          this.setState({ isLoading: false });
          return;
        }
      }

      // Validate token by fetching user info
      const user = await this.getCurrentUser();
      if (user) {
        this.setState({
          isAuthenticated: true,
          user,
          token: this.getStoredToken(),
          refreshToken: this.getStoredRefreshToken(),
          isLoading: false,
          error: null
        });
        this.scheduleTokenRefresh();
      } else {
        this.clearAuth();
        this.setState({ isLoading: false });
      }
    } catch (error) {
      console.error('[AuthManager] Init error:', error);
      this.clearAuth();
      this.setState({ isLoading: false, error: 'Authentication initialization failed' });
    }
  }

  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<AuthResult> {
    try {
      this.setState({ isLoading: true, error: null });
      
      const response = await this.apiService.login({ email, password });
      
      if (response.access_token && response.user) {
        // Store tokens
        this.setStoredToken(response.access_token);
        if (response.refresh_token) {
          this.setStoredRefreshToken(response.refresh_token);
        }
        
        // Update state
        this.setState({
          isAuthenticated: true,
          user: response.user,
          token: response.access_token,
          refreshToken: response.refresh_token || null,
          isLoading: false,
          error: null
        });
        
        this.scheduleTokenRefresh();
        
        return { success: true, user: response.user };
      } else {
        const error = 'Invalid response from server';
        this.setState({ isLoading: false, error });
        return { success: false, error };
      }
    } catch (error: any) {
      console.error('[AuthManager] Login error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      this.setState({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Register new user
   */
  async register(userData: RegisterData): Promise<AuthResult> {
    try {
      this.setState({ isLoading: true, error: null });
      
      const response = await this.apiService.register(userData);
      
      if (response.user) {
        this.setState({ isLoading: false, error: null });
        return { success: true, user: response.user };
      } else {
        const error = 'Registration failed';
        this.setState({ isLoading: false, error });
        return { success: false, error };
      }
    } catch (error: any) {
      console.error('[AuthManager] Registration error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed';
      this.setState({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint if token exists
      if (this.state.token) {
        await this.apiService.logout();
      }
    } catch (error) {
      console.error('[AuthManager] Logout error:', error);
    } finally {
      this.clearAuth();
      this.setState({
        isAuthenticated: false,
        user: null,
        token: null,
        refreshToken: null,
        isLoading: false,
        error: null
      });
    }
  }

  /**
   * Get current user from API
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const token = this.getStoredToken();
      if (!token) return null;
      
      const user = await this.apiService.getCurrentUser();
      return user;
    } catch (error) {
      console.error('[AuthManager] Get current user error:', error);
      return null;
    }
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(): Promise<boolean> {
    if (this.isRefreshing) {
      return this.refreshPromise || Promise.resolve(false);
    }

    this.isRefreshing = true;
    this.refreshPromise = this.performTokenRefresh();
    
    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<boolean> {
    try {
      const refreshToken = this.getStoredRefreshToken();
      if (!refreshToken || this.isTokenExpired(refreshToken)) {
        return false;
      }

      const response = await this.apiService.refreshToken(refreshToken);
      
      if (response.access_token) {
        this.setStoredToken(response.access_token);
        if (response.refresh_token) {
          this.setStoredRefreshToken(response.refresh_token);
        }
        
        this.setState({
          token: response.access_token,
          refreshToken: response.refresh_token || this.state.refreshToken
        });
        
        this.scheduleTokenRefresh();
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('[AuthManager] Token refresh error:', error);
      return false;
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const token = this.getStoredToken();
    if (!token) return false;
    
    if (this.isTokenExpired(token)) {
      const refreshed = await this.refreshAccessToken();
      return refreshed;
    }
    
    return true;
  }

  /**
   * Get current auth state
   */
  getState(): AuthState {
    return { ...this.state };
  }

  /**
   * Subscribe to auth state changes
   */
  subscribe(listener: (state: AuthState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Get current access token
   */
  getToken(): string | null {
    return this.getStoredToken();
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<AuthResult> {
    try {
      this.setState({ isLoading: true, error: null });
      
      const updatedUser = await this.apiService.updateProfile(userData);
      
      if (updatedUser) {
        this.setState({
          user: updatedUser,
          isLoading: false,
          error: null
        });
        return { success: true, user: updatedUser };
      } else {
        const error = 'Profile update failed';
        this.setState({ isLoading: false, error });
        return { success: false, error };
      }
    } catch (error: any) {
      console.error('[AuthManager] Profile update error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Profile update failed';
      this.setState({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<AuthResult> {
    try {
      this.setState({ isLoading: true, error: null });
      
      await this.apiService.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });
      
      this.setState({ isLoading: false, error: null });
      return { success: true };
    } catch (error: any) {
      console.error('[AuthManager] Password change error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Password change failed';
      this.setState({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Update onboarding progress for the current user
   */
  async updateOnboarding(step: number, data: any): Promise<{ success: boolean }>{
    try {
      this.setState({ isLoading: true, error: null });

      const user = this.state.user;
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Save step progress or complete onboarding
      if (step >= 6) {
        await this.apiService.post(`/api/v1/onboarding/${user.id}/complete`, undefined, true);
        // Optimistically update local state
        this.setState({
          user: { ...(this.state.user as User), onboardingCompleted: true },
          isLoading: false,
          error: null
        });
        return { success: true };
      } else {
        await this.apiService.post(
          `/api/v1/onboarding/${user.id}`,
          { step_number: step, data },
          true
        );
        this.setState({ isLoading: false, error: null });
        return { success: true };
      }
    } catch (error: any) {
      console.error('[AuthManager] Update onboarding error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update onboarding';
      this.setState({ isLoading: false, error: errorMessage });
      return { success: false };
    }
  }

  // Private methods
  private setState(updates: Partial<AuthState>): void {
    this.state = { ...this.state, ...updates };
    this.listeners.forEach(listener => listener(this.state));
  }

  private getStoredToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
  }

  private setStoredToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('auth_token', token);
  }

  private getStoredRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  private setStoredRefreshToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('refresh_token', token);
  }

  private clearAuth(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp < currentTime;
    } catch (error) {
      console.error('[AuthManager] Token parsing error:', error);
      return true;
    }
  }

  private scheduleTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    const token = this.getStoredToken();
    if (!token) return;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      const timeUntilExpiry = payload.exp - currentTime;
      
      // Refresh 5 minutes before expiry
      const refreshTime = Math.max(0, (timeUntilExpiry - 300) * 1000);
      
      this.refreshTimer = setTimeout(() => {
        this.refreshAccessToken();
      }, refreshTime);
    } catch (error) {
      console.error('[AuthManager] Token scheduling error:', error);
    }
  }
}

// Export singleton instance
export const authManager = new AuthManager();

// React hook for using auth state
export function useAuth() {
  const [state, setState] = React.useState<AuthState>(authManager.getState());

  React.useEffect(() => {
    const unsubscribe = authManager.subscribe(setState);
    return unsubscribe;
  }, []);

  return {
    ...state,
    login: authManager.login.bind(authManager),
    register: authManager.register.bind(authManager),
    logout: authManager.logout.bind(authManager),
    updateProfile: authManager.updateProfile.bind(authManager),
    changePassword: authManager.changePassword.bind(authManager),
    updateOnboarding: authManager.updateOnboarding.bind(authManager),
    refreshToken: authManager.refreshAccessToken.bind(authManager)
  };
}

// Add React import for the hook
if (typeof window !== 'undefined') {
  // @ts-ignore
  const React = require('react');
}
