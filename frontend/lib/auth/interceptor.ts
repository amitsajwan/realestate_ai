/**
 * Authentication Interceptor
 * =========================
 * Global HTTP interceptor that handles token expiration and automatic logout
 */

import { logger } from '../logger';
import { authManager } from './manager';

export class AuthInterceptor {
    private static instance: AuthInterceptor;
    private isLoggingOut = false;

    static getInstance(): AuthInterceptor {
        if (!AuthInterceptor.instance) {
            AuthInterceptor.instance = new AuthInterceptor();
        }
        return AuthInterceptor.instance;
    }

    /**
     * Intercept fetch responses to handle 401 authentication errors
     */
    async interceptResponse(response: Response, originalUrl?: string): Promise<Response> {
        // If we get a 401 and we're currently authenticated, the token has expired
        if (response.status === 401 && !this.isLoggingOut) {
            const currentState = authManager.getState();

            // Skip auto-logout for login/register endpoints
            const isAuthEndpoint = originalUrl && (
                originalUrl.includes('/auth/login') ||
                originalUrl.includes('/auth/register')
            );

            // Only auto-logout if we were previously authenticated and it's not an auth endpoint
            // This prevents logout loops during login attempts
            if (currentState.isAuthenticated && currentState.token && !isAuthEndpoint) {
                logger.warn('[AuthInterceptor] 401 Unauthorized detected - token expired, logging out', {
                    endpoint: originalUrl,
                    component: 'AuthInterceptor',
                    action: 'token_expiration'
                });

                await this.handleTokenExpiration();
            }
        }

        return response;
    }

    /**
     * Handle token expiration by logging out the user
     */
    private async handleTokenExpiration(): Promise<void> {
        if (this.isLoggingOut) {
            logger.debug('[AuthInterceptor] Logout already in progress, skipping');
            return;
        }

        try {
            this.isLoggingOut = true;
            logger.info('[AuthInterceptor] Handling token expiration - logging out user');

            // Log out the user
            await authManager.logout();

            // Show user notification
            if (typeof window !== 'undefined') {
                // Use a simple notification instead of importing toast to avoid circular dependencies
                this.showTokenExpiredNotification();

                // Redirect to login page if not already there
                if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
                    logger.info('[AuthInterceptor] Redirecting to login page');
                    window.location.href = '/login';
                }
            }
        } catch (error) {
            logger.error('[AuthInterceptor] Error during automatic logout', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
        } finally {
            this.isLoggingOut = false;
        }
    }

    /**
     * Show token expiration notification to user
     */
    private showTokenExpiredNotification(): void {
        // Create a simple notification without external dependencies
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 9999;
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 14px;
            max-width: 300px;
        `;
        notification.textContent = 'Your session has expired. Please log in again.';

        document.body.appendChild(notification);

        // Remove notification after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

/**
 * Enhanced fetch function that automatically handles authentication and errors
 */
export async function fetchWithAuthInterceptor(
    input: RequestInfo | URL,
    init?: RequestInit
): Promise<Response> {
    const interceptor = AuthInterceptor.getInstance();

    try {
        // Get the current auth state and add authorization header if available
        const authState = authManager.getState();
        const token = authState.token;

        // Merge the authorization header with existing headers
        const enhancedInit: RequestInit = {
            ...init,
            headers: {
                ...init?.headers,
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        };

        const response = await fetch(input, enhancedInit);

        // Intercept the response to handle 401s
        await interceptor.interceptResponse(response, typeof input === 'string' ? input : input.toString());

        return response;
    } catch (error) {
        logger.error('[AuthInterceptor] Fetch error', {
            endpoint: typeof input === 'string' ? input : input.toString(),
            component: 'AuthInterceptor',
            action: 'fetch_error'
        });
        throw error;
    }
}

// Export singleton instance
export const authInterceptor = AuthInterceptor.getInstance();
