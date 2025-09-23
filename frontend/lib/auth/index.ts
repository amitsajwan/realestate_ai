/**
 * Authentication Module
 * ====================
 * Centralized authentication module with perfect separation
 */

// Export all types
export * from './types';

// Export main auth manager
export { AuthManager, authManager } from './manager';

// Export API
export { authAPI } from './api';

// Export interceptor
export { AuthInterceptor, authInterceptor, fetchWithAuthInterceptor } from './interceptor';

// Re-export for backward compatibility
export { authManager as default } from './manager';
