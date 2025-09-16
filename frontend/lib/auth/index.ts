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

// Re-export for backward compatibility
export { authManager as default } from './manager';
