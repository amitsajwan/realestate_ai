/**
 * Authentication Manager
 * =====================
 * Centralized authentication state management
 */

import { logger } from '../logger';
import { authAPI } from './api';
import { AuthResult, AuthState, LoginData, RegisterData, User } from './types';

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
    private refreshTimer: ReturnType<typeof setTimeout> | null = null;
    private isRefreshing = false;
    private refreshPromise: Promise<boolean> | null = null;
    private refreshRetryCount = 0;
    private maxRefreshRetries = 3;
    private refreshRetryDelay = 1000;
    private maxApiRetries = 3;
    private apiRetryDelay = 1000;

    constructor() {
        if (typeof window !== 'undefined') {
            this.init();
        }
    }

    /**
     * Retry API call with exponential backoff
     */
    private async retryApiCall<T>(
        apiCall: () => Promise<T>, 
        retries: number = this.maxApiRetries,
        baseDelay: number = this.apiRetryDelay
    ): Promise<T> {
        try {
            return await apiCall();
        } catch (error) {
            if (retries > 0) {
                const delay = baseDelay * Math.pow(2, this.maxApiRetries - retries);
                logger.warn(`API call failed, retrying in ${delay}ms. Retries left: ${retries}`, { errorDetails: error instanceof Error ? error.message : String(error) });
                await new Promise(resolve => setTimeout(resolve, delay));
                return this.retryApiCall(apiCall, retries - 1, baseDelay);
            }
            throw error;
        }
    }

    /**
     * Initialize authentication manager
     */
    async init(): Promise<void> {
        try {
            this.setState({ isLoading: true, error: null });

            // Check for stored token
            const storedToken = this.getStoredToken();
            if (storedToken) {
                try {
                    // Verify token by getting current user with retry logic
                    const userData = await this.retryApiCall(
                        () => authAPI.getCurrentUser(storedToken)
                    );
                    if (userData && (userData.id || userData.user?.id)) {
                        this.setState({
                            isAuthenticated: true,
                            user: this.transformUserData(userData),
                            token: storedToken,
                            isLoading: false,
                            error: null
                        });
                        this.scheduleTokenRefresh();
                        return;
                    }
                } catch (error) {
                    logger.warn('[AuthManager] Token validation failed, clearing auth state', { errorDetails: error instanceof Error ? error.message : String(error) });
                    this.clearStoredTokens();
                }
            }

            this.setState({ isLoading: false, error: null });
        } catch (error) {
            logger.error('[AuthManager] Init error', { errorDetails: error instanceof Error ? error.message : String(error) });
            this.setState({ isLoading: false, error: 'Authentication initialization failed' });
        }
    }

    /**
     * Register a new user
     */
    async register(userData: RegisterData): Promise<AuthResult> {
        try {
            console.log('[AuthManager] Starting registration with data:', userData);
            this.setState({ isLoading: true, error: null });

            // Step 1: Register user (FastAPI Users returns user data only)
            console.log('[AuthManager] Calling authAPI.register...');
            const userResponse = await authAPI.register({
                email: userData.email,
                password: userData.password,
                firstName: userData.firstName || '',
                lastName: userData.lastName || '',
                phone: userData.phone,
                company: userData.company
            });
            console.log('[AuthManager] Registration response:', userResponse);

            if (userResponse && userResponse.id) {
                // Step 2: Login to get access token
                const loginResponse = await authAPI.login({
                    username: userData.email,
                    password: userData.password
                });

                if (loginResponse.access_token) {
                    // Store tokens and user data
                    this.setStoredToken(loginResponse.access_token);

                    // Transform user data to expected format
                    const user = this.transformUserData(userResponse);

                    this.setState({
                        isAuthenticated: true,
                        user: user,
                        token: loginResponse.access_token,
                        refreshToken: null,
                        isLoading: false,
                        error: null
                    });

                    this.scheduleTokenRefresh();
                    return { success: true, user };
                } else {
                    throw new Error('No access token received from login');
                }
            } else {
                throw new Error('User registration failed');
            }
        } catch (error) {
            logger.error('[AuthManager] Registration failed', { errorDetails: error instanceof Error ? error.message : String(error) });
            const errorMessage = error instanceof Error ? error.message : 'Registration failed';
            this.setState({ isLoading: false, error: errorMessage });
            return { success: false, error: errorMessage };
        }
    }

    /**
     * Login user
     */
    async login(credentials: LoginData): Promise<AuthResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await authAPI.login({
                username: credentials.email,
                password: credentials.password
            });

            if (response.access_token) {
                // Get user data with retry logic
                const userData = await this.retryApiCall(
                    () => authAPI.getCurrentUser(response.access_token!)
                );

                this.setStoredToken(response.access_token);

                this.setState({
                    isAuthenticated: true,
                    user: this.transformUserData(userData),
                    token: response.access_token,
                    refreshToken: null,
                    isLoading: false,
                    error: null
                });

                this.scheduleTokenRefresh();
                return { success: true, user: this.transformUserData(userData) };
            } else {
                throw new Error('No access token received');
            }
        } catch (error) {
            logger.error('[AuthManager] Login failed', { errorDetails: error instanceof Error ? error.message : String(error) });
            const errorMessage = error instanceof Error ? error.message : 'Login failed';
            this.setState({ isLoading: false, error: errorMessage });
            return { success: false, error: errorMessage };
        }
    }

    /**
     * Logout user
     */
    async logout(): Promise<void> {
        try {
            const token = this.state.token;
            if (token) {
                await authAPI.logout(token);
            }
        } catch (error) {
            logger.warn('[AuthManager] Logout API call failed', { errorDetails: error instanceof Error ? error.message : String(error) });
        } finally {
            this.clearStoredTokens();
            this.setState({
                isAuthenticated: false,
                user: null,
                token: null,
                refreshToken: null,
                isLoading: false,
                error: null
            });
            this.clearRefreshTimer();
        }
    }

    /**
     * Check if user is authenticated
     */
    async isAuthenticated(): Promise<boolean> {
        return this.state.isAuthenticated && !!this.state.token;
    }

    /**
     * Get current auth state
     */
    getState(): AuthState {
        return { ...this.state };
    }

    /**
     * Subscribe to state changes
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
     * Update onboarding progress
     */
    async updateOnboarding(step: number, formData?: any, completed: boolean = false): Promise<AuthResult> {
        try {
            this.setState({ isLoading: true, error: null });

            // Update user data in backend
            const updateData: any = {
                onboardingStep: step,
                onboardingCompleted: completed
            };

            // Add form data if provided
            if (formData) {
                if (formData.firstName) updateData.firstName = formData.firstName;
                if (formData.lastName) updateData.lastName = formData.lastName;
                if (formData.phone) updateData.phone = formData.phone;
                if (formData.company) updateData.company = formData.company;
            }

            const currentState = this.getState();
            if (!currentState.token) {
                throw new Error('No authentication token available');
            }

            const updatedUser = await this.retryApiCall(
                () => authAPI.updateUser(updateData, currentState.token!)
            );

            if (updatedUser) {
                // Update local state
                const currentState = this.getState();
                const updatedUserData = this.transformUserData(updatedUser);

                this.setState({
                    user: updatedUserData,
                    isLoading: false,
                    error: null
                });

                return { success: true, user: updatedUserData };
            } else {
                throw new Error('Failed to update user data');
            }
        } catch (error) {
            logger.error('[AuthManager] Update onboarding error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: 'Failed to update onboarding progress'
            });
            return { success: false, error: 'Failed to update onboarding progress' };
        }
    }

    /**
     * Transform user data to expected format
     */
    private transformUserData(userData: any): User {
        // Handle both direct user data and wrapped user data
        const user = userData.user || userData;

        return {
            id: user.id,
            email: user.email,
            is_active: user.is_active,
            is_superuser: user.is_superuser,
            is_verified: user.is_verified,
            firstName: user.firstName,
            lastName: user.lastName,
            phone: user.phone,
            company: user.company,
            onboardingCompleted: user.onboardingCompleted,
            onboardingStep: user.onboardingStep,
            created_at: user.created_at,
            updated_at: user.updated_at
        };
    }

    /**
     * Set auth state and notify listeners
     */
    private setState(newState: Partial<AuthState>): void {
        this.state = { ...this.state, ...newState };
        this.listeners.forEach(listener => listener(this.state));
    }

    /**
     * Get stored token
     */
    private getStoredToken(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('auth_token');
    }

    /**
     * Set stored token
     */
    private setStoredToken(token: string): void {
        if (typeof window === 'undefined') return;
        localStorage.setItem('auth_token', token);
    }

    /**
     * Clear stored tokens
     */
    private clearStoredTokens(): void {
        if (typeof window === 'undefined') return;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_refresh_token');
    }

    /**
     * Schedule token refresh
     */
    private scheduleTokenRefresh(): void {
        this.clearRefreshTimer();
        // Token expires in 30 minutes, refresh 5 minutes before
        this.refreshTimer = setTimeout(() => {
            this.refreshToken();
        }, 25 * 60 * 1000); // 25 minutes
    }

    /**
     * Clear refresh timer
     */
    private clearRefreshTimer(): void {
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    /**
     * Refresh token
     */
    private async refreshToken(): Promise<boolean> {
        if (this.isRefreshing && this.refreshPromise) {
            return this.refreshPromise;
        }

        this.isRefreshing = true;
        this.refreshPromise = this.performTokenRefresh();

        try {
            const success = await this.refreshPromise;
            return success;
        } finally {
            this.isRefreshing = false;
            this.refreshPromise = null;
        }
    }

    /**
     * Perform token refresh
     */
    private async performTokenRefresh(): Promise<boolean> {
        try {
            const token = this.getStoredToken();
            if (!token) {
                logger.warn('[AuthManager] No token available for refresh');
                return false;
            }

            // For now, just re-validate the current token
            // In a real app, you'd call a refresh endpoint
            const userData = await authAPI.getCurrentUser(token);
            if (userData && userData.id) {
                this.setState({
                    user: this.transformUserData(userData)
                });
                this.scheduleTokenRefresh();
                return true;
            } else {
                throw new Error('Token validation failed');
            }
        } catch (error) {
            logger.error('[AuthManager] Token refresh failed', { errorDetails: error instanceof Error ? error.message : String(error) });
            this.refreshRetryCount++;

            if (this.refreshRetryCount < this.maxRefreshRetries) {
                setTimeout(() => {
                    this.refreshToken();
                }, this.refreshRetryDelay * this.refreshRetryCount);
            } else {
                this.logout();
            }
            return false;
        }
    }
}

// Export singleton instance
export const authManager = new AuthManager();
