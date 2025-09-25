/**
 * Centralized API Configuration
 * ============================
 * Single source of truth for API base URL configuration
 * Environment-driven - no hardcoded URLs
 */

// Get API base URL from environment variables only
export const getAPIBaseURL = (): string => {
    // Check both possible environment variable names
    const envUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL;

    // If explicitly set to empty string, use relative paths (for Docker/nginx proxy)
    if (envUrl === '') {
        return '';
    }

    // If environment variable is set to a specific URL, use it
    if (envUrl) {
        return envUrl;
    }

    // Default: use relative paths (works with nginx proxy in production)
    // This ensures API calls go through the same domain as the frontend
    return '';
};

// Export the configured API base URL
export const API_BASE_URL = getAPIBaseURL();
