'use client';

import { useEffect, useState } from 'react';
import { AuthResponse, LoginRequest, RegisterData, RegisterRequest, User, UserDataTransformer } from '../types/user';
import { apiService } from './api';
import { errorHandler, handleError, showSuccess } from './error-handler';
import { logger } from './logger';

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

// RegisterData is now imported from '../types/user'

export class AuthManager {
  private state: AuthState = {
    isAuthenticated: false,
    user: null,
    token: null,
    refreshToken: null,
    isLoading: false,
    error: null
  };

  private listeners: Array<(state: AuthState) => void> = [];
  private apiService: any;
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;
  private isRefreshing = false;
  private refreshPromise: Promise<boolean> | null = null;
  private refreshRetryCount = 0;
  private maxRefreshRetries = 3;
  private refreshRetryDelay = 1000; // 1 second

  constructor() {
    this.apiService = apiService;
    if (typeof window !== 'undefined') {
      this.init();
    }
  }

  /**
   * Get bypass user from localStorage (for development/testing)
   */
  private getBypassUser(): User | null {
    if (typeof window === 'undefined') return null;

    try {
      const storedUser = localStorage.getItem('auth_user');
      const isAuthenticated = localStorage.getItem('auth_authenticated') === 'true';

      if (storedUser && isAuthenticated) {
        return JSON.parse(storedUser);
      }
    } catch (error) {
      console.warn('[AuthManager] Error parsing bypass user:', error);
    }

    return null;
  }

  /**
   * Initialize auth manager - load tokens from storage and validate
   */
  async init(): Promise<void> {
    try {
      this.setState({ isLoading: true, error: null });

      // Check for bypass authentication
      const bypassUser = this.getBypassUser();
      if (bypassUser) {
        this.setState({
          isAuthenticated: true,
          user: bypassUser,
          token: 'mock_token_123',
          refreshToken: null,
          isLoading: false,
          error: null
        });
        return;
      }

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
        // Ensure user ID is properly set
        if (!user.id) {
          logger.error('[AuthManager] User ID is missing in getCurrentUser response', {
            component: 'AuthManager',
            action: 'user_validation'
          });
        }

        this.setState({
          isAuthenticated: true,
          user,
          token: this.getStoredToken(),
          refreshToken: this.getStoredRefreshToken(),
          isLoading: false,
          error: null
        });

        // Set token in API service
        // Token will be set in request headers when needed

        this.scheduleTokenRefresh();
      } else {
        this.clearAuth();
        this.setState({ isLoading: false });
      }
    } catch (error) {
      logger.error('[AuthManager] Init error', {
        component: 'AuthManager',
        action: 'init',
        errorDetails: error
      }, error as Error);
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

      // Validate inputs before sending to API
      if (!email || !email.trim()) {
        throw new Error('Email is required');
      }

      if (!password || !password.trim()) {
        throw new Error('Password is required');
      }

      const credentials: LoginRequest = { email: email.trim(), password };
      logger.info('Attempting login', {
        component: 'AuthManager',
        action: 'login_attempt',
        metadata: { email: email.trim() }
      });

      const response: AuthResponse = await this.apiService.login(credentials);

      if (response.accessToken && response.user) {
        // Store tokens
        this.setStoredToken(response.accessToken);
        if (response.refreshToken) {
          this.setStoredRefreshToken(response.refreshToken);
        }

        // Set token in API service
        // Token will be set in request headers when needed

        // Update state
        this.setState({
          isAuthenticated: true,
          user: response.user,
          token: response.accessToken,
          refreshToken: response.refreshToken || null,
          isLoading: false,
          error: null
        });

        this.scheduleTokenRefresh();
        showSuccess('Successfully logged in!');

        return { success: true, user: response.user };
      } else {
        logger.error('Invalid login response format', {
          component: 'AuthManager',
          action: 'login_response_validation',
          metadata: { response }
        });
        throw new Error('Invalid response format from server');
      }
    } catch (error: any) {
      logger.error('Login error', {
        component: 'AuthManager',
        action: 'login',
        errorDetails: error
      }, error);
      const appError = handleError(error, 'Login');
      this.setState({ isLoading: false, error: appError.message });
      return { success: false, error: appError.message };
    }
  }

  /**
   * Register new user
   */
  async register(userData: RegisterData): Promise<AuthResult> {
    try {
      this.setState({ isLoading: true, error: null });

      const registerRequest: RegisterRequest = UserDataTransformer.transformRegisterData(userData);
      const response: AuthResponse = await this.apiService.register(registerRequest);

      if (response.user) {
        // If tokens are provided during registration, store them and authenticate
        if (response.accessToken) {
          this.setStoredToken(response.accessToken);
          if (response.refreshToken) {
            this.setStoredRefreshToken(response.refreshToken);
          }

          // Set token in API service
          // Token will be set in request headers when needed

          this.setState({
            isAuthenticated: true,
            user: response.user,
            token: response.accessToken,
            refreshToken: response.refreshToken || null,
            isLoading: false,
            error: null
          });

          this.scheduleTokenRefresh();
          showSuccess('Account created and logged in successfully!');
        } else {
          this.setState({ isLoading: false, error: null });
          showSuccess('Account created successfully! Please log in.');
        }

        return { success: true, user: response.user };
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error: any) {
      const appError = handleError(error, 'Registration');
      this.setState({ isLoading: false, error: appError.message });
      return { success: false, error: appError.message };
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
      logger.error('[AuthManager] Logout error', {
        component: 'AuthManager',
        action: 'logout',
        errorDetails: error
      }, error as Error);
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

      // Ensure token is set in API service
      // Token will be set in request headers when needed

      const user = await this.apiService.getCurrentUser();
      return user;
    } catch (error) {
      logger.error('[AuthManager] Get current user error', {
        component: 'AuthManager',
        action: 'get_current_user',
        errorDetails: error
      }, error as Error);
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
    const refreshToken = this.getStoredRefreshToken();

    // Validate refresh token exists and is not expired
    if (!refreshToken) {
      logger.warn('[AuthManager] No refresh token available', {
        component: 'AuthManager',
        action: 'token_refresh'
      });
      await this.handleRefreshFailure('No refresh token available');
      return false;
    }

    if (this.isTokenExpired(refreshToken)) {
      logger.warn('[AuthManager] Refresh token expired', {
        component: 'AuthManager',
        action: 'token_refresh'
      });
      await this.handleRefreshFailure('Refresh token expired');
      return false;
    }

    return await this.attemptTokenRefreshWithRetry(refreshToken);
  }

  private async attemptTokenRefreshWithRetry(refreshToken: string): Promise<boolean> {
    for (let attempt = 1; attempt <= this.maxRefreshRetries; attempt++) {
      try {
        logger.info(`[AuthManager] Token refresh attempt ${attempt}/${this.maxRefreshRetries}`, {
          component: 'AuthManager',
          action: 'token_refresh_attempt',
          metadata: { attempt, maxRetries: this.maxRefreshRetries }
        });

        const response = await this.apiService.refreshToken(refreshToken);

        if (response.accessToken) {
          // Success - reset retry count and update tokens
          this.refreshRetryCount = 0;

          this.setStoredToken(response.accessToken);
          if (response.refreshToken) {
            this.setStoredRefreshToken(response.refreshToken);
          }

          // Set new token in API service
          // Token will be set in request headers when needed

          this.setState({
            token: response.accessToken,
            refreshToken: response.refreshToken || this.state.refreshToken,
            error: null
          });

          this.scheduleTokenRefresh();
          logger.info('[AuthManager] Token refresh successful', {
            component: 'AuthManager',
            action: 'token_refresh_success'
          });
          return true;
        } else {
          throw new Error('Invalid refresh response - no access token');
        }
      } catch (error: any) {
        logger.error(`[AuthManager] Token refresh attempt ${attempt} failed`, {
          component: 'AuthManager',
          action: 'token_refresh_attempt',
          metadata: { attempt },
          errorDetails: error
        }, error);

        // Check if this is a permanent failure (401, 403)
        if (error?.response?.status === 401 || error?.response?.status === 403) {
          logger.warn('[AuthManager] Refresh token invalid - permanent failure', {
            component: 'AuthManager',
            action: 'token_refresh_permanent_failure'
          });
          await this.handleRefreshFailure('Invalid refresh token');
          return false;
        }

        // If this is the last attempt, handle failure
        if (attempt === this.maxRefreshRetries) {
          logger.error('[AuthManager] All refresh attempts failed', {
            component: 'AuthManager',
            action: 'token_refresh_all_attempts_failed',
            metadata: { maxRetries: this.maxRefreshRetries }
          });
          await this.handleRefreshFailure(`Token refresh failed after ${this.maxRefreshRetries} attempts`);
          return false;
        }

        // Wait before retrying (exponential backoff)
        const delay = this.refreshRetryDelay * Math.pow(2, attempt - 1);
        logger.info(`[AuthManager] Waiting ${delay}ms before retry`, {
          component: 'AuthManager',
          action: 'token_refresh_retry_wait',
          metadata: { delay, attempt }
        });
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    return false;
  }

  private async handleRefreshFailure(reason: string): Promise<void> {
    logger.error(`[AuthManager] Token refresh failed: ${reason}`, {
      component: 'AuthManager',
      action: 'token_refresh_failure',
      metadata: { reason }
    });

    // Clear invalid tokens
    this.clearAuth();

    // Update state to reflect unauthenticated status
    this.setState({
      isAuthenticated: false,
      user: null,
      token: null,
      refreshToken: null,
      error: 'Session expired. Please log in again.'
    });

    // Show user-friendly error message
    const appError = errorHandler.createError('TOKEN_EXPIRED', 'Your session has expired. Please log in again.');
    errorHandler.handleError(appError, 'Token Refresh');

    // Redirect to login if we're in a browser environment
    if (typeof window !== 'undefined') {
      // Small delay to ensure error message is shown
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
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
  async updateOnboarding(step: number, data: any, completed: boolean = false): Promise<boolean> {
    try {
      this.setState({ isLoading: true, error: null });

      const user = this.state.user;
      if (!user) {
        throw errorHandler.createError('UNAUTHORIZED', 'User not authenticated');
      }

      // Check if user ID is missing and try to refresh user data
      if (!user.id) {
        console.warn('[AuthManager] User ID is missing, attempting to refresh user data');
        try {
          // Try to get fresh user data from API
          const refreshedUser = await this.getCurrentUser();
          if (refreshedUser && refreshedUser.id) {
            // Update user in state with refreshed data that has ID
            this.setState({
              user: refreshedUser
            });
            console.log('[AuthManager] Successfully refreshed user data with ID:', refreshedUser.id);
          } else {
            throw errorHandler.createError('INVALID_USER', 'Could not retrieve valid user ID');
          }
        } catch (refreshError) {
          console.error('[AuthManager] Failed to refresh user data:', refreshError);
          throw errorHandler.createError('INVALID_USER', 'User ID is undefined and refresh failed');
        }
      }

      // Get the potentially updated user from state
      const currentUser = this.state.user;
      if (!currentUser || !currentUser.id) {
        throw errorHandler.createError('INVALID_USER', 'User ID is still undefined after refresh attempt');
      }

      console.log('[AuthManager] Updating onboarding:', { step, completed, userId: currentUser.id });

      const updateRequest = {
        step_number: step,
        data
      };

      const response = await this.apiService.updateOnboarding(currentUser.id, updateRequest);

      if (response && response.step_number) {
        // If onboarding is being completed, call completion endpoint
        if (completed) {
          console.log('[AuthManager] Onboarding completed - calling completion endpoint');
          try {
            // Call the completion endpoint
            const completionResponse = await this.apiService.completeOnboarding(currentUser.id);
            if (completionResponse && completionResponse.user_id) {
              // Add a small delay to ensure database write is committed
              await new Promise(resolve => setTimeout(resolve, 100));

              // Refresh user data from server with retry logic
              let userResponse = null;
              let retryCount = 0;
              const maxRetries = 3;

              while (retryCount < maxRetries && !userResponse?.onboardingCompleted) {
                userResponse = await this.apiService.getCurrentUser();
                if (userResponse?.onboardingCompleted) {
                  break;
                }
                retryCount++;
                if (retryCount < maxRetries) {
                  console.log(`[AuthManager] Retry ${retryCount}/${maxRetries} - onboarding not completed yet, waiting...`);
                  await new Promise(resolve => setTimeout(resolve, 200));
                }
              }

              if (userResponse && userResponse.onboardingCompleted) {
                this.setState({
                  user: userResponse,
                  isLoading: false,
                  error: null
                });
                console.log('[AuthManager] Refreshed user state after onboarding completion:', userResponse);
                console.log('[AuthManager] User onboarding status:', {
                  onboardingCompleted: userResponse.onboardingCompleted,
                  onboardingStep: userResponse.onboardingStep
                });
              } else {
                console.warn('[AuthManager] Onboarding completion not reflected in user data after retries');
                // Fallback to manual state update
                const updatedUser = {
                  ...currentUser,
                  onboardingCompleted: true,
                  onboardingStep: 6
                };
                this.setState({
                  user: updatedUser,
                  isLoading: false,
                  error: null
                });
              }
            }
          } catch (completionError) {
            console.error('[AuthManager] Failed to complete onboarding:', completionError);
            // Fallback to manual update
            const updatedUser = {
              ...currentUser,
              onboardingStep: step,
              onboarding_completed: completed,
              onboardingCompleted: completed // Handle both naming conventions
            };
            this.setState({
              user: updatedUser,
              isLoading: false,
              error: null
            });
          }
        } else {
          // For non-completion updates, use response data if available, otherwise update locally
          if (response.data) {
            this.setState({
              user: response.data,
              isLoading: false,
              error: null
            });
            console.log('[AuthManager] Updated user state with API response data:', response.data);
            console.log('[AuthManager] User onboarding status:', {
              onboardingCompleted: response.data.onboardingCompleted,
              onboardingStep: response.data.onboardingStep
            });
          } else {
            // Update local user state with new onboarding info
            const updatedUser = {
              ...currentUser,
              onboardingStep: step,
              onboardingCompleted: completed
            };
            this.setState({
              user: updatedUser,
              isLoading: false,
              error: null
            });
            console.log('[AuthManager] Updated user state locally:', { step, completed });
          }
        }
      } else {
        throw new Error(JSON.stringify(response.errors) || 'Failed to update onboarding');
      }

      console.log('[AuthManager] Onboarding update successful');
      showSuccess(completed ? 'Onboarding completed!' : 'Progress saved!');
      return true;
    } catch (error: any) {
      console.error('[AuthManager] Onboarding update failed:', error);
      const appError = handleError(error, 'Update Onboarding');
      this.setState({ isLoading: false, error: appError.message });
      return false;
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

    // Clear token from API service
    // Token will be cleared from request headers when needed

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

// Make AuthManager available globally in browser context
if (typeof window !== 'undefined') {
  (window as any).authManager = authManager;
  console.log('🔧 AuthManager initialized in browser context');
}

// React hook for using auth state
export function useAuth() {
  const [state, setState] = useState<AuthState>(authManager.getState());

  useEffect(() => {
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
